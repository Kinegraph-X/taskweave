from dataclasses import dataclass, field
from whisper_infer.states import SessionState
from whisper_infer.pipeline import Pipeline
from whisper_infer.snapshots import PipelineFailure

@dataclass
class Session:
    id: str                          # UUID
    media_path: str
    keywords: list[str]
    started_at: float = field(default = 0.0)
    pipelines: list[Pipeline] = field(default_factory=list)
    state: SessionState = SessionState.PENDING
    failure_reasons: list[PipelineFailure] = field(default_factory=list) # pipeline_id + raison + timestamp