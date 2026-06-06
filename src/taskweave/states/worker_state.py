from enum import Enum

class WorkerState(Enum):
    PENDING = "stopped"
    STOPPED = "stopped"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
