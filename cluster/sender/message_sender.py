import socket
from cluster.common.event import Event
from cluster.serializer.serializer import Serializer

class MessageSender():
    def __init__(self):
        self.serializer = Serializer()

    def send(self, conn: socket.socket, event: Event):
        conn.sendall((self.serializer.serialize(event) + "\n").encode("utf-8"))