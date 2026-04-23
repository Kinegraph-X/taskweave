from dataclasses import dataclass
from uuid import uuid4

@dataclass
class PipelineFailure:
    pipeline_id : str
    reason : str
    timestamp : float