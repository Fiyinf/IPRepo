from datetime import datetime, timedelta
from typing import Dict

import pandas as pd

from .agents import CROInterfaceAgent, ClinicalOpsAgent, MESAgent, LogisticsAgent
from .bus import MessageBus
from .models import SiteActivatedEvent


class Simulation:
    def __init__(self, seed: int = 42):
        self.study_id = "STUDY-ALPHA"
        self.bus = MessageBus()
        self.cro_systems_seed = seed
        from .systems import MockSystems
        self.systems = MockSystems(self.study_id, seed=seed)
        self.cro = CROInterfaceAgent("CRO Interface Agent", self.bus, self.systems)
        self.clinops = ClinicalOpsAgent("Clinical Ops Agent", self.bus, self.systems)
        self.mes = MESAgent("MES Agent", self.bus, self.systems)
        self.logistics = LogisticsAgent("Logistics Agent", self.bus, self.systems)
        self.metrics: Dict[str, float] = {
            "order_to_delivery_days": 0.0,
            "shipment_cost": 0.0,
            "compliance_events": 0.0,
            "forecast_accuracy": 0.0,
        }

    def activate_new_site(self, site: Dict[str, str]) -> None:
        _sites = self.cro.get_sites()
        _enroll90 = self.cro.get_site_enrollment(self.study_id, site["site_id"], days=90)

        event = SiteActivatedEvent(study_id=self.study_id, site_id=site["site_id"], activation_date=datetime.utcnow())
        self.clinops.receive_site_activated(event)

        _erp = self.clinops.query_erp_inventory()
        initial_qty = 50
        alloc_req = self.clinops.send_allocate_request(self.study_id, site["site_id"], initial_qty)

        alloc_resp = self.mes.allocate_lots(alloc_req)
        self.clinops.receive_allocate_response(alloc_resp)

        target_delivery = datetime.utcnow() + timedelta(days=3)
        ship_req = self.clinops.send_create_shipment(site["site_id"], alloc_resp.batch_ids, target_delivery)

        plan = self.logistics.plan_shipment(ship_req)
        self.clinops.receive_shipment_plan(plan)

        self.metrics["order_to_delivery_days"] = (plan.eta - event.activation_date).days
        self.metrics["shipment_cost"] = plan.cost
        self.metrics["compliance_events"] = 0

        enroll7 = self.cro.get_site_enrollment(self.study_id, site["site_id"], days=7)
        forecast_total = sum(enroll7.forecast_daily)
        actual_supply = 50
        self.metrics["forecast_accuracy"] = min(1.0, actual_supply / forecast_total) if forecast_total > 0 else 1.0

    def timeline_df(self) -> pd.DataFrame:
        return self.bus.to_dataframe()
