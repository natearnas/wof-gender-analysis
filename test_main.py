from main import SEASONS
print('Seasons config loaded:')
for s in SEASONS:
    print(f'  {s["name"]}: {s["start"].date()} to {s["end"].date()}')
print('✓ Configuration valid')
