from src.scraper import WoFScraper
from datetime import datetime
import os

# --- CONFIGURATION ---
# Let's try to grab one month of data from Season 39 to start
START_DATE = datetime(2021, 9, 13)
END_DATE = datetime(2021, 10, 13) 

def main():
    scraper = WoFScraper()
    
    print("--- Starting Data Collection Experiment ---")
    df = scraper.batch_scrape_season(START_DATE, END_DATE)
    
    if not df.empty:
        # Save the raw dataset
        output_file = os.path.join("data", "processed", "season_39_sample.csv")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        df.to_csv(output_file, index=False)
        print(f"\nSUCCESS: Collected {len(df)} episodes.")
        print(f"Data saved to: {output_file}")
        print("\nFirst 5 rows:")
        print(df.head())
    else:
        print("\nWARNING: No data found. Check your dates or internet connection.")

if __name__ == "__main__":
    main()