import time
from threading import Thread
from cluster.coordinator.coordinator import Coordinator
from cluster.worker.worker import Worker
from cluster.common.event_type import EventType

def test_coordinator_worker_simple_integration():
    coordinator = Coordinator()
    coord_thread = Thread(target=coordinator.start)
    coord_thread.daemon = True
    coord_thread.start()

    worker = Worker()
    worker_thread = Thread(target=worker.start, args=("127.0.0.1", 5002,))
    worker_thread.daemon = True
    worker_thread.start()

    timeout = 5
    start_time = time.time()
    while worker.last_event_received is None:
        if time.time() - start_time > timeout:
            break
        time.sleep(0.1)

    assert coordinator.connections_last_received[worker.id] is not None
    assert worker.last_event_received is not None
    assert worker.last_event_received.type == EventType.TASK_ASSIGN