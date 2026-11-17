"""Analysis functions answering the three sub-questions.

- SQ1 Finishing: is a player's goals-vs-xG gap more than luck?
  (Monte Carlo simulation of his shots)
- SQ2 Output: how does a player rank per 90 against his position group?
  (percentiles and z-scores)
- SQ3 Replacement: who has the statistical profile closest to the target?
  (standardised metric vectors + cosine similarity)

Every function takes DataFrames and returns
a new DataFrame or dict
"""

import numpy as np
import pandas as pd
from scipy import stats

from moneyball.config import (
    FINISHING_INTERVAL,
    MIN_SHOTS,
    N_SIMULATIONS,
    RANDOM_SEED,
    SIMILARITY_METRICS,
)

# --- SQ1: finishing -------------------------------------------------------


def non_penalty_shots(events):
    """Extract the non-penalty shots used by the finishing simulation.

    Parameters
    ----------
    events : pandas.DataFrame
        Events table.

    Returns
    -------
    pandas.DataFrame
        Columns ``player_id, player_name, team_name, match_id, x, y, xg,
        is_goal, shot_outcome_name, shot_body_part_name``.
    """
    is_shot = events["type_name"] == "Shot"
    is_penalty = events["shot_type_name"] == "Penalty"
    shots = events[is_shot & ~is_penalty].copy()

    shots["xg"] = shots["shot_statsbomb_xg"]
    shots["is_goal"] = shots["shot_outcome_name"] == "Goal"
    shots["player_id"] = shots["player_id"].astype("int64")

    columns = [
        "player_id",
        "player_name",
        "team_name",
        "match_id",
        "x",
        "y",
        "xg",
        "is_goal",
        "shot_outcome_name",
        "shot_body_part_name",
    ]
    return shots[columns].reset_index(drop=True)


def simulate_goals(xg, n_sims=N_SIMULATIONS, rng=None):
    """Simulate how many goals an average finisher scores from given chances.

    Each shot is an independent Bernoulli trial that succeeds with
    probability equal to its xG. One row of the random matrix is one
    simulated season; comparing it with ``xg`` (broadcast across rows) and
    summing the booleans gives the goals of that season. The result follows
    a Poisson-binomial distribution with mean ``sum(xg)``.

    Parameters
    ----------
    xg : array-like of float
        xG of each shot, between 0 and 1.
    n_sims : int, optional
        Number of simulated seasons.
    rng : numpy.random.Generator, optional
        Random generator; pass a seeded one for reproducible results.

    Returns
    -------
    numpy.ndarray of int
        Array of length ``n_sims`` with simulated goal totals.
    """
    if rng is None:
        rng = np.random.default_rng()
    xg = np.asarray(xg, dtype=float)

    # One row per simulated season, one column per shot, uniform numbers in [0, 1).
    random_numbers = rng.random((n_sims, len(xg)))

    is_scored = random_numbers < xg
    return is_scored.sum(axis=1)


def _player_rng(player_id, seed):
    """Return a generator seeded by (seed, player) so results do not depend
    on the order in which players are simulated."""
    return np.random.default_rng([seed, int(player_id)])


def simulate_player(shots, player_id, n_sims=N_SIMULATIONS, seed=RANDOM_SEED):
    """Simulate one player's season of non-penalty shots.

    Parameters
    ----------
    shots : pandas.DataFrame
        Output of ``non_penalty_shots``.
    player_id : int
        Player to simulate.
    n_sims : int, optional
        Number of simulated seasons.
    seed : int, optional
        Base seed; the same seed gives the same numbers as
        ``finishing_table``.

    Returns
    -------
    tuple
        ``(sims, actual)``: simulated goal totals and real goals scored.

    Raises
    ------
    ValueError
        If the player has no non-penalty shot.
    """
    player_shots = shots[shots["player_id"] == player_id]
    if player_shots.empty:
        raise ValueError(f"No non-penalty shots for player_id {player_id}.")
    rng = _player_rng(player_id, seed)
    sims = simulate_goals(player_shots["xg"], n_sims, rng)
    actual = int(player_shots["is_goal"].sum())
    return sims, actual


