import socket
import time
from threading import Thread
from serializer.serializer import Serializer
from common.event import Event
from common.event_type import EventType
from dispatcher.event_dispatcher import EventDispatcher
from sender.message_sender import MessageSender

class Worker:
    def __init__(self):
        self.serializer = Serializer()
        self.dispatcher = EventDispatcher()
        self.message_sender = MessageSender()
        self.connection = None
        self.running = True
        self.id = "worker#1"
        self.address = "127.0.0.1:5001"
        self.dispatcher.register_handler(EventType.TASK_ASSIGN, self.handle_task_assign)

    def start(self, address: str, port: int):
        self.connect(address, port)
        self.handle_connection()

    def connect(self, address: str, port: int):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((address, port))
        event = Event(EventType.TASK_REQUEST, self.id, self.address, {})
        self.message_sender.send(self.connection, event)

    def handle_connection(self):
        while True:
            print("[" + self.id + "]: waiting for response ...")
            data_bytes = self.connection.recv(4096)
            if not data_bytes:
                break
            print("[" + self.id + "]: received response: " + data_bytes.decode())
            data = self.serializer.deserialize(data_bytes.decode())
            self.dispatcher.dispatch(data)
        self.connection.close()

    def handle_task_assign(self, event: Event):
        task_execution_thread = Thread(target=self.execute_task, args=(event,))
        task_execution_thread.start()

    def execute_task(self, event: Event):
        print("[" + self.id + "]: starting to execute given event (" + event.type.name + ") ...")
        time.sleep(3.0)
        print("[" + self.id + "]: completed execution of given event")

