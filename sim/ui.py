from datetime import datetime
from typing import Dict

import plotly.express as px
import streamlit as st

from .agents import BaseAgent
from .models import PROTOCOL_COLOR, CHANNEL_COLOR
from .diagram import comms_diagram


def protocol_badge(protocol: str) -> str:
    color = PROTOCOL_COLOR.get(protocol, "#999999")
    return f"<span style='background:{color};color:white;padding:2px 6px;border-radius:6px;font-size:11px;'>{protocol}</span>"


def render_agent_card(agent: BaseAgent):
    with st.container(border=True):
        st.subheader(agent.name)
        if agent.name == "Logistics Agent":
            inv = agent.systems.get_depot_inventory(agent.bus)
            total_units = sum(b.available_units for b in inv.batches)
            soon_expiring = sum(1 for b in inv.batches if (b.expiry_date - datetime.utcnow()).days < 45)
            st.metric("Depot Units", f"{total_units}")
            st.metric("Batches", f"{len(inv.batches)}")
            st.metric("Expiring <45d", f"{soon_expiring}")
        if agent.name == "Clinical Ops Agent":
            st.write("Pending/Decisions:")
            if not agent.state.pending_orders:
                st.caption("None")
            else:
                for o in agent.state.pending_orders[-5:]:
                    st.json(o, expanded=False)
            st.write("Active Shipments:")
            if not agent.state.active_shipments:
                st.caption("None")
            else:
                for srec in agent.state.active_shipments[-5:]:
                    st.json(srec, expanded=False)
        if agent.name == "MES Agent":
            batches = agent.systems.get_batch_stability(agent.bus)
            soon_exp = sorted(batches, key=lambda b: b.expiry_date)[:3]
            for b in soon_exp:
                st.caption(f"{b.batch_id}: exp {b.expiry_date.date()} units {b.available_units}")
        if agent.name == "CRO Interface Agent":
            sites = agent.systems.get_trial_sites(agent.bus)
            st.caption(", ".join([s["site_id"] for s in sites]))


def render_timeline(df):
    if df.empty:
        st.info("No events yet. Trigger a scenario to see the timeline.")
        return
    df_sorted = df.sort_values("t")
    df_sorted["time_str"] = df_sorted["t"].dt.strftime("%H:%M:%S")
    color_key = "channel" if "channel" in df_sorted.columns else "protocol"
    cmap = CHANNEL_COLOR if color_key == "channel" else PROTOCOL_COLOR
    fig = px.scatter(
        df_sorted,
        x="t",
        y="actor",
        color=color_key,
        color_discrete_map=cmap,
        symbol=color_key,
        hover_data={"action": True, "details": True, "target": True, "t": True},
    )
    fig.update_traces(marker=dict(size=10))
    fig.update_layout(height=400, legend_title_text="Protocol")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Event Log"):
        cols = ["t", "channel", "protocol", "actor", "target", "action", "details"]
        cols = [c for c in cols if c in df_sorted.columns]
        show = df_sorted[cols]
        st.dataframe(show, use_container_width=True)


def render_metrics(metrics: Dict[str, float]):
    cols = st.columns(4)
    cols[0].metric("Order-to-Delivery (days)", f"{metrics.get('order_to_delivery_days', 0):.1f}")
    cols[1].metric("Shipment Cost ($)", f"{metrics.get('shipment_cost', 0):,.0f}")
    cols[2].metric("Compliance Events", f"{metrics.get('compliance_events', 0):.0f}")
    cols[3].metric("Forecast Accuracy", f"{metrics.get('forecast_accuracy', 0)*100:.0f}%")
