from typing import Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass

S = TypeVar('S', bound=Enum)

@dataclass
class StateHandler(Generic[S]):
    state: S
    transitions: dict[S, set[S]]  # valid transitions
    on_transition: Callable[[S, S], None]
    cleanup : Callable[[], None] | None = None
    cleanup_triggers : list[S] | None = None
    
    def __post_init__(self):
        if self.cleanup is None:
            self.cleanup = lambda : None

    def transition(self, new_state: S) -> bool:
        if self.cleanup_triggers and new_state in self.cleanup_triggers:
            assert self.cleanup is not None
            self.cleanup()

        if new_state not in self.transitions.get(self.state, set()):
            return False
        old = self.state
        self.state = new_state
        self.on_transition(old, new_state)
        return True