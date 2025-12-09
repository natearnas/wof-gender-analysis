# Scraper Comparison & Combined Implementation

## Overview
This document explains the differences between the two scraper versions and how they were combined.

## Key Differences

### Original Version (buyavowel.boards.net)
- **URL**: `https://buyavowel.boards.net/thread/{thread_id}`
- **Structure**: Forum-based with thread IDs
- **Pros**: 
  - More comprehensive content
  - Community discussions
- **Cons**:
  - Thread IDs are unpredictable
  - Requires searching multiple URLs
  - Slower and less reliable

### Alternate Version (andynwof.wordpress.com) ✓ **CHOSEN**
- **URL**: `https://andynwof.wordpress.com/YYYY/MM/DD/wof-recap-month-day-year/`
- **Structure**: WordPress blog with predictable date-based URLs
- **Pros**:
  - **Deterministic URL structure** (dates map directly to URLs)
  - Faster scraping (no searching required)
  - More reliable (404 = no episode aired)
  - Cleaner HTML structure
- **Cons**:
  - Only recaps (no community discussion)

## Combined Features

The final implementation uses **Andy's WordPress blog** as the primary source with enhanced features:

### 1. **Robust URL Generation**
```python
date_str = date_obj.strftime("%B-%d-%Y").lower()  # "september-13-2021"
url = f"{BASE_URL}/{date_obj.year}/{date_obj.month:02d}/{date_obj.day:02d}/wof-recap-{date_str}/"
```

### 2. **Enhanced Player Name Extraction**
Three extraction patterns to catch various formats:
- **Pattern 1**: "Tonight's contestants: Name1, Name2, and Name3"
- **Pattern 2**: Position markers (Red:, Yellow:, Blue: or $1000:, $2000:, $3000:)
- **Pattern 3**: Bold tags (Andy often bolds player names)

### 3. **Improved Event Detection**
Uses word boundaries to avoid false positives:
```python
bankrupts = len(re.findall(r'\bBANKRUPT\b', text, re.IGNORECASE))
lose_a_turns = len(re.findall(r'\bLOSE\s+A\s+TURN\b', text, re.IGNORECASE))
```

### 4. **Data Normalization**
Converts episode-level data to player-level:
- Episode with 3 players and 6 Bankrupts → 3 rows with 2.0 estimated bankrupts each
- **Important**: This is an *estimate* since we don't have spin-level data

### 5. **Better Error Handling**
- Distinguishes between network errors and missing episodes
- Provides detailed progress output
- Respects server with configurable delays

## Usage Example

```python
from src.scraper import WoFScraper
from datetime import datetime

# Initialize scraper
scraper = WoFScraper(delay=1.0, data_dir="data/raw")

# Scrape a date range
start = datetime(2021, 9, 13)  # Season 39 premiere
end = datetime(2021, 10, 13)
df = scraper.batch_scrape_season(start, end)

# Save episode-level data
scraper.save_to_csv(df, "season_39_episodes.csv")

# Normalize to player-level
player_df = scraper.normalize_player_data(df)
scraper.save_to_csv(player_df, "season_39_players.csv")
```

## Data Integrity Considerations

### What We Measure
- **Bankrupts**: Count of "BANKRUPT" occurrences in recap text
- **Lose-a-Turns**: Count of "LOSE A TURN" occurrences in recap text

### Known Limitations
1. **Inter-Observer Reliability**: Single coder (Andy) writing recaps
   - No inter-rater reliability testing
   - Potential for human transcription errors
   
2. **Missing Spin-Level Data**: We don't know *which player* hit each event
   - Current solution: Distribute evenly across players
   - Better solution: Manual coding from video (future work)

3. **Missing Episodes**: Gaps in coverage
   - Use `analysis.py` to identify missing episodes
   - Consider multiple sources or manual verification

4. **Gender Classification**: Currently uses simple name-based heuristic
   - **Critical**: Replace with proper gender-name database (US SSA data)
   - **Best practice**: Manual verification + multiple coders

## Next Steps

1. **Test the scraper** on a small date range
2. **Validate player extraction** manually on sample episodes
3. **Implement proper gender classification** using census data
4. **Run gap analysis** to identify missing episodes
5. **Consider manual coding** for a subset to validate automated counts
