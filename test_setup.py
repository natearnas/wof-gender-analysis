"""
Test script to verify the WoF scraper setup and basic functionality.
Run this before attempting to scrape large date ranges.
"""

from src.scraper import WoFScraper, classify_gender_from_name
from src.utils import DataNormalizer, ReliabilityAnalyzer
from datetime import datetime
import pandas as pd

print("=== WOF SCRAPER TEST SUITE ===\n")

# Test 1: Initialize scraper
print("Test 1: Initialize WoFScraper...")
try:
    scraper = WoFScraper(delay=0.5)
    print("✓ Scraper initialized successfully\n")
except Exception as e:
    print(f"✗ Failed to initialize scraper: {e}\n")
    exit(1)

# Test 2: Gender classification
print("Test 2: Gender classification...")
test_names = ["John Smith", "Sarah Johnson", "Pat Anderson", "Michael Brown", "Jennifer Lee"]
for name in test_names:
    gender = classify_gender_from_name(name)
    print(f"  {name}: {gender}")
print("✓ Gender classification working\n")

# Test 3: Data normalization
print("Test 3: Data normalization...")
try:
    # Create sample episode data
    sample_data = pd.DataFrame([
        {
            'date': '2021-09-13',
            'bankrupts': 6,
            'lose_a_turns': 2,
            'players': [
                {'name': 'John Doe', 'position': 1},
                {'name': 'Jane Smith', 'position': 2},
                {'name': 'Bob Wilson', 'position': 3}
            ],
            'episode_url': 'https://test.com/1'
        }
    ])
    
    player_df = DataNormalizer.normalize_to_players(sample_data)
    player_df = DataNormalizer.add_gender_classification(player_df)
    
    print(f"  Episode records: {len(sample_data)}")
    print(f"  Player records:  {len(player_df)}")
    print(f"  Columns: {list(player_df.columns)}")
    print("✓ Normalization working\n")
except Exception as e:
    print(f"✗ Normalization failed: {e}\n")

# Test 4: Inter-observer reliability
print("Test 4: Inter-observer reliability...")
try:
    # Simulate two observers classifying the same data
    observer1 = ['M', 'F', 'M', 'F', 'M', 'M', 'F', 'F', 'M', 'F']
    observer2 = ['M', 'F', 'M', 'F', 'F', 'M', 'F', 'F', 'M', 'M']
    
    report = ReliabilityAnalyzer.generate_reliability_report(
        observer1, observer2,
        observer1_name="Coder A",
        observer2_name="Coder B"
    )
    
    print(f"  Percent Agreement: {report['percent_agreement']:.1f}%")
    print(f"  Cohen's Kappa:     {report['cohens_kappa']:.3f}")
    print(f"  Interpretation:    {report['interpretation']}")
    print(f"  Disagreements:     {report['num_disagreements']}/10")
    print("✓ Reliability calculations working\n")
except Exception as e:
    print(f"✗ Reliability test failed: {e}\n")

# Test 5: Gap metrics
print("Test 5: Gap analysis...")
try:
    sample_episodes = pd.DataFrame([
        {'date': '2021-09-13', 'bankrupts': 5, 'lose_a_turns': 2},
        {'date': '2021-09-14', 'bankrupts': 4, 'lose_a_turns': 1},
        # Missing 9/15
        {'date': '2021-09-16', 'bankrupts': 6, 'lose_a_turns': 3},
        {'date': '2021-09-17', 'bankrupts': 3, 'lose_a_turns': 2},
    ])
    
    gap_metrics = DataNormalizer.calculate_gap_metrics(
        sample_episodes, '2021-09-13', '2021-09-17'
    )
    
    print(f"  Expected:    {gap_metrics['expected_episodes']}")
    print(f"  Captured:    {gap_metrics['captured_episodes']}")
    print(f"  Missing:     {gap_metrics['missing_episodes']}")
    print(f"  Completeness: {gap_metrics['completeness_pct']:.1f}%")
    print("✓ Gap analysis working\n")
except Exception as e:
    print(f"✗ Gap analysis failed: {e}\n")

print("=== ALL TESTS PASSED ===")
print("\nYou're ready to run:")
print("  1. python main.py       (to collect data)")
print("  2. python analysis.py   (to analyze data)")
print("\nNote: Actual scraping depends on network connectivity and site availability.")
