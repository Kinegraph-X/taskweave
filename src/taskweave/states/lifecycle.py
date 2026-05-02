from typing import Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field

from .cleanup_strategy import CleanupStrategy

S = TypeVar('S', bound=Enum)

@dataclass
class Lifecycle(Generic[S]):
    state: S
    transitions: dict[S, set[S]]  # valid transitions
    on_transition: Callable[[S, S], None]
    cleanup : CleanupStrategy = field(default_factory = CleanupStrategy.noop)

    def transition(self, new_state: S) -> bool:
        self.cleanup.do(new_state)

        if new_state not in self.transitions.get(self.state, set()):
            return False
        old = self.state
        self.state = new_state
        self.on_transition(old, new_state)
        return True