def finishing_table(
    shots, players, min_shots=MIN_SHOTS, n_sims=N_SIMULATIONS, seed=RANDOM_SEED
):
    """Compare real and simulated goals for every regular shooter.

    Parameters
    ----------
    shots : pandas.DataFrame
        Output of ``non_penalty_shots``.
    players : pandas.DataFrame
        Player table with ``player_id, player_name, team_name,
        position_group`` (e.g. from ``add_per90``); only these players are
        simulated.
    min_shots : int, optional
        Minimum number of non-penalty shots to be included.
    n_sims : int, optional
        Simulated seasons per player.
    seed : int, optional
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        One row per player, sorted by ``p_at_least``: ``shots, goals,
        expected`` (simulation mean, ~ sum of xG), ``low``/``high`` (the
        5th-95th percentile band), ``p_at_least`` (share of simulations
        with at least the real number of goals), ``p_at_most`` and
        ``verdict`` (``"above"``, ``"below"`` or ``"within"`` the band).

    Notes
    -----
    A small ``p_at_least`` (e.g. < 0.05) means an average finisher would
    rarely score that many from those chances.
    """
    low_pct, high_pct = FINISHING_INTERVAL
    shots = shots[shots["player_id"].isin(players["player_id"])]
    rows = []
    for player_id, player_shots in shots.groupby("player_id"):
        if len(player_shots) < min_shots:
            continue
        rng = _player_rng(player_id, seed)
        sims = simulate_goals(player_shots["xg"], n_sims, rng)
        actual = int(player_shots["is_goal"].sum())
        low, high = np.percentile(sims, [low_pct, high_pct])
        rows.append(
            {
                "player_id": player_id,
                "shots": len(player_shots),
                "goals": actual,
                "npxg": player_shots["xg"].sum(),
                "expected": sims.mean(),
                "low": low,
                "high": high,
                # mean of boolean array: the share of True values
                "p_at_least": (sims >= actual).mean(),
                "p_at_most": (sims <= actual).mean(),
            }
        )

    table = pd.DataFrame(rows)
    if table.empty:
        return table

    # np.select picks, row by row, the label of the first True condition,
    # and the default when none is True.
    is_above = table["goals"] > table["high"]
    is_below = table["goals"] < table["low"]
    table["verdict"] = np.select(
        [is_above, is_below], ["above", "below"], default="within"
    )

    info = players[["player_id", "player_name", "team_name", "position_group"]]
    table = info.merge(table, on="player_id")
    table = table.sort_values("p_at_least")
    return table.reset_index(drop=True)


# --- SQ2: output percentiles ---------------------------------------------


def position_percentiles(table, metrics):
    """Rank every player against his position group on each metric.

    Parameters
    ----------
    table : pandas.DataFrame
        Per-90 player table from ``add_per90``.
    metrics : list of str
        Columns to rank.

    Returns
    -------
    pandas.DataFrame
        Long format, one row per (player, metric): ``player_id,
        player_name, team_name, position_group, metric, value, percentile``
        (0-100) and ``zscore`` (standard deviations from the group mean).
    """
    # 1. Wide tables: one row per player, one column per metric.
    by_group = table.groupby("position_group")[metrics]
    # rank(pct=True) gives each player's rank within his group as a percentile
    percentiles = by_group.rank(pct=True) * 100
    # transform returns one value per row (unlike agg, one per group).
    # A metric with zero spread in a group gives NaN z-scores: set them to 0.
    zscores = by_group.transform(stats.zscore).fillna(0.0)

    # Both tables keep the row index of table: join adds the matching player_id.
    percentiles = percentiles.join(table["player_id"])
    zscores = zscores.join(table["player_id"])

    # 2. Long tables (melt): one row per (player, metric)
    id_columns = ["player_id", "player_name", "team_name", "position_group"]
    long_values = table.melt(id_vars=id_columns, value_vars=metrics, var_name="metric")
    long_pct = percentiles.melt(
        id_vars="player_id", var_name="metric", value_name="percentile"
    )
    long_z = zscores.melt(id_vars="player_id", var_name="metric", value_name="zscore")

    # 3. Put value, percentile and z-score side by side.
    keys = ["player_id", "metric"]
    result = long_values.merge(long_pct, on=keys)
    result = result.merge(long_z, on=keys)
    return result


