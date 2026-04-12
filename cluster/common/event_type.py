from enum import Enum

class EventType(Enum):
    TASK_ASSIGN = 1
    TASK_RESULT = 2
    TASK_REQUEST = 3
    HEARTBEAT = 4