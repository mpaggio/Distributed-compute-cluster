import pytest
import json
from cluster.serializer.serializer import Serializer
from cluster.common.event import Event
from cluster.common.event_type import EventType

@pytest.fixture
def serializer():
    return Serializer()

def test_serializer_serialization_output(serializer):
    event = Event(
        type=EventType.TASK_REQUEST,
        node_id="worker#1",
        address="127.0.0.1:5001",
        payload={}
    )
    serialized_event = serializer.serialize(event)
    assert isinstance(serialized_event, str)
    assert "TASK_REQUEST" in serialized_event
    assert "worker#1" in serialized_event
    assert "127.0.0.1:5001" in serialized_event

def test_serializer_with_simple_payload(serializer):
    event = Event(
        type=EventType.TASK_REQUEST,
        node_id="worker#1",
        address="127.0.0.1:5001",
        payload={}
    )
    serialized_event = serializer.serialize(event)
    deserialized_event = serializer.deserialize(serialized_event)
    assert deserialized_event == event

def test_serializer_with_complex_payload(serializer):
    event = Event(
        type=EventType.TASK_ASSIGN,
        node_id="coordinator#1",
        address="127.0.0.1:5002",
        payload={
            "numbers": [1,2,3],
            "nested": {
                "a": True,
                "b": None
            },
            "string": "example"
        }
    )
    serialized_event = serializer.serialize(event)
    deserialized_event = serializer.deserialize(serialized_event)
    assert deserialized_event == event

def test_deserializer_with_invalid_json(serializer):
    with pytest.raises(json.JSONDecodeError):
        serializer.deserialize("Example")