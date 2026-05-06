from typing import Callable, Protocol
from dataclasses import dataclass, field
import subprocess, threading
from time import time
from taskweave.utils import StrSerializable
from taskweave.workers import WorkerPool, WorkerManager, SubProcessManager
from taskweave.messages import LogProducer


class TaskRunner(Protocol):
    manager : WorkerPool
    def __post_init__(self):
        raise NotImplementedError
    def run(self, *, task_name: str | StrSerializable, task_cmd : list[str | StrSerializable], log_producer : LogProducer, on_success: Callable, on_failure: Callable, on_cancel : Callable):
        raise NotImplementedError
    def cleanup(self, task_name: str | StrSerializable) -> None:
        raise NotImplementedError

@dataclass(kw_only = True)
class PoolTaskRunner:
    max_parallel: int = field(default = 4)
    manager: WorkerManager = field(default_factory=WorkerManager)

    def __post_init__(self):
        self.manager.max_count = self.max_parallel

    def run(
            self,
            *,
            task_name : str | StrSerializable,
            task_cmd : list[str | StrSerializable],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable
        ):
        self.manager.add_worker(
            name = str(task_name),
            args_list = [str(cmd) for cmd in task_cmd],
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure,
            on_cancel = on_cancel
        )

    def cleanup(
            self,
            task_name: str | StrSerializable
        ) -> None:
        self.manager.stop_worker(str(task_name))
        self.manager.remove_worker(str(task_name))

@dataclass(kw_only = True)
class SubprocessTaskRunner:
    manager : WorkerPool = field(default_factory = SubProcessManager)
    def run(
            self,
            *,
            task_name : str | StrSerializable,
            task_cmd : list[str | StrSerializable],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable
        ):
        self.manager.add_worker(
            name = str(task_name),
            args_list = [str(cmd) for cmd in task_cmd],
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure,
            on_cancel  = on_cancel
        )

    def cleanup(
            self,
            task_name: str | StrSerializable
        ) -> None:
        self.manager.stop_worker(str(task_name))

class ExternalStrategy:
    """
    This could be implemented depending on your syncing strategy:
    progress file on disk, distant queue, socket synchronisation...
    """
    def run(self, task, on_success, on_failure):
        raise NotImplementedError


@dataclass
class NoOpRunner:
    manager : WorkerPool = field(default_factory = WorkerPool)
    def run(
            self,
            *,
            task_name : str | StrSerializable,
            task_cmd : list[str | StrSerializable],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable
        ):
        raise NotImplementedError(
            "Task must be submitted to a SessionManager/Orchestrator before execution"
        )

    def cleanup(
            self,
            task_name: str | StrSerializable
        ) -> None:
        raise NotImplementedError(
            "Task must be submitted to a SessionManager/Orchestrator before execution"
        )
    


class ExecutionStrategy(Protocol):
    def make_runner(self, pools : dict[str, TaskRunner]):
        raise NotImplementedError

@dataclass(kw_only = True)
class PoolStrategy:
    pool_name : str
    def make_runner(self, pools : dict[str, TaskRunner]):
        return pools[self.pool_name]

@dataclass(kw_only = True)
class SynchronousStrategy:
    def make_runner(self, pools : dict[str, TaskRunner]):
        return SubprocessTaskRunner()