"""Visualisation: each function takes DataFrames and returns a figure.

The distribution chart uses matplotlib; charts that benefit from hovering
use Plotly.
"""

import numpy as np
import plotly.graph_objects as go
from matplotlib.figure import Figure

from moneyball.config import (
    DATA_CREDIT,
    FINISHING_INTERVAL,
    HIGHLIGHT_COLOR,
    MUTED_COLOR,
    SECOND_COLOR,
)


def _credit_plotly(fig):
    """Add the data source note in the bottom-right corner of a Plotly figure."""
    fig.add_annotation(
        text=DATA_CREDIT,
        xref="paper",
        yref="paper",
        x=1,
        y=-0.12,
        showarrow=False,
        font={"size": 10, "color": "grey"},
        xanchor="right",
    )
    return fig


def _player_points(players, color, size, mode, name):
    """Build one scatter trace of npxG (x) against goals (y) for some players.

    The hover box shows name, team and minutes.
    """
    hover = (
        "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
        "npxG %{x:.1f} · goals %{y}<br>%{customdata[2]:.0f} minutes<extra></extra>"
    )
    return go.Scatter(
        x=players["npxg"],
        y=players["np_goals"],
        mode=mode,
        text=players["player_name"],
        textposition="top center",
        marker={"color": color, "size": size},
        customdata=players[["player_name", "team_name", "minutes"]],
        hovertemplate=hover,
        name=name,
    )


def goals_vs_xg_scatter(table, highlight=()):
    """Plot non-penalty goals against npxG for every player.

    Parameters
    ----------
    table : pandas.DataFrame
        Player table with ``player_name, team_name, minutes, npxg, np_goals``.
    highlight : sequence of str, optional
        Player names drawn in colour and labelled.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    table = table.assign(diff=table["np_goals"] - table["npxg"])
    # idxmax gives the index label of the largest value
    top = table.loc[table["diff"].idxmax()]

    is_highlight = table["player_name"].isin(highlight)
    others = table[~is_highlight]
    highlighted = table[is_highlight]

    fig = go.Figure()

    # Diagonal: Goals = npxG
    limit = max(table["npxg"].max(), table["np_goals"].max()) + 1
    fig.add_trace(
        go.Scatter(
            x=[0, limit],
            y=[0, limit],
            mode="lines",
            line={"color": "black", "dash": "dash", "width": 1},
            name="Goals = npxG",
            hoverinfo="skip",
        )
    )

    # Normal players: grey points
    fig.add_trace(_player_points(others, MUTED_COLOR, 6, "markers", "Other players"))
    # Highlighted players: blue points
    fig.add_trace(
        _player_points(highlighted, HIGHLIGHT_COLOR, 9, "markers+text", "Highlighted")
    )

    fig.update_layout(
        title=f"{top['player_name']} beat his npxG by the widest margin ({top['diff']:+.1f} goals)",
        xaxis_title="Non-penalty expected goals (npxG, season total)",
        yaxis_title="Non-penalty goals (season total)",
        template="plotly_white",
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    return _credit_plotly(fig)


def simulation_histogram(sims, actual, player_name):
    """Show the simulated goal distribution against the real goal total.

    Parameters
    ----------
    sims : numpy.ndarray
        Simulated goal totals from ``analysis.simulate_player``.
    actual : int
        Goals actually scored.
    player_name : str
        Used in the title.

    Returns
    -------
    matplotlib.figure.Figure
        Bars of the simulated distribution, the shaded 5-95% band and a
        dashed line at the real total.
    """
    low_pct, high_pct = FINISHING_INTERVAL
    low, high = np.percentile(sims, [low_pct, high_pct])

    fig = Figure(figsize=(8, 4.5))
    ax = fig.subplots()
    bins = np.arange(sims.min(), max(sims.max(), actual) + 2) - 0.5
    ax.hist(
        sims, bins=bins, color=MUTED_COLOR, edgecolor="white", label="Simulated seasons"
    )

    ax.axvspan(
        low - 0.5,
        high + 0.5,
        color=HIGHLIGHT_COLOR,
        alpha=0.12,
        label=f"{low_pct}-{high_pct}% range",
    )
    ax.axvline(
        actual,
        color=SECOND_COLOR,
        linestyle="--",
        linewidth=2.5,
        label=f"Actual: {actual}",
    )

    ax.set_xlabel("Non-penalty goals in a simulated season")
    ax.set_ylabel(f"Number of simulations (of {len(sims):,})")
    title = ""
    if actual >= sims.mean():
        share = (sims >= actual).mean()
        title = (
            f"{player_name}: {actual} goals vs {sims.mean():.1f} expected; "
            f"{share:.1%} of simulations reach {actual}"
        )

    else:
        share = (sims <= actual).mean()
        title = (
            f"{player_name}: {actual} goals vs {sims.mean():.1f} expected; "
            f"only {share:.1%} of simulations score {actual} or fewer"
        )

    ax.set_title(
        title,
        fontsize=11,
    )
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.99, 0.01, DATA_CREDIT, ha="right", fontsize=8, color="grey")
    fig.tight_layout()
    return fig
