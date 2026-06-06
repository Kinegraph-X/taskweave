from typing import Callable 

from .session_control import SessionControl
from .session_manager import SessionManager
from .execution_registry import ExecutionRegistry, ParseError

class SessionGateway:
    def __init__(self):
        self._registry = ExecutionRegistry()
        self._control: SessionControl | None = None

    def submit(self, payload: dict) -> None:
        parsed = self._registry.parse_plan(payload)
        if isinstance(parsed, ParseError):
            raise parsed
        
        # TODO : ensure cancel_policy & observability_policy are enums in plan
        self._control = SessionManager.create(
            cancel_policy=parsed.plan.cancel_policy
        )
        
        # construit les PoolStrategy dans SessionControl
        for name, strategy in parsed.pools.pools.items():
            self._control.add_pool(name, strategy.max_parallel)
        
        self._stored_plan = payload
        self._control.execute(parsed.plan)

    def get_plan(self):
        return self._registry.get_json_plan(
            self._control.plan,
            self._control.pool_provider.execution_pools
        )