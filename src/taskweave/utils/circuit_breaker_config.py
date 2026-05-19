from typing import Protocol
from dataclasses import dataclass
from enum import Enum

class PersistConfig(Protocol):
    threshold : int
    recovery_timeout : float
    retry_on_queue_full : bool

@dataclass(kw_only = True)
class PersistConfigLocal:
    threshold : int = 1
    recovery_timeout : float = 0.0
    retry_on_queue_full : bool = False

@dataclass(kw_only = True)
class PersistConfigNetwork:
    threshold : int = 5
    recovery_timeout : float = 30.0
    retry_on_queue_full : bool = True

class CircuitBreakerConfig(Enum):
    LOCAL = PersistConfigLocal
    NETWORK = PersistConfigNetwork