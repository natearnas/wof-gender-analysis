"""
Enhanced Analysis Script for Wheel of Fortune Gender Analysis
Includes: Data gap analysis, player-level normalization, gender-based statistical tests,
and inter-observer reliability metrics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils import DataNormalizer, StatisticalAnalyzer
import ast


#%% 1. Load the Scraped Data
print("=== WHEEL OF FORTUNE GENDER ANALYSIS ===\n")
print("Loading episode data...")

df = pd.read_csv("data/processed/season_39_multi_source.csv")
df['date'] = pd.to_datetime(df['date'])

# Parse the 'players' column (stored as string representation of list)
if 'players' in df.columns:
    df['players'] = df['players'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '[]' else [])

print(f"✓ Loaded {len(df)} episodes.")


#%% 2. Data Integrity Analysis (Gap Analysis)
print("\n--- DATA INTEGRITY REPORT ---")

start_date = df['date'].min().strftime('%Y-%m-%d')
end_date = df['date'].max().strftime('%Y-%m-%d')

gap_metrics = DataNormalizer.calculate_gap_metrics(df, start_date, end_date)

print(f"Expected Episodes: {gap_metrics['expected_episodes']}")
print(f"Captured Episodes: {gap_metrics['captured_episodes']}")
print(f"Missing Episodes:  {gap_metrics['missing_episodes']}")
print(f"Completeness:      {gap_metrics['completeness_pct']:.1f}%")

if gap_metrics['missing_dates']:
    print(f"\nMissing Dates: {gap_metrics['missing_dates']}")


#%% 3. Visualize Data Gaps (The "Barcode" Plot)
print("\n--- GENERATING GAP VISUALIZATION ---")

# Generate ideal business day range
ideal_range = pd.bdate_range(start=start_date, end=end_date)
ideal_df = pd.DataFrame({'date': ideal_range})

# Merge to find gaps
merged_df = pd.merge(ideal_df, df[['date', 'bankrupts']], on='date', how='left')
merged_df['status'] = merged_df['bankrupts'].notna().astype(int)

plt.figure(figsize=(14, 2))
sns.heatmap(merged_df[['status']].T, 
            cmap=['salmon', 'lightgreen'], 
            cbar=False, 
            yticklabels=False,
            xticklabels=merged_df['date'].dt.strftime('%m-%d'))
plt.title("Dataset Continuity (Green = Data Found, Red = Missing)", fontsize=12, pad=10)
plt.xlabel("Date", fontsize=10)
plt.tight_layout()
plt.savefig("data/processed/gap_analysis.png", dpi=150, bbox_inches='tight')
print("✓ Gap visualization saved to: data/processed/gap_analysis.png")
plt.show()


#%% 4. Normalize to Player-Level Data
print("\n--- NORMALIZING TO PLAYER LEVEL ---")

if 'players' in df.columns and any(len(p) > 0 for p in df['players']):
    player_df = DataNormalizer.normalize_to_players(df)
    
    # Fill only missing/Unknown genders using scraper estimator
    player_df = DataNormalizer.add_gender_classification(player_df)
    
    print(f"✓ Expanded to {len(player_df)} player records")
    print("  Gender breakdown:")
    print(f"    Male:    {(player_df['gender'] == 'M').sum()}")
    print(f"    Female:  {(player_df['gender'] == 'F').sum()}")
    print(f"    Unknown: {(player_df['gender'] == 'Unknown').sum()}")
    
    # Save player-level data
    player_df.to_csv("data/processed/player_level_data.csv", index=False)
    print("✓ Player-level data saved to: data/processed/player_level_data.csv")
    
else:
    print("⚠ No player data found in dataset. Skipping player-level analysis.")
    player_df = None


#%% 5. Statistical Analysis (Gender-Based Variance)
if player_df is not None and len(player_df) > 0:
    print("\n--- STATISTICAL ANALYSIS ---")
    
    # Test for gender variance in bankrupt rates
    bankrupt_results = StatisticalAnalyzer.test_gender_variance(player_df, 'bankrupt_rate')
    
    if 'error' not in bankrupt_results:
        print("\nBankrupt Rate Analysis:")
        print(f"  Male (n={bankrupt_results['male_n']}):   {bankrupt_results['male_mean']:.4f} ± {bankrupt_results['male_std']:.4f}")
        print(f"  Female (n={bankrupt_results['female_n']}): {bankrupt_results['female_mean']:.4f} ± {bankrupt_results['female_std']:.4f}")
        print(f"  t-statistic: {bankrupt_results['t_statistic']:.3f}")
        print(f"  p-value:     {bankrupt_results['p_value']:.4f}")
        print(f"  Cohen's d:   {bankrupt_results['cohens_d']:.3f} ({bankrupt_results['interpretation']})")
        print(f"  Significant: {'YES' if bankrupt_results['significant'] else 'NO'} (α=0.05)")
    
    # Test for gender variance in lose-a-turn rates
    lat_results = StatisticalAnalyzer.test_gender_variance(player_df, 'lose_a_turn_rate')
    
    if 'error' not in lat_results:
        print("\nLose-a-Turn Rate Analysis:")
        print(f"  Male (n={lat_results['male_n']}):   {lat_results['male_mean']:.4f} ± {lat_results['male_std']:.4f}")
        print(f"  Female (n={lat_results['female_n']}): {lat_results['female_mean']:.4f} ± {lat_results['female_std']:.4f}")
        print(f"  t-statistic: {lat_results['t_statistic']:.3f}")
        print(f"  p-value:     {lat_results['p_value']:.4f}")
        print(f"  Cohen's d:   {lat_results['cohens_d']:.3f} ({lat_results['interpretation']})")
        print(f"  Significant: {'YES' if lat_results['significant'] else 'NO'} (α=0.05)")


#%% 6. Visualization: Gender Comparison
if player_df is not None and len(player_df[player_df['gender'].isin(['M', 'F'])]) > 0:
    print("\n--- GENERATING COMPARISON VISUALIZATIONS ---")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Filter to only M and F
    plot_df = player_df[player_df['gender'].isin(['M', 'F'])].copy()
    
    # Bankrupt Rate by Gender
    sns.boxplot(data=plot_df, x='gender', y='bankrupt_rate', hue='gender', ax=axes[0], palette=['skyblue', 'lightcoral'], legend=False)
    axes[0].set_title('Bankrupt Rate by Gender', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Gender', fontsize=11)
    axes[0].set_ylabel('Bankrupt Rate (per spin)', fontsize=11)
    
    # Lose-a-Turn Rate by Gender
    sns.boxplot(data=plot_df, x='gender', y='lose_a_turn_rate', hue='gender', ax=axes[1], palette=['skyblue', 'lightcoral'], legend=False)
    axes[1].set_title('Lose-a-Turn Rate by Gender', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Gender', fontsize=11)
    axes[1].set_ylabel('Lose-a-Turn Rate (per spin)', fontsize=11)
    
    plt.tight_layout()
    plt.savefig("data/processed/gender_comparison.png", dpi=150, bbox_inches='tight')
    print("✓ Gender comparison plot saved to: data/processed/gender_comparison.png")
    plt.show()


#%% 7. Inter-Observer Reliability Example
print("\n--- INTER-OBSERVER RELIABILITY ---")
print("Note: For rigorous research, manually verify gender classifications")
print("      and have multiple coders independently classify a sample.")
print("\nExample reliability test:")
print("  If you had two observers classify the same 50 players,")
print("  you would use ReliabilityAnalyzer.generate_reliability_report()")
print("  to calculate Cohen's Kappa and percent agreement.")
print("\n  Target: Kappa > 0.80 (Almost Perfect Agreement)")


print("\n=== ANALYSIS COMPLETE ===")
print("\nNext Steps:")
print("1. Manually verify gender classifications for Unknown players")
print("2. Expand dataset to full season for robust statistical power")
print("3. Conduct inter-rater reliability with second coder")
print("4. Document methodology for blog post on experimental rigor")