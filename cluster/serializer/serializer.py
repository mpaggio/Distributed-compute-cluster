from common.event import Event
from common.event_type import EventType
import json

class Serializer:
    def serialize(self, event: Event) -> str:
        event_dict = {
            "type": event.type.name,
            "node_id": event.node_id,
            "address": event.address,
            "payload": event.payload,
        }
        return json.dumps(event_dict)
    
    def deserialize(self, json_str: str) -> Event:
        event_dict: dict = json.loads(json_str)
        return Event(
            type = EventType[event_dict["type"]], 
            node_id = event_dict["node_id"], 
            address = event_dict["address"], 
            payload = event_dict["payload"]
        )