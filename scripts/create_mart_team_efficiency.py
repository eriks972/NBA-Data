# scripts/create_mart_team_efficiency.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

fact_games_path = PROCESSED_DIR / f"fact_games_{season}.csv"
fact_player_stats_path = PROCESSED_DIR / f"fact_player_game_stats_{season}.csv"
output_path = PROCESSED_DIR / f"mart_team_efficiency_{season}.csv"

games = pd.read_csv(fact_games_path)
player_stats = pd.read_csv(fact_player_stats_path)

# -----------------------------
# Standardize column names
# -----------------------------

games.columns = (
    games.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

player_stats.columns = (
    player_stats.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Games columns:")
print(games.columns.tolist())

print("\nPlayer stats columns:")
print(player_stats.columns.tolist())

# -----------------------------
# Build team-game rows from fact_games
# -----------------------------
# fact_games has one row per game.
# We convert it into two rows per game:
# one for the home team and one for the away team.

home_games = pd.DataFrame({
    "game_id": games["game_id"].astype(str),
    "season": games["season"],
    "team": games["home_team"],
    "opponent": games["away_team"],
    "location": "home",
    "points_scored": pd.to_numeric(games["home_score"], errors="coerce"),
    "points_allowed": pd.to_numeric(games["away_score"], errors="coerce"),
})

away_games = pd.DataFrame({
    "game_id": games["game_id"].astype(str),
    "season": games["season"],
    "team": games["away_team"],
    "opponent": games["home_team"],
    "location": "away",
    "points_scored": pd.to_numeric(games["away_score"], errors="coerce"),
    "points_allowed": pd.to_numeric(games["home_score"], errors="coerce"),
})

team_games = pd.concat([home_games, away_games], ignore_index=True)

# Remove games without final scores
team_games = team_games.dropna(subset=["points_scored", "points_allowed"])

team_games["point_diff"] = team_games["points_scored"] - team_games["points_allowed"]
team_games["win"] = (team_games["points_scored"] > team_games["points_allowed"]).astype(int)
team_games["loss"] = (team_games["points_scored"] < team_games["points_allowed"]).astype(int)

# -----------------------------
# Aggregate game-level team metrics
# -----------------------------

team_game_summary = (
    team_games
    .groupby(["season", "team"], as_index=False)
    .agg(
        games_played=("game_id", "nunique"),
        wins=("win", "sum"),
        losses=("loss", "sum"),
        avg_points_scored=("points_scored", "mean"),
        avg_points_allowed=("points_allowed", "mean"),
        total_points_scored=("points_scored", "sum"),
        total_points_allowed=("points_allowed", "sum"),
        avg_point_diff=("point_diff", "mean"),
        total_point_diff=("point_diff", "sum"),
        home_games=("location", lambda x: (x == "home").sum()),
        away_games=("location", lambda x: (x == "away").sum()),
    )
)

team_game_summary["win_pct"] = (
    team_game_summary["wins"] / team_game_summary["games_played"]
).where(team_game_summary["games_played"] > 0, 0)

# -----------------------------
# Aggregate player production metrics by team
# -----------------------------

# Make sure numeric columns exist
numeric_cols = [
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
    "turnovers",
    "minutes",
    "field_goals_made",
    "field_goals_attempted",
    "three_point_field_goals_made",
    "three_point_field_goals_attempted",
    "free_throws_made",
    "free_throws_attempted",
    "true_shooting_pct_est",
    "production_score",
]

for col in numeric_cols:
    if col not in player_stats.columns:
        player_stats[col] = 0
    player_stats[col] = pd.to_numeric(player_stats[col], errors="coerce").fillna(0)

player_stats["game_id"] = player_stats["game_id"].astype(str)

player_team_summary = (
    player_stats
    .groupby(["season", "team"], as_index=False)
    .agg(
        total_player_points=("points", "sum"),
        total_rebounds=("rebounds", "sum"),
        total_assists=("assists", "sum"),
        total_steals=("steals", "sum"),
        total_blocks=("blocks", "sum"),
        total_turnovers=("turnovers", "sum"),
        total_minutes=("minutes", "sum"),
        total_fgm=("field_goals_made", "sum"),
        total_fga=("field_goals_attempted", "sum"),
        total_3pm=("three_point_field_goals_made", "sum"),
        total_3pa=("three_point_field_goals_attempted", "sum"),
        total_ftm=("free_throws_made", "sum"),
        total_fta=("free_throws_attempted", "sum"),
        avg_true_shooting_pct=("true_shooting_pct_est", "mean"),
        total_player_production=("production_score", "sum"),
        avg_player_production=("production_score", "mean"),
        unique_players=("player_name", "nunique"),
    )
)

# -----------------------------
# Merge game and player summaries
# -----------------------------

team_efficiency = team_game_summary.merge(
    player_team_summary,
    on=["season", "team"],
    how="left"
)

# Fill missing player summary values
fill_cols = [
    col for col in team_efficiency.columns
    if col not in ["season", "team"]
]

team_efficiency[fill_cols] = team_efficiency[fill_cols].fillna(0)

# -----------------------------
# Derived team efficiency metrics
# -----------------------------

team_efficiency["avg_rebounds_per_game"] = (
    team_efficiency["total_rebounds"] / team_efficiency["games_played"]
).where(team_efficiency["games_played"] > 0, 0)

team_efficiency["avg_assists_per_game"] = (
    team_efficiency["total_assists"] / team_efficiency["games_played"]
).where(team_efficiency["games_played"] > 0, 0)

team_efficiency["avg_turnovers_per_game"] = (
    team_efficiency["total_turnovers"] / team_efficiency["games_played"]
).where(team_efficiency["games_played"] > 0, 0)

team_efficiency["assist_turnover_ratio"] = (
    team_efficiency["total_assists"] / team_efficiency["total_turnovers"]
).where(team_efficiency["total_turnovers"] > 0, 0)

team_efficiency["field_goal_pct"] = (
    team_efficiency["total_fgm"] / team_efficiency["total_fga"]
).where(team_efficiency["total_fga"] > 0, 0)

team_efficiency["three_point_pct"] = (
    team_efficiency["total_3pm"] / team_efficiency["total_3pa"]
).where(team_efficiency["total_3pa"] > 0, 0)

team_efficiency["free_throw_pct"] = (
    team_efficiency["total_ftm"] / team_efficiency["total_fta"]
).where(team_efficiency["total_fta"] > 0, 0)

team_efficiency["points_per_player_minute"] = (
    team_efficiency["total_player_points"] / team_efficiency["total_minutes"]
).where(team_efficiency["total_minutes"] > 0, 0)

# Simple normalized efficiency score
# This combines winning, scoring margin, shooting, ball movement, and production.
# It is not an official NBA metric, but it is useful for portfolio/dashboard analysis.

def min_max_scale(series):
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)

    return (series - min_val) / (max_val - min_val)


team_efficiency["win_pct_score"] = min_max_scale(team_efficiency["win_pct"])
team_efficiency["point_diff_score"] = min_max_scale(team_efficiency["avg_point_diff"])
team_efficiency["shooting_score"] = min_max_scale(team_efficiency["field_goal_pct"])
team_efficiency["three_point_score"] = min_max_scale(team_efficiency["three_point_pct"])
team_efficiency["assist_turnover_score"] = min_max_scale(team_efficiency["assist_turnover_ratio"])
team_efficiency["avg_player_production_per_game"] = (
    team_efficiency["total_player_production"] / team_efficiency["games_played"]
).where(team_efficiency["games_played"] > 0, 0)

team_efficiency["production_score_scaled"] = min_max_scale(
    team_efficiency["avg_player_production_per_game"]
)

team_efficiency["team_efficiency_score"] = (
    team_efficiency["win_pct_score"] * 0.30
    + team_efficiency["point_diff_score"] * 0.25
    + team_efficiency["shooting_score"] * 0.15
    + team_efficiency["three_point_score"] * 0.10
    + team_efficiency["assist_turnover_score"] * 0.10
    + team_efficiency["production_score_scaled"] * 0.10
) * 100

team_efficiency["team_efficiency_rank"] = team_efficiency["team_efficiency_score"].rank(
    ascending=False,
    method="dense"
).astype(int)

# -----------------------------
# Sort and save
# -----------------------------

team_efficiency = team_efficiency.sort_values(
    ["team_efficiency_rank", "team"]
)

team_efficiency.to_csv(output_path, index=False)

print(f"\nSaved team efficiency mart to: {output_path}")
print("\nTop 15 teams by efficiency score:")
print(
    team_efficiency[
        [
            "team",
            "games_played",
            "wins",
            "losses",
            "win_pct",
            "avg_points_scored",
            "avg_points_allowed",
            "avg_point_diff",
            "field_goal_pct",
            "three_point_pct",
            "assist_turnover_ratio",
            "team_efficiency_score",
            "team_efficiency_rank",
        ]
    ].head(15)
)

print("\nShape:", team_efficiency.shape)