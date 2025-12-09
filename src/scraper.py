"""
WoFScraper: Scrapes Wheel of Fortune episode data from Andy's WoF Blog
with enhanced player name extraction and data normalization capabilities.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import os
from typing import Dict, List, Optional


class WoFScraper:
    """
    Scrapes Wheel of Fortune episode data from Andy's WoF Blog (andynwof.wordpress.com).
    
    Features:
    - Batch scraping across date ranges using predictable URL structure
    - Player name extraction from episode recaps
    - Bankrupt and Lose-a-Turn frequency tracking
    - Data normalization (per-player statistics)
    - Gap identification for missing episodes
    """
    
    WORDPRESS_URL = "https://andynwof.wordpress.com"
    FORUM_URL = "https://buyavowel.boards.net/thread"
    
    def __init__(self, delay: float = 1.0, data_dir: str = "data/raw", sources: List[str] = None):
        """
        Initialize the scraper.
        
        Args:
            delay: Seconds to wait between requests (be respectful to the server)
            data_dir: Directory to store raw data files
            sources: List of sources to scrape. Options: ['wordpress', 'forum', 'both']
                     Default is ['wordpress', 'forum'] for maximum data coverage
        """
        self.delay = delay
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Default to both sources for inter-observer reliability
        if sources is None:
            sources = ['wordpress', 'forum']
        self.sources = sources
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WoF-Research-Bot/1.0 (Educational Research Project)'
        })
    
    
    def batch_scrape_season(self, start_date: datetime, end_date: datetime, skip_weekends: bool = True, 
                           track_missing: bool = True) -> pd.DataFrame:
        """
        Scrape multiple episodes across a date range from all configured sources.
        
        Args:
            start_date: First episode date
            end_date: Last episode date
            skip_weekends: If True, skip Saturday and Sunday (WoF typically airs Mon-Fri)
            track_missing: If True, create rows for dates with no data found (for gap analysis)
            
        Returns:
            DataFrame with columns: date, source, bankrupts, lose_a_turns, players, url, data_available
        """
        results = []
        current_date = start_date
        total_days = (end_date - start_date).days
        
        print(f"[*] Starting scrape for {total_days} days...")
        print(f"[*] Sources: {', '.join(self.sources)}")
        print(f"[*] Missing data tracking: {'ON' if track_missing else 'OFF'}")
        print("-" * 60)
        
        while current_date <= end_date:
            # Skip weekends if requested (WoF typically airs Monday-Friday)
            if skip_weekends and current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
                continue
                
            print(f"   -> {current_date.strftime('%Y-%m-%d')}:", end=" ")
            
            # Try each source for this date
            found_any = False
            
            if 'wordpress' in self.sources:
                wp_data = self.scrape_wordpress(current_date)
                if wp_data:
                    results.append(wp_data)
                    print(f"✓ WordPress (B:{wp_data['bankrupts']}, LAT:{wp_data['lose_a_turns']}, P:{len(wp_data.get('players', []))})", end=" ")
                    found_any = True
                else:
                    print("✗ WordPress", end=" ")
            
            if 'forum' in self.sources:
                forum_data = self.scrape_forum(current_date)
                if forum_data:
                    results.append(forum_data)
                    print(f"✓ Forum (B:{forum_data['bankrupts']}, LAT:{forum_data['lose_a_turns']}, P:{len(forum_data.get('players', []))})", end=" ")
                    found_any = True
                else:
                    print("✗ Forum", end=" ")
            
            # Track missing data if requested
            if track_missing and not found_any:
                results.append(self._create_missing_data_row(current_date))
                print("⚠ MISSING DATA RECORDED", end=" ")
            
            print()  # New line
            current_date += timedelta(days=1)
            time.sleep(self.delay)  # Be nice to the server
        
        print("-" * 60)
        print(f"[+] Scrape complete: {len(results)} total records")
        
        df = pd.DataFrame(results)
        
        if not df.empty:
            # Count data availability by source
            print("\n[*] Data Summary:")
            if 'source' in df.columns:
                print(df['source'].value_counts().to_string())
            if 'data_available' in df.columns:
                available = df['data_available'].sum()
                missing = (~df['data_available']).sum()
                total = len(df)
                print(f"\nAvailable: {available} ({available/total*100:.1f}%)")
                print(f"Missing: {missing} ({missing/total*100:.1f}%)")
        
        return df
    
    
    def _create_missing_data_row(self, date_obj: datetime) -> Dict:
        """
        Create a row indicating missing data for a specific date.
        
        Args:
            date_obj: Date for which data is missing
            
        Returns:
            Dictionary with missing data indicators
        """
        return {
            'date': date_obj.strftime('%Y-%m-%d'),
            'source': 'MISSING',
            'bankrupts': None,
            'lose_a_turns': None,
            'players': [],
            'url': None,
            'data_available': False
        }
    
    def scrape_wordpress(self, date_obj: datetime) -> Optional[Dict]:
        """
        Scrapes Andy's WordPress Blog for a specific date.
        
        Andy's Blog uses predictable URLs:
        https://andynwof.wordpress.com/YYYY/MM/DD/wof-recap-month-day-year/
        
        Args:
            date_obj: Episode air date
            
        Returns:
            Dictionary with episode data or None if not found
        """
        # Format date for URL: "wof-recap-september-13-2021"
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
            
            # Count occurrences of specific event strings (case-insensitive)
            bankrupts = len(re.findall(r'\bBANKRUPT\b', text, re.IGNORECASE))
            lose_a_turns = len(re.findall(r'\bLOSE\s+A\s+TURN\b', text, re.IGNORECASE))
            
            # Extract player names
            players = self._extract_player_names(soup, content)
            
            return {
                "date": date_obj.strftime("%Y-%m-%d"),
                "source": "WordPress",
                "bankrupts": bankrupts,
                "lose_a_turns": lose_a_turns,
                "players": players,
                "url": url,
                "data_available": True
            }
            
        except requests.RequestException:
            # Network error - don't print, just return None
            return None
        except Exception:
            # Unexpected error - don't print, just return None
            return None
    
    def scrape_forum(self, date_obj: datetime) -> Optional[Dict]:
        """
        Scrapes buyavowel.boards.net forum for a specific date.
        
        This uses thread ID estimation since the forum doesn't have date-based URLs.
        Less reliable than WordPress but provides a second source for comparison.
        
        Args:
            date_obj: Episode air date
            
        Returns:
            Dictionary with episode data or None if not found
        """
        thread_id = self._estimate_thread_id(date_obj)
        
        # Search nearby thread IDs (smaller range for performance)
        for offset in range(-5, 6):
            url = f"{self.FORUM_URL}/{thread_id + offset}"
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Check if this episode matches our target date
                    episode_data = self._parse_forum_page(soup, date_obj, url)
                    
                    if episode_data:
                        return episode_data
                        
            except requests.RequestException:
                continue
            except Exception:
                continue
        
        return None
    
    def _estimate_thread_id(self, air_date: datetime) -> int:
        """
        Estimate the forum thread ID based on air date.
        
        Season 39 starts around thread 4200 (Sept 2021).
        This is a heuristic and may need adjustment for different seasons.
        """
        season_39_start = datetime(2021, 9, 13)
        days_diff = (air_date - season_39_start).days
        
        # Approximate: ~5 episodes per week, 1 thread per episode
        estimated_thread = 4200 + (days_diff // 7) * 5
        
        return max(4200, estimated_thread)
    
    def _parse_forum_page(self, soup: BeautifulSoup, target_date: datetime, url: str) -> Optional[Dict]:
        """
        Parse a forum page to extract relevant data.
        
        Args:
            soup: BeautifulSoup object of the page
            target_date: Date we're looking for
            url: URL of the page
            
        Returns:
            Dictionary with episode data or None if not matching
        """
        page_text = soup.get_text()
        
        # Common date formats on the forum
        date_patterns = [
            target_date.strftime("%B %d, %Y"),   # "September 13, 2021"
            target_date.strftime("%m/%d/%Y"),     # "09/13/2021"
            target_date.strftime("%m/%d/%y"),     # "09/13/21"
        ]
        
        date_found = any(pattern in page_text for pattern in date_patterns)
        
        if not date_found:
            return None
        
        # Extract bankrupts and lose-a-turns
        bankrupts = len(re.findall(r'\bBANKRUPT\b', page_text, re.IGNORECASE))
        lose_a_turns = len(re.findall(r'\bLOSE\s+A\s+TURN\b', page_text, re.IGNORECASE))
        
        # Extract player names
        players = self._extract_player_names(soup)
        
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'source': 'Forum',
            'bankrupts': bankrupts,
            'lose_a_turns': lose_a_turns,
            'players': players,
            'url': url,
            'data_available': True
        }
    
    def scrape_andy_recap(self, date_obj: datetime) -> Optional[Dict]:
        """
        DEPRECATED: Use scrape_wordpress() instead.
        Kept for backward compatibility.
        """
        return self.scrape_wordpress(date_obj)
    
    
    def _extract_player_names(self, soup: BeautifulSoup, content_div=None) -> List[Dict[str, str]]:
        """
        Extract player names from the episode recap.
        
        WoF typically has 3 players per episode. Andy's Blog usually lists them
        at the beginning of the recap in various formats.
        
        Args:
            soup: BeautifulSoup object of the page
            content_div: Optional specific content div to search (for efficiency)
            
        Returns:
            List of player dictionaries with 'name' and 'position' keys
        """
        players = []
        
        # Use provided content div or search for common content areas
        search_areas = [content_div] if content_div else []
        search_areas.extend(soup.find_all('div', class_=['entry-content', 'post', 'content', 'message']))
        
        for div in search_areas:
            if not div:
                continue
                
            text = div.get_text()
            
            # Pattern 1: "Tonight's contestants:" or "Players:" or similar
            contestant_match = re.search(
                r'(?:tonight[\'s]*|today[\'s]*)\s+(?:contestants?|players?|competitors?):\s*([^\n\.!?]+)',
                text,
                re.IGNORECASE
            )
            
            if contestant_match:
                player_text = contestant_match.group(1)
                # Split by commas and 'and'
                names = re.split(r',\s*(?:and\s+)?|\s+and\s+', player_text)
                
                for i, name in enumerate(names[:3]):  # Max 3 players
                    clean_name = self._clean_player_name(name)
                    if clean_name:
                        players.append({
                            'name': clean_name,
                            'position': i + 1  # 1, 2, or 3
                        })
                
                if players:
                    break
            
            # Pattern 2: Look for position markers "Red:", "Yellow:", "Blue:" or "$1000:", "$2000:", "$3000:"
            # Sometimes Andy uses colored positions or dollar amounts
            position_pattern = r'(?:Red|Yellow|Blue|\$1,?000|\$2,?000|\$3,?000):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            position_matches = re.findall(position_pattern, text)
            
            if position_matches and not players:
                position_counter = 1
                for name in position_matches:
                    clean_name = self._clean_player_name(name)
                    if clean_name and position_counter <= 3:
                        players.append({
                            'name': clean_name,
                            'position': position_counter
                        })
                        position_counter += 1
                        
                if players:
                    break
            
            # Pattern 3: Look for bolded names at the start (Andy often bolds player names)
            if not players:
                bold_tags = div.find_all(['b', 'strong'])
                for i, tag in enumerate(bold_tags[:3]):
                    potential_name = tag.get_text().strip()
                    clean_name = self._clean_player_name(potential_name)
                    if clean_name and len(clean_name.split()) <= 3:  # Reasonable name length
                        players.append({
                            'name': clean_name,
                            'position': i + 1
                        })
        
        # Return up to 3 players (standard WoF format)
        return players[:3] if players else []
    
    def _clean_player_name(self, name: str) -> Optional[str]:
        """
        Clean and validate a player name string.
        
        Args:
            name: Raw name string
            
        Returns:
            Cleaned name or None if invalid
        """
        if not name:
            return None
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Remove common suffixes/prefixes that aren't part of names
        name = re.sub(r'\(.*?\)', '', name)  # Remove parentheses
        name = re.sub(r'from\s+.*$', '', name, flags=re.IGNORECASE)  # Remove "from Location"
        name = name.strip()
        
        # Sanity checks
        if len(name) < 2 or len(name) > 50:
            return None
        
        # Should contain at least one letter
        if not re.search(r'[A-Za-z]', name):
            return None
        
        # Should not be all uppercase (unless it's an acronym, which is unlikely for names)
        if name.isupper() and len(name) > 4:
            name = name.title()
        
        return name
    
    
    def normalize_player_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize episode-level data to player-level data.
        
        This expands each episode into individual rows (one per player) and calculates
        per-player statistics. Since we don't know which player hit which Bankrupt/LAT,
        we distribute them evenly as estimates.
        
        Args:
            df: DataFrame with episode-level data (must have 'players' column)
            
        Returns:
            DataFrame with player-level data including normalized frequencies
        """
        player_rows = []
        
        for _, episode in df.iterrows():
            players = episode.get('players', [])
            
            if not players or len(players) == 0:
                # Episode has no player data - skip or create placeholder
                continue
            
            num_players = len(players)
            
            # Distribute bankrupts and lose-a-turns across players
            # NOTE: This is an ESTIMATE since we don't have spin-level data
            avg_bankrupts = episode['bankrupts'] / num_players if num_players > 0 else 0
            avg_lose_a_turns = episode['lose_a_turns'] / num_players if num_players > 0 else 0
            
            for player in players:
                player_rows.append({
                    'date': episode['date'],
                    'player_name': player['name'],
                    'position': player['position'],
                    'episode_bankrupts': episode['bankrupts'],
                    'episode_lose_a_turns': episode['lose_a_turns'],
                    'estimated_bankrupts_per_player': avg_bankrupts,
                    'estimated_lose_a_turns_per_player': avg_lose_a_turns,
                    'source': episode.get('source', 'Unknown'),
                    'url': episode.get('url', '')
                })
        
        return pd.DataFrame(player_rows)
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """
        Save DataFrame to CSV in the data directory.
        
        Args:
            df: DataFrame to save
            filename: Name of the output file (without path)
            
        Returns:
            Full path to the saved file
        """
        output_path = os.path.join(self.data_dir, filename)
        df.to_csv(output_path, index=False)
        return output_path


# Utility function for gender classification
def classify_gender_from_name(name: str) -> str:
    """
    Simple gender classification based on common first names.
    
    This is a placeholder - for rigorous research, you should use:
    1. A gender-name database (e.g., US SSA baby names)
    2. Manual verification
    3. Multiple coders for inter-rater reliability
    
    Args:
        name: Player's first name
        
    Returns:
        'M', 'F', or 'Unknown'
    """
    # Extract first name
    first_name = name.split()[0].lower() if name else ""
    
    # Very basic heuristic lists (NOT comprehensive - use a proper database!)
    male_names = {'john', 'michael', 'david', 'james', 'robert', 'william', 'richard', 
                  'thomas', 'charles', 'daniel', 'matthew', 'mark', 'paul', 'steven'}
    
    female_names = {'mary', 'patricia', 'jennifer', 'linda', 'barbara', 'elizabeth',
                    'susan', 'jessica', 'sarah', 'karen', 'nancy', 'lisa', 'betty',
                    'dorothy', 'sandra', 'ashley', 'emily', 'amanda', 'melissa'}
    
    if first_name in male_names:
        return 'M'
    elif first_name in female_names:
        return 'F'
    else:
        return 'Unknown'
