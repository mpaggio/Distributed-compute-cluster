import socket
from dispatcher.event_dispatcher import EventDispatcher
from serializer.serializer import Serializer
from common.event_type import EventType
from common.event import Event
from sender.message_sender import MessageSender

class Coordinator:
    def __init__(self):
        self.address = "127.0.0.1:5002"
        self.id = "coordinator#1"
        self.dispatcher = EventDispatcher()
        self.serializer = Serializer()
        self.message_sender = MessageSender()
        self.dispatcher.register_handler(EventType.TASK_REQUEST, self.handle_task_request)

    def start(self):
        print("Coordinator started!")
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, _, port = self.address.partition(":")
        self.connection.bind((addr, int(port)))
        self.connection.listen()
        while True:
            print("Waiting for connection ...")
            conn, addr = self.connection.accept()
            print("Connected from: " + str(addr))
            self.handle_connection(conn)

    def handle_connection(self, conn: socket.socket):
        while True:
                data_bytes = conn.recv(4096)
                if not data_bytes:
                    break
                print("Decoded: ", data_bytes.decode())
                data = self.serializer.deserialize(data_bytes.decode())
                self.dispatcher.dispatch(data, conn)
        conn.close()

    def handle_task_request(self, event: Event, conn: socket.socket):
         print("Worker " + event.node_id + " ha richiesto un task")
         response = Event (
            type = EventType.TASK_ASSIGN,
            node_id = self.id,
            address = self.address,
            payload = {"task" : "example"}
         )
         self.message_sender.send(conn, response)