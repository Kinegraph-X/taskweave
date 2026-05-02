from typing import Callable, Protocol
from dataclasses import dataclass, field
import subprocess, threading
from time import time
from taskweave.utils import StrSerializable
from taskweave.workers import WorkerPool, WorkerManager, SubProcessManager
from taskweave.messages import LogProducer

class ExecutionStrategy(Protocol):
    manager : WorkerPool
    def __init__(self):
        raise NotImplementedError
    def run(self, *, task_name: str | StrSerializable, task_cmd : list[str | StrSerializable], log_producer : LogProducer, on_success: Callable, on_failure: Callable):
        raise NotImplementedError
    def cleanup(self, task_name: str | StrSerializable) -> None:
        raise NotImplementedError



@dataclass
class LocalProcessStrategy:
    max_count: int = 4
    manager: WorkerManager = field(default_factory=WorkerManager)

    def __post_init__(self):
        self.manager.max_count = self.max_count

    def run(
            self,
            *,
            task_name : str | StrSerializable,
            task_cmd : list[str | StrSerializable],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable
        ):
        self.manager.add_worker(
            name = task_name,
            args_list = task_cmd,
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure
        )

    def cleanup(
            self,
            task_name: str | StrSerializable
        ) -> None:
        self.manager.stop_worker(str(task_name))
        self.manager.remove_worker(str(task_name))

@dataclass
class SubprocessStrategy:
    manager : WorkerPool = field(default_factory = SubProcessManager)
    def run(
            self,
            *,
            task_name : str | StrSerializable,
            task_cmd : list[str | StrSerializable],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable
        ):
        self.manager.add_worker(
            name = task_name,
            args_list = task_cmd,
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure
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