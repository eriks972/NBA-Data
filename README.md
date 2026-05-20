# NBA Team Efficiency & Player Dependency Analytics Dashboard

This project analyzes NBA team performance, roster balance, and player production using a SportsDataverse-powered Python analytics pipeline and Tableau dashboard.

The pipeline ingests NBA schedule and player box score data, cleans the raw CSVs with pandas, creates fact tables and analytics marts, and visualizes the results in Tableau Public.

## Tools Used
- SportsDataverse
- Python
- pandas
- Tableau Public
- CSV-based analytics marts
- Data quality checks

## Dashboard Focus
- Overall team analytics ranking
- Team efficiency vs. star dependency
- Star dependency by team
- Top player-team production scores

## Data Limitation
This version uses a partial SportsDataverse NBA dataset containing 1,123 completed regular-season games from October 22, 2024 through April 11, 2025. A full NBA regular season contains 1,230 games, so metrics are normalized using per-game averages, percentages, and production shares.