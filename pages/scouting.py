"""Scouting page (SQ3): most similar players and radar comparison."""

import streamlit as st

from moneyball import plots
from moneyball.analysis import similar_players
from moneyball.config import PERCENTILE_METRICS, SIMILARITY_METRICS
from ui_common import (
    get_percentiles,
    get_players,
    get_tables,
    min_minutes,
    player_index,
)

get_tables()
threshold = min_minutes()
players = get_players(threshold)
names = players.sort_values("player_name")["player_name"].tolist()

st.title("Scouting: who plays like the target? (SQ3)")
left, middle, right = st.columns([2, 1, 1])
target = left.selectbox("Target player", names, index=player_index(names))
top_n = right.slider("Number of results", 3, 20, 10)

similar = similar_players(players, target, SIMILARITY_METRICS, top_n=top_n)
st.dataframe(
    similar[["player_name", "team_name", "position_group", "minutes", "similarity"]],
    hide_index=True,
    column_config={
        "player_name": "Player",
        "team_name": "Team",
        "position_group": "Group",
        "minutes": st.column_config.NumberColumn("Minutes", format="%d"),
        "similarity": st.column_config.ProgressColumn(
            "Cosine similarity", min_value=0, max_value=1, format="%.2f"
        ),
    },
)

st.subheader("Radar comparison (percentiles within position group)")
default = similar["player_name"].head(2).tolist()
compare = st.multiselect(
    "Compare with", similar["player_name"].tolist(), default=default, max_selections=4
)
st.plotly_chart(
    plots.radar_comparison(
        get_percentiles(threshold), [target, *compare], PERCENTILE_METRICS
    ),
    width="stretch",
)

with st.expander("Metric values of the similar players"):
    st.dataframe(similar.drop(columns=["player_id"]), hide_index=True)
st.caption(
    "Metrics are standardised (z-scores) before computing cosine similarity, so that "
    "pressures per 90 (scale ~20) do not outweigh npxG per shot (scale ~0.1)."
)
