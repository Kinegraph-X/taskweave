from enum import Enum

class PipelineState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELED = "canceled"
    STOPPING = "stopping"
    FAILED =  "failed"
    SUCCESS = "success"
