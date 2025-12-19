import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from .models import CHANNEL_COLOR

LANES = ["CRO", "Clinical Ops", "Depot/WMS", "Logistics", "MES/QA"]
LANE_Y = {name: i for i, name in enumerate(LANES)}

def create_gantt_timeline(events_df):
    """Create a Gantt-style timeline showing communication delays by actor and channel.
    
    Args:
        events_df: DataFrame with columns: t, actor, target, channel, action, details
    
    Returns:
        Plotly figure with horizontal bars showing timing and duration of each interaction
    """
    if events_df is None or events_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No events to display",
            height=400,
            margin=dict(l=120, r=20, t=50, b=50)
        )
        return fig

    df = events_df.copy().reset_index(drop=True)
    
    # Normalize actor names for lane mapping
    def normalize_actor(name: str) -> str:
        n = str(name).replace(" (Human)", "").strip()
        return n
    
    df['normalized_actor'] = df['actor'].apply(normalize_actor)
    
    # Filter to actors we have lanes for
    df = df[df['normalized_actor'].isin(LANES)]
    
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No events for tracked actors",
            height=400,
            margin=dict(l=120, r=20, t=50, b=50)
        )
        return fig
    
    # Sort by time
    df = df.sort_values('t')
    
    # Convert to hours from start for easier display
    start_time = df['t'].min()
    df['hours_from_start'] = (df['t'] - start_time).dt.total_seconds() / 3600
    df['days_from_start'] = df['hours_from_start'] / 24
    
    # Create bars - we'll group consecutive events by same actor to show durations
    bars = []
    
    # For now, create individual bars for each event with estimated durations
    for idx, row in df.iterrows():
        actor = row['normalized_actor']
        channel = row['channel']
        action = row['action']
        details = row.get('details', '')
        
        # Estimate duration based on channel type - made longer for better visibility
        if channel == 'email':
            duration_hours = 4    # Longer bar for email events
        elif channel == 'manual':
            duration_hours = 8    # Longer for manual work
        elif channel == 'ticket':
            duration_hours = 16   # Much longer for ticket work
        elif channel == 'system':
            duration_hours = 2    # Longer for system lookups
        else:
            duration_hours = 6    # Default longer
        
        y_pos = LANE_Y.get(actor, 0)
        color = CHANNEL_COLOR.get(channel, '#999999')
        
        bars.append({
            'actor': actor,
            'channel': channel,
            'start_hours': row['hours_from_start'],
            'duration_hours': duration_hours,
            'y_pos': y_pos,
            'color': color,
            'action': action,
            'details': details,
            'start_day': row['days_from_start']
        })
    
    # Create the figure
    fig = go.Figure()
    
    # Add horizontal bars
    for bar in bars:
        fig.add_trace(go.Scatter(
            x=[bar['start_hours'], bar['start_hours'] + bar['duration_hours']],
            y=[bar['y_pos'], bar['y_pos']],
            mode='lines',
            line=dict(color=bar['color'], width=20),
            showlegend=False,
            hovertemplate=(
                f"<b>{bar['actor']}</b><br>"
                f"Channel: {bar['channel']}<br>"
                f"Action: {bar['action']}<br>"
                f"Details: {bar['details']}<br>"
                f"Day {bar['start_day']:.1f}<br>"
                f"Duration: {bar['duration_hours']:.1f}h"
                "<extra></extra>"
            )
        ))
    
    # Add lane labels and grid lines
    for lane, y in LANE_Y.items():
        # Horizontal grid line
        fig.add_hline(y=y, line_color="rgba(128,128,128,0.2)", line_width=1)
    
    # Configure layout
    max_hours = max([b['start_hours'] + b['duration_hours'] for b in bars]) if bars else 24
    max_days = max_hours / 24
    
    # Create day markers for x-axis
    day_ticks = []
    day_labels = []
    for day in range(int(max_days) + 2):
        day_ticks.append(day * 24)
        day_labels.append(f"Day {day}")
    
    fig.update_layout(
        title="Timeline: Communication Delays by Actor",
        xaxis=dict(
            title="Time",
            tickmode='array',
            tickvals=day_ticks,
            ticktext=day_labels,
            range=[-2, max(max_hours + 6, 48)],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)"
        ),
        yaxis=dict(
            title="Actor",
            tickmode='array',
            tickvals=list(LANE_Y.values()),
            ticktext=list(LANE_Y.keys()),
            range=[-0.5, len(LANES) - 0.5],
            showgrid=False
        ),
        height=400,
        margin=dict(l=120, r=20, t=50, b=50),
        hovermode='closest'
    )
    
    return fig