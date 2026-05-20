# scripts/create_fact_player_game_stats.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

box_path = PROCESSED_DIR / f"clean_nba_player_box_scores_{season}.csv"
output_path = PROCESSED_DIR / f"fact_player_game_stats_{season}.csv"

box = pd.read_csv(box_path)

# Standardize column names again just in case
box.columns = (
    box.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Available player box score columns:")
print(box.columns.tolist())


def find_column(df, options):
    """
    Finds the first matching column name from a list of possible names.
    """
    for option in options:
        if option in df.columns:
            return option
    return None


possible_columns = {
    "game_id": [
        "game_id",
        "id",
        "gameid",
        "event_id",
        "eventid",
        "competition_id"
    ],
    "season": [
        "season",
        "year"
    ],
    "game_date": [
        "game_date",
        "date",
        "start_date",
        "game_date_time",
        "game_datetime"
    ],
    "team": [
        "team",
        "team_name",
        "team_short_display_name",
        "team_abbreviation",
        "athlete_team",
        "team_display_name"
    ],
    "team_id": [
        "team_id",
        "team_uid",
        "athlete_team_id"
    ],
    "opponent": [
        "opponent",
        "opponent_name",
        "opponent_team",
        "opponent_display_name"
    ],
    "player_id": [
        "player_id",
        "athlete_id",
        "athlete_uid",
        "id"
    ],
    "player_name": [
        "player_name",
        "athlete_display_name",
        "athlete_name",
        "name",
        "display_name"
    ],
    "position": [
        "position",
        "athlete_position",
        "position_abbreviation"
    ],
    "starter": [
        "starter",
        "is_starter",
        "started"
    ],
    "minutes": [
        "minutes",
        "min",
        "minutes_played"
    ],
    "points": [
        "points",
        "pts"
    ],
    "rebounds": [
        "rebounds",
        "reb",
        "total_rebounds"
    ],
    "assists": [
        "assists",
        "ast"
    ],
    "steals": [
        "steals",
        "stl"
    ],
    "blocks": [
        "blocks",
        "blk"
    ],
    "turnovers": [
        "turnovers",
        "to"
    ],
    "personal_fouls": [
        "personal_fouls",
        "pf",
        "fouls"
    ],
    "field_goals_made": [
        "field_goals_made",
        "fgm"
    ],
    "field_goals_attempted": [
        "field_goals_attempted",
        "fga"
    ],
    "three_point_field_goals_made": [
        "three_point_field_goals_made",
        "three_pointers_made",
        "three_point_made",
        "3pm",
        "fg3m"
    ],
    "three_point_field_goals_attempted": [
        "three_point_field_goals_attempted",
        "three_pointers_attempted",
        "three_point_attempts",
        "3pa",
        "fg3a"
    ],
    "free_throws_made": [
        "free_throws_made",
        "ftm"
    ],
    "free_throws_attempted": [
        "free_throws_attempted",
        "fta"
    ],
    "offensive_rebounds": [
        "offensive_rebounds",
        "oreb",
        "orb"
    ],
    "defensive_rebounds": [
        "defensive_rebounds",
        "dreb",
        "drb"
    ],
    "plus_minus": [
        "plus_minus",
        "plusminus",
        "pm"
    ]
}

cols = {key: find_column(box, values) for key, values in possible_columns.items()}

print("\nDetected player box score columns:")
for key, value in cols.items():
    print(f"{key}: {value}")

required = ["game_id", "player_name", "team"]

missing = [col for col in required if cols[col] is None]

if missing:
    raise ValueError(
        f"Missing required columns for fact_player_game_stats: {missing}. "
        "Check the printed box score columns and add the correct names to possible_columns."
    )

fact_player_stats = pd.DataFrame()

fact_player_stats["game_id"] = box[cols["game_id"]].astype(str)

if cols["season"]:
    fact_player_stats["season"] = box[cols["season"]]
else:
    fact_player_stats["season"] = season

if cols["game_date"]:
    fact_player_stats["game_date"] = pd.to_datetime(
        box[cols["game_date"]],
        errors="coerce"
    )
else:
    fact_player_stats["game_date"] = pd.NaT

if cols["team_id"]:
    fact_player_stats["team_id"] = box[cols["team_id"]].astype(str)
else:
    fact_player_stats["team_id"] = None

fact_player_stats["team"] = box[cols["team"]]

if cols["opponent"]:
    fact_player_stats["opponent"] = box[cols["opponent"]]
else:
    fact_player_stats["opponent"] = None

if cols["player_id"]:
    fact_player_stats["player_id"] = box[cols["player_id"]].astype(str)
else:
    fact_player_stats["player_id"] = None

fact_player_stats["player_name"] = box[cols["player_name"]]

if cols["position"]:
    fact_player_stats["position"] = box[cols["position"]]
else:
    fact_player_stats["position"] = None

if cols["starter"]:
    fact_player_stats["starter"] = box[cols["starter"]]
else:
    fact_player_stats["starter"] = None


def add_numeric_column(output_df, source_df, output_col, source_col):
    """
    Adds a numeric stat column.
    If source column is missing, fills with 0.
    """
    if source_col:
        output_df[output_col] = pd.to_numeric(source_df[source_col], errors="coerce").fillna(0)
    else:
        output_df[output_col] = 0


numeric_stat_map = {
    "minutes": cols["minutes"],
    "points": cols["points"],
    "rebounds": cols["rebounds"],
    "assists": cols["assists"],
    "steals": cols["steals"],
    "blocks": cols["blocks"],
    "turnovers": cols["turnovers"],
    "personal_fouls": cols["personal_fouls"],
    "field_goals_made": cols["field_goals_made"],
    "field_goals_attempted": cols["field_goals_attempted"],
    "three_point_field_goals_made": cols["three_point_field_goals_made"],
    "three_point_field_goals_attempted": cols["three_point_field_goals_attempted"],
    "free_throws_made": cols["free_throws_made"],
    "free_throws_attempted": cols["free_throws_attempted"],
    "offensive_rebounds": cols["offensive_rebounds"],
    "defensive_rebounds": cols["defensive_rebounds"],
    "plus_minus": cols["plus_minus"]
}

for output_col, source_col in numeric_stat_map.items():
    add_numeric_column(fact_player_stats, box, output_col, source_col)

# Derived shooting metrics
fact_player_stats["field_goal_pct"] = (
    fact_player_stats["field_goals_made"] / fact_player_stats["field_goals_attempted"]
).where(fact_player_stats["field_goals_attempted"] > 0, 0)

fact_player_stats["three_point_pct"] = (
    fact_player_stats["three_point_field_goals_made"] /
    fact_player_stats["three_point_field_goals_attempted"]
).where(fact_player_stats["three_point_field_goals_attempted"] > 0, 0)

fact_player_stats["free_throw_pct"] = (
    fact_player_stats["free_throws_made"] / fact_player_stats["free_throws_attempted"]
).where(fact_player_stats["free_throws_attempted"] > 0, 0)

# Estimated true shooting percentage
# TS% = PTS / (2 * (FGA + 0.44 * FTA))
shot_attempt_denominator = 2 * (
    fact_player_stats["field_goals_attempted"] +
    0.44 * fact_player_stats["free_throws_attempted"]
)

fact_player_stats["true_shooting_pct_est"] = (
    fact_player_stats["points"] / shot_attempt_denominator
).where(shot_attempt_denominator > 0, 0)

# Simple fantasy-style production score
fact_player_stats["production_score"] = (
    fact_player_stats["points"] * 1.0
    + fact_player_stats["rebounds"] * 1.2
    + fact_player_stats["assists"] * 1.5
    + fact_player_stats["steals"] * 3.0
    + fact_player_stats["blocks"] * 3.0
    - fact_player_stats["turnovers"] * 1.0
)

# Remove exact duplicates
dedupe_cols = ["game_id", "player_name", "team"]

if "player_id" in fact_player_stats.columns and fact_player_stats["player_id"].notna().any():
    dedupe_cols = ["game_id", "player_id", "team"]

fact_player_stats = fact_player_stats.drop_duplicates(subset=dedupe_cols)

# Sort
fact_player_stats = fact_player_stats.sort_values(
    ["game_date", "game_id", "team", "player_name"],
    na_position="last"
)

fact_player_stats.to_csv(output_path, index=False)

print(f"\nSaved fact_player_game_stats file to: {output_path}")
print(fact_player_stats.head())
print("\nShape:", fact_player_stats.shape)