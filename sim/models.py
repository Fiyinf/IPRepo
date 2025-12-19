import uuid
from datetime import datetime
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

# Protocol constants
PROTOCOL_MCP = "MCP"
PROTOCOL_A2A = "A2A"

# Colors retained for protocol (backward-compat)
PROTOCOL_COLOR = {
    PROTOCOL_MCP: "#1f77b4",  # blue
    PROTOCOL_A2A: "#ff7f0e",  # orange
}

# Channels for timeline visualization
CHANNEL_MCP = "mcp"
CHANNEL_A2A = "a2a"
CHANNEL_EMAIL = "email"
CHANNEL_MANUAL = "manual"
CHANNEL_TICKET = "ticket"
CHANNEL_SYSTEM = "system"

CHANNEL_COLOR = {
    CHANNEL_MCP: "#06b6d4",     # Cyan (system-to-system)
    CHANNEL_A2A: "#10b981",     # Green (agent-to-agent)
    CHANNEL_EMAIL: "#ef4444",   # Modern red (email)
    CHANNEL_MANUAL: "#6b7280",  # Modern gray (manual decision/review)
    CHANNEL_TICKET: "#8b5cf6",  # Modern violet (workflow ticketing)
    CHANNEL_SYSTEM: "#3b82f6",  # Blue (human dashboard/report lookup)
}

# Site fixtures (US only)
US_SITES = [
    {"site_id": "US-001", "name": "Cleveland Clinic"},
    {"site_id": "US-002", "name": "Mayo Clinic"},
    {"site_id": "US-003", "name": "Mass General"},
    {"site_id": "US-004", "name": "UCSF"},
    {"site_id": "US-005", "name": "MD Anderson"},
]

# ------------------------------
# A2A message models
# ------------------------------

class SiteActivatedEvent(BaseModel):
    protocol: Literal[PROTOCOL_A2A] = PROTOCOL_A2A
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    study_id: str
    site_id: str
    activation_date: datetime


class AllocateLotRequest(BaseModel):
    protocol: Literal[PROTOCOL_A2A] = PROTOCOL_A2A
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    study_id: str
    site_id: str
    quantity: int


class AllocateLotResponse(BaseModel):
    protocol: Literal[PROTOCOL_A2A] = PROTOCOL_A2A
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    batch_ids: List[str]
    release_date: datetime
    constraints: List[str] = []


class CreateShipmentRequest(BaseModel):
    protocol: Literal[PROTOCOL_A2A] = PROTOCOL_A2A
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    site_id: str
    batch_ids: List[str]
    target_delivery_date: datetime


class ShipmentPlan(BaseModel):
    protocol: Literal[PROTOCOL_A2A] = PROTOCOL_A2A
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    shipment_id: str
    departure_date: datetime
    eta: datetime
    cost: float


# ------------------------------
# MCP tool result models (mock data structures)
# ------------------------------

class EnrollmentData(BaseModel):
    study_id: str
    site_id: str
    forecast_daily: List[int]
    cumulative: List[int]


class BatchInfo(BaseModel):
    batch_id: str
    manufacture_date: datetime
    expiry_date: datetime
    available_units: int


class DepotInventory(BaseModel):
    depot_id: str
    country: str
    batches: List[BatchInfo]
