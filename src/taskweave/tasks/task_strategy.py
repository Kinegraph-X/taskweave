from typing import Callable, Protocol
from dataclasses import dataclass, field
from queue import Queue

from .task_runner import TaskRunner, PoolTaskRunner, SubprocessTaskRunner
from .execution_context import ExecutionContext, PoolExecutionContext, SynchronousExecutionContext

from taskweave.utils import TaskId
from taskweave.workers import SubProcessManager
from taskweave.buses import MiniBus
from taskweave.info_stream import StreamWriter

class ExecutionStrategy(Protocol):
    def _get_runner(
            self,
            context : ExecutionContext
        ) -> TaskRunner:
        raise NotImplementedError


@dataclass(kw_only = True)
class PoolStrategy:
    pool_name : str
    max_parallel : int
    def _get_runner(
            self,
            context : PoolExecutionContext
        ) -> TaskRunner:
        return context.pools[self.pool_name]

@dataclass(kw_only = True)
class SynchronousStrategy:
    def _get_runner(
            self,
            context : SynchronousExecutionContext
        ) -> TaskRunner:
        manager = SubProcessManager(
            source_id = str(context.source_id),
            log_bus = context.event_bus
        )
        return SubprocessTaskRunner(manager = manager)

@dataclass(kw_only = True)
class ExternalStrategy:
    """
    This could be implemented depending on your syncing strategy:
    progress file on disk, distant queue, socket synchronisation...
    """
    def _get_runner(
            self,
            context : ExecutionContext
        ) -> None:
        return None # -> ExternalRunner