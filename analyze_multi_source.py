"""
Multi-Source Data Analysis for Wheel of Fortune
Handles missing data tracking and inter-observer reliability between sources
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

def load_multi_source_data(filepath):
    """Load data with proper handling of missing values and player lists."""
    df = pd.read_csv(filepath)
    
    # Convert string representations of lists back to lists
    import ast
    df['players'] = df['players'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '[]' else [])
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    return df

def analyze_missing_data(df):
    """Analyze patterns in missing data."""
    print("=" * 70)
    print("MISSING DATA ANALYSIS")
    print("=" * 70)
    
    # Overall missing rate
    total_dates = len(df['date'].unique())
    missing_dates = df[df['source'] == 'MISSING']['date'].nunique()
    available_dates = df[df['data_available']]['date'].nunique()
    
    print(f"\nTotal unique dates in range: {total_dates}")
    print(f"Dates with available data: {available_dates} ({available_dates/total_dates*100:.1f}%)")
    print(f"Dates with missing data: {missing_dates} ({missing_dates/total_dates*100:.1f}%)")
    
    # Missing by weekday
    df_missing = df[df['source'] == 'MISSING'].copy()
    if not df_missing.empty:
        df_missing['weekday'] = df_missing['date'].dt.day_name()
        print("\nMissing data by weekday:")
        weekday_counts = df_missing['weekday'].value_counts()
        for day, count in weekday_counts.items():
            print(f"  {day}: {count}")
    
    return missing_dates, available_dates

def compare_sources(df):
    """Compare data between sources for inter-observer reliability."""
    print("\n" + "=" * 70)
    print("INTER-OBSERVER RELIABILITY ANALYSIS")
    print("=" * 70)
    
    # Find dates with multiple sources
    df_available = df[df['data_available']].copy()
    
    # Pivot to wide format for comparison
    comparison_data = []
    
    for date in df_available['date'].unique():
        date_rows = df_available[df_available['date'] == date]
        
        if len(date_rows) > 1:  # Multiple sources for this date
            sources = {}
            for _, row in date_rows.iterrows():
                sources[row['source']] = {
                    'bankrupts': row['bankrupts'],
                    'lose_a_turns': row['lose_a_turns'],
                    'num_players': len(row['players']) if row['players'] else 0
                }
            
            # Calculate differences if we have 2 sources
            if len(sources) == 2:
                source_list = list(sources.keys())
                s1, s2 = source_list[0], source_list[1]
                
                comparison_data.append({
                    'date': date,
                    'source_1': s1,
                    'source_2': s2,
                    'bankrupts_diff': abs(sources[s1]['bankrupts'] - sources[s2]['bankrupts']),
                    'lat_diff': abs(sources[s1]['lose_a_turns'] - sources[s2]['lose_a_turns']),
                    's1_bankrupts': sources[s1]['bankrupts'],
                    's2_bankrupts': sources[s2]['bankrupts'],
                    's1_lat': sources[s1]['lose_a_turns'],
                    's2_lat': sources[s2]['lose_a_turns'],
                })
    
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        
        print(f"\nFound {len(comp_df)} dates with data from both sources")
        
        # Agreement statistics
        exact_match_b = (comp_df['bankrupts_diff'] == 0).sum()
        exact_match_lat = (comp_df['lat_diff'] == 0).sum()
        
        print("\nExact Agreement:")
        print(f"  Bankrupts: {exact_match_b}/{len(comp_df)} ({exact_match_b/len(comp_df)*100:.1f}%)")
        print(f"  Lose-a-Turns: {exact_match_lat}/{len(comp_df)} ({exact_match_lat/len(comp_df)*100:.1f}%)")
        
        # Mean absolute difference
        print("\nMean Absolute Difference:")
        print(f"  Bankrupts: {comp_df['bankrupts_diff'].mean():.2f}")
        print(f"  Lose-a-Turns: {comp_df['lat_diff'].mean():.2f}")
        
        # Show disagreements
        disagreements_b = comp_df[comp_df['bankrupts_diff'] > 0]
        disagreements_lat = comp_df[comp_df['lat_diff'] > 0]
        
        if not disagreements_b.empty:
            print(f"\nBankrupt disagreements ({len(disagreements_b)} dates):")
            for _, row in disagreements_b.head(5).iterrows():
                print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['source_1']}={row['s1_bankrupts']:.0f}, {row['source_2']}={row['s2_bankrupts']:.0f} (diff={row['bankrupts_diff']:.0f})")
        
        if not disagreements_lat.empty:
            print(f"\nLose-a-Turn disagreements ({len(disagreements_lat)} dates):")
            for _, row in disagreements_lat.head(5).iterrows():
                print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['source_1']}={row['s1_lat']:.0f}, {row['source_2']}={row['s2_lat']:.0f} (diff={row['lat_diff']:.0f})")
        
        return comp_df
    else:
        print("\nNo overlapping dates found between sources.")
        return None

def visualize_coverage(df, output_dir="data/processed"):
    """Create visualizations of data coverage and source comparison."""
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Data availability timeline
    fig, ax = plt.subplots(figsize=(14, 6))
    
    df_sorted = df.sort_values('date')
    colors = {'WordPress': 'green', 'Forum': 'blue', 'MISSING': 'red'}
    
    for source in df_sorted['source'].unique():
        source_data = df_sorted[df_sorted['source'] == source]
        ax.scatter(source_data['date'], [source] * len(source_data), 
                  c=colors.get(source, 'gray'), label=source, s=50, alpha=0.6)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Data Source', fontsize=12)
    ax.set_title('Data Coverage by Source Over Time', fontsize=14, fontweight='bold')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    coverage_file = os.path.join(output_dir, 'data_coverage_timeline.png')
    plt.savefig(coverage_file, dpi=150)
    print(f"✓ Saved: {coverage_file}")
    plt.close()
    
    # 2. Source comparison (if we have multiple sources)
    df_available = df[df['data_available']]
    if len(df_available['source'].unique()) > 1:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Bankrupts by source
        df_available.boxplot(column='bankrupts', by='source', ax=axes[0])
        axes[0].set_title('Bankrupts Distribution by Source')
        axes[0].set_xlabel('Source')
        axes[0].set_ylabel('Count')
        
        # Lose-a-Turns by source
        df_available.boxplot(column='lose_a_turns', by='source', ax=axes[1])
        axes[1].set_title('Lose-a-Turn Distribution by Source')
        axes[1].set_xlabel('Source')
        axes[1].set_ylabel('Count')
        
        plt.suptitle('')  # Remove automatic title
        plt.tight_layout()
        
        comparison_file = os.path.join(output_dir, 'source_comparison.png')
        plt.savefig(comparison_file, dpi=150)
        print(f"✓ Saved: {comparison_file}")
        plt.close()
    
    # 3. Missing data pattern
    fig, ax = plt.subplots(figsize=(10, 6))
    
    missing_by_date = df.groupby('date')['data_available'].any()
    missing_counts = missing_by_date.value_counts()
    
    colors_avail = {True: 'green', False: 'red'}
    labels_avail = {True: 'Data Available', False: 'Missing Data'}
    
    ax.bar([labels_avail[k] for k in missing_counts.index], 
           missing_counts.values,
           color=[colors_avail[k] for k in missing_counts.index])
    
    ax.set_ylabel('Number of Dates', fontsize=12)
    ax.set_title('Data Availability Summary', fontsize=14, fontweight='bold')
    
    # Add percentage labels
    total = missing_counts.sum()
    for i, (k, v) in enumerate(missing_counts.items()):
        ax.text(i, v, f'{v}\n({v/total*100:.1f}%)', 
               ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    missing_file = os.path.join(output_dir, 'missing_data_summary.png')
    plt.savefig(missing_file, dpi=150)
    print(f"✓ Saved: {missing_file}")
    plt.close()

def main():
    # Load data
    data_file = "data/processed/season_39_multi_source.csv"
    
    if not os.path.exists(data_file):
        print(f"ERROR: Data file not found: {data_file}")
        print("Please run main_multi_source.py first to collect data.")
        return
    
    print("\nLoading data from:", data_file)
    df = load_multi_source_data(data_file)
    
    print(f"\nLoaded {len(df)} records")
    print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    
    # Analysis
    analyze_missing_data(df)
    comp_df = compare_sources(df)
    visualize_coverage(df)
    
    # Save comparison data if available
    if comp_df is not None and not comp_df.empty:
        comp_file = "data/processed/source_comparison.csv"
        comp_df.to_csv(comp_file, index=False)
        print(f"\n✓ Saved source comparison data: {comp_file}")
    
    print("\n" + "=" * 70)
    print("✓ Analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
