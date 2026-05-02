from dataclasses import dataclass
from .task_snapshot import TaskSnapshot
from taskweave.states import PipelineState
from taskweave.utils import StrSerializable

@dataclass  
class PipelineSnapshot:
    id : str
    tasks: dict[str | StrSerializable, TaskSnapshot]
    state : PipelineState
    started_at: float
    elapsed: float
    early_exit: bool