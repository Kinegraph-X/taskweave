from typing import Protocol, runtime_checkable

@runtime_checkable
class StrSerializable(Protocol):
    def __str__(self) -> str:
        return ''