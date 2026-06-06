from typing import Callable
from time import sleep
import os

from .session import Session
from .submission_type import SubmissionType

from taskweave.context import Config, get_app_context
config, constants, args = get_app_context()

from taskweave.pipeline import PipelineOrchestrator, ObservabilityContext, ExecutionPlan
from taskweave.states import SessionState, TaskState
from taskweave.snapshots import SessionSnapshot
from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.tasks import CancelPolicy, PoolProvider, PoolStrategy
from taskweave.utils import TaskId

from taskweave_protocol import ControlCommand


class SessionControl:
    def __init__(
        self,
        cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY,
        observability_policy : ObservabilityPolicy = ObservabilityPolicy.SAFE
    ):
        self.obs = ObservabilityContext(
            snapshot_getter = self.snapshot,
            observability_policy = observability_policy
        )

        self.pool_provider = PoolProvider(
            _log_bus = self.obs.log_bus
        )
        
        self.orchestrator = PipelineOrchestrator(
            obs = self.obs,
            pool_provider = self.pool_provider,
            cancel_policy = cancel_policy
        )
    
        self.session = Session(
            pipelines = self.orchestrator.pipelines
        )

        self._plan = ExecutionPlan()

    def add_pool(self, pool_name = str, max_parallel = int) -> PoolStrategy:
        return self.pool_provider.add_pool(
            pool_name = pool_name,
            max_parallel = max_parallel
        )

    def execute(self, plan: ExecutionPlan) -> None:
        self._plan = plan
        self.orchestrator.execute_plan(
            session_id = self.session.id,
            plan = plan
        )
        self.session.cycle.transition(SessionState.RUNNING)

    def stop(self) -> None:
        self.session.cycle.transition(SessionState.STOPPING)
        self.orchestrator.stop_all_pipelines()
        self.session.cycle.transition(SessionState.CANCELED)

    def stop_pipeline(self, pipeline_id) -> None:
        self.orchestrator.stop_pipeline(pipeline_id)

    def _wait_for_stop(self) -> None:
        while any(
            t.cycle.state == TaskState.RUNNING
                for p in self.orchestrator.pipelines.values()
                    for t in p.tasks
        ):
            sleep(0.5)

        
        self.obs.emit(
            self.session.cycle.transition(SessionState.SUCCESS)
        )

    def snapshot(self) -> SessionSnapshot:
        return self.session.snapshot()
    
    def send_command(self, cmd: ControlCommand) -> None: ...

    def ensure_safe_context(self):
        os.makedirs(constants.log_dir, exist_ok = True)