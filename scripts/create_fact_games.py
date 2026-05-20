# scripts/create_fact_games.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

schedule_path = PROCESSED_DIR / f"clean_nba_schedule_{season}.csv"
output_path = PROCESSED_DIR / f"fact_games_{season}.csv"

schedule = pd.read_csv(schedule_path)

schedule.columns = (
    schedule.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Available schedule columns:")
print(schedule.columns.tolist())


def find_column(df, options):
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
    "game_date": [
        "game_date",
        "date",
        "start_date",
        "game_date_time",
        "game_datetime",
        "commence_time"
    ],
    "season": [
        "season",
        "year"
    ],
    "season_type": [
        "season_type",
        "season_type_id",
        "seasontype",
        "type",
        "season_slug"
    ],
    "home_team": [
        "home_team",
        "home_team_name",
        "home_display_name",
        "home_short_display_name",
        "home_team_short_display_name",
        "home_name"
    ],
    "away_team": [
        "away_team",
        "away_team_name",
        "away_display_name",
        "away_short_display_name",
        "away_team_short_display_name",
        "away_name"
    ],
    "home_team_id": [
        "home_team_id",
        "home_id",
        "home_team_uid"
    ],
    "away_team_id": [
        "away_team_id",
        "away_id",
        "away_team_uid"
    ],
    "home_score": [
        "home_score",
        "home_points",
        "home_team_score",
        "home_total",
        "home_score_total"
    ],
    "away_score": [
        "away_score",
        "away_points",
        "away_team_score",
        "away_total",
        "away_score_total"
    ],
    "venue": [
        "venue",
        "venue_name",
        "arena",
        "site"
    ],
    "status": [
        "status",
        "game_status",
        "status_type_name",
        "status_name"
    ]
}

cols = {key: find_column(schedule, values) for key, values in possible_columns.items()}

print("\nDetected schedule columns:")
for key, value in cols.items():
    print(f"{key}: {value}")

required = ["game_id", "home_team", "away_team", "home_score", "away_score"]
missing = [col for col in required if cols[col] is None]

if missing:
    raise ValueError(
        f"Missing required columns for fact_games: {missing}. "
        "Check the printed schedule columns and add the correct names to possible_columns."
    )

fact_games = pd.DataFrame()

fact_games["game_id"] = schedule[cols["game_id"]].astype(str)

if cols["game_date"]:
    fact_games["game_date"] = pd.to_datetime(schedule[cols["game_date"]], errors="coerce")
else:
    fact_games["game_date"] = pd.NaT

if cols["season"]:
    fact_games["season"] = schedule[cols["season"]]
else:
    fact_games["season"] = season

if cols["season_type"]:
    fact_games["season_type"] = schedule[cols["season_type"]]
else:
    fact_games["season_type"] = None

fact_games["home_team"] = schedule[cols["home_team"]]
fact_games["away_team"] = schedule[cols["away_team"]]

if cols["home_team_id"]:
    fact_games["home_team_id"] = schedule[cols["home_team_id"]].astype(str)
else:
    fact_games["home_team_id"] = None

if cols["away_team_id"]:
    fact_games["away_team_id"] = schedule[cols["away_team_id"]].astype(str)
else:
    fact_games["away_team_id"] = None

fact_games["home_score"] = pd.to_numeric(schedule[cols["home_score"]], errors="coerce")
fact_games["away_score"] = pd.to_numeric(schedule[cols["away_score"]], errors="coerce")

if cols["venue"]:
    fact_games["venue"] = schedule[cols["venue"]]
else:
    fact_games["venue"] = None

if cols["status"]:
    fact_games["game_status"] = schedule[cols["status"]]
else:
    fact_games["game_status"] = None

# --------------------------------------------------
# FILTER 1: Keep only games with final scores
# --------------------------------------------------

fact_games = fact_games.dropna(subset=["home_score", "away_score"])

# --------------------------------------------------
# FILTER 2: Remove All-Star / special teams
# --------------------------------------------------

non_nba_teams = [
    "Team Shaq",
    "Team Chuck",
    "Team Kenny",
    "Team Candace",
    "Team LeBron",
    "Team Giannis",
    "Team Durant",
    "Team Stephen",
    "Team USA",
    "Team World",
]

fact_games = fact_games[
    ~fact_games["home_team"].isin(non_nba_teams)
    & ~fact_games["away_team"].isin(non_nba_teams)
]

# --------------------------------------------------
# FILTER 3: Try to keep regular season only
# --------------------------------------------------
# In many sports datasets:
# season_type 2 = regular season
# season_type 3 = postseason/playoffs
#
# But if your file uses text labels, this also handles that.

if "season_type" in fact_games.columns and fact_games["season_type"].notna().any():
    fact_games["season_type_str"] = fact_games["season_type"].astype(str).str.lower()

    regular_values = [
        "2",
        "regular",
        "regular season",
        "reg",
        "regular-season"
    ]

    fact_games = fact_games[
        fact_games["season_type_str"].isin(regular_values)
    ]

    fact_games = fact_games.drop(columns=["season_type_str"])

# --------------------------------------------------
# Derived fields
# --------------------------------------------------

fact_games["winner"] = None

fact_games.loc[
    fact_games["home_score"] > fact_games["away_score"],
    "winner"
] = fact_games["home_team"]

fact_games.loc[
    fact_games["away_score"] > fact_games["home_score"],
    "winner"
] = fact_games["away_team"]

fact_games["home_win"] = (
    fact_games["home_score"] > fact_games["away_score"]
).astype(int)

fact_games["home_point_diff"] = fact_games["home_score"] - fact_games["away_score"]

# Remove duplicate games
fact_games = fact_games.drop_duplicates(subset=["game_id"])

# Sort
fact_games = fact_games.sort_values(["game_date", "game_id"])

fact_games.to_csv(output_path, index=False)

print(f"\nSaved fact_games file to: {output_path}")

print("\nGames per team after filtering:")
team_counts = pd.concat([
    fact_games["home_team"],
    fact_games["away_team"]
]).value_counts().sort_values(ascending=False)

print(team_counts)

print("\nShape:", fact_games.shape)