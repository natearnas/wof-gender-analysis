import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast
from scipy import stats

def load_and_clean_data(file_path):
    """
    Loads raw data and explodes it into a clean, flat format.
    STRICTLY removes any players with 'Unknown' gender.
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print("Error: Run main.py first to generate the data.")
        return None

    player_rows = []
    
    for _, row in df.iterrows():
        # Parse the stringified list of players
        if isinstance(row['players'], str):
            try:
                players_list = ast.literal_eval(row['players'])
            except:
                continue 
                
            for p in players_list:
                # --- THE FILTER ---
                # We strictly only keep M or F. 
                # "Unknown", "Andy", or "Mostly" are discarded to ensure high rigor.
                gender = p.get('gender', 'Unknown')
                if gender not in ['M', 'F']:
                    continue
                    
                player_rows.append({
                    'date': row['date'],
                    'name': p.get('name'),
                    'gender': gender,
                    'winnings': p.get('winnings', 0),
                    # We use episode totals as a proxy for the environment risk
                    'episode_bankrupts': row['bankrupts'],
                    'episode_lats': row['lose_a_turns']
                })

    return pd.DataFrame(player_rows)

def run_analysis():
    # 1. Load Data
    print("--- 1. LOADING & FILTERING ---")
    df = load_and_clean_data("data/processed/season_39_sample.csv")
    
    if df is None or df.empty:
        print("No valid M/F data found yet.")
        return

    # Basic Counts
    print(f"Total Confirmed Players: {len(df)}")
    print(df['gender'].value_counts())
    
    # 2. STATISTICAL ANALYSIS (The "Meat" of the post)
    print("\n--- 2. WINNINGS ANALYSIS ---")
    m_winnings = df[df['gender'] == 'M']['winnings']
    f_winnings = df[df['gender'] == 'F']['winnings']
    
    print(f"Avg Winnings (Men):   ${m_winnings.mean():,.2f}")
    print(f"Avg Winnings (Women): ${f_winnings.mean():,.2f}")
    
    # T-Test (Does the difference matter?)
    t_stat, p_val = stats.ttest_ind(m_winnings, f_winnings, equal_var=False)
    print(f"T-Test p-value: {p_val:.4f}")
    if p_val < 0.05:
        print(">> RESULT: Statistically Significant Difference found!")
    else:
        print(">> RESULT: Difference is likely due to chance (Null Hypothesis).")

    # 3. VISUALIZATION
    # Set a professional style
    sns.set_theme(style="whitegrid")
    
    # Plot 1: Winnings Distribution
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='gender', y='winnings', palette={'M': 'skyblue', 'F': 'lightpink'})
    plt.title("Distribution of Winnings by Gender (Excluding Unknowns)")
    plt.ylabel("Winnings ($)")
    plt.savefig("winnings_by_gender.png") # Saves image for your blog
    print("\nSaved plot: winnings_by_gender.png")
    
    plt.show()

if __name__ == "__main__":
    run_analysis()