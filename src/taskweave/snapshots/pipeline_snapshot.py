from dataclasses import dataclass
from whisper_infer.snapshots import TaskSnapshot
from whisper_infer.states import PipelineState

@dataclass  
class PipelineSnapshot:
    id : str
    tasks: dict[str, TaskSnapshot]
    state : PipelineState
    started_at: float
    elapsed: float
    early_exit: bool