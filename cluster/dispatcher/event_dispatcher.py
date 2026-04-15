from enum import Enum
from cluster.common.event import Event
from cluster.common.event_type import EventType

class EventDispatcher:

    class RegistrationResult(Enum):
        REGISTERED = (0, "Operation successful")
        OVERRIDED = (1, "Handler overrided")

    class DispatchResult(Enum):
        HANDLED = (0, "Operation successful")
        NOT_REGISTERED = (1, "Event not registered")
        NOT_HANDLED = (2, "Error during dispatch")

    def __init__(self): 
        self.handlers = {}

    def register_handler(self, event_type: EventType, fun: callable) -> RegistrationResult:
        result = self.RegistrationResult.REGISTERED
        if event_type in self.handlers:
            result = self.RegistrationResult.OVERRIDED
        self.handlers[event_type] = fun
        return result 

    def dispatch(self, event: Event) -> DispatchResult:
        if event.type not in self.handlers:
            return self.DispatchResult.NOT_REGISTERED
        handler = self.handlers[event.type]
        try:
            handler(event)
            return self.DispatchResult.HANDLED
        except Exception as e:
            print(f"[Dispatcher] Error while handling {event.type.name}: {e}")
            return self.DispatchResult.NOT_HANDLED
        