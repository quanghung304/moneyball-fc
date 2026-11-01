"""
Shared constants for the Moneyball FC package.
"""

from pathlib import Path

# Data source: StatsBomb Open Data, Serie A 2015/16
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
COMPETITION_ID = 12
SEASON_ID = 27

# Folders, built from the location of this file so they work from anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Downloads
TIMEOUT_SECONDS = 30

# data processing
EVENT_TYPES = [
    "Shot",
    "Pass",
    "Carry",
    "Pressure",
    "Ball Recovery",
    "Interception",
    "Dribble",
    "Own Goal Against",
    "Half End",
]

EVENT_COLUMNS = [
    "id",
    "index",
    "period",
    "minute",
    "second",
    "type_name",
    "play_pattern_name",
    "team_name",
    "player_id",
    "player_name",
    "position_name",
    "location",
    "under_pressure",
    "pass_end_location",
    "pass_outcome_name",
    "pass_shot_assist",
    "pass_goal_assist",
    "pass_recipient_name",
    "carry_end_location",
    "shot_statsbomb_xg",
    "shot_outcome_name",
    "shot_type_name",
    "shot_body_part_name",
    "shot_key_pass_id",
    "dribble_outcome_name",
    "interception_outcome_name",
    "ball_recovery_recovery_failure",
]

# Columns that are either True or missing in the raw JSON.
FLAG_COLUMNS = [
    "under_pressure",
    "pass_shot_assist",
    "pass_goal_assist",
    "ball_recovery_recovery_failure",
]
