from dataclasses import dataclass, field
from taskweave.states import TaskState

@dataclass
class TaskSnapshot:
    name: str
    state: TaskState
    started_at: float
    elapsed: float
    last_error: str
    retries: int = field(default = 0)
    progress: dict = field(default_factory = dict) # extensible : {"lines_processed": 42, ...}