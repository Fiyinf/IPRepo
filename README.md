# Clinical-Trial Supply-Chain: MCP vs A2A Simulation (Streamlit)

A self-contained Streamlit simulation that demonstrates how MCP (Model Context Protocol) direct system queries and A2A (agent-to-agent) coordination work together across a clinical-trial supply chain.

Run locally with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, if you use a virtual environment:

```powershell
cd "c:\Users\leave\Documents\HBS Semester 3\IP\Pharma Code"
py -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
streamlit run app.py
```

## What you’ll see
- Four agents with state and decision logic
  - CRO Interface Agent
  - Clinical Ops Agent
  - MES Agent
  - Logistics Agent
- Mixed protocols:
  - MCP (blue): direct queries to mock systems (CTMS, LIMS, WMS, ERP)
  - A2A (orange): structured messages between agents (allocation, shipping)
- UI elements:
  - Agent state cards (inventory, pending decisions, shipments)
  - Message timeline (color-coded by protocol)
  - Metrics (order-to-delivery, cost, compliance, forecast accuracy)
  - Sidebar to trigger scenario (Activate New Site)

## Project structure
```
.
├─ app.py                    # Streamlit entry point and page wiring
├─ requirements.txt          # Dependencies
└─ sim/
   ├─ __init__.py
   ├─ models.py              # Pydantic models, constants, site fixtures
   ├─ bus.py                 # Timeline event model and message bus
   ├─ systems.py             # Mock MCP tools: CTMS, LIMS, WMS, ERP
   ├─ agents.py              # CRO, Clinical Ops, MES, Logistics agents
   ├─ sim.py                 # Simulation orchestrator
   └─ ui.py                  # UI helpers (cards, timeline, metrics)
```

## Protocols in this simulation
- MCP (Model Context Protocol): direct calls to systems; no agent-to-agent coordination.
  - Examples:
    - CRO → CTMS: `get_trial_sites()`, `get_enrollment_data()`
    - MES → LIMS: `get_batch_stability()`, `check_batch_expiry()`
    - Logistics → WMS/Compliance: `get_depot_inventory()`, `check_compliance_rules()`
- A2A (Agent-to-Agent): structured messages between agents.
  - Examples:
    - Clinical Ops → MES: `AllocateLotRequest { study_id, site_id, quantity }`
    - MES → Clinical Ops: `AllocateLotResponse { batch_ids, release_date, constraints }`
    - Clinical Ops → Logistics: `CreateShipmentRequest { site_id, batch_ids, target_delivery_date }`
    - Logistics → Clinical Ops: `ShipmentPlan { shipment_id, departure_date, eta, cost }`

## Data models
Defined in `sim/models.py` (Pydantic):
- A2A messages: `SiteActivatedEvent`, `AllocateLotRequest`, `AllocateLotResponse`, `CreateShipmentRequest`, `ShipmentPlan`
- MCP tool results: `EnrollmentData`, `BatchInfo`, `DepotInventory`

## Simulation flow (high level)
1. CRO (MCP): Queries CTMS for trial sites and enrollment forecast (90-day ramp).
2. Clinical Ops (A2A + MCP): Receives site activation event; queries ERP for inventory; sends lot allocation request to MES.
3. MES (A2A + MCP): Checks LIMS stability/expiry; allocates via FEFO; responds with allocation and release date.
4. Logistics (A2A + MCP): Queries WMS and compliance; returns a shipment plan with ETA and cost.

## Metrics
- Order-to-delivery (days): ETA minus activation time
- Shipment cost: Base + per-batch + expedite if target delivery <= 2 days
- Compliance events: Mocked as 0 when rules exist
- Forecast accuracy: 7-day enrollment forecast vs initial supply (simple proxy)

## Customization ideas
- Allocation policy options (FEFO/FIFO), safety stock, or per-site initial quantities
- Multiple site activations, delays, temperature excursions, or compliance violations
- Unit-level tracking and deduction in Logistics
- Step-by-step timeline replay and per-site dashboards

## Troubleshooting
- If `streamlit` is not found, ensure your virtual environment is activated.
- If port 8501 is busy, Streamlit will choose a new port; check the terminal output.
- To stop the server: press Ctrl+C in the terminal.

## License
This demo is provided for educational purposes; adapt freely for your internal projects.
