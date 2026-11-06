"""Download and process a full StatsBomb season into Parquet tables."""

import logging
import sys
from pathlib import Path
import pandas as pd
import argparse
import time

# Make the moneyball package importable when running this file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from moneyball.config import COMPETITION_ID, SEASON_ID, PROCESSED_DIR # noqa: E402
from moneyball.data_loader import StatsBombClient, StatsBombError # noqa: E402
from moneyball.processing import (  # noqa: E402
    events_to_dataframe,
    lineups_to_appearances,
    match_end_minute,
    matches_to_dataframe,
    reconcile_goals,
)

logger = logging.getLogger("build_dataset")

PROGRESS_CHECK = 20

# Repeated text values stored as category: much smaller Parquet and memory.
CATEGORY_COLUMNS = ["type_name", "play_pattern_name", "team_name", "position_name",
                    "pass_outcome_name", "shot_outcome_name", "shot_type_name",
                    "shot_body_part_name", "dribble_outcome_name", "interception_outcome_name"]

def main():
    """Build data tables and write to Parquet file"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    args = parse_args()
    start_time = time.perf_counter()
    
    client = StatsBombClient()
    matches = matches_to_dataframe(client.get_matches(COMPETITION_ID, SEASON_ID))
    if args.max_matches is not None:
        matches = matches.head(args.max_matches)
    logger.info("Load %d matches", len(matches))
    
    # Collect per-match frames in a list and concatenate once at the end
    event_frames = []
    appearance_frames = []
    failed = []
    
    for number, match_id in enumerate(matches["match_id"], start=1):
        try:
            events, appearances = process_match(client, match_id)
        except(StatsBombError, ValueError, KeyError) as error:
            logger.error("Match %s skipped: %s", match_id, error)
            failed.append(match_id)
            continue
    
        event_frames.append(events)
        appearance_frames.append(appearances)
                
        if number % PROGRESS_CHECK == 0:
            logger.info("%d/%d matches done", number, len(matches))
        
    if not event_frames:
        logger.error("No match could be processed, nothing written.")
        sys.exit(1)
    
    events = pd.concat(event_frames, ignore_index=True)
    appearances = pd.concat(appearance_frames, ignore_index=True)
    
    # Keep only the matches that were processed, so the tables stay consistent.
    is_processed = ~matches["match_id"].isin(failed)
    matches = matches[is_processed].reset_index(drop=True)
    events[CATEGORY_COLUMNS] = events[CATEGORY_COLUMNS].astype("category")

    check = reconcile_goals(events, matches)
    if check["mismatched_matches"]:
        logger.warning("Goal totals differ in matches %s", check["mismatched_matches"])
    logger.info("Reconciliation: %d goals from events vs %d from match scores",
                check["event_goals"], check["score_goals"])
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tables = {
        "matches": matches, 
        "events": events, 
        "appearances": appearances
    }
    
    for name, table in tables.items():
        path = args.output_dir / f"{name}.parquet"
        table.to_parquet(path, index=False)
        logger.info("Wrote %s: %d rows, %.1f MB", 
                    path.name, len(table), path.stat().st_size / 1e6)

    elapsed = time.perf_counter() - start_time
    failed_list = f": {failed}" if failed else ""  # list the ids only when there are some
    logger.info(
        "Done in %.0f s. %d matches processed, %d failed%s",
        elapsed,
        len(matches),
        len(failed),
        failed_list,
    )
    
    
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


def parse_args():
    """
    Parse command-line options.

    Returns
    -------
    argparse.Namespace
        ``max_matches`` (int or None) and ``output_dir`` (Path).
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-matches", type=int, default=None,
                        help="process only the first N matches of the season (default: all)")
    parser.add_argument("--output-dir", type=Path, default=PROCESSED_DIR,
                        help=f"where to write the Parquet files (default: {PROCESSED_DIR})")
    return parser.parse_args()
   
    
if __name__ == "__main__":
    main()
