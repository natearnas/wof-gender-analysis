import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import ast
import numpy as np
from scipy import stats

# --- CONFIGURATION ---
DATA_PATH = "data/processed/longitudinal_data_raw.csv" 
IMG_DIR = "."

def load_multi_season_data(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        # Fallback for different folder structures
        try:
            df = pd.read_csv("longitudinal_data_raw.csv")
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
            except (ValueError, SyntaxError, TypeError):
                continue
    return pd.DataFrame(player_rows)

def analyze_interface_impact(df):
    print("--- INTERFACE CHANGE ANALYSIS (Difference-in-Differences) ---")
    
    # 1. Define the Eras
    target_seasons = ['S38', 'S39']
    df['is_white_thing_era'] = df['season'].isin(target_seasons)
    print("Seasons found in data:", sorted(df['season'].unique()))
    
    # --- PLOTTING SECTION ---
    
    # Plot A: The Longitudinal Trend (Figure 1 in Blog)
    plt.figure(figsize=(12, 6))
    season_stats = df.groupby(['season', 'gender'])['winnings'].agg(['mean', 'count']).reset_index()
    sns.lineplot(data=season_stats, x='season', y='mean', hue='gender', 
                 palette={'M': 'skyblue', 'F': 'lightpink'}, marker="o", linewidth=2.5)
    plt.axvspan('S38', 'S39', color='gray', alpha=0.15, label='Plastic Cap Era')
    plt.title(f"Impact of Physical Interface on Winnings (N={len(df)})")
    plt.ylabel("Average Winnings ($)")
    plt.xlabel("Season")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(f"{IMG_DIR}/did_analysis_trend.png")
    print(f"Saved plot: {IMG_DIR}/did_analysis_trend.png")

    # Plot B: The "Gap Eraser" Bar Chart (Figure 2 in Blog) -- [ADDED THIS]
    plt.figure(figsize=(10, 6))
    # Create readable labels for the X-axis
    df['Era_Label'] = df['is_white_thing_era'].apply(lambda x: "Plastic Cap (S38-39)" if x else "Normal (S36-37, S40-41)")
    
    sns.barplot(
        data=df, 
        x='Era_Label', 
        y='winnings', 
        hue='gender', 
        palette={'M': 'skyblue', 'F': 'lightpink'},
        order=["Normal (S36-37, S40-41)", "Plastic Cap (S38-39)"], # Force specific order
        capsize=.1,
        errorbar=('ci', 68) # Standard Error bars
    )
    plt.title("Gender Winnings Gap: Normal vs. Plastic Cap Era")
    plt.xlabel("Interface Era")
    plt.ylabel("Average Winnings ($)")
    plt.savefig(f"{IMG_DIR}/winnings_by_era_barplot.png")
    print(f"Saved plot: {IMG_DIR}/winnings_by_era_barplot.png")

    # Plot C: The Distributions (Figure 3 in Blog)
    plt.figure(figsize=(14, 6))

    # Winnings Histogram
    plt.subplot(1, 2, 1)
    sns.histplot(data=df, x='winnings', hue='gender', kde=True, 
                 palette={'M': 'skyblue', 'F': 'lightpink'}, element="step")
    plt.title("Distribution of Winnings (Non-Normal)")
    plt.xlabel("Winnings ($)")
    plt.ylabel("Frequency")

    # Bankrupts Histogram
    plt.subplot(1, 2, 2)
    sns.histplot(data=df, x='bankrupts', hue='gender', multiple="dodge", 
                 shrink=.8, bins=range(0, 10), palette={'M': 'skyblue', 'F': 'lightpink'})
    plt.title("Distribution of Bankrupts")
    plt.xlabel("Bankrupts per Episode")
    plt.ylabel("Count")

    plt.tight_layout()
    plt.savefig(f"{IMG_DIR}/distributions.png")
    print(f"Saved plot: {IMG_DIR}/distributions.png")
    
    # --- STATISTICS SECTION ---

    # 2. Difference-in-Differences (DiD) Model
    print("\n[Running OLS Regression...]")
    model = smf.ols("winnings ~ C(gender) * C(is_white_thing_era)", data=df).fit()
    print(model.summary())
    
    try:
        interaction_p = model.pvalues['C(gender)[T.M]:C(is_white_thing_era)[T.True]']
        print(f"\n>> INTERACTION P-VALUE: {interaction_p:.4f}")
    except KeyError:
        print("Error: Could not calculate interaction.")

    # 3. Global Economy Check
    print("\n" + "="*50)
    print("--- GLOBAL ECONOMY CHECK ---")
    
    global_stats = df.groupby('is_white_thing_era')['winnings'].mean()
    print("\nAverage Winnings per Player:")
    print(global_stats)
    
    normal_era = df[~df['is_white_thing_era']]['winnings']
    cap_era = df[df['is_white_thing_era']]['winnings']
    
    t_stat, p_val = stats.ttest_ind(normal_era, cap_era, equal_var=False)
    print(f"\nGlobal Winnings T-Test (Cap vs. Normal): P-Value = {p_val:.4f}")

    # 4. Robustness Checks
    print("\n" + "="*50)
    print("--- ROBUSTNESS CHECKS ---")

    # A. Mann-Whitney U Test
    m_winnings = df[(~df['is_white_thing_era']) & (df['gender'] == 'M')]['winnings']
    f_winnings = df[(~df['is_white_thing_era']) & (df['gender'] == 'F')]['winnings']
    u_stat, mw_p_val = stats.mannwhitneyu(m_winnings, f_winnings, alternative='greater')
    print(f"\n1. Mann-Whitney U Test (Baseline Gap): P-Value = {mw_p_val:.5f}")

    # B. Bootstrap Resampling
    print("\n2. Bootstrap Resampling (2,000 Iterations)...")
    
    n_bootstraps = 2000
    boot_diffs = []
    
    for i in range(n_bootstraps):
        resample = df.sample(frac=1.0, replace=True)
        means = resample.groupby(['is_white_thing_era', 'gender'])['winnings'].mean()
        try:
            gap_cap = means[True]['M'] - means[True]['F']
            gap_norm = means[False]['M'] - means[False]['F']
            boot_diffs.append(gap_cap - gap_norm)
        except KeyError:
            continue

    ci_lower = np.percentile(boot_diffs, 2.5)
    ci_upper = np.percentile(boot_diffs, 97.5)
    mean_est = np.mean(boot_diffs)

    print(f"   Mean Estimated Effect: ${mean_est:.2f}")
    print(f"   95% CI: [${ci_lower:.2f}, ${ci_upper:.2f}]")
    
    if ci_upper < 0:
        print("   >> RESULT: ROBUST (CI does not cross zero).")
    else:
        print("   >> RESULT: WEAK (CI crosses zero).")

if __name__ == "__main__":
    df = load_multi_season_data(DATA_PATH)
    if df is not None and not df.empty:
        analyze_interface_impact(df)