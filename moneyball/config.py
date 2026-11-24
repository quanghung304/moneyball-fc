"""
Shared constants for the Moneyball FC package.
"""

from pathlib import Path

# Data source: StatsBomb Open Data, Serie A 2015/16
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
COMPETITION_ID = 12
SEASON_ID = 27
COMPETITION_LABEL = "Serie A 2015/16"
DATA_CREDIT = "Data: StatsBomb Open Data"

# Folders, built from the location of this file so they work from anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TABLE_NAMES = ("matches", "events", "appearances", "player_season")

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

# Position groups
POSITION_GROUP_ORDER = ["GK", "DEF", "MID", "WING", "FWD"]

POSITION_GROUPS = {
    "Goalkeeper": "GK",
    "Right Back": "DEF",
    "Right Center Back": "DEF",
    "Center Back": "DEF",
    "Left Center Back": "DEF",
    "Left Back": "DEF",
    "Right Wing Back": "DEF",
    "Left Wing Back": "DEF",
    "Right Defensive Midfield": "MID",
    "Center Defensive Midfield": "MID",
    "Left Defensive Midfield": "MID",
    "Right Center Midfield": "MID",
    "Center Midfield": "MID",
    "Left Center Midfield": "MID",
    "Right Attacking Midfield": "MID",
    "Center Attacking Midfield": "MID",
    "Left Attacking Midfield": "MID",
    "Right Midfield": "WING",
    "Left Midfield": "WING",
    "Right Wing": "WING",
    "Left Wing": "WING",
    "Right Center Forward": "FWD",
    "Left Center Forward": "FWD",
    "Center Forward": "FWD",
    "Striker": "FWD",
    "Secondary Striker": "FWD",
}

# --- Pitch geometry (pitch size: 120 x 80, attacking towards x = 120)
GOAL_X = 120
GOAL_Y = 40  # centre of the goal
GOAL_WIDTH = 8

# Progressive action: starts beyond own deep third and ends at most 75% of
# the previous distance to the centre of the goal.
PROGRESSIVE_MIN_X = 40
PROGRESSIVE_DISTANCE_RATIO = 0.75

# --- Analysis thresholds
MIN_MINUTES = 900  # ~10 full matches
N_SIMULATIONS = 10000
RANDOM_SEED = 42
MIN_SHOTS = 20  # minimum non-penalty shots for the finishing simulation
FINISHING_INTERVAL = (5, 95)  # percentile band. From 5-95: normal
TARGET_PLAYER = "Gonzalo Gerardo Higuaín"
# Recommendation chosen from SQ1-SQ3: same position group, >= 80th percentile
# on npxG/90, not at a top-5 club, most similar with target player.
SHORTLIST = (
    "Josef Alexander Martínez Mencia",
    "Duván Esteban Zapata Banguera",
    "Leonardo Pavoletti",
    "Luca Toni",
    "Carlos Arturo Bacca Ahumada",
)

# --- Metrics
PER90_COLUMNS = [
    "goals",
    "np_goals",
    "shots",
    "np_shots",
    "npxg",
    "xa",
    "key_passes",
    "assists",
    "progressive_passes",
    "progressive_carries",
    "dribbles_completed",
    "pressures",
    "ball_recoveries",
    "interceptions",
]

# Attacking profile used for SQ2 percentiles and the radar chart.
PERCENTILE_METRICS = [
    "np_goals_p90",
    "npxg_p90",
    "np_shots_p90",
    "npxg_per_shot",
    "xa_p90",
    "key_passes_p90",
    "progressive_carries_p90",
    "dribbles_completed_p90",
    "pressures_p90",
]

# Style vector used for SQ3 similarity
SIMILARITY_METRICS = [
    "np_goals_p90",
    "npxg_p90",
    "np_shots_p90",
    "npxg_per_shot",
    "xa_p90",
    "key_passes_p90",
    "progressive_carries_p90",
    "dribbles_completed_p90",
    "pressures_p90",
]

METRIC_LABELS = {
    "np_goals_p90": "Non-penalty goals per 90",
    "npxg_p90": "npxG per 90",
    "np_shots_p90": "Non-penalty shots per 90",
    "npxg_per_shot": "npxG per shot",
    "xa_p90": "xA per 90",
    "key_passes_p90": "Key passes per 90",
    "progressive_passes_p90": "Progressive passes per 90",
    "progressive_carries_p90": "Progressive carries per 90",
    "dribbles_completed_p90": "Completed dribbles per 90",
    "pressures_p90": "Pressures per 90",
    "goals_minus_npxg": "Non-penalty goals minus npxG",
}

# --- Chart style
HIGHLIGHT_COLOR = "#0072B2"  # blue: player(s) of interest
SECOND_COLOR = "#E69F00"  # orange: comparison player / goals
MUTED_COLOR = "#B0B0B0"  # grey: everyone else
