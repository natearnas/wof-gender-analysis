import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import ast

# --- CONFIGURATION ---
DATA_PATH = "data/processed/longitudinal_data_raw.csv" 
IMG_DIR = "."

def load_multi_season_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("Error: File not found. Wait for the scrape to finish!")
        return None

    player_rows = []
    
    for _, row in df.iterrows():
        # Handle stringified list of players
        if isinstance(row['players'], str):
            try:
                players_list = ast.literal_eval(row['players'])
                for p in players_list:
                    gender = p.get('gender', 'Unknown')
                    # Strict Filter: Only M/F
                    if gender in ['M', 'F']:
                        player_rows.append({
                            'season': row.get('season_id', 'Unknown'),
                            'date': row['date'],
                            'gender': gender,
                            'winnings': p.get('winnings', 0),
                            'bankrupts': row['bankrupts']
                        })
            except:
                continue
    return pd.DataFrame(player_rows)

def analyze_interface_impact(df):
    print("--- INTERFACE CHANGE ANALYSIS (Difference-in-Differences) ---")
    
    # 1. Define the Eras (The "Experimental Design")
    # Treatment Group (Plastic Cap): S38, S39
    # Control Group (Hands on Wheel): S36, S37, S40, S41
    target_seasons = ['S38', 'S39']
    df['is_white_thing_era'] = df['season'].isin(target_seasons)
    
    # Check if we actually have data for these seasons
    print("Seasons found in data:", sorted(df['season'].unique()))
    
    # 2. Visualize the Trend (The "Hero Graph")
    plt.figure(figsize=(12, 6))
    
    # Calculate average winnings per season per gender
    season_stats = df.groupby(['season', 'gender'])['winnings'].mean().reset_index()
    
    # Plot Trend Lines
    sns.lineplot(data=season_stats, x='season', y='winnings', hue='gender', 
                 palette={'M': 'skyblue', 'F': 'lightpink'}, marker="o", linewidth=2.5)
    
    # Highlight the "White Thing" Era
    plt.axvspan('S38', 'S39', color='gray', alpha=0.15, label='Plastic Cap Era')
    
    plt.title("Impact of Physical Interface on Winnings (S36-S41)")
    plt.ylabel("Average Winnings ($)")
    plt.xlabel("Season")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.savefig(f"{IMG_DIR}/did_analysis_trend.png")
    print(f"Saved plot: {IMG_DIR}/did_analysis_trend.png")
    
    # 3. Difference-in-Differences (DiD) Model
    # We are testing: Did the GAP change during the Cap Era?
    # Formula: Winnings ~ Gender + Era + (Gender * Era)
    print("\n[Running OLS Regression...]")
    model = smf.ols("winnings ~ C(gender) * C(is_white_thing_era)", data=df).fit()
    
    print(model.summary())
    
    # Extract the "Interaction Term" (The most important number)
    try:
        interaction_p = model.pvalues['C(gender)[T.M]:C(is_white_thing_era)[T.True]']
        print(f"\n>> INTERACTION P-VALUE: {interaction_p:.4f}")
        
        if interaction_p < 0.05:
            print(">> SIGNIFICANT RESULT: The plastic cap altered the gender dynamics of the game.")
        else:
            print(">> NULL RESULT: The plastic cap had NO statistically significant effect on the gender gap.")
    except KeyError:
        print("Error: Could not calculate interaction. Check if S38/S39 data exists.")

if __name__ == "__main__":
    df = load_multi_season_data(DATA_PATH)
    if df is not None and not df.empty:
        analyze_interface_impact(df)