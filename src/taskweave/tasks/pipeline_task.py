import time
from typing import List, Callable, cast
from dataclasses import dataclass

from .task import Task
from .task_strategy import ExecutionStrategy, LocalProcessStrategy, SubprocessStrategy

from taskweave.snapshots import TaskSnapshot
from taskweave.states import TaskState, StateHandler, task_transitions
from taskweave.workers import WorkerManager
# from taskweave.states import WorkerContext
from taskweave.utils import StrSerializable

@dataclass
class PipelineTask:
    def __init__(
            self,
            task_spec : Task,
            on_change : Callable,
            session_id : str = 'local',
            on_cleanup : Callable[[], None] | None = None
        ):
        if isinstance(task_spec.name, StrSerializable):
            self.name = cast(StrSerializable, task_spec.name)(f"_{session_id}") # concatenated
        else:
            self.name = f"{task_spec.name}_{session_id}"
        # self.manager: WorkerManager | None = task_spec.manager
        self.cmd: List[str | StrSerializable] = task_spec.cmd
        self.strategy : ExecutionStrategy  = task_spec.strategy
        self.producer = task_spec.producer
        self.after_complete : Callable | None = task_spec.after_complete
        self.early_exit_on_success : Callable | None = task_spec.early_exit_on_success
        self.cancellable: bool = task_spec.cancellable
        # self.context: WorkerContext      # état métier
        self.state: TaskState = TaskState.PENDING
        self.handler = StateHandler(
            state = TaskState.PENDING,
            transitions = task_transitions,
            on_transition = on_change,
            cleanup = on_cleanup,
            cleanup_triggers = [TaskState.SUCCESS, TaskState.CANCELED, TaskState.FAILED]
            )
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