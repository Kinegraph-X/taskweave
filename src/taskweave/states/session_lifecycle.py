import time
from typing import List, Callable, cast
from dataclasses import dataclass, field

from .lifecycle import Lifecycle
from .session_state import SessionState
from .session_transitions import session_transitions
from .cleanup_strategy import CleanupStrategy

from taskweave.utils import TaskId

from taskweave_protocol import LogEvent, SourceType, MsgType

@dataclass(kw_only = True)
class SessionLifecycle(Lifecycle[SessionState]):
    source_id : TaskId
    state : SessionState = SessionState.PENDING
    transitions = session_transitions
    on_transition: Callable[[SessionState, SessionState, LogEvent | None], None]
    cleanup : CleanupStrategy = field(default_factory = CleanupStrategy.noop)
    started_at : float = 0.0

    def transition(self, new: SessionState) -> None:
        self.cleanup.do(new)

        if new not in self.transitions.get(self.state, set()):
            raise RuntimeError(f"session state mismatch {self.source_id} : state {self.state.value}, expected {self.transitions.get(self.state, set())}")
        
        if new == SessionState.RUNNING:
            self.started_at = time.time()

        old = self.state
        self.state = new
        self.on_transition(old, new, self.get_event(new))

    def get_event(
            self,
            state : SessionState
        ):
        return LogEvent(
            source_id = self.source_id,
            state = state.value,
            source_type= SourceType.SESSION,
            msg_type = MsgType.STATE_CHANGE,
            timestamp = time.time()
        )