import socket
import time
from threading import Thread
from cluster.serializer.serializer import Serializer
from cluster.common.event import Event
from cluster.common.event_type import EventType
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.sender.message_sender import MessageSender

class Worker:
    def __init__(self):
        self.serializer = Serializer()
        self.dispatcher = EventDispatcher()
        self.message_sender = MessageSender()
        self.connection = None
        self.running = True
        self.id = "worker#1"
        self.address = "127.0.0.1:5001"
        self.last_event_received = None
        self.dispatcher.register_handler(EventType.TASK_ASSIGN, self.handle_task_assign)

    def start(self, address: str, port: int):
        self.connect(address, port)
        self.heartbeat_thread = Thread(target=self.start_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        self.handle_connection()

    def connect(self, address: str, port: int):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((address, port))
        self.connection.settimeout(1.0)
        event = Event(EventType.TASK_REQUEST, self.id, self.address, {})
        self.message_sender.send(self.connection, event)

    def handle_connection(self):
        buffer = ""
        while self.running:
            print("[" + self.id + "]: waiting for response ...")
            try:
                data_bytes = self.connection.recv(4096)
            except socket.timeout:
                continue
            if not data_bytes:
                break
            data_decoded = data_bytes.decode()
            buffer += data_decoded
            while "\n" in buffer:
                event, buffer = buffer.split("\n", 1)
                print("[" + self.id + "]: received response: " + event)
                data = self.serializer.deserialize(event)
                self.dispatcher.dispatch(data)
        self.running = False
        self.connection.close()

    def handle_task_assign(self, event: Event):
        self.last_event_received = event
        task_execution_thread = Thread(target=self.execute_task, args=(event,))
        task_execution_thread.start()

    def execute_task(self, event: Event):
        print("[" + self.id + "]: starting to execute given event (" + event.type.name + ") ...")
        time.sleep(3.0)
        event = Event(EventType.TASK_COMPLETED, self.id, self.address, {})
        self.message_sender.send(self.connection, event)
        print("[" + self.id + "]: completed execution of given event")

    def start_heartbeat(self):
        while self.running:
            if not self.connection:
                time.sleep(0.1)
                continue
            try:
                event = Event(EventType.HEARTBEAT, self.id, self.address, {})
                self.message_sender.send(self.connection, event)
                print(f"[{self.id}]: heartbeat sent")
            except Exception:
                print(f"[{self.id}]: heartbeat failed")
                break
            time.sleep(1)

    def stop(self):
        self.running = False
        try:
            self.heartbeat_thread.join(timeout=2)
            if self.connection:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
        except Exception:
            pass

if __name__ == "__main__":
    worker = Worker()
    worker.start("127.0.0.1", 5002)