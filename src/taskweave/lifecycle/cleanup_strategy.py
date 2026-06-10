from __future__ import annotations

from typing import Callable, Generic, TypeVar
from dataclasses import dataclass, field
from enum import Enum

S = TypeVar('S', bound=Enum)

@dataclass(kw_only=True)
class CleanupStrategy(Generic[S]):
    triggers: list[S] = field(default_factory = list)
    handler: Callable[[], None]

    @classmethod
    def noop(cls) -> CleanupStrategy:
        # Lifecycle ends cleanly — no external resources to release.
        return cls(handler=lambda: None)

    @classmethod
    def on_end(cls, triggers: list[S], handler: Callable[[], None]) -> CleanupStrategy:
        # Lifecycle ends with cleanup — e.g. unregister a sink, close a file.
        return cls(triggers=triggers, handler=handler)
    
    def do(self, state : S):
        if state in self.triggers:
            self.handler()