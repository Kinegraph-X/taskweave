from typing import Callable
import subprocess, threading
from .pipeline_task import PipelineTask

class ExecutionStrategy:
    def run(self, task: PipelineTask, on_success: Callable, on_failure: Callable):
        raise NotImplementedError

class LocalProcessStrategy(ExecutionStrategy):
    def run(self, task, on_success, on_failure):
        task.manager.add_worker(task.name, task.cmd, on_success, on_failure)

class SubprocessStrategy(ExecutionStrategy):
    def run(self, task, on_success, on_failure):
        threading.Thread(
            target=self._run,
            args=(task, on_success, on_failure),
            daemon=True
        ).start()

    def _run(self, task, on_success, on_failure):
        result = subprocess.run(task.cmd)
        on_success() if result.returncode == 0 else on_failure()

class ExternalStrategy(ExecutionStrategy):
    """
    This Must be implemented depending on your syncing strategy:
    progress file on disk, distant queue, socket synchronisation
    """
    def run(self, task, on_success, on_failure):
        raise NotImplementedError