from enum import Enum

class WorkerState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
