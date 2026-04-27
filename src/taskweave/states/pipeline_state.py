from enum import Enum

class PipelineState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    STOPPING = "stopping"
    FAILED =  "failed"
    SUCCESS = "success"
