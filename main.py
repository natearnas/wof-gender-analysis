from src.scraper import WoFScraper
from datetime import datetime
import pandas as pd
import os

# --- CONFIGURATION ---
# EXPERIMENTAL DESIGN (2-2-2 Balanced Block):
# Baseline (Hands on Wheel): S36, S37
# Variable (Plastic Cap):    S38, S39
# Recovery (Hands on Wheel): S40, S41
SEASONS = [
    {"name": "S36", "start": datetime(2018, 9, 10), "end": datetime(2019, 6, 7)},
    {"name": "S37", "start": datetime(2019, 9, 9),  "end": datetime(2020, 6, 5)},
    {"name": "S38", "start": datetime(2020, 9, 14), "end": datetime(2021, 6, 11)}, # Cap Introduced
    {"name": "S39", "start": datetime(2021, 9, 13), "end": datetime(2022, 6, 10)}, # Cap Continued
    {"name": "S40", "start": datetime(2022, 9, 12), "end": datetime(2023, 6, 9)}, # Cap Removed
    {"name": "S41", "start": datetime(2023, 9, 11), "end": datetime(2024, 6, 7)}, # Pat's Final Season
]

def main():
    scraper = WoFScraper()
    all_season_data = []

    print(f"--- Starting Longitudinal Study ({len(SEASONS)} Seasons) ---")

    for season in SEASONS:
        print(f"\n>> PROCESSING {season['name']} ({season['start'].date()} to {season['end'].date()})")

        checkpoint_dir = os.path.join("data", "processed")
        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_path = os.path.join(checkpoint_dir, f"{season['name']}_raw.csv")

        # Skip seasons we've already scraped (resume-friendly)
        if os.path.exists(checkpoint_path):
            print(f"   [skip] {season['name']} already exists at {checkpoint_path}")
            # Load for master merge
            try:
                existing_df = pd.read_csv(checkpoint_path)
                existing_df['season_id'] = season['name']
                all_season_data.append(existing_df)
            except Exception as e:
                print(f"   [warn] Could not load existing checkpoint: {e}")
            continue
        
        # Scrape the specific date range
        df = scraper.batch_scrape_season(season['start'], season['end'])
        
        if not df.empty:
            # Tag the data with the season name (Crucial for the DiD Analysis)
            df['season_id'] = season['name']
            all_season_data.append(df)
            
            # Save individual checkpoints (safety first!)
            df.to_csv(checkpoint_path, index=False)
            print(f"   [Saved Checkpoint]: {checkpoint_path}")
        else:
            print(f"   [!] Warning: No data found for {season['name']}")

    # Combine everything into one Master Dataset
    if all_season_data:
        master_df = pd.concat(all_season_data, ignore_index=True)
        master_path = os.path.join("data", "processed", "longitudinal_data_raw.csv")
        master_df.to_csv(master_path, index=False)
        
        print("\n" + "="*50)
        print(f"LONGITUDINAL SCRAPE COMPLETE")
        print(f"Total Episodes Collected: {len(master_df)}")
        print(f"Master File: {master_path}")
        print("="*50)
    else:
        print("\n[!] Critical Failure: No data collected from any season.")

if __name__ == "__main__":
    main()