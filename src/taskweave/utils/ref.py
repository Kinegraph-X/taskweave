from typing import Generic, TypeVar, SupportsFloat

T = TypeVar("T", bound=SupportsFloat)

class Ref(Generic[T]):
    def __init__(self, value: T):
        self._value = value
    
    def set(self, value: T) -> None:
        self._value = value
    
    def get(self) -> T:
        return self._value
    
    def __str__(self) -> str:
        return str(self._value)
    
    def __int__(self) -> int:
        return int(self._value)  # type: ignore
    
    def __float__(self) -> float:
        return float(self._value)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ref):
            return self._value == other._value
        if isinstance(other, type(self._value)):
            return self._value == other  # same type → direct comparison
        return NotImplemented