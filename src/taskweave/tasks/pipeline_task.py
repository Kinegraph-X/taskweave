import time
from typing import List, Callable, cast
from dataclasses import dataclass

from .pool_provider import PoolProvider
from .task import Task
from .task_strategy import TaskRunner, ExecutionStrategy, PoolTaskRunner, SubprocessTaskRunner
from .task_runner import TaskRunner, SubprocessTaskRunner

from taskweave.messages import LogProducer
from taskweave.snapshots import TaskSnapshot
from taskweave.states import TaskState, TaskLifecycle, CleanupStrategy, task_transitions
from taskweave.utils import TaskId, CmdParam

class PipelineTask:
    def __init__(
            self,
            task_spec : Task,
            on_change : Callable,
            session_id : TaskId,
            on_cleanup : Callable[[], None] | None = None
        ):
        self.name : TaskId = task_spec.name
        self.cmd: List[CmdParam] = [cmd if isinstance(cmd, CmdParam) else CmdParam(cmd) for cmd in task_spec.cmd]
        self.strategy : ExecutionStrategy  = task_spec.strategy
        self._runner : TaskRunner = SubprocessTaskRunner() # default constructed for type-checking, but must be explicitly assigned

        self.producer : LogProducer = task_spec.producer
        
        self.on_success : Callable | None = task_spec.on_success
        self.on_failure : Callable | None = task_spec.on_failure
        self.on_cancel : Callable | None = task_spec.on_cancel
        self.on_finally : Callable | None = task_spec.on_finally
        
        if on_cleanup is not None:
            self.cycle = TaskLifecycle(
                source_id = self.name,
                transitions = task_transitions,
                on_transition = on_change,
                cleanup = CleanupStrategy.on_end(
                    handler = on_cleanup,
                    triggers = [TaskState.SUCCESS, TaskState.CANCELED, TaskState.FAILED]
                )
            )
        else:
            self.cycle = TaskLifecycle(
                source_id = self.name,
                transitions = task_transitions,
                on_transition = on_change
            )


    def snapshot(self):
        return TaskSnapshot(
            self.name,
            self.cycle.state.value,
            self.cycle.started_at,
            time.time() - self.cycle.started_at if self.cycle.started_at else 0,
            self.last_error
        )