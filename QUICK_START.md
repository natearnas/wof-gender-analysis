# Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the Scraper
```bash
python test_scraper.py
```

### 3. Run Your First Scrape
```bash
python main.py
```

## 📊 Common Tasks

### Scrape a Custom Date Range
Edit `main.py`:
```python
START_DATE = datetime(2021, 9, 13)  # Your start date
END_DATE = datetime(2021, 10, 13)    # Your end date
```

### Get Player-Level Data
```python
from src.scraper import WoFScraper
from datetime import datetime

scraper = WoFScraper()
df = scraper.batch_scrape_season(datetime(2021, 9, 13), datetime(2021, 9, 17))

# Normalize to player level
player_df = scraper.normalize_player_data(df)
print(player_df)
```

### Identify Missing Episodes
```bash
python analysis.py
```

## 🔍 Key Features

| Feature | Description |
|---------|-------------|
| **Episode Scraping** | Scrapes Bankrupt and Lose-a-Turn counts |
| **Player Extraction** | Extracts player names and positions |
| **Data Normalization** | Converts episode → player level |
| **Gap Analysis** | Identifies missing episodes |
| **Gender Classification** | Basic name-based gender inference |

## 📁 Output Files

After running `main.py`:
- `data/processed/season_39_sample.csv` - Episode-level data
- `data/raw/` - Cached raw data (if saving enabled)

## ⚠️ Important Notes

1. **Be respectful**: Default 1-second delay between requests
2. **Validate data**: Always manually check a sample of results
3. **Gender classification**: Replace with proper database for research
4. **Missing episodes**: Use `analysis.py` to identify gaps

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No episodes found" | Check dates (WoF airs Mon-Fri) |
| Import errors | Run `pip install -r requirements.txt` |
| Connection errors | Check internet, increase delay |
| Player extraction fails | Some episodes lack player info (expected) |

## 📝 Files You'll Edit

- **`main.py`**: Change date ranges, output paths
- **`analysis.py`**: Customize visualizations
- **`src/scraper.py`**: Modify scraping logic (advanced)

## 🎯 Next Steps for Your Blog Post

1. Run test scraper on small sample
2. Validate data quality manually
3. Document limitations (inter-observer reliability, etc.)
4. Run gap analysis to quantify missing data
5. Implement proper gender classification
6. Scale up to full season(s)
7. Run statistical tests (chi-square, etc.)

## 💡 Tips

- Start with **1 week** of data to validate
- **Manually verify** 5-10 episodes before scaling
- Use **analysis.py** to visualize coverage gaps
- Consider **multiple coders** for reliability testing
- Document all **assumptions and limitations**
