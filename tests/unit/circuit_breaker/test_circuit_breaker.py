import pytest
from time import time, sleep, monotonic

from taskweave.persist import BackendTransientFailure, BackendFatalError, CircuitBreaker

from taskweave_protocol import BackendErrorKind



def test_circuit_breaker():
    class persist_config:
        threshold = 5
        recovery_timeout = 1.0

    circuit_breaker = CircuitBreaker(
        config = persist_config()
    )

    def run():
        raise BackendTransientFailure(
            kind = BackendErrorKind.RATE_LIMITED,
            msg = "rate limited"
        )
    
    for i in range(0, 5):
        try:
            circuit_breaker.call(
                fn = run,
                args_list = []
            )
        except:
            pass
    
    assert circuit_breaker._is_open() == True

    circuit_breaker._open_since = monotonic() - circuit_breaker.config.recovery_timeout - 1.0

    assert circuit_breaker._is_open() == False


def test_circuit_breaker_raises():
    class persist_config:
        threshold = 5
        recovery_timeout = 1.0
    
    circuit_breaker = CircuitBreaker(
        config = persist_config()
    )

    def run():
        raise BackendTransientFailure(
            kind = BackendErrorKind.RATE_LIMITED,
            msg = "rate limited"
        )
    
    with pytest.raises(BackendTransientFailure) as excinfo1:
        for i in range(0, 5):
            circuit_breaker.call(
                fn = run,
                args_list = []
            )
        assert "rate limited" in str(excinfo1.value)

    with pytest.raises(BackendTransientFailure) as excinfo2:
        circuit_breaker.call(
            fn = run,
            args_list = []
        )
        assert "backend unavailable" in str(excinfo2.value)


def test_circuit_breaker_raises_fatal_and_raises_unavailable():
    class persist_config:
        threshold = 1
        recovery_timeout = 0.0
    
    circuit_breaker = CircuitBreaker(
        config = persist_config()
    )

    def run():
        raise BackendTransientFailure(
            kind = BackendErrorKind.OS_ERROR,
            msg = "os error"
        )
    
    with pytest.raises(BackendFatalError) as excinfo1:
        for i in range(0, 5):
            circuit_breaker.call(
                fn = run,
                args_list = []
            )
        assert "fatal error" in str(excinfo1.value)

    with pytest.raises(BackendTransientFailure) as excinfo2:
        circuit_breaker.call(
            fn = run,
            args_list = []
        )
        assert "backend unavailable" in str(excinfo2.value)
