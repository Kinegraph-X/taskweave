from typing import List, Callable
import threading, subprocess
from time import time

from .pipeline import Pipeline

from taskweave.states import PipelineState, TaskState
from taskweave.tasks import Task, CancelPolicy, ExternalStrategy
from taskweave.session import SessionManager, Session
from taskweave.messages import LogEvent, MsgType

class PipelineOrchestrator:
    def __init__(
            self,
            session_id : str,
            on_pipeline_failure : Callable[[str, str], None],
            cancel_policy=CancelPolicy.CANCEL_PENDING_ONLY
            ):
        self._on_pipeline_failure = on_pipeline_failure
        self.pipelines : List[Pipeline] = []
        self.cancel_policy = cancel_policy
        self._early_exit = threading.Event()
        self._sink : Callable | None = None

    def add_pipeline(self, pipeline : Pipeline):
        self.pipelines.append(pipeline)
        return pipeline.id
    
    def add_task(self, pipeline_id : str, task : Task, on_change : Callable):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'add_task() on non-existing pipeline. pipeline_id is {pipeline_id}')
        pipeline.add_task(task, on_change)

    def start_pipeline(self, pipeline_id : str):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'start_pipeline() on non-existing pipeline. pipeline_id is {pipeline_id}')
        pipeline.started_at = time()
        self._next_task(pipeline, 0)
        pipeline.handler.transition(PipelineState.RUNNING)

    def start_all_pipelines(self):
        for pipeline in self.pipelines:
            self._next_task(pipeline, 0)
            pipeline.handler.transition(PipelineState.RUNNING)

    def stop_pipeline(self, pipeline_id : str):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'start_pipeline() on non-existing pipeline. pipeline_id is {pipeline_id}')
        
        self._cleanup_pipeline(pipeline)

    def _next_task(self, pipeline, idx):
        if idx >= len(pipeline.tasks):
            pipeline.handler = PipelineState.DONE
            return

        task = pipeline.tasks[idx]
        task.handler.transition(TaskState.RUNNING)

        task.strategy.run(
            task,
            on_success=lambda: self._on_task_success(pipeline, idx),
            on_failure=lambda: self._on_task_failure(pipeline, idx)
        )

        # allow external syncing mechanism : all tasks may be run simultaneously
        if isinstance(task.strategy, ExternalStrategy):
            self._next_task(pipeline, idx + 1)

    def _on_task_success(self, pipeline: Pipeline, idx: int):
        next_idx = idx + 1

        task = pipeline.tasks[idx]
        task.strategy.cleanup(task)

        # first check if early_exit has bee trigger meanwhile
        if self._early_exit.is_set():
            return

        if task.after_complete:
            task.after_complete(task.name)

        task.handler.transition(TaskState.SUCCESS)

        if callable(task.early_exit_on_success):
            if task.early_exit_on_success():
                self.early_exit()
                return
        elif task.early_exit_on_success:
            self.early_exit()
            return

        if next_idx >= len(pipeline.tasks):
            pipeline.handler.transition(PipelineState.SUCCESS)
            return

        self._next_task(pipeline, next_idx)

    def _on_task_failure(self, pipeline: Pipeline, idx: int):
        task = pipeline.tasks[idx]
        task.handler.transition(TaskState.FAILED)
        pipeline.handler.transition(PipelineState.FAILED)
        self._on_pipeline_failure(pipeline.id, f'task {task.name} failed')

        task.strategy.cleanup(task)
        for task in pipeline.tasks[idx + 1:]:
            if task.cancellable:
                task.handler.transition(TaskState.CANCELED)
                return

    def early_exit(self):
        self._early_exit.set()
        for pipeline in self.pipelines:
            self._cleanup_pipeline(pipeline, is_early_exit=True)
            pipeline.early_exit = True

    def graceful_stop(self):
        for pipeline in self.pipelines:
            self._cleanup_pipeline(pipeline.id)

    def _cleanup_pipeline(self, pipeline, is_early_exit = False):
        # cancel pending tasks, let running tasks go to end
        for task in pipeline.tasks:
            if task.state == TaskState.PENDING and task.cancellable:
                task.handler.transition(TaskState.CANCELED)
            elif (task.state == TaskState.RUNNING
                    and self.cancel_policy == CancelPolicy.CANCEL_ALL):
                task.strategy.cleanup(task)

        if self.cancel_policy == CancelPolicy.CANCEL_ALL:
            if is_early_exit:
                pipeline.handler.transition(PipelineState.EARLY_EXIT)
            else:
                pipeline.handler.transition(PipelineState.CANCELLED)
        else:
            pipeline.handler.transition(PipelineState.STOPPING)