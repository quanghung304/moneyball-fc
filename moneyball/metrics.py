"""
Player metrics: shot geometry, progressive actions and the season table.
"""

import numpy as np

from moneyball.config import GOAL_WIDTH, GOAL_X, GOAL_Y


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
    
