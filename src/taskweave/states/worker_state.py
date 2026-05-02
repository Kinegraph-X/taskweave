from enum import Enum

class WorkerState(Enum):
    PENDING = "stopped"
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
