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
