from datetime import datetime
from typing import Optional, List, Literal

import pandas as pd
from pydantic import BaseModel

from .models import PROTOCOL_MCP, PROTOCOL_A2A


class TimelineEvent(BaseModel):
    t: datetime
    # protocol is kept for AFTER mode visuals; may be omitted for email flows
    protocol: Optional[Literal[PROTOCOL_MCP, PROTOCOL_A2A]] = None
    # channel is used for coloring: mcp, a2a, email
    channel: str
    actor: str
    target: Optional[str] = None
    action: str
    details: str


class MessageBus:
    def __init__(self):
        self.events: List[TimelineEvent] = []

    def log(self, event: TimelineEvent):
        self.events.append(event)

    def to_dataframe(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=["t", "protocol", "channel", "actor", "target", "action", "details"])
        return pd.DataFrame([e.model_dump() for e in self.events])
