"""Data preparation: turn nested StatsBomb JSON into flat analysis tables.

Functions: take parsed JSON or DataFrames and return a new
DataFrame without modifying their input.
"""

import pandas as pd

from moneyball.config import EVENT_COLUMNS, EVENT_TYPES, FLAG_COLUMNS

MATCH_COLUMNS = {
    "match_id": "match_id",
    "match_date": "match_date",
    "match_week": "match_week",
    "home_team_home_team_name": "home_team",
    "away_team_away_team_name": "away_team",
    "home_score": "home_score",
    "away_score": "away_score",
}

# Columns holding coordinates information
LIST_COLUMNS = ["location", "pass_end_location", "carry_end_location"]

SECONDS_PER_MINUTE = 60


def matches_to_dataframe(matches):
    """
    Flatten the season match list into one row per match.

    Parameters
    ----------
    matches : list of dict
        Output of ``StatsBombClient.get_matches``.

    Returns
    -------
    pandas.DataFrame
        Columns ``match_id, match_date, match_week, home_team, away_team,
        home_score, away_score``, sorted by date.
    """
    df = pd.json_normalize(matches, sep="_")
    df = df[list(MATCH_COLUMNS)].rename(columns=MATCH_COLUMNS)
    df["match_date"] = pd.to_datetime(df["match_date"])
    return df.sort_values(["match_date", "match_id"]).reset_index(drop=True)

def _split_coordinates(points):
    """Split a column of ``[x, y]`` lists into two float Series."""
    points = points.astype(object)
    return points.str[0].astype(float), points.str[1].astype(float)


def events_to_dataframe(events, match_id):
    """
    Flatten one match's events and keep only what the analysis needs.

    Parameters
    ----------
    events : list of dict
        Output of ``StatsBombClient.get_events``.
    match_id : int
        Id of the match, stored in a ``match_id`` column.

    Returns
    -------
    pandas.DataFrame
        One row per event of a type in ``config.EVENT_TYPES``, with the
        columns of ``config.EVENT_COLUMNS`` (list columns replaced by ``x, y,
        end_x, end_y``) plus ``match_id``. Columns missing from this match are
        present and filled with NaN, so every match has the same schema.
    """
    df = pd.json_normalize(events, sep="_")
    
    # reindex keeps a fixed schema
    df = df.reindex(columns=EVENT_COLUMNS)
    
    # keep only the event types to analyse
    is_wanted_type = df["type_name"].isin(EVENT_TYPES)
    df = df[is_wanted_type].copy()
    
    df["x"], df["y"] = _split_coordinates(df["location"])
    
    # A row is either a Pass or a Carry, never both: one end column suffices.
    # combine_first takes the pass end, and the carry end where it is missing.
    end_location = df["pass_end_location"].combine_first(df["carry_end_location"])
    df["end_x"], df["end_y"] = _split_coordinates(end_location)
    
    df = df.drop(columns=LIST_COLUMNS)
    
    # StatsBomb only writes these flags when they are true; absent means False.
    # eq(True) gives True for True and False for NaN.
    df[FLAG_COLUMNS] = df[FLAG_COLUMNS].eq(True)
    
    # Half End rows have no player: nullable integers keep ids as integers.
    df["player_id"] = df["player_id"].astype("Int64")
    
    df["match_id"] = match_id
    df = df.reset_index(drop=True)
    
    return df
    
    
def clock_to_minutes(clock):
    """Convert ``"mm:ss"`` clock into decimal minutes.

    Parameters
    ----------
    clock : str
        Match clock such as ``"59:44"``. Minutes can exceed 59 (``"95:08"``).

    Returns
    -------
    float
        Decimal minutes, e.g. ``59.733`` for ``"59:44"``.

    Examples
    --------
    >>> round(clock_to_minutes("59:44"), 3)
    59.733
    """
    minute, second = clock.split(":")
    return int(minute) + int(second) / SECONDS_PER_MINUTE


def match_end_minute(events_df):
    """
    Return the minute where the match ends.

    Parameters
    ----------
    events_df : pandas.DataFrame
        Flattened events of one match, including the ``Half End`` rows.

    Returns
    -------
    float
        ``minute + second / 60`` of the last period's ``Half End`` event,
        e.g. ``95.133`` for a match ending at 95:08.

    Raises
    ------
    ValueError
        If the events contain no ``Half End`` row.
    """
    half_end = events_df[events_df["type_name"] == "Half End"]
    if half_end.empty:
        raise ValueError("No 'Half End' event found: cannot determine match length.")
    
    # Every period has a Half End row for each team: keep those of the last period.
    last_period_number = half_end["period"].max()
    last_period = half_end[half_end["period"] == last_period_number]
    
    end_minutes = last_period["minute"] + last_period["second"] / SECONDS_PER_MINUTE
    return end_minutes.max()


def lineups_to_appearances(lineups, match_id, end_minute):
    """Compute minutes played and main position for every player of a match.

    Each lineup entry lists the "spells" a player spent in a position with
    ``from``/``to`` clocks. Minutes played is the sum of spell lengths;
    ``to = None`` means the player stayed on until the final whistle.

    Parameters
    ----------
    lineups : list of dict
        Output of ``StatsBombClient.get_lineups`` (one dict per team).
    match_id : int
        Id of the match.
    end_minute : float
        Final whistle minute, from ``match_end_minute``.

    Returns
    -------
    pandas.DataFrame
        One row per player who played, with columns ``match_id, player_id,
        player_name, team_name, position, minutes``.
        ``position`` is the position held for the most time in the match.
    """
    # 1. One row per position spell, for both teams.
    frames = []
    for team in lineups:
        # record_path makes one row per item of each player's "positions" list;
        # meta copies the player's id and name onto each of those rows.
        # Unused substitutes have an empty positions list and disappear here.
        spells = pd.json_normalize(
            team["lineup"], record_path="positions", meta=["player_id", "player_name"]
        )
        spells["team_name"] = team["team_name"]
        frames.append(spells)
    spells = pd.concat(frames, ignore_index=True)
    
    # 2. Length of each spell in minutes.
    # map: call the function for each spell["from"]
    start = spells["from"].map(clock_to_minutes)
    
    # na_action="ignore" skips the None clocks instead of calling clock_to_minutes(None);
    # they stay NaN and are then set to the final whistle.
    end = spells["to"].map(clock_to_minutes, na_action="ignore")
    end = end.fillna(end_minute)
    
    # clip(lower=0) turns a negative length into 0. Cuz clock restarts at 45:00 in the second half,
    # while the first half may exceed 45:00
    spells["duration"] = (end - start).clip(lower=0)
    
    # 3. Minutes per (player, position).
    keys = ["player_id", "player_name", "team_name"]
    per_position = spells.groupby(keys + ["position"], as_index=False)["duration"].sum()

    # 4. Main position: sort longest first, then keep the first row of each player.
    longest_first = per_position.sort_values("duration", ascending=False)
    main_position = longest_first.drop_duplicates("player_id")
    main_position = main_position[["player_id", "position"]]

    # 5. Total minutes per player.
    minutes = per_position.groupby(keys, as_index=False)["duration"].sum()
    minutes = minutes.rename(columns={"duration": "minutes"})

    # 6. Put the pieces together.
    appearances = minutes.merge(main_position, on="player_id")
    appearances["player_id"] = appearances["player_id"].astype("int64")
    appearances.insert(0, "match_id", match_id)

    columns = ["match_id", "player_id", "player_name", "team_name", "position", "minutes"]
    return appearances[columns]
