"""
Data normalization and statistical utilities for Wheel of Fortune gender analysis.
Focuses on per-player statistics and inter-observer reliability metrics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class DataNormalizer:
    """
    Normalizes episode-level data to player-level statistics.
    Handles missing data and calculates frequencies per spin/player.
    """
    
    @staticmethod
    def normalize_to_players(episode_df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert episode-level data to player-level normalized data.
        
        Args:
            episode_df: DataFrame with columns: date, bankrupts, lose_a_turns, players
            
        Returns:
            Player-level DataFrame with normalized frequencies
        """
        player_records = []
        
        for _, row in episode_df.iterrows():
            players = row.get('players', [])
            
            if not isinstance(players, list) or len(players) == 0:
                continue
            
            # Typical WoF episode has ~60-70 spins total
            # Assume equal distribution across 3 players (~20 spins each)
            estimated_spins_per_player = 20
            
            for player in players:
                player_records.append({
                    'date': row['date'],
                    'episode_url': row.get('url', row.get('episode_url', '')),
                    'player_name': player.get('name', 'Unknown'),
                    'position': player.get('position', 0),
                    'winnings': player.get('winnings', 0),
                    'gender': player.get('gender', 'Unknown'),
                    'episode_bankrupts': row.get('bankrupts', 0),
                    'episode_lose_a_turns': row.get('lose_a_turns', 0),
                    'estimated_spins': estimated_spins_per_player,
                })
        
        player_df = pd.DataFrame(player_records)
        
        # Calculate per-player frequencies (assuming equal distribution)
        player_df['bankrupts_per_player'] = player_df['episode_bankrupts'] / 3
        player_df['lose_a_turns_per_player'] = player_df['episode_lose_a_turns'] / 3
        
        # Normalize to per-spin rates
        player_df['bankrupt_rate'] = player_df['bankrupts_per_player'] / player_df['estimated_spins']
        player_df['lose_a_turn_rate'] = player_df['lose_a_turns_per_player'] / player_df['estimated_spins']
        
        return player_df
    
    @staticmethod
    def add_gender_classification(player_df: pd.DataFrame, gender_map: Dict[str, str] = None) -> pd.DataFrame:
        """
        Add/fill gender classification to player data.

        If a gender column already exists, only fill missing/Unknown values.
        Otherwise, classify all players using WoFScraper's estimator or an
        optional provided gender_map.
        """
        from src.scraper import WoFScraper

        scraper = WoFScraper(sources=['wordpress'])

        def classify(name: str) -> str:
            if gender_map and name in gender_map:
                return gender_map[name]
            return scraper.estimate_gender(name)

        if 'gender' in player_df.columns:
            mask = player_df['gender'].isna() | (player_df['gender'].str.lower() == 'unknown')
            player_df.loc[mask, 'gender'] = player_df.loc[mask, 'player_name'].apply(classify)
        else:
            player_df['gender'] = player_df['player_name'].apply(classify)

        return player_df
    
    @staticmethod
    def calculate_gap_metrics(episode_df: pd.DataFrame, 
                              start_date: str, 
                              end_date: str) -> Dict:
        """
        Calculate data integrity metrics (missing episodes, gaps).
        
        Args:
            episode_df: Episode-level DataFrame with 'date' column
            start_date: Expected start date (YYYY-MM-DD)
            end_date: Expected end date (YYYY-MM-DD)
            
        Returns:
            Dictionary with gap analysis metrics
        """
        episode_df['date'] = pd.to_datetime(episode_df['date'])
        
        # Generate ideal business day range (Mon-Fri)
        ideal_range = pd.bdate_range(start=start_date, end=end_date)
        ideal_df = pd.DataFrame({'date': ideal_range})
        
        # Find missing episodes
        merged = pd.merge(ideal_df, episode_df, on='date', how='left', indicator=True)
        missing_episodes = merged[merged['_merge'] == 'left_only']
        
        return {
            'expected_episodes': len(ideal_df),
            'captured_episodes': len(episode_df),
            'missing_episodes': len(missing_episodes),
            'completeness_pct': (len(episode_df) / len(ideal_df)) * 100 if len(ideal_df) > 0 else 0,
            'missing_dates': missing_episodes['date'].dt.strftime('%Y-%m-%d').tolist()
        }


