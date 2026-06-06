from dataclasses import dataclass, field
from time import time
from uuid import uuid4
from taskweave.pipeline import RuntimePipeline
from taskweave.states import SessionState, SessionLifecycle
from taskweave.snapshots import PipelineFailure, SessionSnapshot
from taskweave.utils import TaskId

@dataclass(kw_only = True)
class Session:
    pipelines : dict[TaskId, RuntimePipeline]
    id: TaskId = field(default_factory = lambda : TaskId(f"session_{uuid4().hex[:6]}")) #hex(int(time() * 1000) >> 32)[16:]

    def __post_init__(self):
        self.cycle = SessionLifecycle(
            source_id = self.id,
            on_transition = lambda old, new, event: None
        )

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
                id=str(self.id),
                state = str(self.cycle.state),
                started_at=self.cycle.started_at,
                elapsed=time() - self.cycle.started_at if self.cycle.started_at else 0,
                pipelines={str(id) : p.snapshot() for id, p in self.pipelines.items()},
                failure_reasons=self.failure_reasons
            )
    
