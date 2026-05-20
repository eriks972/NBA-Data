# scripts/check_nba_data_quality.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

files = {
    "fact_games": PROCESSED_DIR / f"fact_games_{season}.csv",
    "fact_player_game_stats": PROCESSED_DIR / f"fact_player_game_stats_{season}.csv",
    "mart_team_dashboard_summary": PROCESSED_DIR / f"mart_team_dashboard_summary_{season}.csv",
}

for name, path in files.items():
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    df = pd.read_csv(path)

    print("Shape:", df.shape)
    print("Columns:")
    print(df.columns.tolist())

    if "team" in df.columns and "games_played" in df.columns:
        print("\nGames played by team:")
        print(
            df[["team", "games_played", "wins", "losses"]]
            .sort_values("games_played", ascending=False)
            .to_string(index=False)
        )

    if name == "fact_games":
        print("\nUnique home teams:")
        print(sorted(df["home_team"].dropna().unique()))

        print("\nUnique away teams:")
        print(sorted(df["away_team"].dropna().unique()))

        if "game_status" in df.columns:
            print("\nGame status counts:")
            print(df["game_status"].value_counts(dropna=False))

        if "season_type" in df.columns:
            print("\nSeason type counts:")
            print(df["season_type"].value_counts(dropna=False))