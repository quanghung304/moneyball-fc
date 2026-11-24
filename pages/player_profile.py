"""Player profile page: key numbers, percentiles in group (SQ2), finishing (SQ1)."""

import streamlit as st

from moneyball import plots
from moneyball.analysis import simulate_player
from moneyball.config import FINISHING_INTERVAL, MIN_SHOTS
from ui_common import (
    get_finishing,
    get_percentiles,
    get_players,
    get_shots,
    get_tables,
    min_minutes,
    player_index,
)

get_tables() #make sure there's data to show
threshold = min_minutes()
players = get_players(threshold).sort_values("player_name")
finishing = get_finishing(threshold)
names = players["player_name"].tolist()

st.title("Player profile")
name = st.selectbox("Player", names, index=player_index(names))
player = players[players["player_name"] == name].iloc[0]

st.caption(
    f"{player['team_name']} · {player['position']} ({player['position_group']}) · "
    f"{player['matches']} matches · {player['minutes']:.0f} minutes"
)
cols = st.columns(5)
cols[0].metric("Non-penalty goals", int(player["np_goals"]))
cols[1].metric(
    "npxG", f"{player['npxg']:.1f}", delta=f"{player['goals_minus_npxg']:+.1f} goals vs npxG"
)
cols[2].metric("npxG per 90", f"{player['npxg_p90']:.2f}")
cols[3].metric("xA per 90", f"{player['xa_p90']:.2f}")
cols[4].metric("npxG per shot", f"{player['npxg_per_shot']:.3f}")

st.subheader("Output compared with the same position (SQ2)")
st.plotly_chart(plots.percentile_bars(get_percentiles(threshold), name), width="stretch")

st.subheader("Finishing: skill or luck? (SQ1)")
row = finishing[finishing["player_name"] == name]
if row.empty:
    st.info(f"{name} has fewer than {MIN_SHOTS} non-penalty shots, so he is not simulated.")
else:
    row = row.iloc[0]
    sims, actual = simulate_player(get_shots(), row["player_id"])
    st.pyplot(plots.simulation_histogram(sims, actual, name))
    low, high = FINISHING_INTERVAL
    st.markdown(
        f"Each non-penalty shot is replayed 10,000 times as a coin flip that succeeds with "
        f"probability equal to its xG. **{name}** scored **{actual}** goals from "
        f"**{row['npxg']:.1f} npxG**; {row['p_at_least']:.1%} of simulated seasons reach "
        f"{actual} or more, so the real total is **{row['verdict']}** the {low}-{high}% band."
    )

with st.expander("Finishing table of all simulated players"):
    st.dataframe(
        finishing.drop(columns=["player_id"]),
        hide_index=True,
        column_config={
            "npxg": st.column_config.NumberColumn("npxG", format="%.1f"),
            "expected": st.column_config.NumberColumn("Simulated mean", format="%.1f"),
            "p_at_least": st.column_config.NumberColumn("P(≥ actual)", format="%.3f"),
            "p_at_most": st.column_config.NumberColumn("P(≤ actual)", format="%.3f"),
        },
    )
    st.caption(
        "With this many players tested, about 5% fall outside the band by chance alone "
        "(multiple testing), so a single flag is a reason to watch video, not proof of skill."
    )
