"""
Player metrics: shot geometry, progressive actions and the season table.
"""

import numpy as np

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
