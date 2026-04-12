from threading import Thread
from cluster.coordinator.coordinator import Coordinator
from cluster.worker.worker import Worker
import time

def main():
    coordinator = Coordinator()
    coordinator_thread = Thread(target=coordinator.start)
    coordinator_thread.start()
    time.sleep(5.0)
    addr, _, port = coordinator.address.partition(":")
    worker = Worker()
    worker_thread = Thread(target=worker.connect, args=(addr, int(port),))
    worker_thread.start()