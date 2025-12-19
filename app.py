import random
from datetime import datetime
import os

import streamlit as st
from pydantic import ValidationError

from sim.models import US_SITES
from sim.sim import Simulation
from sim.before import BeforeSimulation
from sim.ui import render_agent_card, render_timeline, render_metrics
from sim.diagram import comms_diagram
from sim.gantt import create_gantt_timeline
from sim.inventory_chart import create_inventory_chart, calculate_inventory_metrics
from sim.agent_inventory_chart import create_agent_inventory_chart
from sim.agent_comm_flow import create_agent_comm_flow
from sim.table import format_before_table


def run_before(site, cro_review_days, wms_delay, mesqa_delay, log_roundtrip, log_rounds):
    sim = BeforeSimulation(seed=42)
    sim.activate_new_site(
        site,
        cro_review_delay_hours=cro_review_days * 24.0,
        wms_email_delay_hours=wms_delay,
        mesqa_email_delay_hours=mesqa_delay,
        logistics_roundtrip_hours=log_roundtrip,
        logistics_rounds=log_rounds,
    )
    return sim


def run_after(site):
    sim = Simulation(seed=42)
    sim.activate_new_site(site)
    return sim


def main():
    st.set_page_config(page_title="Cendrix Bio", layout="wide")

    # Use fixed site - Mass General Brigham
    fixed_site = {"name": "Mass General Brigham", "site_id": "US-BOS-001", "region": "MA"}

    top_tabs = st.tabs(["Simulation", "Agentic Interoperability - Final Deliverable"]) 

    # =============================
    # Research Paper tab
    # =============================
    with top_tabs[1]:
        st.title("Agentic Interoperability Paper")
        pdf_name = "Agentic Interoperability - Final Deliverable.pdf"
        pdf_path = pdf_name
        if not os.path.exists(pdf_path):
            st.warning(f"Could not find '{pdf_name}' in the app directory.")
            st.info("Place the PDF in the same folder as app.py and reload.")
        else:
            # Center a large download icon and button
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.markdown("<div style='text-align:center;font-size:80px;'>⬇️</div>", unsafe_allow_html=True)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=pdf_name,
                    mime="application/pdf",
                    key="download_research_paper"
                )

    # ==============================
    # Simulation tab with subtabs
    # ==============================
    with top_tabs[0]:
        st.title("Cendrix Bio")
        
        # Fixed site display
        st.info(f"**Site:** {fixed_site['name']} ({fixed_site['site_id']})")
        site = fixed_site

        before_tab, after_tab = st.tabs(["Before (Human-driven)", "With Agents"])

        # -------------------------
        # BEFORE (Human-driven)
        # -------------------------
        with before_tab:
            colL, colR = st.columns([1, 2])
            with colL:
                with st.container(border=True):
                    st.subheader("Before: Human communications")
                    st.write(
                        "In the current architecture, there are no agents. All cross-team coordination happens via email and meetings. The timeline below shows those emails as explicit events, with their delays driving how quickly the trial can respond to trouble."
                    )
                    st.markdown(
                        """
                        Scenario: Fast-enrolling US site creates stockout risk.
                        A US site in the trial starts enrolling patients much faster than originally forecast. As patients are randomized, the site consumes kits more quickly and its on-site stock begins to run low. CTMS, IRT, and EDC all capture this behavior in real time, but Clinical Ops only sees it in a weekly enrollment report and has to coordinate by email with the depot, logistics, and QA. The timeline below shows how those emails and meetings drive when the risk is detected and whether the site runs out of drug.
                        """
                    )
                with st.expander("Architecture (current state)", expanded=False):
                    st.image(
                        "Pharma Supply Chain Architecture.png",
                        caption="Current-state architecture: human coordination via email across CRO, Clinical Ops, WMS/Depot, Logistics/TMS, and MES/QA",
                        use_column_width=True,
                    )

            with colR:
                with st.container(border=True):
                    st.subheader("Scenario Parameters")
                    st.markdown(
                        """
                        **Fixed simulation parameters:**
                        - CRO review cycle: 7 days (weekly reports)
                        - WMS response delay: 18 hours (ticket processing)
                        - MES/QA delay: 24 hours (batch validation)
                        - Logistics turnaround: 8 hours per round
                        - Negotiation rounds: 2 (quote → approval)
                        """
                    )

                # Use hardcoded values
                cro_review_days = 7
                wms_delay = 18
                mesqa_delay = 24
                log_roundtrip = 8
                log_rounds = 2

                sim_before = st.session_state.get("sim_before")
                if not sim_before:
                    sim_before = run_before(fixed_site, cro_review_days, wms_delay, mesqa_delay, log_roundtrip, log_rounds)
                    st.session_state.sim_before = sim_before

            st.markdown(
                """
                Scenario (Before: human coordination):
                A US site in the trial enrolls much faster than planned and risks running out of IMP. CTMS/IRT/EDC record this immediately, but Clinical Ops reacts based on weekly reports, workflow tickets, and email. The timeline below shows how long it takes to detect the risk and organize resupply in the current architecture.
                """
            )
            # Compact legend for channels
            from sim.models import CHANNEL_COLOR
            legend_items = [
                ("Email", CHANNEL_COLOR.get("email", "#d62728"), "ad-hoc communication"),
                ("Ticket", CHANNEL_COLOR.get("ticket", "#9467bd"), "workflow system (e.g., Jira/Service Desk)"),
                ("System", CHANNEL_COLOR.get("system", "#2ca02c"), "human dashboard/report check"),
                ("Manual", CHANNEL_COLOR.get("manual", "#7f7f7f"), "reading reports / making decisions"),
            ]
            legend_html = "".join([
                f"<span style='display:inline-block;margin-right:12px;'>"
                f"<span style='display:inline-block;width:10px;height:10px;background:{color};border-radius:2px;margin-right:6px;'></span>"
                f"<span style='font-size:12px;'>{label} – {desc}</span>"
                f"</span>" for (label, color, desc) in legend_items
            ])
            st.markdown(f"<div style='margin:6px 0 8px 0;'>{legend_html}</div>", unsafe_allow_html=True)

            # Add 2-view switcher for BEFORE visualizations
            before_view_tabs = st.tabs(["Inventory Chart", "Delays"])

            with before_view_tabs[0]:  # Inventory Chart
                st.subheader("Inventory Chart with Event Markers")
                st.caption("Visualizes inventory depletion and delays in response")
                df_b = sim_before.timeline_df()
                
                # Create two columns: inventory chart and metrics
                col_chart, col_metrics = st.columns([3, 1])
                
                with col_chart:
                    inventory_fig = create_inventory_chart(df_b, simulation_days=18)
                    st.plotly_chart(inventory_fig, use_container_width=True)
                    
                    # Add text legends below chart
                    st.markdown(
                        """
                        **Inventory Lines:** Site Inventory <span style="display:inline-block;width:10px;height:10px;background:#ff6b6b;border-radius:50%;margin:0 4px;"></span> | Depot Inventory <span style="display:inline-block;width:10px;height:10px;background:#4ecdc4;border-radius:50%;margin:0 4px;"></span>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Add legend for event markers
                    from sim.models import CHANNEL_COLOR
                    st.markdown("**Event Markers:**")
                    marker_legend = [
                        ("◆ Email", CHANNEL_COLOR.get("email", "#ef4444")),
                        ("■ Manual", CHANNEL_COLOR.get("manual", "#6b7280")),
                        ("● Ticket", CHANNEL_COLOR.get("ticket", "#8b5cf6")),
                        ("▲ System", CHANNEL_COLOR.get("system", "#10b981")),
                    ]
                    legend_html = " | ".join([
                        f"<span style='color:{color};'>{symbol}</span>" 
                        for symbol, color in marker_legend
                    ])
                    st.markdown(legend_html, unsafe_allow_html=True)
                
                with col_metrics:
                    st.markdown("#### Impact Metrics")
                    
                    # Calculate inventory-specific metrics
                    metrics = calculate_inventory_metrics(df_b)
                    
                    with st.container(border=True):
                        st.metric("Detection Delay", f"{metrics['detection_delay']:.1f} days", 
                                 help="Time from spike start to human detection")
                        st.metric("Total Response Time", f"{metrics['total_response_time']:.1f} days",
                                 help="Time from spike start to resupply")
                        
                        # Visual stockout indication based on chart data
                        st.markdown("---")
                        if metrics['total_response_time'] > 10:
                            st.error("STOCKOUT VISIBLE IN CHART")
                            st.caption("Site inventory hits zero around days 8-15")
                        elif metrics['total_response_time'] > 7:
                            st.warning("HIGH STOCKOUT RISK")
                
                # Add events table below the chart
                st.markdown("---")
                st.markdown("#### Communication Events & Delays")
                st.caption("Timeline of human coordination activities shown in the chart above")
                
                # Use the same table format as in the Delays tab
                tbl = format_before_table(df_b)
                if tbl is not None and not tbl.empty:
                    st.table(tbl)
                    
                    # Add summary of delays (simplified)
                    st.markdown("**Key Delays:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        email_count = len(df_b[df_b['channel'] == 'email'])
                        st.metric("Email Events", f"{email_count}")
                    with col2:
                        ticket_count = len(df_b[df_b['channel'] == 'ticket'])
                        st.metric("Ticket Events", f"{ticket_count}")
                    with col3:
                        manual_events = df_b[df_b['channel'] == 'manual']
                        if not manual_events.empty:
                            start_time = df_b['t'].min()
                            first_manual = manual_events['t'].min()
                            detection_delay = (first_manual - start_time).total_seconds() / (24 * 3600)
                            st.metric("Detection Delay", f"{detection_delay:.1f} days")
                        else:
                            st.metric("Detection Delay", "0.0 days")
                else:
                    st.info("No events yet. Adjust delays or select a site.")

            with before_view_tabs[1]:  # Delays
                st.subheader("Delay Timeline")
                st.caption("Shows who does what, when, and where delays occur")
                df_b = sim_before.timeline_df()
                
                # Create two columns: gantt chart and metrics
                col_gantt, col_metrics = st.columns([3, 1])
                
                with col_gantt:
                    gantt_fig = create_gantt_timeline(df_b)
                    st.plotly_chart(gantt_fig, use_container_width=True)
                
                with col_metrics:
                    st.markdown("#### Impact Metrics")
                    
                    # Calculate some basic metrics from the timeline
                    if df_b is not None and not df_b.empty:
                        start_time = df_b['t'].min()
                        end_time = df_b['t'].max()
                        total_duration = (end_time - start_time).total_seconds() / (24 * 3600)  # days
                        
                        # Detection delay (time to first manual review)
                        manual_events = df_b[df_b['channel'] == 'manual']
                        detection_delay = 0
                        if not manual_events.empty:
                            first_manual = manual_events['t'].min()
                            detection_delay = (first_manual - start_time).total_seconds() / (24 * 3600)
                        
                        # Count events by channel
                        email_count = len(df_b[df_b['channel'] == 'email'])
                        ticket_count = len(df_b[df_b['channel'] == 'ticket'])
                        
                        with st.container(border=True):
                            st.metric("Detection Delay", f"{detection_delay:.1f} days", 
                                     help="From spike start to human detection")
                            st.metric("Total Response Time", f"{total_duration:.1f} days",
                                     help="From spike start to shipment arrival")
                            st.metric("Email Events", f"{email_count}")
                            st.metric("Ticket Events", f"{ticket_count}")
                            
                            if total_duration > 10:
                                st.error("STOCKOUT RISK")
                            elif total_duration > 7:
                                st.warning("SUPPLY CRITICAL")
                    else:
                        st.info("Run simulation to see metrics")

                # Table with explicit columns
                tbl = format_before_table(df_b)
                if tbl is not None and not tbl.empty:
                    st.table(tbl)
                else:
                    st.info("No events yet. Adjust delays or select a site.")

                st.subheader("Metrics")
                with st.container(border=True):
                    render_metrics(sim_before.metrics)

    # -------------------------
    # AFTER (Agents)
    # -------------------------
    with after_tab:

            # Agent-Powered Optimization header (no background, no emoji)
            st.markdown("### Agent-Powered Optimization")
            st.markdown(
                """
                - Real-time enrollment monitoring via CRO Interface Agent (MCP)
                - Automated supply forecasting and coordination (A2A)
                - Optimized batch allocation minimizes waste
                - Sub-hour response time from enrollment signal to shipment planning
                - Predictive analytics prevent stockouts
                """
            )


            # Get or create simulation
            sim_after = st.session_state.get("sim_after")
            if not sim_after:
                # Lazy run once for preview
                sim_after = run_after(fixed_site)
                st.session_state.sim_after = sim_after

            # Add 2-view switcher for AFTER visualizations (same as BEFORE)
            after_view_tabs = st.tabs(["Inventory Chart", "Agent Communication"])

            with after_view_tabs[0]:  # Inventory Chart
                st.subheader("Optimized Inventory Management")
                st.caption("Shows how agents prevent stockouts through real-time coordination")
                
                # Create two columns: inventory performance and agent cards
                col_chart, col_agents = st.columns([3, 1])
                
                with col_chart:
                    # Create optimized inventory chart showing agent coordination
                    df_a = sim_after.timeline_df()
                    
                    # Create agent-optimized inventory chart
                    agent_inventory_fig = create_agent_inventory_chart(df_a, simulation_days=18)
                    st.plotly_chart(agent_inventory_fig, use_container_width=True)
                    
                    # Add text legends below chart
                    st.markdown(
                        """
                        **Inventory Lines:** Site Inventory <span style="display:inline-block;width:10px;height:10px;background:#8b5cf6;border-radius:50%;margin:0 4px;"></span> | Depot Inventory <span style="display:inline-block;width:10px;height:10px;background:#f59e0b;border-radius:50%;margin:0 4px;"></span>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Add legend for agent events
                    from sim.models import CHANNEL_COLOR
                    st.markdown("**Agent Events:**")
                    agent_legend = [
                        ("◆ MCP", CHANNEL_COLOR.get("mcp", "#3b82f6")),
                        ("● A2A", CHANNEL_COLOR.get("a2a", "#f59e0b")),
                        ("■ System", CHANNEL_COLOR.get("system", "#10b981")),
                    ]
                    legend_html = " | ".join([
                        f"<span style='color:{color};'>{symbol}</span>" 
                        for symbol, color in agent_legend
                    ])
                    st.markdown(legend_html, unsafe_allow_html=True)
                    
                    # Add detailed agent activity timeline
                    st.markdown("---")
                    st.markdown("#### Agent Activity Timeline")
                    with st.container(border=True):
                        st.markdown("**Day 0 - Emergency Response (All Agents Active):**")
                        st.markdown(
                            """
                            • **CRO Interface Agent:** Detects 15+ patient enrollment spike at Mass General Brigham  
                            • **Clinical Ops Agent:** Triggers emergency alert and calculates 50-unit resupply need  
                            • **MES Agent:** Queries batch system, validates quality, allocates optimal batches  
                            • **Logistics Agent:** Coordinates expedited cold-chain shipment with 48h delivery
                            """
                        )
                        
                        st.markdown("**Days 1-3 - Continuous Monitoring:**")
                        st.markdown(
                            """
                            • **CRO Interface Agent:** Daily enrollment pattern monitoring  
                            • **Clinical Ops Agent:** Consumption analysis and forecast model updates
                            """
                        )
                        
                        st.markdown("**Days 4-8 - Dynamic Optimization:**")
                        st.markdown(
                            """
                            • **Logistics Agent:** First emergency shipment delivered (Day 4)  
                            • **Clinical Ops Agent:** Trend stabilization analysis (Day 5)  
                            • **MES Agent:** Proactive second shipment coordination (Day 7-8)
                            """
                        )
                        
                        st.markdown("**Days 10-17 - Predictive Management:**")
                        st.markdown(
                            """
                            • **Clinical Ops Agent:** Weekly consumption reviews and safety stock adjustments  
                            • **MES Agent:** Predictive restocking with automated batch selection  
                            • **All Agents:** Steady-state monitoring to maintain optimal inventory levels
                            """
                        )
                        
                        st.markdown("---")
                        st.caption(
                            "Unlike manual processes that react to weekly reports, these agents coordinate in real-time "
                            "to prevent stockouts through continuous monitoring and predictive actions."
                        )
                
                with col_agents:
                    st.markdown("#### Active Agents")
                    
                    # Compact agent list
                    with st.container(border=True):
                        st.markdown("**CRO Interface Agent**")
                        st.caption("Patient Enrollment Interface")
                        
                        st.markdown("**Clinical Ops Agent**")
                        st.caption("Supply Planning")
                        
                        st.markdown("**MES Agent**")
                        st.caption("Manufacturing Execution")
                        
                        st.markdown("**Logistics Agent**")
                        st.caption("Distribution Management")

            with after_view_tabs[1]:  # Agent Communication
                st.subheader("Agent Communication & Interoperability")
                st.caption("Shows real-time coordination between autonomous agents")
                
                # Create two columns: timeline and agent details
                col_timeline, col_details = st.columns([3, 1])
                
                with col_timeline:
                    # Interactive communication flow
                    create_agent_comm_flow(sim_after.timeline_df())
                
                with col_details:
                    st.markdown("#### Agent Details")
                    
                    # Expandable agent cards
                    with st.expander("CRO Interface Agent", expanded=True):
                        st.markdown(
                            """
                            **Role:** Patient Enrollment Interface  
                            **Monitors:** Patient enrollment data from CROs  
                            **Triggers:** Supply forecasts when enrollment spikes detected
                            """
                        )
                    
                    with st.expander("Clinical Ops Agent"):
                        st.markdown(
                            """
                            **Role:** Supply Planning  
                            **Coordinates:** Supply planning based on enrollment forecasts  
                            **Manages:** Site demand predictions and inventory allocation
                            """
                        )
                    
                    with st.expander("MES Agent"):
                        st.markdown(
                            """
                            **Role:** Manufacturing Execution  
                            **Manages:** Batch inventory, expiry tracking  
                            **Coordinates:** Depot inventory and batch allocation
                            """
                        )
                    
                    with st.expander("Logistics Agent"):
                        st.markdown(
                            """
                            **Role:** Distribution Management  
                            **Optimizes:** Shipments from depot to sites  
                            **Uses:** Optimized allocation and demand forecasting
                            """
                        )



if __name__ == "__main__":
    main()
