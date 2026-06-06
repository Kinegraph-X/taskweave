import time
from uuid import uuid4
from typing import List, Set, Callable
from dataclasses import dataclass

from taskweave.snapshots import PipelineSnapshot
from taskweave.tasks import PipelineTask, Task
from taskweave.states import PipelineState, PipelineLifecycle, pipeline_transitions
from taskweave.utils import TaskId

class RuntimePipeline():
    def __init__(
            self,
            id : TaskId,
            session_id : TaskId,
            on_change : Callable
        ):
        self.id = id
        self.session_id = session_id
        self.tasks : List[PipelineTask] = []
        self._task_names : Set[TaskId] = set()  # enforce local unicity
        self.cycle = PipelineLifecycle(
            source_id = self.id,
            transitions = pipeline_transitions,
            on_transition = on_change
        )
        self.early_exit : bool = False

    def add_task(self, task_spec : Task, on_change : Callable, on_cleanup : Callable[[], None] | None = None):
        task = PipelineTask(task_spec, on_change, self.session_id, on_cleanup)
        if task.name in self._task_names:
            raise ValueError(f"Task name '{task.name}' already exists in this pipeline")
        self._task_names.add(task.name)
        self.tasks.append(task)
        return task
    
    def snapshot(self) -> PipelineSnapshot:
        return PipelineSnapshot(
            id = str(self.id),
            session_id = str(self.session_id),
            tasks = {str(t.name) : t.snapshot() for t in self.tasks},
            state=self.cycle.state.value,
            early_exit = self.early_exit,
            started_at=self.cycle.started_at,
            elapsed=time.time() - self.cycle.started_at if self.cycle.started_at else 0
        )