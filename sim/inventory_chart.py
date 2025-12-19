import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .models import CHANNEL_COLOR

def create_inventory_chart(events_df, simulation_days=20):
    """Create an inventory depletion chart with event markers showing when humans acted.
    
    Args:
        events_df: DataFrame with timeline events
        simulation_days: Number of days to show on x-axis
        
    Returns:
        Plotly figure with inventory lines and event markers
    """
    
    # Create the subplot with secondary y-axis for events
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": False}]]
    )
    
    # Generate realistic inventory data
    days = np.linspace(0, simulation_days, simulation_days * 4)  # 4 points per day for smooth curves
    
    # Site inventory - starts at ~150, declines due to enrollment spike
    # Normal consumption: ~5 units/day
    # Spike consumption: ~15 units/day starting day 3
    site_inventory = []
    current_site = 150
    
    for day in days:
        if day < 3:
            # Normal consumption
            daily_consumption = 5
        elif day < 8:
            # Enrollment spike - higher consumption
            daily_consumption = 15
        elif day < 15:
            # Still elevated but slowing
            daily_consumption = 10
        else:
            # Back to normal after resupply
            daily_consumption = 5
        
        # Add some randomness
        consumption = daily_consumption * (1/4) * (1 + np.random.normal(0, 0.1))
        current_site = max(0, current_site - consumption)
        
        # Resupply event around day 15
        if 14.8 <= day <= 15.2:
            current_site += 100  # Shipment arrives
            
        site_inventory.append(current_site)
    
    # Depot inventory - starts high, steps down when shipments are sent
    depot_inventory = []
    current_depot = 800
    
    for day in days:
        # Step down at shipment events
        if 14.8 <= day <= 15.2:
            current_depot -= 100  # Shipment sent to site
        elif 8.0 <= day <= 8.2:
            current_depot -= 5   # Small test shipment
            
        depot_inventory.append(current_depot)
    
    # Add site inventory line (red/orange)
    fig.add_trace(
        go.Scatter(
            x=days,
            y=site_inventory,
            mode='lines+markers',
            name='Site Inventory',
            line=dict(color='#ff6b6b', width=3),
            marker=dict(size=4),
            hovertemplate="Day %{x:.1f}<br>Site Units: %{y:.0f}<extra></extra>"
        )
    )
    
    # Add depot inventory line (teal/blue)
    fig.add_trace(
        go.Scatter(
            x=days,
            y=depot_inventory,
            mode='lines+markers',
            name='Depot Inventory',
            line=dict(color='#4ecdc4', width=3, dash='dot'),
            marker=dict(size=4),
            hovertemplate="Day %{x:.1f}<br>Depot Units: %{y:.0f}<extra></extra>"
        )
    )
    
    # Add critical inventory zone (red background when site inventory is low)
    fig.add_shape(
        type="rect",
        x0=0, x1=simulation_days,
        y0=0, y1=20,
        fillcolor="rgba(255, 107, 107, 0.2)",
        layer="below",
        line_width=0,
    )
    
    # Add event markers if events are provided
    if events_df is not None and not events_df.empty:
        df = events_df.copy()
        
        # Convert timestamps to days from start
        start_time = df['t'].min()
        df['days_from_start'] = (df['t'] - start_time).dt.total_seconds() / (24 * 3600)
        
        # Filter to key events and add markers
        key_events = df[df['channel'].isin(['email', 'manual', 'ticket', 'system'])]
        
        for idx, row in key_events.iterrows():
            day = row['days_from_start']
            channel = row['channel']
            action = row['action']
            
            # Get color for channel
            color = CHANNEL_COLOR.get(channel, '#999999')
            
            # Determine marker position (above the chart)
            y_pos = 880  # Fixed height above the chart to allow label above point
            
            # Add marker symbol based on channel
            if channel == 'email':
                symbol = 'diamond'
            elif channel == 'manual':
                symbol = 'square'
            elif channel == 'ticket':
                symbol = 'circle'
            elif channel == 'system':
                symbol = 'triangle-up'
            else:
                symbol = 'cross'
            
            # Prepare small label for the event marker
            # Prepare small label for the event marker
            label = str(action) if action is not None else ""
            if len(label) > 24:
                label = label[:21] + "..."

            # Add event marker (labels only on hover)
            fig.add_trace(
                go.Scatter(
                    x=[day],
                    cliponaxis=False,
                    y=[y_pos],
                    mode='markers',
                    marker=dict(
                        symbol=symbol,
                        size=12,
                        color=color,
                        line=dict(color='white', width=1)
                    ),
                    showlegend=False,
                    hovertemplate=f"<b>Day {day:.1f}</b><br>{action}<br>Channel: {channel}<extra></extra>"
                )
            )
            
            # Add vertical line from marker to chart
            fig.add_shape(
                type="line",
                x0=day, x1=day,
                y0=0, y1=y_pos-50,
                line=dict(color=color, width=2, dash="dash"),
                opacity=0.6
            )
    
    # Configure layout
    fig.update_layout(
        title="Inventory Levels Over Time",
        xaxis=dict(
            title="Days",
            range=[0, simulation_days],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)"
        ),
        yaxis=dict(
            title="Units",
            range=[0, 950],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)"
        ),
        height=500,
        showlegend=False,
        hovermode='closest',
        margin=dict(l=50, r=20, t=80, b=50)
    )
    
    # Add annotation for critical zone
    fig.add_annotation(
        x=1,
        y=10,
        text="Critical Level",
        showarrow=False,
        font=dict(color="red", size=10),
        bgcolor="rgba(255,255,255,0.8)"
    )
    
    return fig

def calculate_inventory_metrics(events_df):
    """Calculate key metrics for inventory management"""
    if events_df is None or events_df.empty:
        return {
            'detection_delay': 0,
            'total_response_time': 0,
            'stockout_duration': 0,
            'patients_affected': 0
        }
    
    start_time = events_df['t'].min()
    end_time = events_df['t'].max()
    
    # Time to first manual detection
    manual_events = events_df[events_df['channel'] == 'manual']
    detection_delay = 0
    if not manual_events.empty:
        first_manual = manual_events['t'].min()
        detection_delay = (first_manual - start_time).total_seconds() / (24 * 3600)
    
    # Total response time
    total_response_time = (end_time - start_time).total_seconds() / (24 * 3600)
    
    # Estimated stockout duration (simplified - based on total time)
    stockout_duration = max(0, total_response_time - 15) if total_response_time > 15 else 0
    
    # Estimated patients affected (simplified calculation)
    patients_affected = int(stockout_duration * 3) if stockout_duration > 0 else 0
    
    return {
        'detection_delay': detection_delay,
        'total_response_time': total_response_time,
        'stockout_duration': stockout_duration,
        'patients_affected': patients_affected
    }