from typing import Callable, Protocol
import subprocess, threading
from time import time
from .pipeline_task import PipelineTask
from taskweave.workers import WorkerPool, WorkerManager, SubProcessManager

class ExecutionStrategy(Protocol):
    def __init__(self):
        raise NotImplementedError
    def run(self, task: PipelineTask, on_success: Callable, on_failure: Callable):
        raise NotImplementedError
    def cleanup(self, task: PipelineTask) -> None:
        raise NotImplementedError

class LocalProcessStrategy:
    def __init__(
            self,
            *,
            max_count = 4,
            manager : WorkerManager = WorkerManager()
        ):
        manager.max_count = max_count
        self.manager = manager

    def run(self, task, on_success, on_failure):
        task.started_at = time()
        self.manager.add_worker(task.name, task.cmd, on_success, on_failure)

    def cleanup(self, task: PipelineTask) -> None:
        self.manager.stop_worker(str(task.name))
        self.manager.remove_worker(str(task.name))

class SubprocessStrategy:
    manager : WorkerPool = SubProcessManager(source_id = "")
    def run(self, task, on_success, on_failure):
        task.started_at = time()
        self.manager.add_worker(task.name, task.cmd, on_success, on_failure)

    def cleanup(self, task: PipelineTask) -> None:
        self.manager.stop_worker(str(task.name))

class ExternalStrategy:
    """
    This could be implemented depending on your syncing strategy:
    progress file on disk, distant queue, socket synchronisation...
    """
    def run(self, task, on_success, on_failure):
        raise NotImplementedError