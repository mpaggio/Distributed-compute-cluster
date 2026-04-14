import socket
from common.event import Event
from serializer.serializer import Serializer

class MessageSender():
    def __init__(self):
        self.serializer = Serializer()

    def send(self, conn: socket.socket, event: Event):
        conn.sendall(self.serializer.serialize(event).encode("utf-8"))