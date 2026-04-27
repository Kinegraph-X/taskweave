from typing import Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass

S = TypeVar('S', bound=Enum)

@dataclass
class StateHandler(Generic[S]):
    state: S
    transitions: dict[S, set[S]]  # valid transitions
    on_transition: Callable[[S, S], None]

    def transition(self, new_state: S) -> bool:
        if new_state not in self.transitions.get(self.state, set()):
            return False
        old = self.state
        self.state = new_state
        self.on_transition(old, new_state)
        return True