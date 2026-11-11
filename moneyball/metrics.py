"""
Player metrics: shot geometry, progressive actions and the season table.
"""

import numpy as np
import pandas as pd

from moneyball.config import (
    GOAL_WIDTH, 
    GOAL_X, 
    GOAL_Y,
    PROGRESSIVE_DISTANCE_RATIO,
    PROGRESSIVE_MIN_X,
)


def add_shot_geometry(shots):
    """Add distance to goal and visible goal angle to each shot.

    With ``dx = 120 - x``, ``dy = y - 40`` and goal width ``w = 8``:

    - ``distance = sqrt(dx^2 + dy^2)``
    - angle = the angle (in radians) between the lines from the shot to each post. 
    arctan2 handles a negative denominator for shots taken very close to goal.

    Parameters
    ----------
    shots : pandas.DataFrame
        Shots with ``x`` and ``y`` columns in StatsBomb coordinates.

    Returns
    -------
    pandas.DataFrame
        Copy of ``shots`` with ``distance`` and ``angle`` columns.

    Examples
    --------
    A penalty taken from (108, 40) is 12 units out with an angle of ~0.64 rad.
    """
    dx = GOAL_X - shots["x"]
    dy = shots["y"] - GOAL_Y
    distance = np.hypot(dx, dy)
    
    half_width = GOAL_WIDTH / 2
    angle = np.arctan2(GOAL_WIDTH * dx, dx**2 + dy**2 - half_width**2)
    
    result = shots.copy()
    result["distance"] = distance
    result["angle"] = angle
    
    return result
    

def flag_progressive(actions):
    """Flag passes and carries that move the ball substantially towards goal.

    Definition: the action is a completed Pass or a Carry, it starts at 
    ``x >= 40`` and its end point is at most 75% as far from the centre of 
    the goal as its start point.

    Parameters
    ----------
    actions : pandas.DataFrame
        Events with ``type_name, x, y, end_x, end_y, pass_outcome_name``.
        A pass is completed when ``pass_outcome_name`` is missing; carries
        never have an outcome.

    Returns
    -------
    pandas.Series of bool
        True for progressive actions, aligned with ``actions``.
    """
    distance_before = np.hypot(GOAL_X - actions["x"], GOAL_Y - actions["y"])
    distance_after = np.hypot(GOAL_X - actions["end_x"], GOAL_Y - actions["end_y"])
    
    # 4 boolean Series per each condition that form an successfull progressive action
    is_pass_or_carry = actions["type_name"].isin(["Pass", "Carry"])
    is_completed = actions["pass_outcome_name"].isna()
    starts_outside_own_third = actions["x"] >= PROGRESSIVE_MIN_X
    gets_much_closer = distance_after <= distance_before * PROGRESSIVE_DISTANCE_RATIO
    
    return is_pass_or_carry & is_completed & starts_outside_own_third & gets_much_closer


def _main_value(appearances, column):
    """Return, per player, the value of ``column`` with the most minutes."""
    totals = appearances.groupby(["player_id", column], as_index=False)["minutes"].sum()
    most_minutes_first = totals.sort_values("minutes", ascending=False)
    main = most_minutes_first.drop_duplicates("player_id")
    return main.set_index("player_id")[column]


