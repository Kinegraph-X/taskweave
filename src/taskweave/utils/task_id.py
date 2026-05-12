from typing import Any
from __future__ import annotations

class TaskId:
    def __init__(self, base: str):
        self._value = base
    
    def increment(self, suffix: Any) -> TaskId:
        self._value = f"{self._value}{str(suffix)}"
        return self
    
    def __str__(self) -> str:
        return f"{self._value}"