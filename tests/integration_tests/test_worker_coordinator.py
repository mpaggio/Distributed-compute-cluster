import time
from threading import Thread
from cluster.coordinator.coordinator import Coordinator
from cluster.worker.worker import Worker
from cluster.common.event_type import EventType

def test_coordinator_worker_simple_integration():
    coordinator = Coordinator()
    coord_thread = Thread(target=coordinator.start, daemon=True)
    coord_thread.start()

    worker = Worker()
    worker_thread = Thread(target=worker.start, args=("127.0.0.1", 5002,), daemon=True)
    worker_thread.start()

    timeout = 5
    start_time = time.time()
    while worker.last_event_received is None:
        if time.time() - start_time > timeout:
            break
        time.sleep(0.1)

    assert worker.id in coordinator.connections_last_received
    assert coordinator.connections_last_received[worker.id] is not None
    assert worker.last_event_received is not None
    assert worker.last_event_received.type == EventType.TASK_ASSIGN
    worker.stop()
    coordinator.stop()

def test_task_completed_integration():
    coordinator = Coordinator()
    coord_thread = Thread(target=coordinator.start, daemon=True)
    coord_thread.start()

    worker = Worker()
    worker_thread = Thread(target=worker.start, args=("127.0.0.1", 5002,), daemon=True)
    worker_thread.start()

    timeout = 8
    start_time = time.time()
    completed_received = False
    while time.time() - start_time < timeout:
        if worker.id in coordinator.connections_last_received and worker.last_event_received is not None:
            completed_received = True
            break
        time.sleep(0.1)

    assert completed_received
    assert worker.id in coordinator.connections_last_received
    assert coordinator.connections_last_received[worker.id] is not None

    worker.stop()
    coordinator.stop()