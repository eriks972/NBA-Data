# scripts/clean_nba_data.py

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

season = 2025

schedule_path = RAW_DIR / f"nba_schedule_{season}.csv"
pbp_path = RAW_DIR / f"nba_pbp_{season}.csv"
box_path = RAW_DIR / f"nba_player_box_scores_{season}.csv"

schedule = pd.read_csv(schedule_path)
pbp = pd.read_csv(pbp_path)
player_box = pd.read_csv(box_path)

# -----------------------------
# Clean Schedule
# -----------------------------

schedule_clean = schedule.copy()

schedule_clean.columns = (
    schedule_clean.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Save cleaned schedule
schedule_clean.to_csv(
    PROCESSED_DIR / f"clean_nba_schedule_{season}.csv",
    index=False
)

# -----------------------------
# Clean Play-by-Play
# -----------------------------

pbp_clean = pbp.copy()

pbp_clean.columns = (
    pbp_clean.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Drop exact duplicate rows
pbp_clean = pbp_clean.drop_duplicates()

pbp_clean.to_csv(
    PROCESSED_DIR / f"clean_nba_pbp_{season}.csv",
    index=False
)

# -----------------------------
# Clean Player Box Scores
# -----------------------------

player_box_clean = player_box.copy()

player_box_clean.columns = (
    player_box_clean.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Drop exact duplicate rows
player_box_clean = player_box_clean.drop_duplicates()

player_box_clean.to_csv(
    PROCESSED_DIR / f"clean_nba_player_box_scores_{season}.csv",
    index=False
)

print("Cleaned NBA CSVs saved successfully.")
print(f"Schedule: {schedule_clean.shape}")
print(f"Play-by-play: {pbp_clean.shape}")
print(f"Player box scores: {player_box_clean.shape}")