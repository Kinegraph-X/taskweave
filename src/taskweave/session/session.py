from dataclasses import dataclass, field
from time import time
from uuid import uuid4
from taskweave.states import SessionState
from taskweave.pipeline import Pipeline
from taskweave.snapshots import PipelineFailure

@dataclass
class Session:
    # media_path: str
    # keywords: list[str]
    id: str = field(default = f"{uuid4().hex[:6]}") #hex(int(time() * 1000) >> 32)[16:]
    started_at: float = field(default = 0.0)
    pipelines: list[Pipeline] = field(default_factory=list)
    state: SessionState = SessionState.PENDING
    failure_reasons: list[PipelineFailure] = field(default_factory=list) # pipeline_id + raison + timestamp