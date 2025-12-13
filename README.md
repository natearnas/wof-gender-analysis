## Study Summary (S36–S41)

- Key Question: Did the plastic cap alter gender dynamics in winnings?
- Dataset: 1,170 episodes, 7,668 player records
- Main Finding: The male advantage in winnings decreased by ~$1,275 during the plastic cap era (p=0.006, DiD regression). Global winnings stayed stable (p=0.488).

### Hypothesis Testing (Cross-Sectional)
- Mean difference (Men − Women): ~$823
- Mann-Whitney U: p=0.0126
- Bootstrap 95% CI: [$377, $1,276] (excludes $0)

### Longitudinal DiD (Interface Change)
- Treatment: S38–S39 (plastic cap era)
- Control: S36–S37, S40–S41
- Interaction term (Gender × Treatment): −$1,275 (p=0.006)
- Robustness: Mann-Whitney and bootstrap confirm effect; global economy unchanged.

## Quick Start
4. Run analyses:

    - Data validation (player-level expansion, gap plots)

      ```powershell
      .venv\Scripts\python.exe 01_data_validation.py
      ```

    - Hypothesis testing (t-test, MWU, bootstrap)

      ```powershell
      .venv\Scripts\python.exe 02_hypothesis_testing.py
      ```

    - Longitudinal DiD (regression + robustness checks)

      ```powershell
      .venv\Scripts\python.exe 03_longitudinal_analysis.py
      ```

## Key Outputs

- Summaries:
  - data/processed/hypothesis_testing_results.txt
  - data/processed/longitudinal_did_results.txt

- Plots:
  - comprehensive_analysis.png
  - did_analysis_trend.png
  - winnings_by_era_barplot.png
  - gender_comparison.png
  - gap_analysis.png

- Data:
  - data/processed/player_level_data.csv
  - data/processed/longitudinal_data_raw.csv
  - data/processed/S36_raw.csv … S41_raw.csv

## Notes

- Missing data (~22% episodes) largely reflect summer hiatus/coverage gaps.
- Gender for some players marked Unknown; consider manual validation for reliability.
- For publication, review assumptions (parallel trends) and add placebo checks.
# Wheel of Fortune Gender Analysis

A data science project analyzing Wheel of Fortune spin outcomes to test for gender-based variances in "Bankrupt" and "Lose a Turn" frequencies. This project demonstrates experimental design rigor, data integrity analysis, gap analysis, and inter-observer reliability.

## Project Goal

Test whether there are statistically significant gender-based differences in:
- Bankrupt frequency
- Lose-a-Turn frequency

Focus areas:
- **Data Integrity**: Identify and document missing episodes
- **Gap Analysis**: Visualize data continuity
- **Inter-Observer Reliability**: Validate gender classifications
- **Statistical Rigor**: Proper normalization and hypothesis testing

## Project Structure

```
wof-gender-analysis/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # WoFScraper class for data collection
│   └── utils.py            # Data normalization and statistical utilities
├── data/
│   ├── raw/                # Raw scraped data
│   └── processed/          # Cleaned and normalized data
├── main.py                 # Driver script for batch scraping
├── analysis.py             # Statistical analysis and visualization
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Create a virtual environment** (recommended):
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Data Collection

Run `main.py` to scrape episode data from Andy's WoF Blog:

```bash
python main.py
```

This will:
- Scrape episodes from the configured date range (default: Sept-Oct 2021)
- Extract bankrupts, lose-a-turns, and player names
- Save data to `data/processed/season_39_sample.csv`

### 2. Data Analysis

Run `analysis.py` to perform statistical analysis:

```bash
python analysis.py
```

This will:
- Load scraped data
- Perform gap analysis (identify missing episodes)
- Normalize to player-level data
- Add gender classifications
- Run statistical tests (t-tests, Cohen's d)
- Generate visualizations

## Key Features

### WoFScraper
- **Batch scraping** across date ranges
- **Player name extraction** from episode recaps
- **Automatic retry logic** for missing episodes
- **Respectful rate limiting** (configurable delay)

### Data Normalization
- **Episode → Player conversion**: Expands episode data to per-player records
- **Per-spin rates**: Normalizes frequencies by estimated spins
- **Gender classification**: Basic name-based heuristic (requires manual verification)

### Statistical Analysis
- **Independent samples t-test**: Test for gender differences
- **Cohen's d**: Effect size calculation
- **Gap metrics**: Data completeness reporting
- **Inter-observer reliability**: Cohen's Kappa implementation

### Visualizations
- **Gap analysis barcode plot**: Shows data continuity
- **Gender comparison boxplots**: Bankrupt and Lose-a-Turn rates

## Data Sources

- **Andy's WoF Blog**: https://buyavowel.boards.net/
- Fan-maintained episode recaps with spin-by-spin details

## Methodology Notes

### Gender Classification
The current implementation uses a **basic name-based heuristic** for gender classification. For rigorous research:

1. **Manual verification**: Review all "Unknown" classifications
2. **Multiple coders**: Have 2+ independent coders classify a sample
3. **Inter-rater reliability**: Calculate Cohen's Kappa (target: >0.80)
4. **Gender database**: Use SSA baby names or similar for better accuracy

### Statistical Power
- Current sample: ~1 month of episodes
- Recommended: Full season (190+ episodes) for robust conclusions
- Consider multiple seasons for generalizability

### Limitations
1. **Player names**: Not all episodes have clear player name extraction
2. **Spin distribution**: Assumes equal spins per player (~20 each)
3. **Actual spin data**: Not available; using episode-level aggregates
4. **Gender as binary**: Simplified classification for this analysis

## Example Output

```
=== WHEEL OF FORTUNE GENDER ANALYSIS ===

Loading episode data...
✓ Loaded 23 episodes.

--- DATA INTEGRITY REPORT ---
Expected Episodes: 25
Captured Episodes: 23
Missing Episodes:  2
Completeness:      92.0%

--- NORMALIZING TO PLAYER LEVEL ---
✓ Expanded to 69 player records
  Gender breakdown:
    Male:    34
    Female:  28
    Unknown: 7

--- STATISTICAL ANALYSIS ---

Bankrupt Rate Analysis:
  Male (n=34):   0.0458 ± 0.0231
  Female (n=28): 0.0421 ± 0.0198
  t-statistic: 0.678
  p-value:     0.5011
  Cohen's d:   0.173 (Negligible)
  Significant: NO (α=0.05)
```

## Future Enhancements

- [ ] Automated gender API (e.g., genderize.io)
- [ ] Actual spin counts (requires more detailed scraping)
- [ ] Position effects (Red vs Yellow vs Blue player)
- [ ] Temporal analysis (season-over-season trends)
- [ ] Machine learning classification (player behavior patterns)

## Blog Post Topics

This project demonstrates several experimental design concepts:

1. **Data Integrity**: Gap analysis and completeness metrics
2. **Inter-Observer Reliability**: Cohen's Kappa for validation
3. **Normalization**: Why per-player rates matter
4. **Effect Sizes**: Beyond p-values (Cohen's d interpretation)
5. **Transparent Limitations**: Documenting assumptions and constraints

## License

Educational/Research Use

## Author

Data Science Blog Post Project
Contact: [Your email/contact]

## Acknowledgments

- Andy's WoF Blog community for episode recaps
- Wheel of Fortune for providing entertainment and data
