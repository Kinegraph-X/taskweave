from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class StrSerializable(Protocol):
    def __call__(self, increment : Any):
        pass
    def __str__(self) -> str:
        return ''