# --- SQ3: similarity ------------------------------------------------------


def find_player(table, player_name):
    """Return the row of a player, raising a clear error if absent.

    Parameters
    ----------
    table : pandas.DataFrame
        Player table with a ``player_name`` column.
    player_name : str
        Exact player name as written by StatsBomb.

    Returns
    -------
    pandas.Series
        The player's row.

    Raises
    ------
    ValueError
        If no player has this name (e.g. typo or below the minutes threshold).
    """
    matches = table[table["player_name"] == player_name]
    if matches.empty:
        raise ValueError(
            f"Player '{player_name}' not found (check spelling or the minutes threshold)."
        )
    return matches.iloc[0]


def similar_players(
    table, target_name, metrics=SIMILARITY_METRICS, top_n=10, same_group=True
):
    """Find the players whose statistical profile is closest to a target.

    Each metric is standardised (z-score) over the comparison pool so that
    metrics on large scales (pressures per 90) do not dominate small ones
    (npxG per shot). The similarity is the cosine of the angle between the
    standardised vectors: 1 = same profile shape, 0 = unrelated, -1 = opposite.

    Parameters
    ----------
    table : pandas.DataFrame
        Per-90 player table from ``add_per90``.
    target_name : str
        Player to compare against.
    metrics : list of str, optional
        Columns forming the profile vector.
    top_n : int, optional
        Number of players returned (``None`` for all).
    same_group : bool, optional
        If True, only compare with the target's position group.

    Returns
    -------
    pandas.DataFrame
        The ``top_n`` most similar players (target excluded), sorted by
        decreasing ``similarity``, with their metric values.

    Raises
    ------
    ValueError
        If ``target_name`` is not in ``table``.
    """
    target = find_player(table, target_name)
    pool = table
    if same_group:
        pool = table[table["position_group"] == target["position_group"]]
    pool = pool.reset_index(drop=True)

    # Standardise: z = (x - mean) / std, column by column
    values = pool[metrics].to_numpy(dtype=float)
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    # A constant column would divide by zero; nan_to_num turns it into zeros.
    standardised = np.nan_to_num((values - mean) / std)

    # The target's own row. pool was reset to 0, 1, 2..., so the index
    # label is also the row position in ``standardised``.
    is_target = pool["player_id"] == target["player_id"]
    target_row = pool.index[is_target][0]
    target_vector = standardised[target_row]

    # Cosine similarity = (a . b) / (|a| * |b|) for every player at once.
    # @ is the dot product of each row with the target vector.
    dot_products = standardised @ target_vector
    norms = np.linalg.norm(standardised, axis=1) * np.linalg.norm(target_vector)
    # A zero vector has no direction: dividing by NaN gives a NaN similarity.
    norms = np.where(norms == 0, np.nan, norms)
    similarity = dot_products / norms

    # Most similar first, without the target himself.
    result = pool.assign(similarity=similarity)
    result = result[result["player_id"] != target["player_id"]]
    result = result.sort_values("similarity", ascending=False)

    columns = [
        "player_id",
        "player_name",
        "team_name",
        "position_group",
        "minutes",
        "similarity",
    ]
    result = result[columns + list(metrics)]
    # head(None) keeps every row.
    result = result.head(top_n)
    return result.reset_index(drop=True)
