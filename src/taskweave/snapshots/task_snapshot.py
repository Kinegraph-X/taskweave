from dataclasses import dataclass, field
from whisper_infer.states import TaskState

@dataclass
class TaskSnapshot:
    name: str
    state: TaskState
    started_at: float
    elapsed: float
    last_error: str
    retries: int = field(default = 0)
    progress: dict = field(default = {}) # extensible : {"lines_processed": 42, ...}