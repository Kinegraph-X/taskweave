from typing import Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field

from .cleanup_strategy import CleanupStrategy

from taskweave.utils import TaskId

from taskweave_protocol import LogEvent

S = TypeVar('S', bound=Enum)

@dataclass
class Lifecycle(Generic[S]):
    source_id : TaskId
    state: S
    transitions: dict[S, set[S]]  # valid transitions
    on_transition: Callable[[S, S, LogEvent | None], None]
    cleanup : CleanupStrategy = field(default_factory = CleanupStrategy.noop)
    started_at : float = 0.0

    def transition(self, new: S) -> None:
        self.cleanup.do(new)

        if new not in self.transitions.get(self.state, set()):
            raise RuntimeError(f"worker state mismatch {self.source_id} : state {self.state.value}, expected {self.transitions.get(self.state, set())}")
        old = self.state
        self.state = new
        self.on_transition(old, new, None)