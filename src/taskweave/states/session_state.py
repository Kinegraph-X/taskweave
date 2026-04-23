from enum import Enum

class SessionState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = 'stopping'
    SUCCESS = "ssuccess"
    FAILED = "failed"
    CANCELED = "canceled"