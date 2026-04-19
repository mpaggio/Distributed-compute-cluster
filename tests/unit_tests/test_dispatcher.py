import pytest
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.common.event import Event
from cluster.common.event_type import EventType

@pytest.fixture
def dispatcher():
    return EventDispatcher()

@pytest.fixture
def event():
    event = Event(
        type=EventType.TASK_REQUEST,
        node_id="worker#1",
        address="127.0.0.1:5001",
        payload={}
    )
    return event

def test_dispatcher_registration_and_dispatch(dispatcher, event):
    def simple_handler(event: Event):
        print(event.type)
    assert dispatcher.register_handler(EventType.TASK_REQUEST, simple_handler) == EventDispatcher.RegistrationResult.REGISTERED
    assert dispatcher.dispatch(event) == EventDispatcher.DispatchResult.HANDLED
    
def test_dispatcher_passed_event(dispatcher, event):
    received_event: Event = None
    def handler(event: Event):
        nonlocal received_event
        received_event = event
    assert dispatcher.register_handler(EventType.TASK_REQUEST, handler) == EventDispatcher.RegistrationResult.REGISTERED
    assert dispatcher.dispatch(event) == EventDispatcher.DispatchResult.HANDLED
    assert received_event is not None and received_event.type == EventType.TASK_REQUEST

def test_dispatcher_without_handler(dispatcher, event):
    assert dispatcher.dispatch(event) == EventDispatcher.DispatchResult.NOT_REGISTERED

def test_dispatcher_with_handler_failure(dispatcher, event):
    def failing_handler(event: Event):
        raise(Exception)
    assert dispatcher.register_handler(EventType.TASK_REQUEST, failing_handler) == EventDispatcher.RegistrationResult.REGISTERED
    assert dispatcher.dispatch(event) == EventDispatcher.DispatchResult.NOT_HANDLED

def test_dispatcher_override_handler(dispatcher, event):
    called = []
    def handler1(event: Event):
        called.append("h1")
    def handler2(event: Event):
        called.append("h2")
    assert dispatcher.register_handler(EventType.TASK_REQUEST, handler1) == EventDispatcher.RegistrationResult.REGISTERED
    assert dispatcher.register_handler(EventType.TASK_REQUEST, handler2) == EventDispatcher.RegistrationResult.OVERRIDED
    assert dispatcher.dispatch(event) == EventDispatcher.DispatchResult.HANDLED
    assert called == ["h2"]

def test_dispatcher_with_multiple_event_types(dispatcher):
    called = []
    def handler_request_event(event: Event):
        called.append("request")
    def handler_assign_event(event: Event):
        called.append("assign")
    dispatcher.register_handler(EventType.TASK_REQUEST, handler_request_event)
    dispatcher.register_handler(EventType.TASK_ASSIGN, handler_assign_event)
    dispatcher.dispatch(Event(EventType.TASK_REQUEST, "id", "addr", {}))
    dispatcher.dispatch(Event(EventType.TASK_ASSIGN, "id", "addr", {}))
    assert called == ["request", "assign"]