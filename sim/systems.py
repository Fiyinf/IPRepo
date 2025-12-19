import random
from datetime import datetime, timedelta
from typing import List, Dict

from .bus import MessageBus, TimelineEvent
from .models import BatchInfo, DepotInventory, EnrollmentData, PROTOCOL_MCP, US_SITES


class MockSystems:
    def __init__(self, study_id: str, seed: int = 42):
        random.seed(seed)
        self.study_id = study_id
        self.depot_id = "US-DEPOT-1"
        self.country = "United States"
        # Pre-generate mock batches with staggered expiries
        today = datetime.utcnow().date()
        self.batches: List[BatchInfo] = []
        for i in range(10):
            mfg = datetime.combine(today - timedelta(days=60 + i * 7), datetime.min.time())
            expiry = mfg + timedelta(days=180 + i * 10)
            units = random.randint(80, 200)
            self.batches.append(
                BatchInfo(
                    batch_id=f"BATCH-{i+1:03d}",
                    manufacture_date=mfg,
                    expiry_date=expiry,
                    available_units=units,
                )
            )

    # CTMS via MCP
    def get_trial_sites(self, bus: MessageBus):
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="CRO Interface Agent",
                target="CTMS",
                action="get_trial_sites",
                details=f"Returned {len(US_SITES)} US sites",
            )
        )
        return US_SITES

    def get_enrollment_data(self, bus: MessageBus, study_id: str, site_id: str, days: int = 90) -> EnrollmentData:
        base = [max(0, int(1 + i / 10 + random.random() * 1.5)) for i in range(days)]
        cumulative = []
        total = 0
        for b in base:
            total += b
            cumulative.append(total)
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="CRO Interface Agent",
                target="CTMS",
                action="get_enrollment_data",
                details=f"{site_id} {days}-day forecast generated",
            )
        )
        return EnrollmentData(study_id=study_id, site_id=site_id, forecast_daily=base, cumulative=cumulative)

    # LIMS via MCP
    def get_batch_stability(self, bus: MessageBus) -> List[BatchInfo]:
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="MES Agent",
                target="LIMS",
                action="get_batch_stability",
                details=f"Fetched {len(self.batches)} batches",
            )
        )
        return self.batches

    def check_batch_expiry(self, bus: MessageBus, batch_id: str, on_date: datetime) -> bool:
        batch = next((b for b in self.batches if b.batch_id == batch_id), None)
        valid = bool(batch and batch.expiry_date > on_date)
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="MES Agent",
                target="LIMS",
                action="check_batch_expiry",
                details=f"{batch_id} valid_on {on_date.date()} -> {valid}",
            )
        )
        return valid

    # WMS via MCP
    def get_depot_inventory(self, bus: MessageBus) -> DepotInventory:
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="Logistics Agent",
                target="WMS",
                action="get_depot_inventory",
                details=f"Depot {self.depot_id} with {len(self.batches)} batches",
            )
        )
        return DepotInventory(depot_id=self.depot_id, country=self.country, batches=self.batches)

    def check_compliance_rules(self, bus: MessageBus, site_id: str) -> Dict[str, str]:
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="Logistics Agent",
                target="Compliance",
                action="check_compliance_rules",
                details=f"Checked rules for {site_id}",
            )
        )
        return {"temperature": "2-8C", "serialization": "DSCSA", "country": "US"}

    # ERP via MCP
    def get_erp_inventory(self, bus: MessageBus) -> Dict[str, int]:
        total_units = sum(b.available_units for b in self.batches)
        bus.log(
            TimelineEvent(
                t=datetime.utcnow(),
                protocol=PROTOCOL_MCP,
                channel="mcp",
                actor="Clinical Ops Agent",
                target="ERP",
                action="get_erp_inventory",
                details=f"Total units available: {total_units}",
            )
        )
        return {"total_units": total_units, "batch_count": len(self.batches)}
