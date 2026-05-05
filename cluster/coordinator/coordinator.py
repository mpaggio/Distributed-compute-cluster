import time
import socket
import random
from collections import deque
from threading import Lock
from threading import Thread
from queue import Queue, Empty
from cluster.dispatcher.event_dispatcher import EventDispatcher
from cluster.serializer.serializer import Serializer
from cluster.common.event_type import EventType
from cluster.common.event import Event
from cluster.common.task_type import TaskType
from cluster.common.task import Task
from cluster.sender.message_sender import MessageSender

class Coordinator:
    def __init__(self):
        self.address = "127.0.0.1:5002"
        self.id = "coordinator#1"
        self.dispatcher = EventDispatcher()
        self.serializer = Serializer()
        self.message_sender = MessageSender()
        self.connections = {}
        self.conn_to_worker = {}
        self.connections_last_received = {}
        self.running = True
        self.send_queue = Queue()
        self.next_worker_id = 1
        self.tasks: dict = {}
        self.worker_tasks: dict = {}
        self.pending_tasks = deque()
        self.lock = Lock()
        self.dispatcher.register_handler(EventType.TASK_REQUEST, self.handle_task_request)
        self.dispatcher.register_handler(EventType.TASK_COMPLETED, self.handle_task_completed)
        self.dispatcher.register_handler(EventType.HEARTBEAT, self.handle_heartbeat)
        self.dispatcher.register_handler(EventType.REGISTER, self.handle_register)

    def start(self):
        print(f"[{self.id}]: coordinator started!")
        self.monitor_thread = Thread(target=self.monitor_workers)
        self.monitor_thread.start()
        self.sender_thread = Thread(target=self.start_sender, daemon=True)
        self.sender_thread.start()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, _, port = self.address.partition(":")
        self.connection.bind((addr, int(port)))
        self.connection.listen()
        self.connection.settimeout(1.0)
        for i in range(0,20):
            task_id = f"task#{i}"
            task = Task(task_id, {"duration": random.randint(4, 8)})
            self.tasks[task_id] = task
            self.pending_tasks.append(task.task_id)
        while self.running:
            try:  
                print(f"[{self.id}]: waiting for connection ...")
                conn, addr = self.connection.accept()
                print(f"[{self.id}]: connection from {str(addr)}")
            except socket.timeout:
                continue
            except OSError:
                break
            Thread(target=self.handle_connection, args=(conn,), daemon=True).start()

    def handle_connection(self, conn: socket.socket):
        buffer = ""
        conn.settimeout(1.0)
        while self.running:
            try:
                data_bytes = conn.recv(4096)
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
                print(f"[{self.id}]: decoded {event}")
                data = self.serializer.deserialize(event)
                with self.lock:
                    if conn not in self.conn_to_worker:
                        worker_id = f"worker#{self.next_worker_id}"
                        self.next_worker_id += 1
                        self.conn_to_worker[conn] = worker_id
                        self.connections[worker_id] = conn
                        self.connections_last_received[worker_id] = time.time()
                    worker_id = self.conn_to_worker[conn]
                new_data = Event(data.type, worker_id, data.address, data.payload)
                self.dispatcher.dispatch(new_data)
        self.handle_connection_closure(conn)
        conn.close()

    def remove_worker(self, node_id):
        print(f"[{self.id}]: removing worker {node_id}...")
        self.connections.pop(node_id, None)
        self.connections_last_received.pop(node_id, None)
        for task_id in self.worker_tasks.get(node_id, []):
            print(f"[{self.id}]: task {task_id} removed from worker {node_id}.")
            self.tasks[task_id].state = TaskType.ORPHANED
            print(f"[{self.id}]: {task_id} becoming ORPHANED.")  
            self.tasks[task_id].assigned_worker = None  
            self.pending_tasks.append(task_id)
        self.worker_tasks.pop(node_id, None)

    def handle_connection_closure(self, conn: socket.socket):
        with self.lock:
            node_id_to_remove = None
            for node_id, stored_conn in self.connections.items():
                if stored_conn == conn:
                    node_id_to_remove = node_id
                    break
            if node_id_to_remove: 
                self.remove_worker(node_id_to_remove)

    def handle_register(self, event: Event):
        print(f"[{self.id}]: worker registration requested")
        with self.lock:
            conn = self.connections.get(event.node_id)
            if not conn:
                return
            self.worker_tasks[event.node_id] = []
        response = Event(EventType.ASSIGN_ID, self.id, self.address, {"id": event.node_id})
        self.send_queue.put((response, conn))
        print(f"[{self.id}]: assigned id {event.node_id}")

    def handle_task_request(self, event: Event):
        with self.lock:
            print(f"[{self.id}]: worker {event.node_id} requested task")
            self.connections_last_received[event.node_id] = time.time()
            worker_id = event.node_id
            if self.pending_tasks:
                task_assigned_id = self.pending_tasks.popleft()
                print(f"[{self.id}]: extracted {task_assigned_id} from pending tasks")
                print(f"[{self.id}]: pending tasks remained {self.pending_tasks}")
                task_assigned: Task = self.tasks[task_assigned_id]
                task_assigned.state = TaskType.ASSIGNED
                task_assigned.assigned_worker = worker_id
                task_assigned.attempt += 1
                self.worker_tasks[worker_id].append(task_assigned.task_id)
                response = Event (
                    type = EventType.TASK_ASSIGN,
                    node_id = self.id,
                    address = self.address,
                    payload = task_assigned.to_dict()
                )
                conn = self.connections.get(worker_id)
                if conn:
                    self.send_queue.put((response, conn))
                    print(f"[{self.id}]: task {task_assigned_id} assigned to worker {worker_id}")

    def handle_task_completed(self, event: Event):
        with self.lock:
            print(f"[{self.id}]: worker {event.node_id} completed task")
            self.connections_last_received[event.node_id] = time.time()
            completed_task = Task.from_dict(event.payload)
            if self.tasks[completed_task.task_id].attempt == completed_task.attempt:
                self.tasks[completed_task.task_id].state = TaskType.COMPLETED
            if event.node_id in self.worker_tasks:
                if completed_task.task_id in self.worker_tasks[event.node_id]:
                    self.worker_tasks[event.node_id].remove(completed_task.task_id)

    def monitor_workers(self):
        print(f"[{self.id}]: monitoring workers...")
        while self.running:
            time.sleep(1)
            with self.lock:
                timeout = 3
                starting_time = time.time()
                to_remove = []
                print(f"[{self.id}]: last_seen={self.connections_last_received}")
                for node_id in list(self.connections_last_received.keys()):
                    last_seen = self.connections_last_received.get(node_id)
                    if last_seen is None:
                        continue
                    if starting_time - last_seen > timeout:
                        print(f"[{self.id}]: worker {node_id} is dead")
                        to_remove.append(node_id)
                for node_id in to_remove:
                    self.remove_worker(node_id)

    def handle_heartbeat(self, event: Event):
        with self.lock:
            self.connections_last_received[event.node_id] = time.time()

    def start_sender(self):
        while self.running:
            try:
                event, conn = self.send_queue.get(timeout=1)
            except Empty:
                continue
            if event is None:
                break
            try:
                self.message_sender.send(conn, event)
            except OSError:
                break

    def stop(self):
        self.running = False
        self.send_queue.put((None,None))
        try:
            self.connection.close()
        except:
            pass
        for conn in list(self.connections.values()):
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except Exception:
                pass
        try:
            self.monitor_thread.join(timeout=2)
        except:
            pass

if __name__ == "__main__":
    coordinator = Coordinator()
    try:
        coordinator.start()
    except KeyboardInterrupt:
        print(f"[{coordinator.id}]: shutting down coordinator...")
        coordinator.stop()