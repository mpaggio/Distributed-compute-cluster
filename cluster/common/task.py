from cluster.common.task_type import TaskType

class Task:
    task_id: str
    state: TaskType
    attempt: int
    assigned_worker: str
    payload: dict