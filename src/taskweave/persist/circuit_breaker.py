from typing import Callable, Any
from dataclasses import dataclass, field
import time

from .backend_exception import BackendException, BackendTransientFailure, BackendFatalError

from taskweave.utils import PersistConfig, CircuitBreakerConfig

from taskweave_protocol import BackendErrorKind

class CircuitOpenError(RuntimeError):...
class TooManyFailuresError(RuntimeError):...

@dataclass(kw_only = True)
class CircuitBreaker:
    """
    Considers the set of BackendFailureKinds is definitive.
    Would require an injectable conversion map to discriminate transient & fatal
    """
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
            raise BackendTransientFailure(
                kind = BackendErrorKind.CIRCUIT_OPEN,
                msg = "backend unavailable"
            )
        try:
            fn(*args_list)
            self._failures = 0  # reset on success
        except BackendException as e:
            self._failures += 1
            
            if self._failures >= self._threshold:
                    self._open_since = time.monotonic()

            if e.kind == BackendErrorKind.QUEUE_FULL:
                # may be considered transient (network) of not (disk)
                if self.config.retry_on_queue_full:
                    raise BackendTransientFailure(
                    kind = e.kind,
                    msg = f"{self._threshold} failures on circuit-breaker. Last is: {str(e)}"
                )
                else:
                    raise BackendFatalError(
                        kind = e.kind,
                        msg = f"fatal error in circuit-breaker: {e.msg}"
                    )
            if e.kind in (
                    # Transient — circuit breaker waits for recovery
                    BackendErrorKind.RATE_LIMITED,
                    BackendErrorKind.UNAVAILABLE,
                    BackendErrorKind.TIMEOUT,
                    BackendErrorKind.UNKNOWN
            ):
                # may be a bit verbose to re-raise,
                # but the implem of the backend and the client decides
                raise BackendTransientFailure(
                    kind = e.kind,
                    msg = f"{self._threshold} failures on circuit-breaker. Last is: {str(e)}"
                )
            elif e.kind in (
                # Permanent — circuit breaker raiss immediadelty BACKEND_FATAL_ERROR
                BackendErrorKind.BAD_REQUEST,
                BackendErrorKind.UNAUTHORIZED,
                BackendErrorKind.OS_ERROR,
                BackendErrorKind.THREAD_DIED # risk of double messaging -> test
            ):
                raise BackendFatalError(
                    kind = e.kind,
                    msg = f"fatal error in circuit-breaker: {e.msg}"
                )
    
    def _is_open(self) -> bool:
        if self._open_since is None:
            return False
        if time.monotonic() - self._open_since > self._recovery_timeout:
            self._open_since = None  # recovery attempt succeeded
            return False
        return True