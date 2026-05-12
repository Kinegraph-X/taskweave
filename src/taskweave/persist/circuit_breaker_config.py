from typing import Protocol
from dataclasses import dataclass
from enum import Enum

class PersistConfig(Protocol):
    threshold : int
    recovery_timeout : float

@dataclass(kw_only = True)
class PersistConfigLocal:
    threshold : int = 1
    recovery_timeout : float = 10.0

@dataclass(kw_only = True)
class PersistConfigNetwork:
    threshold : int = 5
    recovery_timeout : float = 30.0

class CircuitBreakerConfig(Enum):
    LOCAL = PersistConfigLocal()
    NETWORK = PersistConfigNetwork()