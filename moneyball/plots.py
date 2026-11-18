"""Visualisation: each function takes DataFrames and returns a figure.

The distribution chart uses matplotlib; charts that benefit from hovering
use Plotly.
"""

import plotly.graph_objects as go

def _credit_plotly(fig):
    """Add the data source note in the bottom-right corner of a Plotly figure."""
    fig.add_annotation(
        text="Data: StatsBomb Open Data",
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

    The hover box shows name, team and minutes,
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
            x=[0, limit], y=[0, limit],
            mode="lines",
            line={"color": "black", "dash": "dash", "width": 1},
            name="Goals = npxG",
            hoverinfo="skip",
        )
    )
    
    # Normal players: grey points
    fig.add_trace(_player_points(others, "#B0B0B0", 6, "markers", "Other players"))
    # Highlighted players: blue points
    fig.add_trace(_player_points(highlighted, "#0072B2", 9, "markers+text", "Highlighted"))

    fig.update_layout(
        title=f"{top['player_name']} beat his npxG by the widest margin ({top['diff']:+.1f} goals)",
        xaxis_title="Non-penalty expected goals (npxG, season total)",
        yaxis_title="Non-penalty goals (season total)",
        template="plotly_white",
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    return _credit_plotly(fig)

