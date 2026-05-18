from typing import Callable, Any
from dataclasses import dataclass, field
import time

from .circuit_breaker_config import PersistConfig, CircuitBreakerConfig

class CircuitOpenError(RuntimeError):...
class TooManyFailuresError(RuntimeError):...

@dataclass(kw_only = True)
class CircuitBreaker:
    config : PersistConfig = field(default_factory = CircuitBreakerConfig.LOCAL.value)
    def __post_init__(
            self
            ):
        self._failures = 0
        self._threshold = self.config.threshold
        self._recovery_timeout = self.config.recovery_timeout
        self._open_since: float | None = None
    
    def call(self, *, fn: Callable, args_list : list[str]) -> None:
        if self._is_open():
            raise CircuitOpenError("backend unavailable")
        try:
            fn(*args_list)
            self._failures = 0  # reset on success
        except Exception as e:
            self._failures += 1
            if self._failures >= self._threshold:
                self._open_since = time.monotonic()
                raise TooManyFailuresError(f"{self._threshold} failures on circuit-breaker. Last is: {str(e)}")
    
    def _is_open(self) -> bool:
        if self._open_since is None:
            return False
        if time.monotonic() - self._open_since > self._recovery_timeout:
            self._open_since = None  # recovery attempt succeeded
            return False
        return True