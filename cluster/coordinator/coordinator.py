import time
import uuid
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

class WorkerState:
    def __init__(self, conn: socket, last: float):
        self.conn: socket = conn
        self.last_received: float = last

class Coordinator:
    def __init__(self):
        self.running = True
        self.id = f"coordinator-{uuid.uuid4().hex[:8]}"
        self.address = "127.0.0.1:5002"
        self.dispatcher = EventDispatcher()
        self.serializer = Serializer()
        self.message_sender = MessageSender()
        self.workers: dict[str, WorkerState] = {}
        self.conn_to_worker: dict[socket.socket, str] = {}
        self.send_queue = Queue(maxsize=1000)
        self.lock = Lock()
        self.tasks: dict[str, Task] = {}
        self.worker_tasks: dict[str, list[str]] = {}
        self.pending_tasks: deque[str] = deque()
        self.priority_pending_tasks: deque[str] = deque()
        self.threads: list[Thread] = []
        self.dispatcher.register_handler(EventType.HEARTBEAT, self.handle_heartbeat)
        self.dispatcher.register_handler(EventType.TASK_REQUEST, self.handle_task_request)
        self.dispatcher.register_handler(EventType.TASK_COMPLETED, self.handle_task_completed)

    def start(self):
        print(f"[{self.id}]: coordinator started!")
        monitor_thread = Thread(target=self.monitor_workers, daemon=True)
        self.threads.append(monitor_thread)
        monitor_thread.start()
        sender_thread = Thread(target=self.start_sender, daemon=True)
        self.threads.append(sender_thread)
        sender_thread.start()
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
            connection_thread = Thread(target=self.handle_connection, args=(conn,), daemon=True)
            self.threads.append(connection_thread)
            connection_thread.start()

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
                    worker_id = self.conn_to_worker.get(conn)
                    if not worker_id:
                        worker_id = data.node_id
                        self.conn_to_worker[conn] = worker_id
                        self.workers[worker_id] = WorkerState(conn, time.time())
                new_data = Event(data.type, worker_id, data.address, data.payload)
                self.dispatcher.dispatch(new_data)
        self.handle_connection_closure(conn)
        conn.close()

    def check_expired_tasks(self):
        now = time.time()
        with self.lock:
            for task_id, task in self.tasks.items():
                if task.state == TaskType.ASSIGNED and task.expiry is not None:
                    if now > task.expiry:
                        print(f"[{self.id}]: task {task_id} expired")
                        task.state = TaskType.EXPIRED
                        task.assigned_worker = None
                        task.expiry = None
                        self.priority_pending_tasks.append(task_id)

    def remove_worker(self, node_id):
        with self.lock:
            print(f"[{self.id}]: removing worker {node_id}...")
            if node_id in self.workers:
                worker = self.workers.get(node_id)
                if worker:
                    self.conn_to_worker.pop(worker.conn, None)
                    self.workers.pop(node_id, None)
            for task_id in self.worker_tasks.get(node_id, []):
                print(f"[{self.id}]: task {task_id} removed from worker {node_id}.")
                self.tasks[task_id].state = TaskType.ORPHANED
                print(f"[{self.id}]: {task_id} becoming ORPHANED.")  
                self.tasks[task_id].assigned_worker = None  
                self.priority_pending_tasks.append(task_id)
            self.worker_tasks.pop(node_id, None)

    def handle_connection_closure(self, conn: socket.socket):
        with self.lock:
            node_id_to_remove = None
            for node_id, node_state in self.workers.items():
                if node_state.conn == conn:
                    node_id_to_remove = node_id
                    break
        if node_id_to_remove: 
            self.remove_worker(node_id_to_remove)

    def handle_task_request(self, event: Event):
        with self.lock:
            print(f"[{self.id}]: worker {event.node_id} requested task")
            worker = self.workers.get(event.node_id)
            if not worker:
                return
            worker.last_received = time.time()
            worker_id = event.node_id
            if self.priority_pending_tasks:
                task_assigned_id = self.priority_pending_tasks.popleft()
                print(f"[{self.id}]: extracted {task_assigned_id} from priority pending tasks")
                print(f"[{self.id}]: priority pending tasks remained {self.priority_pending_tasks}")
            elif self.pending_tasks:
                task_assigned_id = self.pending_tasks.popleft()
                print(f"[{self.id}]: extracted {task_assigned_id} from pending tasks")
                print(f"[{self.id}]: pending tasks remained {self.pending_tasks}")
            else:
                return
            task_assigned: Task = self.tasks[task_assigned_id]
            task_assigned.state = TaskType.ASSIGNED
            task_assigned.assigned_worker = worker_id
            task_assigned.attempt += 1
            task_assigned.expiry = time.time() + Task.EXPIRE_OFFSET_SECONDS
            self.worker_tasks.setdefault(worker_id, []).append(task_assigned_id)
            response = Event (
                type = EventType.TASK_ASSIGN,
                node_id = self.id,
                address = self.address,
                payload = task_assigned.to_dict()
            )
            conn = self.workers.get(worker_id).conn
            if conn:
                self.send_queue.put((response, conn))
                print(f"[{self.id}]: task {task_assigned_id} assigned to worker {worker_id}")

    def handle_task_completed(self, event: Event):
        with self.lock:
            print(f"[{self.id}]: worker {event.node_id} completed task")
            worker_state = self.workers.get(event.node_id)
            if worker_state:
                worker_state.last_received = time.time()
                completed_task = Task.from_dict(event.payload)
                saved_task = self.tasks[completed_task.task_id]
                if saved_task.state == TaskType.ASSIGNED and saved_task.attempt == completed_task.attempt and saved_task.assigned_worker == completed_task.assigned_worker:
                    saved_task.state = TaskType.COMPLETED
                if event.node_id in self.worker_tasks:
                    if completed_task.task_id in self.worker_tasks[event.node_id]:
                        self.worker_tasks[event.node_id].remove(completed_task.task_id)

    def monitor_workers(self):
        print(f"[{self.id}]: monitoring workers...")
        while self.running:
            time.sleep(1)
            timeout = 3
            starting_time = time.time()
            to_remove = []
            print(f"[{self.id}]: last_seen={[(i,s.last_received) for i,s in self.workers.items()]}")
            with self.lock:    
                for node_id in self.workers.keys():
                    worker_state = self.workers.get(node_id)
                    if not worker_state:
                        continue
                    last_seen = worker_state.last_received
                    if last_seen is None:
                        continue
                    if starting_time - last_seen > timeout:
                        print(f"[{self.id}]: worker {node_id} is dead")
                        to_remove.append(node_id)
            for node_id in to_remove:
                self.remove_worker(node_id)
            self.check_expired_tasks()

    def handle_heartbeat(self, event: Event):
        with self.lock:
            worker = self.workers.get(event.node_id)
            if worker:
                worker.last_received = time.time()

    def start_sender(self):
        while self.running:
            try:
                event, conn = self.send_queue.get(timeout=1)
                if event is None:
                    break
                self.message_sender.send(conn, event)
            except Empty:
                continue
            except OSError:
                self.running = False
                break

    def stop(self):
        self.running = False
        self.send_queue.put((None,None))
        try:
            self.connection.close()
        except Exception:
            pass
        for conn in list(s.conn for s in self.workers.values()):
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except Exception:
                pass
        for thread in self.threads:
            thread.join(timeout=2)

if __name__ == "__main__":
    coordinator = Coordinator()
    try:
        coordinator.start()
    except KeyboardInterrupt:
        print(f"[{coordinator.id}]: shutting down coordinator...")
        coordinator.stop()