"""Overview page: research question, headline numbers, shortlist, limitations."""

import streamlit as st

from moneyball import plots
from moneyball.config import COMPETITION_LABEL, SHORTLIST, TARGET_PLAYER
from ui_common import get_finishing, get_players, get_tables, min_minutes

tables = get_tables()
threshold = min_minutes()
players = get_players(threshold)
finishing = get_finishing(threshold)

st.title("Moneyball FC: who replaces Higuaín?")
st.markdown(
    f"""
Summer 2016: Napoli lose **{TARGET_PLAYER}** to Juventus after a record season.
Using {COMPETITION_LABEL} data, **which players contribute attacking output at a high
rate per 90, have a profile close to Higuaín, and is that output sustainable or luck?**

1. **SQ1 Finishing**: who scores above or below expectation (goals vs npxG), and is the
   gap outside the range of luck? *Monte Carlo simulation*
2. **SQ2 Output**: who creates and takes the best chances per 90 within his position
   group? *Per-90 metrics + percentiles*
3. **SQ3 Replacement**: whose statistical profile is closest to Higuaín's? *Standardised
   vectors + cosine similarity*
"""
)

col1, col2, col3 = st.columns(3)
col1.metric("Matches", len(tables["matches"]))
col2.metric("Players analysed", len(players), help=f"At least {threshold} minutes")
col3.metric("Players simulated (SQ1)", len(finishing))

st.subheader("Goals vs expected goals")
st.plotly_chart(
    plots.goals_vs_xg_scatter(players, highlight=[TARGET_PLAYER] + list(SHORTLIST)),
    width="stretch",
)

st.subheader("Shortlist")
st.caption(
    "Chosen from SQ1-SQ3: same position group as Higuaín, ≥ 80th percentile on npxG per 90, "
    "not at a top-5 club, most similar profile first. Next step: video scouting and price check."
)
is_shortlisted = players["player_name"].isin(SHORTLIST)
st.dataframe(
    players.loc[
        is_shortlisted,
        [
            "player_name",
            "team_name",
            "minutes",
            "npxg_p90",
            "xa_p90",
            "np_goals",
            "npxg",
        ],
    ],
    hide_index=True,
    column_config={
        "player_name": "Player",
        "team_name": "Team",
        "minutes": st.column_config.NumberColumn("Minutes", format="%d"),
        "npxg_p90": st.column_config.NumberColumn("npxG/90", format="%.2f"),
        "xa_p90": st.column_config.NumberColumn("xA/90", format="%.2f"),
        "np_goals": "NP goals",
        "npxg": st.column_config.NumberColumn("npxG", format="%.1f"),
    },
)

st.subheader("Limitations")
st.markdown(
    """
- One season (2015/16): no trend across seasons. No transfer fees, wages or ages:
  "not at a top-5 club" is only a proxy for affordable.
- Individual numbers depend on team style and team-mates.
- Per-90 values are noisy for low minutes; the threshold is a judgement call (use the slider).
"""
)
