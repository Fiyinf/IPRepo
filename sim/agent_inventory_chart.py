import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from .models import CHANNEL_COLOR

def create_agent_inventory_chart(events_df, simulation_days=20):
    """Create an inventory chart showing how agents prevent stockouts through proactive management.
    
    Args:
        events_df: DataFrame with agent timeline events
        simulation_days: Number of days to show on x-axis
        
    Returns:
        Plotly figure with optimized inventory lines and agent event markers
    """
    
    fig = go.Figure()
    
    # Generate optimized inventory data (agents prevent stockouts)
    days = np.linspace(0, simulation_days, simulation_days * 4)  # 4 points per day for smooth curves
    
    # Site inventory - agents detect spike early and coordinate resupply
    site_inventory_optimized = []
    current_site = 150
    
    for day in days:
        if day < 1:
            # Normal consumption before spike
            daily_consumption = 5
        elif day < 3:
            # Spike detected early by CRO Interface Agent
            daily_consumption = 15
        elif day < 4:
            # Agents coordinate immediate response - consumption continues but resupply coming
            daily_consumption = 15
        elif 4 <= day <= 4.5:
            # First emergency shipment arrives (agent-coordinated)
            daily_consumption = 15
            current_site += 50  # Emergency shipment
        elif day < 7:
            # Continued elevated consumption with proactive resupply
            daily_consumption = 12
        elif 7 <= day <= 7.5:
            # Second optimized shipment arrives
            daily_consumption = 12
            current_site += 60  # Optimized shipment
        elif day < 12:
            # Gradual normalization with predictive inventory management
            daily_consumption = 8
        elif 12 <= day <= 12.5:
            # Predictive restocking by agents
            daily_consumption = 6
            current_site += 40  # Predictive restock
        else:
            # Stabilized with optimal inventory levels
            daily_consumption = 5
        
        # Add small randomness but keep above critical levels
        consumption = daily_consumption * (1/4) * (1 + np.random.normal(0, 0.05))
        current_site = max(25, current_site - consumption)  # Agents maintain safety stock
        
        site_inventory_optimized.append(current_site)
    
    # Depot inventory - more frequent, optimized shipments
    depot_inventory_optimized = []
    current_depot = 800
    
    for day in days:
        # Multiple smaller, optimized shipments
        if 4.0 <= day <= 4.1:
            current_depot -= 50   # Emergency shipment
        elif 7.0 <= day <= 7.1:
            current_depot -= 60   # Optimized shipment
        elif 12.0 <= day <= 12.1:
            current_depot -= 40   # Predictive restock
        elif 15.0 <= day <= 15.1:
            current_depot -= 30   # Maintenance restock
            
        depot_inventory_optimized.append(current_depot)
    
    # Add optimized site inventory line (purple)
    fig.add_trace(
        go.Scatter(
            x=days,
            y=site_inventory_optimized,
            mode='lines+markers',
            name='Site Inventory (Agent-Optimized)',
            line=dict(color='#8b5cf6', width=3),  # Purple for site
            marker=dict(size=4),
            hovertemplate="Day %{x:.1f}<br>Site Units: %{y:.0f}<extra></extra>"
        )
    )
    
    # Add optimized depot inventory line (orange)
    fig.add_trace(
        go.Scatter(
            x=days,
            y=depot_inventory_optimized,
            mode='lines+markers',
            name='Depot Inventory (Agent-Managed)',
            line=dict(color='#f59e0b', width=3, dash='dot'),
            marker=dict(size=4),
            hovertemplate="Day %{x:.1f}<br>Depot Units: %{y:.0f}<extra></extra>"
        )
    )
    
    # Add safety stock zone (light purple background - maintained by agents)
    fig.add_shape(
        type="rect",
        x0=0, x1=simulation_days,
        y0=20, y1=50,
        fillcolor="rgba(139, 92, 246, 0.1)",
        layer="below",
        line_width=0,
    )
    
    # Add critical zone (rarely entered with agents)
    fig.add_shape(
        type="rect",
        x0=0, x1=simulation_days,
        y0=0, y1=20,
        fillcolor="rgba(239, 68, 68, 0.1)",
        layer="below",
        line_width=0,
    )
    
    # Add comprehensive agent monitoring timeline showing continuous operations
    agent_events_timeline = [
        # Day 0: Initial spike detection and emergency response
        {'day': 0, 'channel': 'mcp', 'action': 'Enrollment spike detected (15+ patients)', 'time': 'Day 0 09:00'},
        {'day': 0.01, 'channel': 'a2a', 'action': 'Emergency alert triggered', 'time': 'Day 0 09:00'},
        {'day': 0.02, 'channel': 'mcp', 'action': 'Real-time inventory assessment', 'time': 'Day 0 09:00'},
        {'day': 0.04, 'channel': 'a2a', 'action': 'Emergency batch allocation (50 units)', 'time': 'Day 0 09:01'},
        {'day': 0.07, 'channel': 'a2a', 'action': 'Expedited shipment coordinated', 'time': 'Day 0 09:02'},
        
        # Day 1: Continuous monitoring begins
        {'day': 1, 'channel': 'mcp', 'action': 'Daily enrollment monitoring', 'time': 'Day 1'},
        {'day': 1.5, 'channel': 'mcp', 'action': 'Inventory level check', 'time': 'Day 1'},
        
        # Day 3: Consumption pattern analysis
        {'day': 3, 'channel': 'mcp', 'action': 'Consumption pattern analysis', 'time': 'Day 3'},
        {'day': 3.2, 'channel': 'a2a', 'action': 'Forecast model updated', 'time': 'Day 3'},
        
        # Day 4: First resupply arrives
        {'day': 4, 'channel': 'a2a', 'action': 'Emergency shipment delivered', 'time': 'Day 4'},
        {'day': 4.1, 'channel': 'mcp', 'action': 'Inventory restocked (+50 units)', 'time': 'Day 4'},
        
        # Day 5: Trend stabilization detected
        {'day': 5, 'channel': 'mcp', 'action': 'Enrollment trend stabilization', 'time': 'Day 5'},
        {'day': 5.5, 'channel': 'a2a', 'action': 'Supply plan optimization', 'time': 'Day 5'},
        
        # Day 7: Proactive second shipment
        {'day': 7, 'channel': 'a2a', 'action': 'Proactive shipment triggered', 'time': 'Day 7'},
        {'day': 7.5, 'channel': 'mcp', 'action': 'Optimal batch selection', 'time': 'Day 7'},
        
        # Day 8: Second shipment arrives
        {'day': 8, 'channel': 'a2a', 'action': 'Optimized shipment delivered', 'time': 'Day 8'},
        
        # Day 10: Continuous optimization
        {'day': 10, 'channel': 'mcp', 'action': 'Weekly consumption review', 'time': 'Day 10'},
        {'day': 10.5, 'channel': 'a2a', 'action': 'Safety stock adjustment', 'time': 'Day 10'},
        
        # Day 12: Predictive restocking
        {'day': 12, 'channel': 'a2a', 'action': 'Predictive restock initiated', 'time': 'Day 12'},
        {'day': 12.5, 'channel': 'mcp', 'action': 'Automated batch allocation', 'time': 'Day 12'},
        
        # Day 13: Final optimization
        {'day': 13, 'channel': 'a2a', 'action': 'Maintenance shipment delivered', 'time': 'Day 13'},
        
        # Day 15: Ongoing monitoring
        {'day': 15, 'channel': 'mcp', 'action': 'Continuous monitoring active', 'time': 'Day 15'},
        {'day': 16, 'channel': 'mcp', 'action': 'System health check', 'time': 'Day 16'},
        {'day': 17, 'channel': 'a2a', 'action': 'Steady-state operations', 'time': 'Day 17'}
    ]
    
    for event in agent_events_timeline:
        day = event['day']
        channel = event['channel']
        action = event['action']
        time = event['time']
        
        # Get color for channel
        color = CHANNEL_COLOR.get(channel, '#999999')
        
        # Determine marker position (above the chart)
        y_pos = 850
        
        # Add marker symbol based on channel
        if channel == 'mcp':
            symbol = 'diamond'
        elif channel == 'a2a':
            symbol = 'circle'
        elif channel == 'system':
            symbol = 'square'
        else:
            symbol = 'cross'
        
        # Add event marker
        fig.add_trace(
            go.Scatter(
                x=[day],
                y=[y_pos],
                mode='markers',
                marker=dict(
                    symbol=symbol,
                    size=12,
                    color=color,
                    line=dict(color='white', width=1)
                ),
                showlegend=False,
                hovertemplate=f"<b>{time}</b><br>{action}<br>Channel: {channel}<extra></extra>"
            )
        )
        
        # Add vertical line from marker to chart
        fig.add_shape(
            type="line",
            x0=day, x1=day,
            y0=0, y1=y_pos-50,
            line=dict(color=color, width=2, dash="dot"),
            opacity=0.7
        )
    
    # Configure layout
    fig.update_layout(
        title="Agent-Optimized Inventory Management",
        xaxis=dict(
            title="Days",
            range=[0, simulation_days],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)"
        ),
        yaxis=dict(
            title="Units",
            range=[0, 900],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.2)"
        ),
        height=500,
        showlegend=False,
        hovermode='closest',
        margin=dict(l=50, r=20, t=80, b=50)
    )
    
    # Add annotation for safety stock zone
    fig.add_annotation(
        x=1,
        y=35,
        text="Safety Stock Zone",
        showarrow=False,
        font=dict(color="#8b5cf6", size=10),
        bgcolor="rgba(255,255,255,0.8)"
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