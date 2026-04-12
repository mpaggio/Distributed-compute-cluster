from dataclasses import dataclass
from cluster.common import EventType

@dataclass(frozen=True)
class Event:
    type: EventType
    node_id: str
    address: str
    payload: dict