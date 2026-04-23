from typing import List, Dict
from dataclasses import dataclass
# from events import msg_event
from whisper_infer.snapshots import PipelineSnapshot
from whisper_infer.states import SessionState
from .pipeline_failure import PipelineFailure

@dataclass
class SessionSnapshot:
    id : str
    media_path : str
    keywords : List[str]
    state : SessionState
    started_at : float
    elapsed : float
    pipelines : Dict[str, PipelineSnapshot]
    failure_reasons : List[PipelineFailure]