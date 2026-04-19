import time
import socket
from threading import Thread
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
        self.connections_last_received = {}
        self.running = True
        self.dispatcher.register_handler(EventType.TASK_REQUEST, self.handle_task_request)
        self.dispatcher.register_handler(EventType.TASK_COMPLETED, self.handle_task_completed)
        self.dispatcher.register_handler(EventType.HEARTBEAT, self.handle_heartbeat)

    def start(self):
        print(f"[{self.id}]: coordinator started!")
        self.monitor_thread = Thread(target=self.monitor_workers)
        self.monitor_thread.start()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, _, port = self.address.partition(":")
        self.connection.bind((addr, int(port)))
        self.connection.listen()
        self.connection.settimeout(1.0)
        try:
            while self.running:
                try:  
                    print(f"[{self.id}]: waiting for connection ...")
                    conn, addr = self.connection.accept()
                    print(f"[{self.id}]: connection from {str(addr)}")
                except socket.timeout:
                    continue
                except OSError:
                    break
                self.handle_connection(conn)
        except KeyboardInterrupt:
            self.stop()

    def handle_connection(self, conn: socket.socket):
        buffer = ""
        conn.settimeout(1.0)
        while self.running:
            try:
                data_bytes = conn.recv(4096)
            except socket.timeout:
                continue
            except Exception:
                break
            if not data_bytes:
                break
            data_decoded = data_bytes.decode()
            buffer += data_decoded
            while "\n" in buffer:
                event, buffer = buffer.split("\n", 1)
                print(f"[{self.id}]: decoded {event}")
                data = self.serializer.deserialize(event)
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
            self.connections_last_received.pop(node_id_to_remove)

    def handle_task_request(self, event: Event):
         print(f"[{self.id}]: worker {event.node_id} ha richiesto un task")
         self.connections_last_received[event.node_id] = time.time()
         response = Event (
            type = EventType.TASK_ASSIGN,
            node_id = self.id,
            address = self.address,
            payload = {"task" : "example"}
         )
         self.message_sender.send(self.connections[event.node_id], response)

    def handle_task_completed(self, event: Event):
        print(f"[{self.id}]: worker {event.node_id} completed task")
        self.connections_last_received[event.node_id] = time.time()

    def monitor_workers(self):
        while self.running:
            timeout = 5
            starting_time = time.time()
            to_remove = []
            for node_id, last_seen in self.connections_last_received.items():
                if starting_time - last_seen > timeout:
                    print(f"[{self.id}]: coordinator {node_id} is dead")
                    to_remove.append(node_id)
            for node_id in to_remove:
                self.connections.pop(node_id)
                self.connections_last_received.pop(node_id)
            time.sleep(1)

    def handle_heartbeat(self, event: Event):
        print(f"[{self.id}]: received heartbeat from {event.address}")
        self.connections_last_received[event.node_id] = time.time()

    def stop(self):
        self.running = False
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
    coordinator.start()