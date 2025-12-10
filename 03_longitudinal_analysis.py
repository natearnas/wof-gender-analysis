import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import ast

# --- CONFIGURATION ---
# Point this to your new multi-season file
DATA_PATH = "data/processed/longitudinal_data_raw.csv" 

def load_multi_season_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("Error: File not found. Did you run the 5-season scrape?")
        return None

    player_rows = []
    
    for _, row in df.iterrows():
        if isinstance(row['players'], str):
            try:
                players_list = ast.literal_eval(row['players'])
                for p in players_list:
                    gender = p.get('gender', 'Unknown')
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
    print("--- INTERFACE CHANGE ANALYSIS (The 'White Thing' Test) ---")
    
    # 1. Define the Eras
    # Control: S35, S36, S37, S39 (Normal Wheel)
    # Treatment: S38 (The "White Thing" / Plastic Cap)
    df['is_white_thing_era'] = df['season'] == 'S38'
    
    # 2. Visualize the Trend
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x='season', y='winnings', hue='gender', 
                 palette={'M': 'skyblue', 'F': 'lightpink'}, marker="o")
    plt.title("Gender Winnings Gap Across Seasons\n(Did S38 change the trend?)")
    plt.axvline('S38', color='red', linestyle='--', label='White Thing Era')
    plt.legend()
    plt.savefig("longitudinal_trend.png")
    print("Saved plot: longitudinal_trend.png")
    
    # 3. Difference-in-Differences (DiD) Model
    # Formula: Winnings ~ Gender + Era + (Gender * Era)
    # The "Interaction Term" (Gender * Era) tells us if the ERA changed the GAP.
    model = smf.ols("winnings ~ C(gender) * C(is_white_thing_era)", data=df).fit()
    
    print("\n--- STATISTICAL MODEL RESULTS ---")
    print(model.summary())
    
    # Extract the key insight
    interaction_p_value = model.pvalues['C(gender)[T.M]:C(is_white_thing_era)[T.True]']
    print(f"\nInteraction P-Value: {interaction_p_value:.4f}")
    
    if interaction_p_value < 0.05:
        print(">> RESULT: SIGNIFICANT. The interface change affected Men and Women differently.")
    else:
        print(">> RESULT: NOT SIGNIFICANT. The interface change did not alter the gender gap.")

if __name__ == "__main__":
    df = load_multi_season_data(DATA_PATH)
    if df is not None and not df.empty:
        analyze_interface_impact(df)