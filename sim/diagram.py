from typing import List, Dict
import plotly.graph_objects as go
from .models import CHANNEL_COLOR

LANES = ["CRO", "Clinical Ops", "WMS", "Logistics", "MES/QA"]
LANE_Y = {name: i for i, name in enumerate(LANES)}


def comms_diagram(events_df):
    """Build a simple swimlane diagram with arrows for email/manual events.
    Uses sequential indices on x-axis.
    """
    if events_df is None or events_df.empty:
        fig = go.Figure()
        fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
        return fig

    df = events_df.reset_index(drop=True)
    df = df.assign(idx=df.index)

    fig = go.Figure()
    # Draw swimlanes as light gray horizontal lines
    for lane, y in LANE_Y.items():
        fig.add_trace(go.Scatter(x=[-0.5, len(df)-0.5], y=[y, y], mode="lines", line=dict(color="#e0e0e0", width=1), showlegend=False))

    # Add annotations (arrows) for each event
    for i, row in df.iterrows():
        actor = row.get("actor", "")
        target = row.get("target", "")
        channel = row.get("channel", "")
        # Map to lane names (strip role suffixes)
        def normalize(name: str) -> str:
            n = str(name)
            n = n.replace(" (Human)", "")
            return n
        a = normalize(actor)
        t = normalize(target)
        ay = LANE_Y.get(a, 0)
        ty = LANE_Y.get(t, 0)
        color = CHANNEL_COLOR.get(channel, "#1f77b4")
        fig.add_annotation(
            x=i, y=ay,
            ax=i, ay=ty,
            xref="x", yref="y", axref="x", ayref="y",
            text="✉" if channel == "email" else "",
            showarrow=True,
            arrowhead=2,
            arrowwidth=2,
            arrowcolor=color,
            font=dict(color=color),
        )

    fig.update_yaxes(
        tickmode="array",
        tickvals=list(LANE_Y.values()),
        ticktext=list(LANE_Y.keys()),
        range=[-0.5, len(LANES)-0.5],
        title=None,
    )
    fig.update_xaxes(title=None, showticklabels=False, range=[-0.5, max(0, len(df)-0.5)])
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
    return fig
