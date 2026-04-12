import socket
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.serializer.serializer import Serializer

class Coordinator:
    def __init__(self):
        self.address = "127.0.0.1:5002"
        self.id = "coordinator#1"
        self.dispatcher = EventDispatcher()
        self.serializer = Serializer()

    def start(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, _, port = self.address.partition(":")
        self.connection.bind((addr, int(port)))
        self.connection.listen()
        while True:
            conn, addr = self.connection.accept()
            self.handle_connection(conn)

    def handle_connection(self, conn: socket):
        while True:
                data_bytes = conn.recv(4096)
                if not data_bytes:
                    break
                print("RAW BYTES:", data_bytes)
                print("DECODED:", data_bytes.decode())
                print("EVENT:", data)
                data = self.serializer.deserialize(data_bytes.decode())
                self.dispatcher.dispatch(data)
        conn.close()