import time
from typing import List, Callable, cast
from dataclasses import dataclass, field

from .lifecycle import Lifecycle
from .task_transitions import task_transitions
from .cleanup_strategy import CleanupStrategy

from taskweave.states import TaskState
from taskweave.utils import TaskId

from taskweave_protocol import LogEvent, SourceType, MsgType

@dataclass(kw_only = True)
class TaskLifecycle(Lifecycle[TaskState]):
    source_id : TaskId
    state : TaskState = TaskState.PENDING
    transitions = task_transitions
    on_transition: Callable[[TaskState, TaskState, LogEvent | None], None]
    cleanup : CleanupStrategy = field(default_factory = CleanupStrategy.noop)
    started_at : float = 0.0

    def transition(self, new: TaskState) -> None:
        self.cleanup.do(new)

        if new not in self.transitions.get(self.state, set()):
            raise RuntimeError(f"worker state mismatch {self.source_id} : state {self.state.value}, expected {self.transitions.get(self.state, set())}")

        if new == TaskState.RUNNING:
            self.started_at = time.time()

        old = self.state
        self.state = new
        self.on_transition(old, new, self.get_event(new))

    def get_event(
            self,
            state : TaskState
        ):
        return LogEvent(
            source_id = self.source_id,
            state = state.value,
            source_type= SourceType.TASK,
            msg_type = MsgType.STATE_CHANGE,
            timestamp = time.time()
        )