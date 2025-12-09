"""
Comprehensive test script to verify scraper functionality.
Tests both episode-level and player-level data extraction.
"""

from src.scraper import WoFScraper, classify_gender_from_name
from datetime import datetime
import pandas as pd

def test_single_episode():
    """Test scraping a single known episode."""
    print("=" * 60)
    print("TEST 1: Single Episode Scraping (WordPress)")
    print("=" * 60)
    
    scraper = WoFScraper(delay=0.5, sources=['wordpress'])
    
    # Test with Season 39 premiere (known to exist)
    test_date = datetime(2021, 9, 13)
    print(f"\nAttempting to scrape: {test_date.strftime('%Y-%m-%d')}")
    
    result = scraper.scrape_wordpress(test_date)
    
    if result:
        print("\n✓ SUCCESS! Episode found.")
        print(f"   Date: {result['date']}")
        print(f"   Source: {result['source']}")
        print(f"   Bankrupts: {result['bankrupts']}")
        print(f"   Lose-a-Turns: {result['lose_a_turns']}")
        print(f"   Players found: {len(result['players'])}")
        
        for i, player in enumerate(result['players'], 1):
            print(f"      {i}. {player['name']} (Position {player['position']})")
        
        print(f"   URL: {result['url']}")
        return True
    else:
        print("\n✗ FAILED: Episode not found (this may be expected if it didn't air)")
        return False

def test_batch_scraping():
    """Test batch scraping over a short date range."""
    print("\n" + "=" * 60)
    print("TEST 2: Batch Scraping (1 week, multi-source)")
    print("=" * 60)
    
    scraper = WoFScraper(delay=0.5, sources=['wordpress'])  # Use WordPress only for faster testing
    
    # Test with first week of Season 39
    start_date = datetime(2021, 9, 13)
    end_date = datetime(2021, 9, 17)
    
    print(f"\nScraping from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    df = scraper.batch_scrape_season(start_date, end_date, track_missing=True)
    
    if not df.empty:
        print(f"\n✓ SUCCESS! Found {len(df)} total records")
        print("\nData breakdown:")
        print(df['source'].value_counts().to_string())
        
        if 'data_available' in df.columns:
            available = df['data_available'].sum()
            print(f"\nData available: {available}/{len(df)}")
        
        # Check player data
        df_available = df[df['data_available']]
        if not df_available.empty:
            total_players = sum(len(players) for players in df_available['players'])
            print(f"Total players extracted: {total_players}")
            print(f"Average players per episode: {total_players/len(df_available):.1f}")
        
        return df
    else:
        print("\n✗ FAILED: No episodes found")
        return None

def test_player_normalization(episode_df):
    """Test player-level data normalization."""
    print("\n" + "=" * 60)
    print("TEST 3: Player Data Normalization")
    print("=" * 60)
    
    if episode_df is None or episode_df.empty:
        print("\n⚠ SKIPPED: No episode data available")
        return
    
    scraper = WoFScraper()
    
    # Only normalize rows with data
    df_available = episode_df[episode_df.get('data_available', True)]
    
    if df_available.empty:
        print("\n⚠ SKIPPED: No available episode data to normalize")
        return
    
    player_df = scraper.normalize_player_data(df_available)
    
    if not player_df.empty:
        print(f"\n✓ SUCCESS! Normalized to {len(player_df)} player records")
        print("\nSample player records:")
        print(player_df[['player_name', 'position', 'estimated_bankrupts_per_player', 
                        'estimated_lose_a_turns_per_player']].head())
        
        # Test gender classification
        print("\n" + "-" * 60)
        print("Testing Gender Classification:")
        print("-" * 60)
        
        for name in player_df['player_name'].head(5):
            gender = classify_gender_from_name(name)
            print(f"   {name:20s} → {gender}")
        
        print("\n⚠ WARNING: Gender classification uses a simple heuristic.")
        print("   For rigorous research, use a proper gender-name database!")
        
        return player_df
    else:
        print("\n✗ FAILED: Normalization produced empty dataset")
        return None

def test_data_saving():
    """Test saving data to CSV."""
    print("\n" + "=" * 60)
    print("TEST 4: Data Persistence")
    print("=" * 60)
    
    scraper = WoFScraper(data_dir="data/raw")
    
    # Create a small test dataset
    test_data = pd.DataFrame([
        {
            'date': '2021-09-13',
            'bankrupts': 5,
            'lose_a_turns': 2,
            'players': [
                {'name': 'Test Player 1', 'position': 1},
                {'name': 'Test Player 2', 'position': 2},
                {'name': 'Test Player 3', 'position': 3}
            ],
            'source': 'Test',
            'url': 'http://test.com'
        }
    ])
    
    try:
        output_path = scraper.save_to_csv(test_data, "test_output.csv")
        print(f"\n✓ SUCCESS! Data saved to: {output_path}")
        return True
    except Exception as e:
        print(f"\n✗ FAILED: Could not save data - {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("WHEEL OF FORTUNE SCRAPER TEST SUITE")
    print("=" * 60)
    print("\nThis will test the scraper functionality with real web requests.")
    print("Note: Tests may fail if episodes are not available or URLs have changed.")
    
    # Run all tests
    test_results = []
    
    # Test 1: Single episode
    test_results.append(("Single Episode", test_single_episode()))
    
    # Test 2: Batch scraping
    episode_df = test_batch_scraping()
    test_results.append(("Batch Scraping", episode_df is not None))
    
    # Test 3: Player normalization
    player_df = test_player_normalization(episode_df)
    test_results.append(("Player Normalization", player_df is not None))
    
    # Test 4: Data saving
    test_results.append(("Data Saving", test_data_saving()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"   {test_name:25s} {status}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The scraper is ready to use.")
    else:
        print("\n⚠ Some tests failed. Review the output above for details.")

if __name__ == "__main__":
    main()
