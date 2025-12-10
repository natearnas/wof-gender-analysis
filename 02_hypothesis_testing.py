import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import ast

# --- CONFIGURATION ---
DATA_PATH = "data/processed/season_39_multi_source.csv"  # Ensure this matches your actual filename
IMG_DIR = "."  # Saves images in current directory

def load_and_clean_data(file_path):
    """
    Loads raw scraper output, explodes player lists, and strictly filters 
    for confirmed 'M' or 'F' genders (Listwise Deletion of Unknowns).
    """
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}. Run main.py first.")
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
                # STRICT FILTER: Only 'M' or 'F'
                gender = p.get('gender', 'Unknown')
                if gender not in ['M', 'F']:
                    continue
                    
                player_rows.append({
                    'date': row['date'],
                    'name': p.get('name'),
                    'gender': gender,
                    'winnings': p.get('winnings', 0),
                    # Proxy: Episode bankrupts represent the "Risk Environment" this player faced
                    'episode_bankrupts': row['bankrupts']
                })

    return pd.DataFrame(player_rows)

def analyze_winnings(df):
    print("\n" + "="*40)
    print("  PHASE 1: STANDARD STATISTICAL ANALYSIS")
    print("="*40)
    
    m_winnings = df[df['gender'] == 'M']['winnings']
    f_winnings = df[df['gender'] == 'F']['winnings']
    
    # 1. Descriptive Stats
    print(f"Men (n={len(m_winnings)}):   Mean=${m_winnings.mean():,.2f}, Median=${m_winnings.median():,.2f}")
    print(f"Women (n={len(f_winnings)}): Mean=${f_winnings.mean():,.2f}, Median=${f_winnings.median():,.2f}")
    
    # 2. Standard T-Test (The "Naive" Approach)
    t_stat, p_val_t = stats.ttest_ind(m_winnings, f_winnings, equal_var=False)
    print(f"\n[Standard T-Test] P-Value: {p_val_t:.4f}")
    if p_val_t > 0.05:
        print("   -> Result: No significant difference (Fail to reject H0)")
    else:
        print("   -> Result: Significant difference found!")

    print("\n" + "="*40)
    print("  PHASE 2: NORMALITY & NON-PARAMETRIC")
    print("="*40)

    # 3. Normality Test (Shapiro-Wilk)
    # Note: Shapiro can be sensitive to large samples, but good for checking "Bell Curve" assumption
    shapiro_m = stats.shapiro(m_winnings)
    shapiro_f = stats.shapiro(f_winnings)
    
    print(f"[Normality Check] Men p={shapiro_m.pvalue:.4f}, Women p={shapiro_f.pvalue:.4f}")
    if shapiro_m.pvalue < 0.05 or shapiro_f.pvalue < 0.05:
        print("   -> WARNING: Data is NOT Normal (Right-Skewed). T-Test is unreliable.")
        print("   -> ACTION: Switching to Mann-Whitney U Test.")
    
    # 4. Mann-Whitney U Test (The "Expert" Approach)
    u_stat, p_val_u = stats.mannwhitneyu(m_winnings, f_winnings, alternative='two-sided')
    print(f"\n[Mann-Whitney U] P-Value: {p_val_u:.4f}")
    
    return m_winnings, f_winnings

def run_bootstrap_simulation(m_data, f_data, n_iterations=10000):
    print("\n" + "="*40)
    print(f"  PHASE 3: BOOTSTRAP SIMULATION ({n_iterations} Runs)")
    print("="*40)
    
    obs_diff = np.mean(m_data) - np.mean(f_data)
    print(f"Observed Difference (Men - Women): ${obs_diff:.2f}")
    
    # Resampling Loop
    bootstrap_diffs = []
    np.random.seed(42) # For reproducibility
    
    for _ in range(n_iterations):
        m_sample = np.random.choice(m_data, size=len(m_data), replace=True)
        f_sample = np.random.choice(f_data, size=len(f_data), replace=True)
        diff = np.mean(m_sample) - np.mean(f_sample)
        bootstrap_diffs.append(diff)
        
    bootstrap_diffs = np.array(bootstrap_diffs)
    
    # Calculate Confidence Intervals
    ci_lower = np.percentile(bootstrap_diffs, 2.5)
    ci_upper = np.percentile(bootstrap_diffs, 97.5)
    
    print(f"95% Confidence Interval: [${ci_lower:.2f}, ${ci_upper:.2f}]")
    if ci_lower <= 0 <= ci_upper:
        print("   -> CONCLUSION: The interval contains $0. The observed difference is statistical noise.")
    else:
        print("   -> CONCLUSION: The interval excludes $0. The difference is real.")
        
    return bootstrap_diffs, ci_lower, ci_upper

def plot_results(df, boot_diffs, ci_low, ci_high):
    sns.set_theme(style="whitegrid")
    
    # Create a layout with 2 plots: Box Plot (Raw Data) and Histogram (Bootstrap)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: The Reality (Non-Normal Box Plot)
    sns.boxplot(data=df, x='gender', y='winnings', hue='gender', palette={'M': 'skyblue', 'F': 'lightpink'}, legend=False, ax=axes[0])
    axes[0].set_title("Distribution of Winnings (Raw Data)")
    axes[0].set_ylabel("Winnings ($)")
    
    # Plot 2: The Simulation (Bootstrap Distribution)
    sns.histplot(boot_diffs, kde=True, color='purple', element="step", ax=axes[1])
    axes[1].axvline(ci_low, color='red', linestyle='--', label='95% CI')
    axes[1].axvline(ci_high, color='red', linestyle='--')
    axes[1].axvline(0, color='black', linewidth=2, label='Zero Diff')
    axes[1].set_title(f"Bootstrap Simulation of Gender Gap\n(Men - Women)")
    axes[1].set_xlabel("Difference in Mean Winnings ($)")
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(f"{IMG_DIR}/comprehensive_analysis.png")
    print(f"\n[Visuals] Saved plot to {IMG_DIR}/comprehensive_analysis.png")
    plt.show()

if __name__ == "__main__":
    # 1. Load
    df = load_and_clean_data(DATA_PATH)
    
    if df is not None and not df.empty:
        # 2. Analyze
        men_wins, women_wins = analyze_winnings(df)
        
        # 3. Simulate
        boot_diffs, ci_low, ci_high = run_bootstrap_simulation(men_wins, women_wins)
        
        # 4. Visualize
        plot_results(df, boot_diffs, ci_low, ci_high)