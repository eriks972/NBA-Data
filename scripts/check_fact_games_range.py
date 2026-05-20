# scripts/check_fact_games_range.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

fact_games_path = PROCESSED_DIR / f"fact_games_{season}.csv"
games = pd.read_csv(fact_games_path)

games["game_date"] = pd.to_datetime(games["game_date"], errors="coerce")

print("Shape:", games.shape)

print("\nDate range:")
print("Min date:", games["game_date"].min())
print("Max date:", games["game_date"].max())

print("\nGames per team:")
team_counts = pd.concat([
    games["home_team"],
    games["away_team"]
]).value_counts().sort_values(ascending=False)

print(team_counts)

print("\nTotal team-game rows:", team_counts.sum())
print("Total games:", len(games))

print("\nExpected full NBA regular season:")
print("30 teams * 82 games / 2 = 1230 games")
print("Current games:", len(games))
print("Missing games:", 1230 - len(games))