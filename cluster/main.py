from threading import Thread
from coordinator.coordinator import Coordinator
from worker.worker import Worker
import time

def main():
    coordinator = Coordinator()
    coordinator_thread = Thread(target=coordinator.start)
    coordinator_thread.start()
    time.sleep(5.0)
    addr, _, port = coordinator.address.partition(":")
    worker = Worker()
    worker_thread = Thread(target=worker.start, args=(addr, int(port),))
    worker_thread.start()

if __name__ == "__main__":
    main()