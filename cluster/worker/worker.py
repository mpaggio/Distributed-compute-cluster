import socket
import time
import uuid
from threading import Thread
from queue import Queue, Empty
from cluster.serializer.serializer import Serializer
from cluster.common.event import Event
from cluster.common.event_type import EventType
from cluster.common.task import Task
from cluster.common.task_type import TaskType
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.sender.message_sender import MessageSender

class Worker:
    def __init__(self):
        self.serializer = Serializer()
        self.dispatcher = EventDispatcher()
        self.message_sender = MessageSender()
        self.connection = None
        self.running = True
        self.id = f"worker-{uuid.uuid4().hex[:8]}"
        self.address = "127.0.0.1:5001"
        self.last_event_received = None
        self.send_queue = Queue()
        self.threads: list[Thread] = []
        self.dispatcher.register_handler(EventType.TASK_ASSIGN, self.handle_task_assign)

    def start(self, address: str, port: int):
        self.connect(address, port)
        heartbeat_thread = Thread(target=self.start_heartbeat, daemon=True)
        self.threads.append(heartbeat_thread)
        heartbeat_thread.start()
        send_thread = Thread(target=self.start_sender, daemon=True)
        self.threads.append(send_thread)
        send_thread.start()
        self.handle_connection()

    def connect(self, address: str, port: int):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((address, port))
        self.connection.settimeout(1.0)
        task_request_event = Event(EventType.TASK_REQUEST, self.id, self.address, {})
        self.send_queue.put(task_request_event)

    def handle_connection(self):
        buffer = ""
        while self.running:
            print(f"[{self.id}]: waiting for response ...")
            try:
                data_bytes = self.connection.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not data_bytes:
                break
            data_decoded = data_bytes.decode()
            buffer += data_decoded
            while "\n" in buffer:
                event, buffer = buffer.split("\n", 1)
                print(f"[{self.id}]: received response ({event})")
                data = self.serializer.deserialize(event)
                self.dispatcher.dispatch(data)
        self.running = False
        self.connection.close()

    def handle_task_assign(self, event: Event):
        self.last_event_received = event
        task_execution_thread = Thread(target=self.execute_task, args=(event,), daemon=True)
        self.threads.append(task_execution_thread)
        task_execution_thread.start()

    def execute_task(self, event: Event):
        print(f"[{self.id}]: starting to execute given task [{Task.from_dict(event.payload).to_string()}] ...")
        for _ in range(event.payload["payload"]["duration"]):
            if not self.running:
                print(f"[{self.id}]: task execution interrupted.")
                return
            time.sleep(1)
        #time.sleep(event.payload["payload"]["duration"])
        completed_event = Event(EventType.TASK_COMPLETED, self.id, self.address, event.payload)
        self.send_queue.put(completed_event)
        request_event = Event(EventType.TASK_REQUEST, self.id, self.address, {})
        self.send_queue.put(request_event)
        print(f"[{self.id}]: completed execution of given event.")

    def start_heartbeat(self):
        while self.running:
            if not self.connection:
                time.sleep(0.1)
                continue
            if self.id == "unknown":
                time.sleep(0.1)
                continue
            try:
                event = Event(EventType.HEARTBEAT, self.id, self.address, {})
                self.send_queue.put(event)
                print(f"[{self.id}]: heartbeat sent")
            except Exception:
                print(f"[{self.id}]: heartbeat failed")
                break
            time.sleep(1)

    def start_sender(self):
        while self.running:
            try:
                event = self.send_queue.get(timeout=1)
                if event is None:
                    break
                self.message_sender.send(self.connection, event)
            except Empty:
                continue
            except OSError:
                self.running = False
                break

    def stop(self):
        self.running = False
        self.send_queue.put(None)
        try:
            if self.connection:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            for thread in self.threads:
                thread.join(timeout=2)
        except Exception:
            pass

if __name__ == "__main__":
    worker = Worker()
    try:
        worker.start("127.0.0.1", 5002)
    except KeyboardInterrupt:
        print(f"[{worker.id}]: shutting down worker...")
        worker.stop()