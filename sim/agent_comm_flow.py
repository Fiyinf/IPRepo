import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from .models import CHANNEL_COLOR

def create_agent_comm_flow(events_df):
    """Create a communication flow visualization showing all agent messages."""
    
    if events_df is None or events_df.empty:
        st.info("No agent communication events to display")
        return
    
    # Define the agent communication sequence
    comm_events = [
        {
            'day': 'Day 0',
            'timestamp': '09:00:00',
            'type': 'MCP',
            'from': 'CRO Interface Agent',
            'to': 'Clinical Trial Management System (CTMS) Database',
            'message': 'Query: Latest enrollment data for Mass General Brigham',
            'details': 'Agent monitors real-time enrollment spike detected at Mass General Brigham. Current enrollment rate shows 15+ new patients above forecast, triggering supply chain assessment.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:00:15',
            'type': 'A2A',
            'from': 'CRO Interface Agent', 
            'to': 'Clinical Ops Agent',
            'message': 'Alert: Enrollment spike detected at Mass General Brigham',
            'details': 'Automated alert sent to Clinical Ops Agent about unexpected enrollment increase. Site US-BOS-001 now requires immediate supply forecast adjustment and potential emergency resupply.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:00:30',
            'type': 'MCP',
            'from': 'Clinical Ops Agent',
            'to': 'ERP System',
            'message': 'Query: Current depot inventory levels and site allocation',
            'details': 'Agent queries enterprise resource planning system to assess current inventory at depot and existing allocations to Mass General Brigham to determine resupply requirements.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:01:00',
            'type': 'A2A',
            'from': 'Clinical Ops Agent',
            'to': 'MES Agent',
            'message': 'Request: Batch allocation for emergency resupply (qty: 50 units)',
            'details': 'Clinical Ops Agent calculates that 50 additional units are needed based on enrollment spike projections and requests MES Agent to identify suitable batches using optimal allocation.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:01:15',
            'type': 'MCP',
            'from': 'MES Agent',
            'to': 'Warehouse Management System (WMS)',
            'message': 'Query: Available batches with stability and expiry data',
            'details': 'MES Agent queries the warehouse management system (WMS) to identify all available batches at the depot, checking stability data, remaining shelf life, and available quantities for allocation.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:01:30',
            'type': 'MCP',
            'from': 'MES Agent',
            'to': 'Quality Management System (QMS)',
            'message': 'Query: Batch release status and compliance validation',
            'details': 'Agent validates that selected batches B2024-001 and B2024-003 are fully released for distribution and meet all quality compliance requirements for patient dosing.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:01:45',
            'type': 'A2A',
            'from': 'MES Agent',
            'to': 'Clinical Ops Agent',
            'message': 'Response: Batches B2024-001, B2024-003 allocated (release: Jan 20)',
            'details': 'MES Agent confirms allocation of 50 units from two batches using optimized selection logic. Batches are quality-released and available for immediate shipment to Mass General Brigham.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:02:00',
            'type': 'A2A',
            'from': 'Clinical Ops Agent',
            'to': 'Logistics Agent',
            'message': 'Request: Emergency shipment coordination (batches: B2024-001, B2024-003)',
            'details': 'Clinical Ops Agent requests Logistics Agent to coordinate urgent shipment of allocated batches to Mass General Brigham with target delivery within 48 hours to prevent stockout.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:02:15',
            'type': 'MCP',
            'from': 'Logistics Agent',
            'to': 'Transportation Management System',
            'message': 'Query: Depot capacity and shipment routing optimization',
            'details': 'Logistics Agent queries TMS for current depot capacity, available transport carriers, and optimal routing options for temperature-controlled delivery to Boston area.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:02:30',
            'type': 'MCP',
            'from': 'Logistics Agent',
            'to': 'Regulatory Compliance System',
            'message': 'Validation: Cold-chain and regulatory requirements for MA delivery',
            'details': 'Agent validates Massachusetts state regulations, cold-chain requirements, and Mass General Brigham delivery specifications to ensure compliant shipment planning.'
        },
        {
            'day': 'Day 0',
            'timestamp': '09:02:45',
            'type': 'A2A',
            'from': 'Logistics Agent',
            'to': 'Clinical Ops Agent',
            'message': 'Confirmation: Shipment SP-a1b2c3d4 scheduled (ETA: Jan 19, Cost: $740)',
            'details': 'Logistics Agent confirms expedited shipment is scheduled for next-day delivery to Mass General Brigham. Cold-chain transport secured with tracking and temperature monitoring enabled.'
        }
    ]
    
    # Create two columns: communication flow and details panel
    col_comm, col_details = st.columns([3, 1])
    
    with col_comm:
        st.markdown("### Communication Flow")
        st.caption("Complete agent coordination sequence (< 3 minutes)")
        
        # Display all communication events in a scrollable container
        with st.container(height=500):
            for i, event in enumerate(comm_events):
                # Determine colors based on communication type
                if event['type'] == 'MCP':
                    border_color = CHANNEL_COLOR.get('mcp', '#3b82f6')
                    bg_color = "#eff6ff"
                    type_badge_color = "#1e40af"
                elif event['type'] == 'A2A':
                    border_color = CHANNEL_COLOR.get('a2a', '#f59e0b')
                    bg_color = "#fffbeb"
                    type_badge_color = "#d97706"
                else:
                    border_color = "#6b7280"
                    bg_color = "#f9fafb"
                    type_badge_color = "#374151"
                
                # Compact event card
                st.markdown(
                    f"""
                    <div style='
                        border-left: 4px solid {border_color};
                        padding: 10px 12px;
                        margin: 6px 0;
                        background: {bg_color};
                        border-radius: 0 6px 6px 0;
                    '>
                        <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;'>
                            <div style='display: flex; align-items: center; gap: 6px;'>
                                <span style='
                                    font-size: 11px;
                                    color: #6b7280;
                                    font-weight: 600;
                                '>{event['day']}</span>
                                <span style='
                                    font-size: 11px;
                                    color: #6b7280;
                                    font-family: monospace;
                                '>{event['timestamp']}</span>
                            </div>
                            <span style='
                                background: {type_badge_color};
                                color: white;
                                padding: 2px 6px;
                                border-radius: 10px;
                                font-size: 9px;
                                font-weight: 600;
                            '>{event['type']}</span>
                        </div>
                        <div style='
                            font-weight: 600;
                            color: #111827;
                            font-size: 13px;
                            margin-bottom: 3px;
                        '>
                            {event['from']} → {event['to']}
                        </div>
                        <div style='
                            color: #4b5563;
                            font-size: 12px;
                            line-height: 1.3;
                        '>
                            {event['message']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Compact legend (avoid nested columns; use inline text)
        st.markdown("**Legend:** MCP = Direct system queries | A2A = Agent-to-agent communication")
    
    with col_details:
        st.markdown("#### Communication Details")
        
        # Summary stats in containers
        with st.container(border=True):
            st.metric("🕒 Total Time", "< 3 minutes", help="Complete coordination time")
            st.metric("📡 Messages", f"{len(comm_events)}", help="Agent communications")
            st.metric("🤖 Agents", "4", help="CRO, Clinical Ops, MES, Logistics")
            st.metric("💻 Systems", "7", help="Clinical Trial Management System (CTMS), ERP, Warehouse Management System (WMS), Quality Management System (QMS), TMS, Compliance")
        
        # Key workflow steps
        st.markdown("#### Workflow Summary")
        with st.container(border=True):
            st.markdown(
                """
                **Detection (0-15s)**  
                CRO Agent detects enrollment spike
                
                **Assessment (15-60s)**  
                Clinical Ops queries inventory & forecasts
                
                **Allocation (60-105s)**  
                MES Agent allocates optimal batches
                
                **Logistics (105-165s)**  
                Logistics coordinates expedited shipment
                """
            )
        
        # Comparison highlight
        st.markdown("#### vs. Manual Process")
        with st.container(border=True):
            st.markdown("**Speed:** 3 minutes vs. 13+ days")
            st.markdown("**Accuracy:** 95% forecast vs. 50%")
            st.markdown("**Cost:** Optimized routing")
            st.markdown("**Stockouts:** Prevented vs. 2.5 days")