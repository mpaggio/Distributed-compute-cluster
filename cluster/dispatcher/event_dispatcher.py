from cluster.common.event import Event
from cluster.common.event_type import EventType

class EventDispatcher:

    def __init__(self): 
        self.handlers = {}

    def register_handler(self, event_type: EventType, fun: callable):
        if event_type in self.handlers:
            print("Event type already assigned!")
        self.handlers[event_type] = fun

    def dispatch(self, event: Event):
        if event.type not in self.handlers:
            raise Exception("Illegal argument exception!")
        handler = self.handlers[event.type]
        handler(event)