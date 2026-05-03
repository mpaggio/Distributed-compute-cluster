from dataclasses import dataclass
from cluster.common.task_type import TaskType

@dataclass(frozen=True)
class Task:
    task_id: str
    state: TaskType
    attempt: int
    assigned_worker: str
    payload: dict