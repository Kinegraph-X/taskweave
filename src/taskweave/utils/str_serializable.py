from typing import Protocol, runtime_checkable

@runtime_checkable
class StrSerializable(Protocol):
    def __call__(self):
        pass
    def __str__(self) -> str:
        return ''