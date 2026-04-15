from cluster.serializer.serializer import Serializer
from cluster.common.event import Event
from cluster.common.event_type import EventType

def test_serializer():
    serializer = Serializer()
    event = Event(
        type=EventType.TASK_REQUEST,
        node_id="worker#1",
        address="127.0.0.1:5001",
        payload={"x":10}
    )
    serialized_event = serializer.serialize(event)
    deserialized_event = serializer.deserialize(serialized_event)
    assert deserialized_event == event