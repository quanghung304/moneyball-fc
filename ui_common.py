"""Cached data access shared by the Streamlit pages.

Streamlit re-runs the whole page script on every interaction. Wrapping the
package calls in ``st.cache_data`` means the Parquet files are read and the
analysis tables computed once per parameter value, not on every click.
"""

import streamlit as st

from moneyball.analysis import finishing_table, non_penalty_shots, position_percentiles
from moneyball.config import MIN_MINUTES, PERCENTILE_METRICS, TARGET_PLAYER
from moneyball.data_loader import load_tables
from moneyball.metrics import add_per90


@st.cache_data(show_spinner="Loading processed tables...")
def _load_tables():
    return load_tables()


def get_tables():
    """Return the processed tables

    Returns
    -------
    dict of str to pandas.DataFrame
        Output of ``moneyball.data_loader.load_tables``.
    """
    try:
        return _load_tables()
    except FileNotFoundError as error:
        st.error(f"{error}")
        st.code("python scripts/build_dataset.py", language="bash")
        st.stop()


def min_minutes():
    """Return the minutes threshold chosen in the sidebar."""
    return st.session_state.get("min_minutes", MIN_MINUTES)


@st.cache_data
def get_players(threshold):
    """Per-90 player table for players above ``threshold`` minutes."""
    return add_per90(_load_tables()["player_season"], min_minutes=threshold)


@st.cache_data
def get_shots():
    """Non-penalty shots of the season."""
    return non_penalty_shots(_load_tables()["events"])


@st.cache_data(show_spinner="Running Monte Carlo simulations...")
def get_finishing(threshold):
    """SQ1 finishing table for players above ``threshold`` minutes."""
    return finishing_table(get_shots(), get_players(threshold))


@st.cache_data
def get_percentiles(threshold):
    """SQ2 long percentile table for players above ``threshold`` minutes."""
    return position_percentiles(get_players(threshold), PERCENTILE_METRICS)


def player_index(names, default=TARGET_PLAYER):
    """Index of default in names for a selectbox, 0 if absent."""
    names = list(names)
    return names.index(default) if default in names else 0
