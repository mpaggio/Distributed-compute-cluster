from cluster.common.task_type import TaskType

class Task:
    EXPIRE_OFFSET_SECONDS = 10

    def __init__(self, task_id: str, payload: dict):
        self.task_id = task_id
        self.state = TaskType.PENDING
        self.attempt = 0
        self.assigned_worker = None
        self.payload = payload
        self.expiry: float = None

    def to_string(self):
        return f"ID: {self.task_id}, STATE: {self.state}, ATTEMPT: {self.attempt}, WORKER: {self.assigned_worker}, EXPIRY: {self.expiry}, PAYLOAD: {self.payload}"

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "state": self.state.name,
            "attempt": self.attempt,
            "assigned_worker": self.assigned_worker,
            "expiry": self.expiry,
            "payload": self.payload
        } 
    
    @staticmethod
    def from_dict(event_dict: dict):
        task_id = event_dict.get("task_id")
        state = event_dict.get("state")
        attempt = event_dict.get("attempt")
        assigned_worker = event_dict.get("assigned_worker")
        expiry = event_dict.get("expiry")
        payload = event_dict.get("payload")
        if task_id and state and attempt is not None and assigned_worker and payload: 
            task =  Task(task_id, payload)
            task.state = TaskType[state]
            task.attempt = attempt
            task.assigned_worker = assigned_worker
            task.expiry = float(expiry) if expiry is not None else None
            return task
        else:
            print("Error! trying to convert dict into Task, but dict doesn\'t have the right fields. Operation aborted!!!")