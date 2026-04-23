import time
from typing import List, Callable
from dataclasses import dataclass

from .task import Task
from .task_strategy import ExecutionStrategy, LocalProcessStrategy, SubprocessStrategy

from whisper_infer.snapshots import TaskSnapshot
from whisper_infer.states import TaskState
from whisper_infer.workers import WorkerManager
from whisper_infer.states import WorkerContext
from whisper_infer.utils import StrSerializable

@dataclass
class PipelineTask:
    def __init__(self, task_spec : Task, session_id : str = 'local'):
        session_prefix = session_id[:6]
        self.name = f"{session_prefix}_{task_spec.name}"
        self.manager: WorkerManager | None = task_spec.manager
        self.cmd: List[str | StrSerializable] = task_spec.cmd
        self.strategy : ExecutionStrategy  = LocalProcessStrategy()
        self.after_complete : Callable | None = task_spec.after_complete
        self.early_exit_on_success : bool | Callable = task_spec.early_exit_on_success
        self.cancellable: bool = task_spec.cancellable
        self.context: WorkerContext      # état métier
        self.state: TaskState = TaskState.PENDING
        self.started_at : float = time.time()
        self.last_error : str = ''
        self.on_success: Callable | None = None
        self.on_failure: Callable | None = None
        self.on_cancel: Callable | None = None

    def snapshot(self):
        return TaskSnapshot(
            self.name,
            self.state,
            self.started_at,
            time.time() - self.started_at if self.started_at else 0,
            self.last_error
        )