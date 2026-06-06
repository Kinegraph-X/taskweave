from dataclasses import dataclass

from .session_control import SessionControl

from taskweave.pipeline import ExecutionPlan
from taskweave.tasks import CancelPolicy
from taskweave.buses import ObservabilityPolicy

@dataclass(kw_only = True)
class SessionManager:

    @staticmethod
    def create(
        cancel_policy : CancelPolicy | None = None,
        observability_policy : ObservabilityPolicy | None = None
    ):
        control = SessionControl(
            cancel_policy = cancel_policy,
            observability_policy = observability_policy
        )

    @staticmethod
    def from_plan(
        plan: ExecutionPlan
    ) -> SessionControl:
        control = SessionManager.create(
            cancel_policy = plan.cancel_policy,
            observability_policy = plan.observability_policy
        )
        # pré-enregistre les pools du plan
        for pool in plan.pools:
            control._pool_provider.add_pool(
                pool.pool_name,
                pool.max_parallel
            )
        return control