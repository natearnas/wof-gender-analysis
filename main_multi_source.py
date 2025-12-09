from src.scraper import WoFScraper
from datetime import datetime
import os
import pandas as pd

# --- CONFIGURATION ---
# Let's try to grab one month of data from Season 39 to start
START_DATE = datetime(2021, 9, 13)
END_DATE = datetime(2021, 10, 13) 

# Source configuration: 'wordpress', 'forum', or both
SOURCES = ['wordpress', 'forum']  # Try both sources for maximum coverage

def main():
    # Initialize scraper with both sources
    scraper = WoFScraper(sources=SOURCES, delay=1.0)
    
    print("=" * 70)
    print("WHEEL OF FORTUNE DATA COLLECTION - MULTI-SOURCE")
    print("=" * 70)
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Sources: {', '.join(SOURCES)}")
    print("=" * 70)
    print()
    
    # Scrape with missing data tracking enabled
    df = scraper.batch_scrape_season(START_DATE, END_DATE, track_missing=True)
    
    if not df.empty:
        # Ensure output directory exists
        output_dir = os.path.join("data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the combined dataset with source column
        output_file = os.path.join(output_dir, "season_39_multi_source.csv")
        
        # Flatten the players list for CSV storage (store as string)
        df_export = df.copy()
        df_export['players'] = df_export['players'].apply(lambda x: str(x) if x else '[]')
        df_export.to_csv(output_file, index=False)
        
        print("\n" + "=" * 70)
        print("COLLECTION SUMMARY")
        print("=" * 70)
        print(f"Total records: {len(df)}")
        print(f"Data saved to: {output_file}")
        
        # Show data availability
        if 'data_available' in df.columns:
            available = df['data_available'].sum()
            missing = (~df['data_available']).sum()
            print("\nData Coverage:")
            print(f"  Available: {available} records")
            print(f"  Missing: {missing} records")
            
        # Show breakdown by source
        if 'source' in df.columns:
            print("\nBy Source:")
            source_counts = df['source'].value_counts()
            for source, count in source_counts.items():
                print(f"  {source}: {count} records")
        
        # Show sample of data
        print("\n" + "-" * 70)
        print("SAMPLE DATA (first 10 rows):")
        print("-" * 70)
        display_cols = ['date', 'source', 'bankrupts', 'lose_a_turns', 'data_available']
        print(df[display_cols].head(10).to_string(index=False))
        
        # Inter-observer reliability check (if we have data from both sources on same dates)
        if len(SOURCES) > 1:
            print("\n" + "-" * 70)
            print("INTER-OBSERVER RELIABILITY CHECK:")
            print("-" * 70)
            
            # Find dates where we have multiple sources
            date_counts = df[df['data_available']].groupby('date').size()
            overlap_dates = date_counts[date_counts > 1].index.tolist()
            
            if overlap_dates:
                print(f"Found {len(overlap_dates)} dates with multiple sources:")
                for date in overlap_dates[:5]:  # Show first 5
                    date_data = df[df['date'] == date]
                    print(f"\n  Date: {date}")
                    for _, row in date_data.iterrows():
                        if row['data_available']:
                            print(f"    {row['source']:12s} - B:{row['bankrupts']:2.0f}, LAT:{row['lose_a_turns']:2.0f}")
                
                if len(overlap_dates) > 5:
                    print(f"\n  ... and {len(overlap_dates) - 5} more dates with overlap")
            else:
                print("No overlapping dates found between sources.")
        
        print("\n" + "=" * 70)
        print("✓ Data collection complete!")
        print("=" * 70)
        
    else:
        print("\nWARNING: No data found. Check your dates or internet connection.")

if __name__ == "__main__":
    main()
