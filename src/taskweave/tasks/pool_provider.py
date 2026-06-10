from dataclasses import dataclass, field

from .pipeline_task import PipelineTask
from .task_strategy import PoolStrategy
from .task_runner import PoolTaskRunner, TaskRunner
from .execution_context import ExecutionPool

from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.workers import WorkerManager


@dataclass(kw_only = True)
class PoolProvider:
    _execution_pools : dict[str, TaskRunner] = field(default_factory = dict)
    _log_bus : MiniBus

    def add_pool(self, pool_name : str, max_parallel : int = 4) -> PoolStrategy:
        """
        pools are a parallelization/synchronization mecanism
        The user defines Task.strategy, PipelineOrchestrator makes the glue
        """
        manager = WorkerManager(
            max_count = max_parallel,
            log_bus = self._log_bus
        )
        self._execution_pools[pool_name] = PoolTaskRunner(manager = manager)
        return PoolStrategy(
            pool_name = pool_name,
            max_parallel = max_parallel
            )

    def define_runner(self, task : PipelineTask) -> None :
        """
        Pool tasks have the same _runner.
        Each synchronous task has a _runner which mimics PoolRunner.
        TaskRunner(Protocol) -> (TaskPoolRunner, SubprocessTaskRunner, NoOpRunner)
        -> get_runner() consumes what's needed 
        """
        context = ExecutionPool(
            source_id = task.name,
            pools = self._execution_pools,
            event_bus = self._log_bus
        )
        task._runner = task.strategy._get_runner(
            context = context
        )