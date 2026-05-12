from typing import Callable, Any
from dataclasses import dataclass, field
import time

from .circuit_breaker_config import CircuitBreakerConfig

class CircuitOpenError(RuntimeError):...

@dataclass(kw_only = True)
class CircuitBreaker:
    config : CircuitBreakerConfig = field(default = CircuitBreakerConfig.LOCAL)
    def __post_init__(
            self
            ):
        self._failures = 0
        self._threshold = self.config.threshold
        self._recovery_timeout = self.config.recovery_timeout
        self._open_since: float | None = None
    
    def call(self, *, fn: Callable, args_list : list[Any]) -> None:
        if self._is_open():
            raise CircuitOpenError("backend unavailable")
        try:
            fn(*args_list)
            self._failures = 0  # reset sur succès
        except Exception:
            self._failures += 1
            if self._failures >= self._threshold:
                self._open_since = time.monotonic()
            raise
    
    def _is_open(self) -> bool:
        if self._open_since is None:
            return False
        if time.monotonic() - self._open_since > self._recovery_timeout:
            self._open_since = None  # tentative de recovery
            return False
        return True