"""Streamlit entry point: declares the pages and the shared sidebar.

Run with ``streamlit run app.py`` after ``python scripts/build_dataset.py``.
"""

import streamlit as st

from moneyball.config import COMPETITION_LABEL, MIN_MINUTES, DATA_CREDIT

st.set_page_config(page_title="Moneyball FC", page_icon=":material/sports_soccer:", layout="wide")

pages = [
    st.Page("pages/overview.py", title="Overview", icon=":material/home:", default=True),
]

with st.sidebar:
    st.markdown(f"**Moneyball FC** · {COMPETITION_LABEL}")
    st.slider(
        "Minimum minutes played",
        min_value=450,
        max_value=2700,
        value=MIN_MINUTES,
        step=90,
        key="min_minutes",
        help="Per-90 metrics of players below this threshold are too noisy to compare.",
    )
    st.caption(DATA_CREDIT)

st.navigation(pages).run()
