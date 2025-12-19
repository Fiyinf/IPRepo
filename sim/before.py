from datetime import datetime, timedelta
from typing import Dict

import pandas as pd

from .bus import MessageBus, TimelineEvent
from .models import CHANNEL_EMAIL, CHANNEL_MANUAL, CHANNEL_TICKET, CHANNEL_SYSTEM
from .systems import MockSystems


class BeforeSimulation:
    """Human-driven process using email and meetings (no agents)."""

    def __init__(self, seed: int = 42):
        self.study_id = "STUDY-ALPHA"
        self.bus = MessageBus()
        self.systems = MockSystems(self.study_id, seed=seed)
        self.metrics = {
            "order_to_delivery_days": 0.0,
            "shipment_cost": 0.0,
            "compliance_events": 0.0,
            "forecast_accuracy": 0.0,
            "latency_hours": 0.0,
        }
        self.now = datetime.utcnow()

    def _advance(self, hours: float):
        self.now += timedelta(hours=hours)
        self.metrics["latency_hours"] += hours

    def activate_new_site(
        self,
        site: Dict[str, str],
        cro_review_delay_hours: float = 24.0 * 7,  # weekly review cadence (manual review)
        wms_email_delay_hours: float = 18.0,       # repurposed as WMS ticket queue delay (hours)
        mesqa_email_delay_hours: float = 24.0,     # repurposed as MES/QA ticket queue delay (hours)
        logistics_roundtrip_hours: float = 8.0,    # per negotiation step for ticket turnaround
        logistics_rounds: int = 2,                 # request -> quote -> confirm
        email_delay_hours: float = 8.0,            # generic email clarification delay
        ticket_queue_delay_hours: float | None = None,  # default uses per-team values above
        system_lookup_delay_hours: float = 0.5,    # quick dashboard/report lookup
    ) -> None:
        # CRO sends weekly enrollment report via email (with Excel attachment)
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_EMAIL,
                actor="CRO (Human)",
                target="Clinical Ops (Human)",
                action="Email sent: Weekly enrollment report",
                details=f"Excel attachment for {site['site_id']}",
            )
        )
        # Clinical Ops reviews weekly (issues may be detected late)
        self._advance(cro_review_delay_hours)
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel="manual",
                actor="Clinical Ops (Human)",
                target="Clinical Ops (Human)",
                action="Report reviewed: Enrollment report",
                details="Potential supply risk flagged",
            )
        )

        # Clinical Ops creates a supply request ticket to Depot/WMS
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_TICKET,
                actor="Clinical Ops (Human)",
                target="Depot/WMS (Human)",
                action="Ticket opened: Inventory check request",
                details=f"Initial stocking for site {site['site_id']} (Clinical Supply queue)",
            )
        )
        # Queue delay until Depot/WMS picks up the ticket
        _wms_queue = ticket_queue_delay_hours if ticket_queue_delay_hours is not None else wms_email_delay_hours
        self._advance(_wms_queue)
        # WMS performs system lookup (dashboard/report)
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_SYSTEM,
                actor="Depot/WMS (Human)",
                target="Depot/WMS (Human)",
                action="System lookup: ERP/WMS inventory",
                details="Checked depot inventory dashboard",
            )
        )
        self._advance(system_lookup_delay_hours)
        total_units = sum(b.available_units for b in self.systems.batches)
        # Post the result back into the ticket
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_TICKET,
                actor="Depot/WMS (Human)",
                target="Clinical Ops (Human)",
                action="Ticket update: Inventory status",
                details=f"Total units at depot: {total_units}",
            )
        )

        # Clinical Ops opens a MES/QA ticket re: release/expiry
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_TICKET,
                actor="Clinical Ops (Human)",
                target="MES/QA (Human)",
                action="Ticket opened: Release/expiry inquiry",
                details="Which lots are releasable in next 3 days?",
            )
        )
        # Queue delay until MES/QA picks up
        _mes_queue = ticket_queue_delay_hours if ticket_queue_delay_hours is not None else mesqa_email_delay_hours
        self._advance(_mes_queue)
        # MES/QA does LIMS/QMS lookup
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_SYSTEM,
                actor="MES/QA (Human)",
                target="MES/QA (Human)",
                action="System lookup: LIMS/QMS release status",
                details="Checked batch release/expiry in LIMS/QMS",
            )
        )
        self._advance(system_lookup_delay_hours)
        self.bus.log(
            TimelineEvent(
                t=self.now,
                channel=CHANNEL_TICKET,
                actor="MES/QA (Human)",
                target="Clinical Ops (Human)",
                action="Ticket update: Release/expiry list",
                details="Provided list of non-expired lots",
            )
        )

        # Logistics/TMS negotiation primarily via tickets
        optional_email_done = False
        for i in range(logistics_rounds):
            self.bus.log(
                TimelineEvent(
                    t=self.now,
                    channel=CHANNEL_TICKET,
                    actor="Clinical Ops (Human)",
                    target="Logistics/TMS (Human)",
                    action=("Ticket opened: Urgent shipment request" if i == 0 else "Ticket update: Follow-up / confirmation"),
                    details=f"Negotiation round {i+1}",
                )
            )
            self._advance(logistics_roundtrip_hours)
            self.bus.log(
                TimelineEvent(
                    t=self.now,
                    channel=CHANNEL_TICKET,
                    actor="Logistics/TMS (Human)",
                    target="Clinical Ops (Human)",
                    action="Ticket update: Quote / ETA",
                    details=f"Proposed plan after {i+1} round(s)",
                )
            )
            # Optional email clarification after first round
            if not optional_email_done and email_delay_hours > 0:
                optional_email_done = True
                self.bus.log(
                    TimelineEvent(
                        t=self.now,
                        channel=CHANNEL_EMAIL,
                        actor="Clinical Ops (Human)",
                        target="Logistics/TMS (Human)",
                        action="Email sent: Clarification on ticket",
                        details="Clarifying cold-chain requirements",
                    )
                )
                self._advance(email_delay_hours)
                self.bus.log(
                    TimelineEvent(
                        t=self.now,
                        channel=CHANNEL_EMAIL,
                        actor="Logistics/TMS (Human)",
                        target="Clinical Ops (Human)",
                        action="Email reply: Clarification received",
                        details="Confirmed handling instructions",
                    )
                )

        # Simple metrics approximation (BEFORE has high latency -> longer order-to-delivery)
        self.metrics["order_to_delivery_days"] = self.metrics["latency_hours"] / 24.0 + 1.0
        self.metrics["shipment_cost"] = 500 + 120 * 2 + (200 if logistics_rounds > 2 else 0)
        self.metrics["compliance_events"] = 0
        self.metrics["forecast_accuracy"] = 0.8

    def timeline_df(self) -> pd.DataFrame:
        return self.bus.to_dataframe()
