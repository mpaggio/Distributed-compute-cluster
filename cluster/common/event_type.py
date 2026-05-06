from enum import Enum

class EventType(Enum):
    TASK_ASSIGN = 1
    TASK_RESULT = 2
    TASK_REQUEST = 3
    TASK_COMPLETED = 4
    HEARTBEAT = 5