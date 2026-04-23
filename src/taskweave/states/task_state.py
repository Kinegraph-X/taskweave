from enum import Enum

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "ssuccess"
    FAILED = "failed"
    CANCELED = "canceled"