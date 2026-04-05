"""
WoFScraper: Scrapes Wheel of Fortune episode data from Andy's WoF Blog
with enhanced player name extraction, financial data, and gender inference.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import os
from typing import Dict, List, Optional
import gender_guesser.detector as gender  # <--- NEW DEPENDENCY

class WoFScraper:
    """
    Scrapes Wheel of Fortune episode data from Andy's WoF Blog (andynwof.wordpress.com).
    
    Features:
    - Batch scraping across date ranges
    - Financial extraction (Winnings)
    - Gender inference using gender_guesser
    - Robust Bankrupt/LAT tracking
    - Gap identification for missing episodes
    """
    
    WORDPRESS_URL = "https://andynwof.wordpress.com"
    FORUM_URL = "https://buyavowel.boards.net/thread"
    
    def __init__(self, delay: float = 1.0, data_dir: str = "data/raw", sources: List[str] = None):
        self.delay = delay
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize Gender Detector
        self.detector = gender.Detector()
        
        # Default to both sources
        if sources is None:
            sources = ['wordpress', 'forum']
        self.sources = sources
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WoF-Research-Bot/2.0 (Educational Research Project)'
        })
    
    # --- NEW: GENDER SENSOR ---
    def estimate_gender(self, name: str) -> str:
        """
        Uses gender_guesser to estimate gender from first name.
        Returns: 'M', 'F', or 'Unknown'
        """
        if not name:
            return 'Unknown'
        
        # Take first word, capitalize
        first_name = name.split()[0].capitalize()
        guess = self.detector.get_gender(first_name)
        
        if 'female' in guess:
            return 'F'
        if 'male' in guess:
            return 'M'
        return 'Unknown'

    # --- NEW: MONEY SENSOR ---
    def parse_winnings_and_players(self, text: str) -> List[Dict]:
        """
        Extracts player names AND their final winnings.
        Looks for patterns like: "Pat: $14,500" or "Vanna: $2,000"
        """
        # Regex: Name (Title Case) followed by colon and dollar sign
        score_pattern = r'([A-Z][a-z]+): \$([0-9,]+)'
        matches = re.findall(score_pattern, text)
        
        results = []
        for name, amount_str in matches:
            # Filter out false positives
            if name in ["Total", "Grand", "Toss", "Round", "Final", "Bonus"]:
                continue
            
            clean_amount = int(amount_str.replace(',', ''))
            
            # Enrich with Gender immediately
            results.append({
                "name": name, 
                "winnings": clean_amount,
                "gender": self.estimate_gender(name),
                # We will guess position later if needed, or assume order of appearance
                "position": len(results) + 1 
            })
            
        return results

    def batch_scrape_season(self, start_date: datetime, end_date: datetime, skip_weekends: bool = True, 
                           track_missing: bool = True) -> pd.DataFrame:
        results = []
        current_date = start_date
        total_days = (end_date - start_date).days
        
        print(f"[*] Starting scrape for {total_days} days...")
        print(f"[*] Sources: {', '.join(self.sources)}")
        print(f"[*] Missing data tracking: {'ON' if track_missing else 'OFF'}")
        print("-" * 60)
        
        while current_date <= end_date:
            if skip_weekends and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
                
            print(f"   -> {current_date.strftime('%Y-%m-%d')}:", end=" ")
            found_any = False
            
            # --- WORDPRESS STRATEGY ---
            if 'wordpress' in self.sources:
                wp_data = self.scrape_wordpress(current_date)
                if wp_data:
                    results.append(wp_data)
                    # Log winnings if found (NEW FEATURE)
                    top_win = max([p.get('winnings', 0) for p in wp_data.get('players', [])], default=0)
                    print(f"✓ WordPress (B:{wp_data['bankrupts']}, LAT:{wp_data['lose_a_turns']}, TopWin:${top_win})", end=" ")
                    found_any = True
                else:
                    print("✗ WordPress", end=" ")
            
            # --- FORUM STRATEGY ---
            if 'forum' in self.sources:
                forum_data = self.scrape_forum(current_date)
                if forum_data:
                    results.append(forum_data)
                    print(f"✓ Forum (B:{forum_data['bankrupts']})", end=" ")
                    found_any = True
                else:
                    print("✗ Forum", end=" ")
            
            if track_missing and not found_any:
                results.append(self._create_missing_data_row(current_date))
                print("⚠ MISSING", end=" ")
            
            print()
            current_date += timedelta(days=1)
            time.sleep(self.delay)
        
        print("-" * 60)
        print(f"[+] Scrape complete: {len(results)} total records")
        return pd.DataFrame(results)

    def scrape_wordpress(self, date_obj: datetime) -> Optional[Dict]:
        date_str = date_obj.strftime("%B-%d-%Y").lower()
        url = f"{self.WORDPRESS_URL}/{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/wof-recap-{date_str}/"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.find('div', class_='entry-content')
            if not content:
                return None
            
            text = content.get_text()
            
            # --- SENSORS ---
            bankrupts = len(re.findall(r'\bBANKRUPT\b', text, re.IGNORECASE))
            # UPDATED: Robust LAT Regex
            lose_a_turns = len(re.findall(r'LOSE\s?-?A\s?-?TURN|\bL\.?A\.?T\.?\b', text, re.IGNORECASE))
            
            # --- PLAYER & FINANCIAL EXTRACTION ---
            # STRATEGY 1: Try to get players WITH money (The New Way)
            players = self.parse_winnings_and_players(text)
            
            # STRATEGY 2: Fallback to your original logic if no scores found
            if not players:
                # We pass the soup/content to your existing helper
                raw_players = self._extract_player_names(soup, content)
                for p in raw_players:
                    players.append({
                        "name": p['name'],
                        "position": p.get('position', 0),
                        "winnings": 0, # Unknown
                        "gender": self.estimate_gender(p['name'])
                    })
            
            return {
                "date": date_obj.strftime("%Y-%m-%d"),
                "source": "WordPress",
                "bankrupts": bankrupts,
                "lose_a_turns": lose_a_turns,
                "players": players,
                "url": url,
                "data_available": True
            }
            
        except Exception:
            return None

    def scrape_forum(self, date_obj: datetime) -> Optional[Dict]:
        thread_id = self._estimate_thread_id(date_obj)
        for offset in range(-5, 6):
            url = f"{self.FORUM_URL}/{thread_id + offset}"
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    episode_data = self._parse_forum_page(soup, date_obj, url)
                    if episode_data:
                        return episode_data
            except Exception:
                continue
        return None
    
    def _parse_forum_page(self, soup: BeautifulSoup, target_date: datetime, url: str) -> Optional[Dict]:
        page_text = soup.get_text()
        date_patterns = [
            target_date.strftime("%B %d, %Y"),
            target_date.strftime("%m/%d/%Y"),
            target_date.strftime("%m/%d/%y"),
        ]
        if not any(pattern in page_text for pattern in date_patterns):
            return None
        
        bankrupts = len(re.findall(r'\bBANKRUPT\b', page_text, re.IGNORECASE))
        # UPDATED: Robust LAT Regex
        lose_a_turns = len(re.findall(r'LOSE\s?-?A\s?-?TURN|\bL\.?A\.?T\.?\b', page_text, re.IGNORECASE))
        
        # Extract names using your original helper
        players = self._extract_player_names(soup)
        
        # Enrich forum players with gender (no winnings logic for forum yet)
        for p in players:
            p['gender'] = self.estimate_gender(p['name'])
            p['winnings'] = 0 
            
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'source': 'Forum',
            'bankrupts': bankrupts,
            'lose_a_turns': lose_a_turns,
            'players': players,
            'url': url,
            'data_available': True
        }

    # --- YOUR ORIGINAL HELPER METHODS (Preserved) ---
    def _create_missing_data_row(self, date_obj: datetime) -> Dict:
        return {
            'date': date_obj.strftime('%Y-%m-%d'),
            'source': 'MISSING',
            'bankrupts': None,
            'lose_a_turns': None,
            'players': [],
            'url': None,
            'data_available': False
        }

    def _estimate_thread_id(self, air_date: datetime) -> int:
        season_39_start = datetime(2021, 9, 13)
        days_diff = (air_date - season_39_start).days
        estimated_thread = 4200 + (days_diff // 7) * 5
        return max(4200, estimated_thread)

    def _extract_player_names(self, soup: BeautifulSoup, content_div=None) -> List[Dict[str, str]]:
        players = []
        search_areas = [content_div] if content_div else []
        search_areas.extend(soup.find_all('div', class_=['entry-content', 'post', 'content', 'message']))
        
        for div in search_areas:
            if not div:
                continue
            text = div.get_text()
            
            # Pattern 1: "Tonight's contestants:"
            contestant_match = re.search(r'(?:tonight[\'s]*|today[\'s]*)\s+(?:contestants?|players?|competitors?):\s*([^\n\.!?]+)', text, re.IGNORECASE)
            if contestant_match:
                names = re.split(r',\s*(?:and\s+)?|\s+and\s+', contestant_match.group(1))
                for i, name in enumerate(names[:3]):
                    clean = self._clean_player_name(name)
                    if clean:
                        players.append({'name': clean, 'position': i + 1})
                if players:
                    break
            
            # Pattern 2: Position markers
            position_pattern = r'(?:Red|Yellow|Blue|\$1,?000|\$2,?000|\$3,?000):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            position_matches = re.findall(position_pattern, text)
            if position_matches and not players:
                for i, name in enumerate(position_matches[:3]):
                    clean = self._clean_player_name(name)
                    if clean:
                        players.append({'name': clean, 'position': i + 1})
                if players:
                    break
                
            # Pattern 3: Bold tags
            if not players:
                bold_tags = div.find_all(['b', 'strong'])
                for i, tag in enumerate(bold_tags[:3]):
                    clean = self._clean_player_name(tag.get_text())
                    if clean and len(clean.split()) <= 3:
                        players.append({'name': clean, 'position': i + 1})
                        
        return players[:3] if players else []

    def _clean_player_name(self, name: str) -> Optional[str]:
        if not name:
            return None
        name = re.sub(r'\s+', ' ', name.strip())
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'from\s+.*$', '', name, flags=re.IGNORECASE)
        name = name.strip()
        if len(name) < 2 or len(name) > 50:
            return None
        if not re.search(r'[A-Za-z]', name):
            return None
        if name.isupper() and len(name) > 4:
            name = name.title()
        return name