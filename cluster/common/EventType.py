from enum import Enum

class EventType(Enum):
    TASK_ASSIGN = 1
    TASK_RESULT = 2
    HEARTBEAT = 3