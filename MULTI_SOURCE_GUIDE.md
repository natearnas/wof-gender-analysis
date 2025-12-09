# Multi-Source Data Collection Guide

## Overview

The scraper now supports **multiple data sources** and **explicit missing data tracking**, which is critical for rigorous statistical analysis and understanding data quality issues.

## Key Features

### ✅ 1. **Multiple Data Sources**
- **WordPress Blog** (andynwof.wordpress.com): Fast, reliable, predictable URLs
- **Forum** (buyavowel.boards.net): Additional source for inter-observer reliability

### ✅ 2. **Missing Data Tracking**
- Creates explicit rows for dates with no data available
- Essential for:
  - Calculating true coverage rates
  - Identifying systematic gaps
  - Proper statistical inference (can't ignore missing data!)

### ✅ 3. **Source Column**
Every row indicates its source:
- `WordPress`: Data from Andy's WordPress blog
- `Forum`: Data from buyavowel.boards.net
- `MISSING`: No data found for this date

### ✅ 4. **Inter-Observer Reliability**
When both sources have data for the same date, you can:
- Compare Bankrupt counts between sources
- Compare Lose-a-Turn counts between sources
- Calculate agreement metrics (Cohen's Kappa, etc.)

## Quick Start

### Step 1: Collect Data from Both Sources
```bash
python main_multi_source.py
```

This will:
- Scrape data from both WordPress and Forum
- Track missing data explicitly
- Show source comparison in real-time
- Save to `data/processed/season_39_multi_source.csv`

### Step 2: Analyze the Data
```bash
python analyze_multi_source.py
```

This will:
- Calculate missing data rates
- Compare sources for inter-observer reliability
- Generate visualizations
- Identify disagreements between sources

## Understanding the Output

### CSV Structure
```
date,source,bankrupts,lose_a_turns,players,url,data_available
2021-09-13,WordPress,5,2,[...],https://...,True
2021-09-13,Forum,5,2,[...],https://...,True
2021-09-14,MISSING,,,[],,False
```

### Key Columns
- **date**: Episode air date
- **source**: Data source (WordPress, Forum, or MISSING)
- **bankrupts**: Count of Bankrupt events
- **lose_a_turns**: Count of Lose-a-Turn events
- **players**: List of player dictionaries
- **url**: Source URL (None for missing data)
- **data_available**: Boolean indicating if data was found

## Configuration Options

### Choose Your Sources

Edit `main_multi_source.py`:

```python
# Option 1: WordPress only (faster, more reliable)
SOURCES = ['wordpress']

# Option 2: Forum only (slower, less reliable)
SOURCES = ['forum']

# Option 3: Both sources (best for reliability testing)
SOURCES = ['wordpress', 'forum']
```

### Control Missing Data Tracking

```python
# Enable missing data tracking (recommended)
df = scraper.batch_scrape_season(start, end, track_missing=True)

# Disable (only get successful scrapes)
df = scraper.batch_scrape_season(start, end, track_missing=False)
```

## Why This Matters for Your Blog Post

### 1. **Data Integrity**
- Explicitly tracking missing data prevents **survivorship bias**
- You can report: "We obtained data for X% of episodes in the date range"

### 2. **Inter-Observer Reliability**
- Having two sources lets you calculate **agreement metrics**
- Example: "Both sources agreed on Bankrupt counts in 95% of cases (Cohen's κ = 0.92)"

### 3. **Transparent Limitations**
- Missing data visualization shows coverage gaps
- Can discuss in methodology: "Data were unavailable for X dates due to..."

### 4. **Statistical Validity**
- Proper handling of missing data in statistical tests
- Can use multiple imputation or complete-case analysis appropriately

## Analysis Examples

### Missing Data Rate
```python
df = load_multi_source_data("data/processed/season_39_multi_source.csv")

total_dates = len(df['date'].unique())
missing = (df['source'] == 'MISSING').sum()
coverage_rate = (total_dates - missing) / total_dates * 100

print(f"Coverage: {coverage_rate:.1f}%")
```

### Inter-Observer Agreement
```python
# For dates with both sources
both_sources = df.groupby('date').filter(lambda x: len(x) == 2)

# Compare bankrupts
wordpress_b = both_sources[both_sources['source'] == 'WordPress']['bankrupts']
forum_b = both_sources[both_sources['source'] == 'Forum']['bankrupts']

agreement = (wordpress_b == forum_b).mean()
print(f"Agreement: {agreement*100:.1f}%")
```

### Visualize Coverage Gaps
```python
import matplotlib.pyplot as plt

dates = df['date'].unique()
has_data = df.groupby('date')['data_available'].any()

plt.figure(figsize=(12, 3))
plt.scatter(dates, has_data, c=has_data, cmap='RdYlGn')
plt.ylabel('Data Available')
plt.xlabel('Date')
plt.title('Data Coverage Timeline')
plt.show()
```

## Comparison: Single vs Multi-Source

| Feature | Single Source | Multi-Source |
|---------|--------------|--------------|
| **Speed** | Faster | Slower (checks both) |
| **Reliability** | Good | Better |
| **Inter-Observer** | ❌ No | ✅ Yes |
| **Missing Data** | Optional | Built-in |
| **Use Case** | Quick analysis | Rigorous research |

## Tips for Your Blog Post

### Methodology Section
Include:
1. "Data were collected from two independent sources..."
2. "Missing data were explicitly tracked, with X% coverage..."
3. "Inter-observer reliability was assessed using..."

### Results Section
Report:
1. Coverage rate by source
2. Agreement statistics between sources
3. How disagreements were resolved

### Limitations Section
Discuss:
1. Dates with missing data
2. Why certain episodes were unavailable
3. Potential bias from missing data

## Troubleshooting

**Q: Forum scraping is slow**
- Forum uses thread ID guessing (less reliable)
- Consider using WordPress only: `SOURCES = ['wordpress']`

**Q: Too many missing data rows**
- Check your date range (WoF doesn't air on weekends)
- Use `skip_weekends=True` (default)

**Q: Sources disagree frequently**
- This is valuable data for your blog post!
- Document disagreement rate
- Manually verify a sample

## Next Steps

1. ✅ Run `main_multi_source.py` to collect data
2. ✅ Run `analyze_multi_source.py` to analyze
3. ✅ Review visualizations in `data/processed/`
4. ✅ Calculate inter-observer reliability metrics
5. ✅ Document missing data patterns
6. ✅ Make informed decisions about data quality
