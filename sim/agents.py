from datetime import datetime, timedelta
from typing import Dict, List
import uuid

from pydantic import BaseModel, Field

from .bus import MessageBus, TimelineEvent
from .models import (
    PROTOCOL_A2A,
    AllocateLotRequest,
    AllocateLotResponse,
    BatchInfo,
    CreateShipmentRequest,
    ShipmentPlan,
    SiteActivatedEvent,
)


class AgentState(BaseModel):
    name: str
    inventory: Dict[str, int] = Field(default_factory=dict)
    pending_orders: List[Dict] = Field(default_factory=list)
    active_shipments: List[Dict] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)


class BaseAgent:
    def __init__(self, name: str, bus: MessageBus, systems):
        self.name = name
        self.bus = bus
        self.systems = systems
        self.state = AgentState(name=name)


class CROInterfaceAgent(BaseAgent):
    def get_sites(self):
        return self.systems.get_trial_sites(self.bus)

    def get_site_enrollment(self, study_id: str, site_id: str, days: int = 90):
        return self.systems.get_enrollment_data(self.bus, study_id, site_id, days)


class ClinicalOpsAgent(BaseAgent):
    def receive_site_activated(self, event: SiteActivatedEvent) -> None:
        self.state.pending_orders.append({
            "type": "SiteActivated",
            "site_id": event.site_id,
            "activation_date": event.activation_date,
        })
        self.bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_A2A,
                channel="a2a",
                actor="CRO Interface Agent",
                target="Clinical Ops Agent",
                action="SiteActivatedEvent",
                details=f"Site {event.site_id} activated",
            )
        )

    def query_erp_inventory(self):
        return self.systems.get_erp_inventory(self.bus)

    def send_allocate_request(self, study_id: str, site_id: str, quantity: int) -> AllocateLotRequest:
        req = AllocateLotRequest(study_id=study_id, site_id=site_id, quantity=quantity)
        self.bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_A2A,
                channel="a2a",
                actor="Clinical Ops Agent",
                target="MES Agent",
                action="AllocateLotRequest",
                details=f"site={site_id}, qty={quantity}",
            )
        )
        return req

    def receive_allocate_response(self, resp: AllocateLotResponse) -> None:
        self.state.pending_orders.append({
            "type": "Allocation",
            "batch_ids": resp.batch_ids,
            "release_date": resp.release_date,
            "constraints": resp.constraints,
        })
        self.bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_A2A,
                channel="a2a",
                actor="MES Agent",
                target="Clinical Ops Agent",
                action="AllocateLotResponse",
                details=f"batches={','.join(resp.batch_ids)} release={resp.release_date.date()}",
            )
        )

    def send_create_shipment(self, site_id: str, batch_ids: List[str], target_delivery_date: datetime) -> CreateShipmentRequest:
        req = CreateShipmentRequest(site_id=site_id, batch_ids=batch_ids, target_delivery_date=target_delivery_date)
        self.bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_A2A,
                channel="a2a",
                actor="Clinical Ops Agent",
                target="Logistics Agent",
                action="CreateShipmentRequest",
                details=f"site={site_id}, batches={','.join(batch_ids)}",
            )
        )
        return req

    def receive_shipment_plan(self, plan: ShipmentPlan) -> None:
        self.state.active_shipments.append({
            "shipment_id": plan.shipment_id,
            "eta": plan.eta,
            "cost": plan.cost,
        })
        self.bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_A2A,
                channel="a2a",
                actor="Logistics Agent",
                target="Clinical Ops Agent",
                action="ShipmentPlan",
                details=f"shipment={plan.shipment_id} eta={plan.eta.date()} cost=${plan.cost:,.0f}",
            )
        )


class MESAgent(BaseAgent):
    def allocate_lots(self, req: AllocateLotRequest) -> AllocateLotResponse:
        all_batches: List[BatchInfo] = self.systems.get_batch_stability(self.bus)
        release_date = datetime.utcnow() + timedelta(days=3)
        valid_batches = [
            b for b in all_batches if self.systems.check_batch_expiry(self.bus, b.batch_id, release_date)
        ]
        valid_batches.sort(key=lambda b: b.expiry_date)

        selected: List[str] = []
        qty_remaining = req.quantity
        constraints: List[str] = []
        for b in valid_batches:
            if qty_remaining <= 0:
                break
            take = min(qty_remaining, b.available_units)
            if take > 0:
                selected.append(b.batch_id)
                b.available_units -= take
                qty_remaining -= take
        if qty_remaining > 0:
            constraints.append(f"Short {qty_remaining} units; partial allocation")

        resp = AllocateLotResponse(
            request_id=req.message_id,
            batch_ids=selected,
            release_date=release_date,
            constraints=constraints,
        )
        return resp


class LogisticsAgent(BaseAgent):
    def plan_shipment(self, req: CreateShipmentRequest) -> ShipmentPlan:
        _inv = self.systems.get_depot_inventory(self.bus)
        _rules = self.systems.check_compliance_rules(self.bus, req.site_id)
        today = datetime.utcnow()
        lead_days = max(1, (req.target_delivery_date.date() - today.date()).days)
        base_cost = 500
        per_batch = 120 * len(req.batch_ids)
        expedite = 400 if lead_days <= 2 else 0
        cost = base_cost + per_batch + expedite
        departure = today + timedelta(days=1)
        eta = today + timedelta(days=2 if expedite == 0 else 1)

        self.state.active_shipments.append({
            "site_id": req.site_id,
            "batches": req.batch_ids,
            "eta": eta,
            "cost": cost,
        })

        plan = ShipmentPlan(
            request_id=req.message_id,
            shipment_id=str(uuid.uuid4())[:8],
            departure_date=departure,
            eta=eta,
            cost=cost,
        )
        return plan
