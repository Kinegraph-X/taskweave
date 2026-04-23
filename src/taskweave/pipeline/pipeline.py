import time
from uuid import uuid4
from typing import List, Set
from dataclasses import dataclass

from whisper_infer.snapshots import PipelineSnapshot
from whisper_infer.tasks import PipelineTask, Task
from whisper_infer.states import PipelineState

class Pipeline():
    def __init__(self, session_id : str = 'local'):
        self.id : str = uuid4().hex
        self.session_id = session_id
        self.tasks : List[PipelineTask] = []
        self._task_names : Set[str] = set()  # enforce local unicity
        self.state : PipelineState = PipelineState.PENDING
        self.currently_running : Task | None = None
        self.started_at : float = time.time()
        self.early_exit : bool = False

    def add_task(self, task_spec : Task):
        task = PipelineTask(task_spec, self.session_id)
        if task.name in self._task_names:
            raise ValueError(f"Task name '{task.name}' already exists in this pipeline")
        self._task_names.add(task.name)
        self.tasks.append(task)
        return 
    
    def snapshot(self) -> PipelineSnapshot:
        return PipelineSnapshot(
            id = self.id,
            tasks = {t.name: t.snapshot() for t in self.tasks},
            state=self.state,
            early_exit = self.early_exit,
            started_at=self.started_at,
            elapsed=time.time() - self.started_at if self.started_at else 0
        )