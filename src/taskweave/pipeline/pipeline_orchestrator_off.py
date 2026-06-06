from typing import List, Callable
import threading, subprocess
from time import time

from .pipeline import Pipeline
from .runtime_pipeline import RuntimePipeline

from taskweave.states import PipelineState, TaskState
from taskweave.tasks import Task, PipelineTask, CancelPolicy, ExternalStrategy
from taskweave.utils import TaskId
from taskweave.workers import TaskOutcome, FinalStatus

class PipelineOrchestrator:
    def __init__(
            self,
            on_pipeline_failure : Callable[[str, str], None],
            cancel_policy=CancelPolicy.CANCEL_PENDING_ONLY
            ):
        self._on_pipeline_failure = on_pipeline_failure
        self.pipelines : List[RuntimePipeline] = []
        self.cancel_policy = cancel_policy
        self._early_exit = threading.Event()
        self._sink : Callable | None = None

    def add_pipeline(self, pipeline : Pipeline) -> TaskId:
        self.pipelines.append(pipeline)
        return pipeline.id
    
    def add_task(self, pipeline_id : TaskId, task : Task, on_change : Callable, on_cleanup : Callable[[], None] | None):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'add_task() on non-existing pipeline. pipeline_id is {pipeline_id}')
        pipeline.add_task(task, on_change, on_cleanup)

    def start_pipeline(self, pipeline_id : TaskId):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'start_pipeline() on non-existing pipeline. pipeline_id is {pipeline_id}')
        self._next_task(pipeline, 0)
        pipeline.cycle.transition(PipelineState.RUNNING)

    def start_all_pipelines(self):
        for pipeline in self.pipelines:
            self._next_task(pipeline, 0)
            pipeline.cycle.transition(PipelineState.RUNNING)

    def stop_pipeline(self, pipeline_id : TaskId):
        pipeline = next((p for p in self.pipelines if p.id == pipeline_id), None)
        if not pipeline:
            raise ValueError(f'start_pipeline() on non-existing pipeline. pipeline_id is {pipeline_id}')
        
        self._cleanup_pipeline(pipeline)

    def _run_task(self, pipeline : RuntimePipeline, task : PipelineTask, idx : int):
        task._runner.run(
            task_name = task.name,
            task_cmd = task.cmd,
            log_producer = task.producer,
            on_start = lambda: self._on_task_start(pipeline, idx),
            on_success = lambda: self._on_task_success(pipeline, idx),
            on_failure = lambda: self._on_task_failure(pipeline, idx),
            on_cancel = lambda: task.on_cancel() if task.on_cancel else None
        )

    def _next_task(self, pipeline, idx):
        if idx >= len(pipeline.tasks):
            pipeline.cycle = PipelineState.DONE
            return

        task = pipeline.tasks[idx]

        self._run_task(pipeline, task, idx)

        # allow external syncing mechanism : all tasks may be run simultaneously
        if isinstance(task._runner, ExternalStrategy):
            self._next_task(pipeline, idx + 1)

    def _on_task_start(self, pipeline: RuntimePipeline, idx: int):
        task = pipeline.tasks[idx]
        task.cycle.transition(TaskState.RUNNING)

    def _on_task_success(self, pipeline: RuntimePipeline, idx: int):
        next_idx = idx + 1
        task = pipeline.tasks[idx]
        task._runner.cleanup(task.name)
        
        # first check if early_exit has bee trigger meanwhile
        if self._early_exit.is_set():
            return
        
        if task.on_finally:
            task.on_finally(
                TaskOutcome(
                    name = str(task.name),
                    status = FinalStatus.SUCCESS,
                    error = None
                )
            )

        task.cycle.transition(TaskState.SUCCESS)

        if callable(task.early_exit_on_success):
            if task.early_exit_on_success():
                self.early_exit()
                return
    
        if next_idx >= len(pipeline.tasks):
            pipeline.cycle.transition(PipelineState.SUCCESS)
            return
        elif task.cycle.state == TaskState.CANCELED:
            pipeline.cycle.transition(PipelineState.CANCELED)
            return

        self._next_task(pipeline, next_idx)

    def _on_task_failure(self, pipeline: RuntimePipeline, idx: int):
        task = pipeline.tasks[idx]
        task.cycle.transition(TaskState.FAILED)
        pipeline.cycle.transition(PipelineState.FAILED)

        if task.on_finally:
            task.on_finally(
                TaskOutcome(
                    name = str(task.name),
                    status = FinalStatus.FAILURE,
                    error = RuntimeError("see task logs")
                )
            )

        self._on_pipeline_failure(str(pipeline.id), f'task {task.name} failed')

        task._runner.cleanup(task.name)
        for task in pipeline.tasks[idx + 1:]:
            if task.cancellable:
                task.cycle.transition(TaskState.CANCELED)
                return

    def early_exit(self):
        self._early_exit.set()
        for pipeline in self.pipelines:
            self._cleanup_pipeline(pipeline, is_early_exit=True)
            pipeline.early_exit = True

    def graceful_stop(self):
        for pipeline in self.pipelines:
            self._cleanup_pipeline(pipeline)

    def _cleanup_pipeline(self, pipeline : RuntimePipeline, is_early_exit = False):
        pipeline.cycle.transition(PipelineState.STOPPING)
        # cancel pending tasks, let running tasks go to end
        for task in pipeline.tasks:
            if task.state == TaskState.PENDING and task.cancellable:
                task.cycle.transition(TaskState.CANCELED)
                cancel_reason = f"was cancelable on {'requested graceful stop' if not is_early_exit else 'early exit'}"
            elif (task.state == TaskState.RUNNING
                    and self.cancel_policy == CancelPolicy.CANCEL_ALL):
                task._runner.cleanup(task.name)
                cancel_reason = f"forcefully stopped due to {'requested graceful stop' if not is_early_exit else 'early exit'}"
            if task.on_cancel:
                task.on_cancel(
                    TaskOutcome(
                        name = str(task.name),
                        status = FinalStatus.CANCELED,
                        error = Exception(f"task canceled : {cancel_reason}")
                    )
                )

        if self.cancel_policy == CancelPolicy.CANCEL_ALL:
            pipeline.cycle.transition(PipelineState.CANCELED)