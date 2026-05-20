import os
import pandas as pd
import sportsdataverse.nba as nba

season = 2025

# Create output folder if it does not exist
os.makedirs("data/raw", exist_ok=True)

# Load NBA data
schedule = nba.load_nba_schedule(seasons=[season], return_as_pandas=True)
pbp = nba.load_nba_pbp(seasons=[season], return_as_pandas=True)
player_box_scores = nba.load_nba_player_boxscore(seasons=[season], return_as_pandas=True)

# Optional: preview data
print("Schedule shape:", schedule.shape)
print("Play-by-play shape:", pbp.shape)
print("Player box scores shape:", player_box_scores.shape)

# Save to CSV
schedule.to_csv(f"data/raw/nba_schedule_{season}.csv", index=False)
pbp.to_csv(f"data/raw/nba_pbp_{season}.csv", index=False)
player_box_scores.to_csv(f"data/raw/nba_player_box_scores_{season}.csv", index=False)

print("NBA CSV files saved successfully.")