import pytest
from time import sleep

from taskweave.utils import CircuitBreaker

class test_persist_config:
    threshold = 5
    recovery_timeout = 1.0

def test_circuit_breaker():
    persist_config = test_persist_config()
    circuit_breaker = CircuitBreaker(
        config = persist_config
    )

    def run():
        raise RuntimeError()
    
    try:
        for i in range(0, 5):
            circuit_breaker.call(
                fn = run,
                args_list = []
            )
    except:
        pass
    

    assert circuit_breaker._is_open() == True

    sleep(persist_config.recovery_timeout + 1.0)

    assert circuit_breaker._is_open() == False

def test_circuit_breaker_raises():
    persist_config = test_persist_config()
    circuit_breaker = CircuitBreaker(
        config = persist_config
    )

    def run():
        raise RuntimeError()
    
    with pytest.raises(Exception) as excinfo1:
        for i in range(0, 5):
            circuit_breaker.call(
                fn = run,
                args_list = []
            )
        assert "failures" in str(excinfo1.value)

    with pytest.raises(Exception) as excinfo2:
        circuit_breaker.call(
            fn = run,
            args_list = []
        )
        assert "backend unavailable" in str(excinfo2.value)