# scripts/inspect_csvs.py

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")

files = [
    "nba_schedule_2025.csv",
    "nba_pbp_2025.csv",
    "nba_player_box_scores_2025.csv"
]

for file in files:
    path = RAW_DIR / file

    print("\n" + "=" * 80)
    print(f"FILE: {file}")
    print("=" * 80)

    df = pd.read_csv(path)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    for col in df.columns:
        print(f"- {col}")

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nMissing values:")
    print(df.isna().sum().sort_values(ascending=False).head(20))