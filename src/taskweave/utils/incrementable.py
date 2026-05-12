from typing import Protocol, Any
from __future__ import annotations

class Incrementable(Protocol):
    def increment(self, value: Any) -> Incrementable: ...