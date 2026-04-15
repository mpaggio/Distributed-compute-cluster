import socket
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.serializer.serializer import Serializer
from cluster.common.event_type import EventType
from cluster.common.event import Event
from cluster.sender.message_sender import MessageSender

class Coordinator:
    def __init__(self):
        self.address = "127.0.0.1:5002"
        self.id = "coordinator#1"
        self.dispatcher = EventDispatcher()
        self.serializer = Serializer()
        self.message_sender = MessageSender()
        self.connections = {}
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
            if data.node_id not in self.connections or self.connections[data.node_id] != conn:
                self.connections[data.node_id] = conn
            self.dispatcher.dispatch(data)
        self.handle_connection_closure(conn)
        conn.close()

    def handle_connection_closure(self, conn: socket.socket):
        node_id_to_remove = None
        for node_id, stored_conn in self.connections.items():
            if stored_conn == conn:
                node_id_to_remove = node_id
                break
        if node_id_to_remove: 
            self.connections.pop(node_id_to_remove)

    def handle_task_request(self, event: Event):
         print("Worker " + event.node_id + " ha richiesto un task")
         response = Event (
            type = EventType.TASK_ASSIGN,
            node_id = self.id,
            address = self.address,
            payload = {"task" : "example"}
         )
         self.message_sender.send(self.connections[event.node_id], response)