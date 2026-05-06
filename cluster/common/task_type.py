from enum import Enum

class TaskType(Enum):
    PENDING = 1
    ASSIGNED = 2
    COMPLETED = 3
    ORPHANED = 4
    EXPIRED = 5