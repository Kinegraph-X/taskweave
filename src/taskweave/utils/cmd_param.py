from typing import TypeVar, SupportsFloat
from __future__ import annotations
from .ref import Ref

T = TypeVar("T", bound = SupportsFloat)

class CmdParam(Ref[T]):
    def _init__(self, value : T):
        self._value = value

    def increment(self, increment) -> CmdParam:
        self._value += increment
        return self