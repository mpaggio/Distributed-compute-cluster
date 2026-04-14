import socket
from serializer.serializer import Serializer
from common.event import Event
from common.event_type import EventType

class Worker:
    def __init__(self):
        self.serializer = Serializer()
        self.id = "worker#1"
        self.address = "127.0.0.1:5001"

    def connect(self, address: str, port: int):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((address, port))
        event = Event(EventType.TASK_REQUEST, self.id, self.address, {})
        serialized_event = self.serializer.serialize(event)
        connection.sendall(serialized_event.encode("utf-8"))