# scripts/create_player_value_mart.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

box_path = PROCESSED_DIR / f"clean_nba_player_box_scores_{season}.csv"
df = pd.read_csv(box_path)

print("Available columns:")
print(df.columns.tolist())

# Rename these after checking your actual column names
# These are common possible names, but you may need to adjust them.
possible_columns = {
    "player_name": ["athlete_display_name", "player_name", "name"],
    "team": ["team_short_display_name", "team_name", "team_abbreviation"],
    "points": ["points", "pts"],
    "rebounds": ["rebounds", "reb"],
    "assists": ["assists", "ast"],
    "minutes": ["minutes", "min"],
    "field_goals_attempted": ["field_goals_attempted", "fga"],
    "free_throws_attempted": ["free_throws_attempted", "fta"],
    "three_point_field_goals_attempted": ["three_point_field_goals_attempted", "three_point_attempts", "3pa"],
    "turnovers": ["turnovers", "to"]
}

def find_column(df, options):
    for option in options:
        if option in df.columns:
            return option
    return None

cols = {key: find_column(df, values) for key, values in possible_columns.items()}

print("\nDetected columns:")
for key, value in cols.items():
    print(f"{key}: {value}")

required = ["player_name", "team", "points", "rebounds", "assists", "minutes"]

missing = [col for col in required if cols[col] is None]

if missing:
    raise ValueError(f"Missing required columns: {missing}. Check your CSV column names above.")

# Convert numeric columns safely
numeric_keys = [
    "points",
    "rebounds",
    "assists",
    "minutes",
    "field_goals_attempted",
    "free_throws_attempted",
    "three_point_field_goals_attempted",
    "turnovers"
]

for key in numeric_keys:
    col = cols.get(key)
    if col is not None:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

group_cols = [cols["player_name"], cols["team"]]

agg_dict = {
    cols["points"]: "sum",
    cols["rebounds"]: "sum",
    cols["assists"]: "sum",
    cols["minutes"]: "sum"
}

optional_sum_cols = [
    "field_goals_attempted",
    "free_throws_attempted",
    "three_point_field_goals_attempted",
    "turnovers"
]

for key in optional_sum_cols:
    if cols.get(key) is not None:
        agg_dict[cols[key]] = "sum"

player_value = (
    df.groupby(group_cols)
    .agg(agg_dict)
    .reset_index()
)

player_value["games_played"] = (
    df.groupby(group_cols)
    .size()
    .values
)

# Rename columns to clean names
rename_map = {
    cols["player_name"]: "player_name",
    cols["team"]: "team",
    cols["points"]: "total_points",
    cols["rebounds"]: "total_rebounds",
    cols["assists"]: "total_assists",
    cols["minutes"]: "total_minutes"
}

if cols.get("field_goals_attempted"):
    rename_map[cols["field_goals_attempted"]] = "total_fga"

if cols.get("free_throws_attempted"):
    rename_map[cols["free_throws_attempted"]] = "total_fta"

if cols.get("three_point_field_goals_attempted"):
    rename_map[cols["three_point_field_goals_attempted"]] = "total_3pa"

if cols.get("turnovers"):
    rename_map[cols["turnovers"]] = "total_turnovers"

player_value = player_value.rename(columns=rename_map)

# Per-game metrics
player_value["points_per_game"] = player_value["total_points"] / player_value["games_played"]
player_value["rebounds_per_game"] = player_value["total_rebounds"] / player_value["games_played"]
player_value["assists_per_game"] = player_value["total_assists"] / player_value["games_played"]
player_value["minutes_per_game"] = player_value["total_minutes"] / player_value["games_played"]

if "total_turnovers" in player_value.columns:
    player_value["turnovers_per_game"] = player_value["total_turnovers"] / player_value["games_played"]

# Simple production score
player_value["production_score"] = (
    player_value["points_per_game"] * 1.0
    + player_value["rebounds_per_game"] * 1.2
    + player_value["assists_per_game"] * 1.5
)

# Rank players by production score
player_value["production_rank"] = player_value["production_score"].rank(
    ascending=False,
    method="dense"
)

player_value = player_value.sort_values("production_score", ascending=False)

output_path = PROCESSED_DIR / f"mart_player_value_{season}.csv"
player_value.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(player_value.head(20))