import pandas as pd

# Load longitudinal data
df = pd.read_csv('data/processed/longitudinal_data_raw.csv')

print('=' * 70)
print('LONGITUDINAL DATA SUMMARY (6-SEASON SCRAPE)')
print('=' * 70)
print(f'\nTotal Rows: {len(df):,}')
print(f'Total Columns: {len(df.columns)}')
print(f'\nColumns: {list(df.columns)}')

print('\n' + '=' * 70)
print('ROWS PER SEASON')
print('=' * 70)
season_counts = df['season_id'].value_counts().sort_index()
for season, count in season_counts.items():
    print(f'{season}: {count:,} rows')

print('\n' + '=' * 70)
print('GENDER DISTRIBUTION (OVERALL)')
print('=' * 70)
if 'gender' in df.columns:
    gender_counts = df['gender'].value_counts(dropna=False)
    print(gender_counts)
    print(f'Missing gender: {df["gender"].isna().sum()}')

print('\n' + '=' * 70)
print('MISSING DATA BY COLUMN')
print('=' * 70)
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
for col in df.columns:
    if missing[col] > 0:
        print(f'{col}: {missing[col]} ({missing_pct[col]}%)')

print('\n' + '=' * 70)
print('SAMPLE ROWS')
print('=' * 70)
print(df.head(3).to_string())