class ReliabilityAnalyzer:
    """
    Calculate inter-observer reliability metrics for data validation.
    Useful for blog post discussing experimental rigor.
    """
    
    @staticmethod
    def calculate_cohens_kappa(observer1: List, observer2: List) -> float:
        """
        Calculate Cohen's Kappa for inter-rater reliability.
        
        Args:
            observer1: First observer's classifications
            observer2: Second observer's classifications
            
        Returns:
            Cohen's Kappa coefficient (-1 to 1)
        """
        if len(observer1) != len(observer2):
            raise ValueError("Observer arrays must be same length")
        
        # Convert to numpy arrays
        obs1 = np.array(observer1)
        obs2 = np.array(observer2)
        
        # Calculate observed agreement
        p_o = np.mean(obs1 == obs2)
        
        # Calculate expected agreement by chance
        categories = set(obs1) | set(obs2)
        p_e = 0
        
        for cat in categories:
            p1 = np.mean(obs1 == cat)
            p2 = np.mean(obs2 == cat)
            p_e += p1 * p2
        
        # Cohen's Kappa
        if p_e == 1:
            return 1.0
        
        kappa = (p_o - p_e) / (1 - p_e)
        return kappa
    
    @staticmethod
    def calculate_percent_agreement(observer1: List, observer2: List) -> float:
        """
        Calculate simple percent agreement between two observers.
        
        Args:
            observer1: First observer's classifications
            observer2: Second observer's classifications
            
        Returns:
            Percentage agreement (0-100)
        """
        if len(observer1) != len(observer2):
            raise ValueError("Observer arrays must be same length")
        
        agreements = sum(o1 == o2 for o1, o2 in zip(observer1, observer2))
        return (agreements / len(observer1)) * 100
    
    @staticmethod
    def generate_reliability_report(observer1: List, observer2: List, 
                                    observer1_name: str = "Observer 1",
                                    observer2_name: str = "Observer 2") -> Dict:
        """
        Generate a comprehensive reliability report.
        
        Args:
            observer1: First observer's data
            observer2: Second observer's data
            observer1_name: Name/ID of first observer
            observer2_name: Name/ID of second observer
            
        Returns:
            Dictionary with reliability metrics
        """
        kappa = ReliabilityAnalyzer.calculate_cohens_kappa(observer1, observer2)
        agreement = ReliabilityAnalyzer.calculate_percent_agreement(observer1, observer2)
        
        # Count disagreements by category
        disagreements = []
        for i, (o1, o2) in enumerate(zip(observer1, observer2)):
            if o1 != o2:
                disagreements.append({
                    'index': i,
                    observer1_name: o1,
                    observer2_name: o2
                })
        
        return {
            'cohens_kappa': kappa,
            'percent_agreement': agreement,
            'total_observations': len(observer1),
            'disagreements': disagreements,
            'num_disagreements': len(disagreements),
            'interpretation': ReliabilityAnalyzer._interpret_kappa(kappa)
        }
    
    @staticmethod
    def _interpret_kappa(kappa: float) -> str:
        """
        Interpret Cohen's Kappa according to Landis & Koch (1977).
        """
        if kappa < 0:
            return "Poor (Less than chance agreement)"
        elif kappa < 0.20:
            return "Slight"
        elif kappa < 0.40:
            return "Fair"
        elif kappa < 0.60:
            return "Moderate"
        elif kappa < 0.80:
            return "Substantial"
        else:
            return "Almost Perfect"


class StatisticalAnalyzer:
    """
    Perform statistical tests for gender-based variance analysis.
    """
    
    @staticmethod
    def test_gender_variance(player_df: pd.DataFrame, metric: str = 'bankrupt_rate') -> Dict:
        """
        Test for significant gender-based variance in a metric.
        
        Args:
            player_df: Player-level DataFrame with 'gender' and metric columns
            metric: Column name to test (e.g., 'bankrupt_rate', 'lose_a_turn_rate')
            
        Returns:
            Dictionary with test results
        """
        try:
            from scipy import stats
        except ImportError:
            return {
                'error': "scipy not installed",
                'message': "Install scipy to run statistical tests (pip install scipy)",
            }
        
        # Filter to only M and F (exclude Unknown)
        df_filtered = player_df[player_df['gender'].isin(['M', 'F'])].copy()
        
        male_data = df_filtered[df_filtered['gender'] == 'M'][metric].dropna()
        female_data = df_filtered[df_filtered['gender'] == 'F'][metric].dropna()
        
        if len(male_data) == 0 or len(female_data) == 0:
            return {
                'error': 'Insufficient data for comparison',
                'male_n': len(male_data),
                'female_n': len(female_data)
            }
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(male_data, female_data)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((male_data.std()**2 + female_data.std()**2) / 2)
        cohens_d = (male_data.mean() - female_data.mean()) / pooled_std if pooled_std > 0 else 0
        
        return {
            'metric': metric,
            'male_mean': male_data.mean(),
            'male_std': male_data.std(),
            'male_n': len(male_data),
            'female_mean': female_data.mean(),
            'female_std': female_data.std(),
            'female_n': len(female_data),
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'significant': p_value < 0.05,
            'interpretation': StatisticalAnalyzer._interpret_effect_size(cohens_d)
        }
    
    @staticmethod
    def _interpret_effect_size(cohens_d: float) -> str:
        """
        Interpret Cohen's d effect size according to Cohen (1988).
        """
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "Negligible"
        elif abs_d < 0.5:
            return "Small"
        elif abs_d < 0.8:
            return "Medium"
        else:
            return "Large"
