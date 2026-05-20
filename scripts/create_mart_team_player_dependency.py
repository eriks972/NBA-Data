# scripts/create_mart_team_player_dependency.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

player_value_path = PROCESSED_DIR / f"mart_player_value_{season}.csv"
fact_games_path = PROCESSED_DIR / f"fact_games_{season}.csv"
output_path = PROCESSED_DIR / f"mart_team_player_dependency_{season}.csv"

player_value = pd.read_csv(player_value_path)
fact_games = pd.read_csv(fact_games_path)

# Standardize columns
player_value.columns = (
    player_value.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

fact_games.columns = (
    fact_games.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Player value columns:")
print(player_value.columns.tolist())

print("\nFact games columns:")
print(fact_games.columns.tolist())

# --------------------------------------------------
# Get valid NBA teams from cleaned fact_games
# --------------------------------------------------

valid_teams = set(fact_games["home_team"].dropna().unique()) | set(
    fact_games["away_team"].dropna().unique()
)

print("\nValid NBA teams from fact_games:")
print(sorted(valid_teams))

# --------------------------------------------------
# Standardize player_value team names to match fact_games
# --------------------------------------------------

TEAM_NAME_MAP = {
    "Hawks": "Atlanta Hawks",
    "Celtics": "Boston Celtics",
    "Nets": "Brooklyn Nets",
    "Hornets": "Charlotte Hornets",
    "Bulls": "Chicago Bulls",
    "Cavaliers": "Cleveland Cavaliers",
    "Mavericks": "Dallas Mavericks",
    "Nuggets": "Denver Nuggets",
    "Pistons": "Detroit Pistons",
    "Warriors": "Golden State Warriors",
    "Rockets": "Houston Rockets",
    "Pacers": "Indiana Pacers",
    "Clippers": "LA Clippers",
    "Lakers": "Los Angeles Lakers",
    "Grizzlies": "Memphis Grizzlies",
    "Heat": "Miami Heat",
    "Bucks": "Milwaukee Bucks",
    "Timberwolves": "Minnesota Timberwolves",
    "Pelicans": "New Orleans Pelicans",
    "Knicks": "New York Knicks",
    "Thunder": "Oklahoma City Thunder",
    "Magic": "Orlando Magic",
    "76ers": "Philadelphia 76ers",
    "Suns": "Phoenix Suns",
    "Trail Blazers": "Portland Trail Blazers",
    "Kings": "Sacramento Kings",
    "Spurs": "San Antonio Spurs",
    "Raptors": "Toronto Raptors",
    "Jazz": "Utah Jazz",
    "Wizards": "Washington Wizards",
}

player_value["team"] = player_value["team"].replace(TEAM_NAME_MAP)

# --------------------------------------------------
# Remove non-NBA teams and keep only valid teams
# --------------------------------------------------

player_value = player_value[player_value["team"].isin(valid_teams)].copy()

print("\nTeams after filtering player_value:")
print(sorted(player_value["team"].dropna().unique()))

# --------------------------------------------------
# Detect production column
# --------------------------------------------------

possible_production_cols = [
    "production_score",
    "total_production_score",
    "player_production_score",
]

production_col = None

for col in possible_production_cols:
    if col in player_value.columns:
        production_col = col
        break

if production_col is None:
    raise ValueError(
        "Could not find a production score column in mart_player_value_2025.csv. "
        "Expected one of: production_score, total_production_score, player_production_score."
    )

required_cols = ["team", "player_name", production_col]

missing = [col for col in required_cols if col not in player_value.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

player_value[production_col] = pd.to_numeric(
    player_value[production_col],
    errors="coerce"
).fillna(0)

print(f"\nUsing production column: {production_col}")
print("Total production:", player_value[production_col].sum())

if player_value[production_col].sum() == 0:
    raise ValueError(
        "Production score is still 0 in mart_player_value_2025.csv. "
        "That means the player value mart needs to be fixed first."
    )

# --------------------------------------------------
# Team totals
# --------------------------------------------------

team_totals = (
    player_value
    .groupby("team", as_index=False)
    .agg(
        total_team_production=(production_col, "sum"),
        roster_players=("player_name", "nunique"),
        avg_player_production=(production_col, "mean"),
    )
)

# --------------------------------------------------
# Rank players within each team
# --------------------------------------------------

player_value["team_production_rank"] = (
    player_value
    .groupby("team")[production_col]
    .rank(ascending=False, method="first")
)

top_players = player_value[player_value["team_production_rank"] <= 3].copy()
top_players["team_production_rank"] = top_players["team_production_rank"].astype(int)

top_pivot = (
    top_players
    .pivot_table(
        index="team",
        columns="team_production_rank",
        values=["player_name", production_col],
        aggfunc="first"
    )
)

top_pivot.columns = [
    f"top_{rank}_{metric}"
    for metric, rank in top_pivot.columns
]

top_pivot = top_pivot.reset_index()

team_dependency = team_totals.merge(
    top_pivot,
    on="team",
    how="left"
)

# --------------------------------------------------
# Normalize expected column names
# --------------------------------------------------
# Depending on production_col, pivot creates names like:
# top_1_production_score
# top_1_total_production_score
#
# We standardize them to top_1_production_score.

for i in [1, 2, 3]:
    old_score_col = f"top_{i}_{production_col}"
    new_score_col = f"top_{i}_production_score"

    if old_score_col in team_dependency.columns:
        team_dependency = team_dependency.rename(
            columns={old_score_col: new_score_col}
        )

    name_col = f"top_{i}_player_name"

    if name_col not in team_dependency.columns:
        team_dependency[name_col] = None

    if new_score_col not in team_dependency.columns:
        team_dependency[new_score_col] = 0

    team_dependency[new_score_col] = pd.to_numeric(
        team_dependency[new_score_col],
        errors="coerce"
    ).fillna(0)

# --------------------------------------------------
# Dependency shares
# --------------------------------------------------

team_dependency["top_1_production_share"] = (
    team_dependency["top_1_production_score"] /
    team_dependency["total_team_production"]
).where(team_dependency["total_team_production"] > 0, 0)

team_dependency["top_2_production_share"] = (
    (
        team_dependency["top_1_production_score"]
        + team_dependency["top_2_production_score"]
    )
    / team_dependency["total_team_production"]
).where(team_dependency["total_team_production"] > 0, 0)

team_dependency["top_3_production_share"] = (
    (
        team_dependency["top_1_production_score"]
        + team_dependency["top_2_production_score"]
        + team_dependency["top_3_production_score"]
    )
    / team_dependency["total_team_production"]
).where(team_dependency["total_team_production"] > 0, 0)

# --------------------------------------------------
# Dependency score
# --------------------------------------------------

team_dependency["dependency_score"] = (
    team_dependency["top_1_production_share"] * 0.50
    + team_dependency["top_2_production_share"] * 0.30
    + team_dependency["top_3_production_share"] * 0.20
) * 100

team_dependency["dependency_rank"] = team_dependency["dependency_score"].rank(
    ascending=False,
    method="dense"
).astype(int)

def classify_dependency(score):
    if score >= 55:
        return "High Star Dependency"
    elif score >= 45:
        return "Moderate Star Dependency"
    else:
        return "Balanced Production"

team_dependency["dependency_tier"] = team_dependency["dependency_score"].apply(
    classify_dependency
)

team_dependency = team_dependency.sort_values(
    ["dependency_rank", "team"]
)

team_dependency.to_csv(output_path, index=False)

print(f"\nSaved team dependency file to: {output_path}")

print("\nDependency score check:")
print(
    team_dependency[
        [
            "team",
            "total_team_production",
            "top_1_player_name",
            "top_1_production_score",
            "top_1_production_share",
            "top_2_production_share",
            "top_3_production_share",
            "dependency_score",
            "dependency_rank",
            "dependency_tier",
        ]
    ]
    .sort_values("dependency_score", ascending=False)
    .to_string(index=False)
)

print("\nShape:", team_dependency.shape)