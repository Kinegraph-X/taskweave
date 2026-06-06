import time
from typing import List, Callable, cast
from dataclasses import dataclass, field

from .lifecycle import Lifecycle
from .pipeline_state import PipelineState
from .pipeline_transitions import pipeline_transitions
from .cleanup_strategy import CleanupStrategy

from taskweave.utils import TaskId

from taskweave_protocol import LogEvent, SourceType, MsgType

@dataclass(kw_only = True)
class PipelineLifecycle(Lifecycle[PipelineState]):
    source_id : TaskId
    state : PipelineState = PipelineState.PENDING
    transitions = pipeline_transitions
    on_transition: Callable[[PipelineState, PipelineState, LogEvent | None], None]
    cleanup : CleanupStrategy = field(default_factory = CleanupStrategy.noop)
    started_at : float = 0.0

    def transition(self, new: PipelineState) -> None:
        self.cleanup.do(new)

        if new not in self.transitions.get(self.state, set()):
            raise RuntimeError(f"pipeline state mismatch {self.source_id} : state {self.state.value}, expected {self.transitions.get(self.state, set())}")
        
        if new == PipelineState.RUNNING:
            self.started_at = time.time()

        old = self.state
        self.state = new
        self.on_transition(old, new, self.get_event(new))

    def get_event(
            self,
            state : PipelineState
        ):
        return LogEvent(
            source_id = self.source_id,
            state = state.value,
            source_type= SourceType.PIPELINE,
            msg_type = MsgType.STATE_CHANGE,
            timestamp = time.time()
        )