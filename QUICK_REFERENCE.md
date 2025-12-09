# 🎯 Quick Reference: Multi-Source Data Collection

## Run the Scraper

```bash
# Collect data from both sources with missing data tracking
python main_multi_source.py
```

## Analyze the Results

```bash
# Analyze missing data and inter-observer reliability
python analyze_multi_source.py
```

## Test Everything

```bash
# Run comprehensive test suite
python test_scraper.py
```

## Output Files

- **`data/processed/season_39_multi_source.csv`** - Full dataset
- **`data/processed/source_comparison.csv`** - Source agreement data
- **`data/processed/data_coverage_timeline.png`** - Visual timeline
- **`data/processed/source_comparison.png`** - Source comparison charts
- **`data/processed/missing_data_summary.png`** - Missing data overview

## Key Features

| Feature | Benefit |
|---------|---------|
| **Multi-Source** | Cross-validation & reliability |
| **Missing Data Tracking** | No survivorship bias |
| **Source Column** | Clear data provenance |
| **Inter-Observer Metrics** | Measure agreement |

## Configure Sources

Edit `main_multi_source.py`:

```python
# WordPress only (fast, recommended)
SOURCES = ['wordpress']

# Both sources (best for reliability)
SOURCES = ['wordpress', 'forum']
```

## CSV Columns Explained

- **date**: Episode air date (YYYY-MM-DD)
- **source**: WordPress | Forum | MISSING
- **bankrupts**: Count of Bankrupt events (None if missing)
- **lose_a_turns**: Count of Lose-a-Turn events (None if missing)
- **players**: List of player dicts (empty list if missing)
- **url**: Source URL (None if missing)
- **data_available**: Boolean flag (True/False)

## For Your Blog Post

### Report These Metrics

1. **Coverage Rate**: "Data available for X% of expected episodes"
2. **Source Agreement**: "Sources agreed Y% of the time"
3. **Missing Data Pattern**: "Missing data showed [pattern]"
4. **Reliability Metric**: "Cohen's κ = 0.XX"

### Example Results Section

```
Data Collection:
- Date range: Sept 13 - Oct 13, 2021 (20 weekdays)
- Available: 18 episodes (90% coverage)
- Missing: 2 episodes (10%)

Inter-Observer Reliability:
- Both sources: 15 episodes
- Bankrupt agreement: 93.3% (14/15)
- LAT agreement: 86.7% (13/15)
- Mean absolute difference: 0.13 (Bankrupts), 0.20 (LAT)
```

## Common Tasks

### Load Data
```python
import pandas as pd
df = pd.read_csv('data/processed/season_39_multi_source.csv')
```

### Filter to Available Data Only
```python
df_available = df[df['data_available']]
```

### Get WordPress Data Only
```python
df_wp = df[df['source'] == 'WordPress']
```

### Calculate Coverage Rate
```python
total = len(df['date'].unique())
available = df[df['data_available']]['date'].nunique()
coverage = available / total * 100
print(f"Coverage: {coverage:.1f}%")
```

### Find Source Disagreements
```python
# Dates with multiple sources
multi = df.groupby('date').filter(lambda x: len(x) > 1)

# Compare bankrupts
for date in multi['date'].unique():
    rows = multi[multi['date'] == date]
    if len(rows['bankrupts'].unique()) > 1:
        print(f"Disagreement on {date}")
        print(rows[['source', 'bankrupts', 'lose_a_turns']])
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Slow scraping | Use `SOURCES = ['wordpress']` |
| Too many MISSING | Check date range (Mon-Fri only) |
| Import errors | Run `pip install -r requirements.txt` |
| Test failures | Check internet connection |

## Important Notes

⚠️ **For Rigorous Research:**
- ✅ Always track missing data
- ✅ Report coverage rates
- ✅ Calculate inter-observer reliability
- ✅ Document disagreements
- ✅ Validate manually (sample 5-10 episodes)

## Documentation Files

- **`MULTI_SOURCE_GUIDE.md`** - Complete documentation
- **`MULTI_SOURCE_SUMMARY.md`** - Implementation summary
- **`SCRAPER_COMPARISON.md`** - Technical details
- **`QUICK_START.md`** - Basic usage guide

---

**You're ready to collect research-grade data! 🎉**
