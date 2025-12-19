import plotly.graph_objects as go
import plotly.express as px
from .models import CHANNEL_COLOR

def create_network_map(events_df):
    """Create a static network map showing system interactions and communication flows.
    
    Args:
        events_df: DataFrame with timeline events
        
    Returns:
        Plotly figure with system boxes and communication arrows
    """
    
    # Define system positions (x, y coordinates)
    systems = {
        "CRO": {"x": 1, "y": 4, "color": "#5470c6", "label": "CRO\nCTMS/EDC"},
        "Clinical Ops": {"x": 3, "y": 4, "color": "#9c3eed", "label": "Clinical Ops\nIRT/RTMS"},
        "Depot/WMS": {"x": 1, "y": 2, "color": "#ee46bc", "label": "Depot/WMS\nWMS"},
        "Logistics": {"x": 3, "y": 2, "color": "#ffa726", "label": "Logistics\nTMS"},
        "MES/QA": {"x": 2, "y": 0.5, "color": "#4caf50", "label": "MES/QA\nERP/LIMS"}
    }
    
    fig = go.Figure()
    
    # Add system boxes
    for system_name, props in systems.items():
        fig.add_trace(go.Scatter(
            x=[props["x"]],
            y=[props["y"]],
            mode='markers+text',
            marker=dict(
                size=120,
                color=props["color"],
                symbol='square',
                line=dict(color='white', width=2)
            ),
            text=props["label"],
            textposition="middle center",
            textfont=dict(color='white', size=11, family="Arial Black"),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Define communication flows based on the BEFORE scenario
    flows = [
        # CRO → Clinical Ops: Weekly report
        {
            "from": "CRO", "to": "Clinical Ops",
            "type": "email", "label": "Weekly enrollment\nreport (email)",
            "delay": "48h"
        },
        # Clinical Ops → Depot/WMS: Inventory check
        {
            "from": "Clinical Ops", "to": "Depot/WMS",
            "type": "ticket", "label": "Check inventory\n(ticket)",
            "delay": "24h"
        },
        # Depot/WMS internal: System query
        {
            "from": "Depot/WMS", "to": "Depot/WMS",
            "type": "system", "label": "ERP/WMS\nquery",
            "delay": "instant", "self_loop": True
        },
        # Clinical Ops → Logistics: Urgent shipment
        {
            "from": "Clinical Ops", "to": "Logistics",
            "type": "ticket", "label": "Urgent shipment\n(ticket)",
            "delay": "16h"
        },
        # Clinical Ops → Logistics: Clarification email
        {
            "from": "Clinical Ops", "to": "Logistics",
            "type": "email", "label": "Clarification\n(email)",
            "delay": "8h", "offset": True
        },
        # Logistics → Depot/WMS: Confirm availability
        {
            "from": "Logistics", "to": "Depot/WMS",
            "type": "ticket", "label": "Confirm depot\navailability",
            "delay": "8h"
        },
        # Depot/WMS → MES/QA: Batch release
        {
            "from": "Depot/WMS", "to": "MES/QA",
            "type": "email", "label": "Batch release\napproval",
            "delay": "20h"
        },
        # MES/QA → MES/QA: LIMS lookup
        {
            "from": "MES/QA", "to": "MES/QA",
            "type": "system", "label": "LIMS/QMS\nquery",
            "delay": "instant", "self_loop": True
        }
    ]
    
    # Add communication arrows
    for flow in flows:
        from_sys = systems[flow["from"]]
        to_sys = systems[flow["to"]]
        channel_type = flow["type"]
        
        # Get color and style based on channel type
        color = CHANNEL_COLOR.get(channel_type, "#999999")
        
        if channel_type == "email":
            line_style = dict(color=color, width=3, dash="dash")
        elif channel_type == "ticket":
            line_style = dict(color=color, width=4)
        elif channel_type == "system":
            line_style = dict(color=color, width=2)
        else:
            line_style = dict(color=color, width=3)
        
        if flow.get("self_loop"):
            # Self-loop for system queries
            fig.add_shape(
                type="circle",
                x0=from_sys["x"] + 0.3, y0=from_sys["y"] + 0.2,
                x1=from_sys["x"] + 0.5, y1=from_sys["y"] + 0.4,
                line=line_style
            )
            # Add label for self-loop
            fig.add_annotation(
                x=from_sys["x"] + 0.6,
                y=from_sys["y"] + 0.3,
                text=flow["label"],
                showarrow=False,
                font=dict(size=9, color=color),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=color,
                borderwidth=1
            )
        else:
            # Regular arrow between systems
            offset_y = -0.1 if flow.get("offset") else 0
            
            fig.add_annotation(
                x=to_sys["x"],
                y=to_sys["y"] + offset_y,
                ax=from_sys["x"],
                ay=from_sys["y"] + offset_y,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.5,
                arrowwidth=line_style["width"],
                arrowcolor=color,
                text="",
                font=dict(size=9, color=color)
            )
            
            # Add label near the middle of the arrow
            mid_x = (from_sys["x"] + to_sys["x"]) / 2
            mid_y = (from_sys["y"] + to_sys["y"]) / 2 + offset_y
            
            fig.add_annotation(
                x=mid_x,
                y=mid_y + 0.15,
                text=flow["label"],
                showarrow=False,
                font=dict(size=9, color=color),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor=color,
                borderwidth=1
            )
    
    # Configure layout
    fig.update_layout(
        title="Communication Network Map",
        xaxis=dict(
            range=[0, 4],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        yaxis=dict(
            range=[0, 5],
            showgrid=False,
            showticklabels=False,
            zeroline=False
        ),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def create_communication_flows_table(events_df):
    """Create a table showing communication flows and delays."""
    if events_df is None or events_df.empty:
        return None
    
    # Analyze events to create flow summary
    df = events_df.copy()
    start_time = df['t'].min()
    df['hours_from_start'] = (df['t'] - start_time).dt.total_seconds() / 3600
    
    flows = []
    
    # Group consecutive events to show flows
    for i, row in df.iterrows():
        actor = row['actor'].replace(' (Human)', '')
        target = row.get('target', '').replace(' (Human)', '')
        channel = row['channel']
        action = row['action']
        hours = row['hours_from_start']
        
        if target and target != actor:
            flows.append({
                'From': actor,
                'To': target,
                'Channel': channel,
                'Action': action,
                'Time': f"{hours:.1f}h",
                'Delay': f"{hours:.0f}h" if hours > 1 else "<1h"
            })
    
    return flows