"""Download and process a full StatsBomb season into Parquet tables."""

import logging
import sys
from pathlib import Path
import pandas as pd

# Make the moneyball package importable when running this file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from moneyball.config import COMPETITION_ID, SEASON_ID # noqa: E402
from moneyball.data_loader import StatsBombClient # noqa: E402
from moneyball.processing import (  # noqa: E402
    events_to_dataframe,
    lineups_to_appearances,
    match_end_minute,
    matches_to_dataframe,
)

DEV_MATCHES = 5

logger = logging.getLogger("build_dataset")

def main():
    """Build data tables and write to Parquet file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    client = StatsBombClient()
    
    matches = matches_to_dataframe(client.get_matches(COMPETITION_ID, SEASON_ID))
    logger.info("Load %d matches", len(matches))
    
    # Collect per-match frames in a list and concatenate once at the end
    event_frames = []
    appearance_frames = []
    for match_id in matches["match_id"].head(DEV_MATCHES):
        events, appearances = process_match(client, match_id)
        event_frames.append(events)
        appearance_frames.append(appearances)
        
    events = pd.concat(event_frames, ignore_index=True)
    appearances = pd.concat(appearance_frames, ignore_index=True)
    logger.info("Events: %d rows, %d columns", *events.shape)
    
def process_match(client, match_id):
    """Download and flatten one match.

    Parameters
    ----------
    client : StatsBombClient
        Client used to fetch the events and lineups.
    match_id : int
        Match to process.

    Returns
    -------
    tuple of pandas.DataFrame
        ``(events, appearances)`` for this match.
    """
    events = events_to_dataframe(client.get_events(match_id), match_id)
    end_minute = match_end_minute(events)
    appearances = lineups_to_appearances(client.get_lineups(match_id), match_id, end_minute)
    return events, appearances

if __name__ == "__main__":
    main()
