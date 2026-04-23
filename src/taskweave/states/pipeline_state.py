from enum import Enum

class PipelineState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED =  "failed"
    DONE = "done"
