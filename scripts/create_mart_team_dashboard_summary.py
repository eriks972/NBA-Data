# scripts/create_mart_team_dashboard_summary.py

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
season = 2025

team_efficiency_path = PROCESSED_DIR / f"mart_team_efficiency_{season}.csv"
team_dependency_path = PROCESSED_DIR / f"mart_team_player_dependency_{season}.csv"
output_path = PROCESSED_DIR / f"mart_team_dashboard_summary_{season}.csv"

team_efficiency = pd.read_csv(team_efficiency_path)
team_dependency = pd.read_csv(team_dependency_path)

# Standardize column names
team_efficiency.columns = (
    team_efficiency.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

team_dependency.columns = (
    team_dependency.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

print("Team efficiency columns:")
print(team_efficiency.columns.tolist())

print("\nTeam dependency columns:")
print(team_dependency.columns.tolist())

# --------------------------------------------------
# Remove non-NBA/special teams if they somehow remain
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

team_efficiency = team_efficiency[~team_efficiency["team"].isin(non_nba_teams)].copy()
team_dependency = team_dependency[~team_dependency["team"].isin(non_nba_teams)].copy()

# --------------------------------------------------
# Merge marts
# --------------------------------------------------

dashboard = team_efficiency.merge(
    team_dependency,
    on="team",
    how="left",
    suffixes=("", "_dependency")
)

# --------------------------------------------------
# Validate merge
# --------------------------------------------------

missing_dependency = dashboard[dashboard["dependency_score"].isna()]["team"].tolist()

if missing_dependency:
    print("\nWARNING: These teams did not match dependency data:")
    print(missing_dependency)

# --------------------------------------------------
# Convert numeric columns
# --------------------------------------------------

dependency_numeric_cols = [
    "total_team_production",
    "roster_players",
    "avg_player_production",
    "top_1_total_production_score",
    "top_2_total_production_score",
    "top_3_total_production_score",
    "top_1_production_share",
    "top_2_production_share",
    "top_3_production_share",
    "dependency_score",
    "dependency_rank",
]

for col in dependency_numeric_cols:
    if col in dashboard.columns:
        dashboard[col] = pd.to_numeric(dashboard[col], errors="coerce").fillna(0)

numeric_cols = [
    "games_played",
    "wins",
    "losses",
    "win_pct",
    "avg_points_scored",
    "avg_points_allowed",
    "avg_point_diff",
    "field_goal_pct",
    "three_point_pct",
    "free_throw_pct",
    "assist_turnover_ratio",
    "team_efficiency_score",
    "team_efficiency_rank",
    "dependency_score",
    "dependency_rank",
]

for col in numeric_cols:
    if col in dashboard.columns:
        dashboard[col] = pd.to_numeric(dashboard[col], errors="coerce").fillna(0)

# --------------------------------------------------
# Create dashboard labels
# --------------------------------------------------

def classify_team_quality(score):
    if score >= 80:
        return "Elite Team"
    elif score >= 65:
        return "Strong Team"
    elif score >= 50:
        return "Average Team"
    elif score >= 35:
        return "Below Average Team"
    else:
        return "Struggling Team"


def classify_balance(dependency_score):
    if dependency_score >= 55:
        return "Star-Heavy"
    elif dependency_score >= 45:
        return "Moderately Star-Dependent"
    else:
        return "Balanced Roster"


def classify_play_style(row):
    scoring = row.get("avg_points_scored", 0)
    three_pct = row.get("three_point_pct", 0)
    assist_to = row.get("assist_turnover_ratio", 0)
    points_allowed = row.get("avg_points_allowed", 999)

    if scoring >= 115 and three_pct >= 0.37:
        return "High-Powered Shooting Team"
    elif scoring >= 112 and assist_to >= 2.0:
        return "Ball Movement Offense"
    elif points_allowed <= 108:
        return "Defense-Oriented Team"
    elif three_pct >= 0.37:
        return "Three-Point Focused Team"
    else:
        return "Balanced/Traditional Team"


dashboard["team_quality_tier"] = dashboard["team_efficiency_score"].apply(
    classify_team_quality
)

dashboard["roster_balance_type"] = dashboard["dependency_score"].apply(
    classify_balance
)

dashboard["play_style_label"] = dashboard.apply(
    classify_play_style,
    axis=1
)

# --------------------------------------------------
# Create final analyst score
# --------------------------------------------------

dashboard["dependency_risk_penalty"] = dashboard["dependency_score"] * 0.20

dashboard["overall_team_analytics_score"] = (
    dashboard["team_efficiency_score"] * 0.80
    - dashboard["dependency_risk_penalty"]
)

dashboard["overall_team_rank"] = dashboard["overall_team_analytics_score"].rank(
    ascending=False,
    method="dense"
).astype(int)

# --------------------------------------------------
# Keep dashboard columns
# --------------------------------------------------

preferred_cols = [
    "team",
    "season",
    "games_played",
    "wins",
    "losses",
    "win_pct",
    "avg_points_scored",
    "avg_points_allowed",
    "avg_point_diff",
    "field_goal_pct",
    "three_point_pct",
    "free_throw_pct",
    "assist_turnover_ratio",
    "team_efficiency_score",
    "team_efficiency_rank",
    "dependency_score",
    "dependency_rank",
    "dependency_tier",
    "roster_balance_type",
    "top_1_player_name",
    "top_1_total_production_score",
    "top_1_production_share",
    "top_2_player_name",
    "top_2_total_production_score",
    "top_2_production_share",
    "top_3_player_name",
    "top_3_total_production_score",
    "top_3_production_share",
    "team_quality_tier",
    "play_style_label",
    "overall_team_analytics_score",
    "overall_team_rank",
]

existing_cols = [col for col in preferred_cols if col in dashboard.columns]

dashboard_final = dashboard[existing_cols].copy()

dashboard_final = dashboard_final.sort_values(
    ["overall_team_rank", "team"]
)

dashboard_final.to_csv(output_path, index=False)

print(f"\nSaved team dashboard summary to: {output_path}")

print("\nDependency score check:")
print(
    dashboard_final[
        [
            "team",
            "dependency_score",
            "top_1_player_name",
            "top_1_production_share",
            "top_2_production_share",
            "top_3_production_share",
        ]
    ]
    .sort_values("dependency_score", ascending=False)
    .head(30)
    .to_string(index=False)
)

print("\nTop teams by overall analytics score:")
print(
    dashboard_final[
        [
            "team",
            "wins",
            "losses",
            "win_pct",
            "team_efficiency_score",
            "dependency_score",
            "overall_team_analytics_score",
            "overall_team_rank",
            "team_quality_tier",
            "roster_balance_type",
            "play_style_label",
        ]
    ].head(15).to_string(index=False)
)

print("\nShape:", dashboard_final.shape)