def build_player_season(events, appearances):
    """Aggregate events and minutes into one row per player for the season.

    Parameters
    ----------
    events : pandas.DataFrame
        Events table from ``processing.events_to_dataframe`` (all matches).
    appearances : pandas.DataFrame
        Appearances table from ``processing.lineups_to_appearances``.

    Returns
    -------
    pandas.DataFrame
        One row per player with minutes > 0. Columns: identity
        (``player_id, player_name, team_name, position, position_group``),
        playing time (``matches, minutes``), shooting (``shots, np_shots,
        goals, np_goals, penalty_goals, xg, npxg``), creation (``xa,
        key_passes, assists``) and ball progression / defending
        (``progressive_passes, progressive_carries, dribbles_completed,
        pressures, ball_recoveries, interceptions``). ``team_name`` and
        ``position`` are those with the most minutes.
    """
    # 1. Minutes, matches, team and main position.
    players = appearances.groupby("player_id").agg(
        player_name=("player_name", "first"),
        matches=("match_id", "nunique"),
        minutes=("minutes", "sum"),
    )
    
    players["team_name"] = _main_value(appearances, "team_name")
    players["position"] = _main_value(appearances, "position")
    players["position_group"] = _main_value(appearances, "position_group")
    
    # drop rows have no player. Eg: Half End
    events = events[events["player_id"].notna()]
    # rows have no player_id (NaN) make the column type float64. Make it plain integers
    events = events.astype({"player_id": "int64"})
    event_type = events["type_name"]
    
    # 2. Finishing. npxg excludes penalties: they are a fixed ~0.76 xG chance
    # and say little about how good a player 
    shots = events[event_type == "Shot"].copy()
    shots["is_goal"] = shots["shot_outcome_name"] == "Goal"
    shots["is_penalty"] = shots["shot_type_name"] == "Penalty"
    # ~ is "not": ~is_penalty is True for every shot that is not a penalty.
    shots["is_np_shot"] = ~shots["is_penalty"]
    shots["is_np_goal"] = shots["is_goal"] & ~shots["is_penalty"]
    shots["is_penalty_goal"] = shots["is_goal"] & shots["is_penalty"]
    # where keeps the xG where the condition is True and puts 0 elsewhere.
    shots["npxg"] = shots["shot_statsbomb_xg"].where(~shots["is_penalty"], 0.0)
    
    shooting = shots.groupby("player_id").agg(
        shots=("id", "size"),
        np_shots=("is_np_shot", "sum"),
        goals=("is_goal", "sum"),
        np_goals=("is_np_goal", "sum"),
        penalty_goals=("is_penalty_goal", "sum"),
        xg=("shot_statsbomb_xg", "sum"),
        npxg=("npxg", "sum"),
    )
    
    # 3. Creation: credit the passer with the xG of the shot it set up.
    passes = events[event_type == "Pass"].copy()
    passers = passes[["id", "player_id"]]
    # merge each shot with its passer. There gonna be 2 "player_id" columns,
    # so we add "_shooter" suffix for shooters, leave "player_id" for passers
    assisted =  shots.merge(
        passers,
        left_on="shot_key_pass_id",
        right_on="id",
        suffixes=("_shooter", ""),
    )
    expected_assists = assisted.groupby("player_id").agg(
        xa=("shot_statsbomb_xg", "sum")
    )
    
    # A key pass is the last pass before a shot (goal or not).
    passes["is_key_pass"] = passes["pass_shot_assist"] | passes["pass_goal_assist"]
    pass_counts = passes.groupby("player_id").agg(
        key_passes=("is_key_pass", "sum"),
        assists=("pass_goal_assist", "sum"),
    )
    # how="outer" keeps players found in only one of the two tables.
    creation = expected_assists.join(pass_counts, how="outer")
    
    # 4. Progression and defending: one True/False column per action type,
    # then the sum per player counts the actions.
    progressive = flag_progressive(events)
    is_dribble = event_type == "Dribble"
    is_completed_dribble = is_dribble & (events["dribble_outcome_name"] == "Complete")
    is_recovery = event_type == "Ball Recovery"
    is_successful_recovery = is_recovery & ~events["ball_recovery_recovery_failure"]
    
    action_flags = pd.DataFrame(
        {
            "player_id": events["player_id"],
            "progressive_passes": progressive & (event_type == "Pass"),
            "progressive_carries": progressive & (event_type == "Carry"),
            "dribbles_completed": is_completed_dribble,
            "pressures": event_type == "Pressure",
            "ball_recoveries": is_successful_recovery,
            "interceptions": event_type == "Interception",
        }
    )
    actions = action_flags.groupby("player_id").sum()
    
    # 5. Left joins on the minutes table: a player with no shots has 0 shots,
    # not "unknown", so we have to fillna(0). Also change the columns with NaN 
    # values to int, except expected column.
    table = players.join([shooting, creation, actions], how="left")
    count_columns = [c for c in table.columns if c not in players.columns]
    table[count_columns] = table[count_columns].fillna(0)
    int_columns = [c for c in count_columns if c not in ("xg", "npxg", "xa")]
    table[int_columns] = table[int_columns].astype("int64")
    
    # Drop players who never got on the pitch
    table = table[table["minutes"] > 0]
    table = table.reset_index()
    table["player_id"] = table["player_id"].astype("int64")
    return table
     
    
    
