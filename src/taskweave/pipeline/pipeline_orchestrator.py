from typing import List, Callable

from .pipeline import Pipeline
from .runtime_pipeline import RuntimePipeline
from .execution_plan import ExecutionPlan

from taskweave.buses import ObservabilityContext
from taskweave.states import PipelineState, TaskState, FinalStatus
from taskweave.tasks import Task, PipelineTask, CancelPolicy, ExternalStrategy, PoolProvider
from taskweave.utils import TaskId, SinkContext
from taskweave.workers import TaskOutcome


class PipelineOrchestrator:
    def __init__(
        self,
        obs : ObservabilityContext,
        pool_provider : PoolProvider,
        cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY
    ):
        self.obs = obs
        self.pool_provider = pool_provider
        self.cancel_policy = cancel_policy

        self.pipelines : dict[TaskId, RuntimePipeline] = {}


    """ FROM PLAN """

    def execute_plan(
        self,
        session_id : TaskId,
        plan : ExecutionPlan
    ):
        self.cancel_policy = plan.cancel_policy
        for pipeline in plan.pipelines:
            self._hydrate_pipeline(
                session_id = session_id,
                pipeline = pipeline
            )

    def _hydrate_pipeline(
        self,
        session_id : TaskId,
        pipeline : Pipeline
    ):
        on_transition = lambda old, new, event: self.obs.emit(event)
        p = RuntimePipeline(
            id = pipeline.id,
            session_id = session_id,
            on_change = on_transition
        )

        for task in pipeline.tasks:
            task.name = self.obs.log_store.register(
                session_id = session_id,
                source_id = task.name
            )
            on_cleanup = self._handle_task_persistence(task)
            t = p.add_task(
                task_spec = task,
                on_change = on_transition,
                on_cleanup = on_cleanup
            )
            self.pool_provider.define_runner(t)

        self.pipelines[pipeline.id] = p

    def _handle_task_persistence(self, task_spec: Task) -> Callable:
        """
        This method connects LogProducer, RoutingPolicy and PersistBackend
        (Due to decoupling with the "workers" package, 
        tasks without specific producer are defaulted to LogEventProducer.)
        """
        if task_spec.backend:
            backend_runner = task_spec.backend.make_runner(
                source_id = str(task_spec.name),
                error_sink = self.obs.log_bus.emit_internal
            )
            task_spec.producer.make_sink(
                context = SinkContext(
                    source_id = str(task_spec.name),
                    backend = task_spec.backend
                )
            )
            self.obs._persist_registry.add_context(
                task_spec.name,
                backend_runner
            )
            def cleanup(): 
                self.obs.stream_writer.unregister_sink(
                    task_spec.name
                )
                task_spec.backend.close()
            return cleanup
        
        return lambda: None


    """ RESTARTS """

    def add_pipeline(
        self,
        session_id : TaskId,
        pipeline : Pipeline
    ) -> TaskId:
        self._hydrate_pipeline(
            session_id = session_id,
            pipeline = pipeline
        )
        return pipeline.id
    
    def add_task(self, pipeline_id : TaskId, task : Task, on_change : Callable, on_cleanup : Callable[[], None] | None):
        pipeline = self.pipelines[pipeline_id]
        pipeline.add_task(task, on_change, on_cleanup)


    """ COMMANDS """

    def start_pipeline(self, pipeline_id : TaskId):
        pipeline = self.pipelines[pipeline_id]
        self._next_task(pipeline, 0)
        pipeline.cycle.transition(PipelineState.RUNNING)

    def start_all_pipelines(self):
        for pipeline in self.pipelines.values():
            self.start_pipeline(pipeline.id)

    def stop_pipeline(self, pipeline_id : TaskId):
        pipeline = self.pipelines[pipeline_id]
        self._cleanup_pipeline(pipeline)

    def stop_all_pipelines(self):
        for pipeline in self.pipelines:
            self._cleanup_pipeline(pipeline)

    def stop_task(self, id : TaskId, pipeline : RuntimePipeline):
        pipeline_task = next(iter([t for t in pipeline.tasks if t.name == id]))
        pipeline_task._runner.cleanup(id)


    """ RUN PHASE """

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


    """ CALLBACKS """

    def _on_task_start(self, pipeline: RuntimePipeline, idx: int):
        task = pipeline.tasks[idx]
        task.cycle.transition(TaskState.RUNNING)

    def _on_task_success(self, pipeline: RuntimePipeline, idx: int):
        next_idx = idx + 1
        task = pipeline.tasks[idx]
        task._runner.cleanup(task.name)

        if task.on_finally:
            task.on_finally(
                TaskOutcome(
                    name = str(task.name),
                    status = FinalStatus.SUCCESS,
                    error = None
                )
            )

        task.cycle.transition(TaskState.SUCCESS)

        if next_idx >= len(pipeline.tasks):
            pipeline.cycle.transition(PipelineState.SUCCESS)
            return
        elif pipeline.tasks[next_idx].cycle.state == TaskState.CANCELED:
            # case of early exit with graceful stop
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

        task._runner.cleanup(task.name)

        for task in pipeline.tasks[idx + 1:]:
            task.cycle.transition(TaskState.CANCELED)


    """ CLEANUP """

    def _cleanup_pipeline(self, pipeline : RuntimePipeline):
        pipeline.cycle.transition(PipelineState.STOPPING)

        if self.cancel_policy == CancelPolicy.CANCEL_ALL:
            for task in pipeline.tasks:
                if (task.cycle.state in (TaskState.PENDING, TaskState.RUNNING)):
                    task._runner.cleanup(task.name)
                    cancel_reason = f"forcefully stopped due to early exit"

                if task.on_cancel:
                    task.on_cancel(
                        TaskOutcome(
                            name = str(task.name),
                            status = FinalStatus.CANCELED,
                            error = Exception(f"task canceled : {cancel_reason}")
                        )
                    )
            pipeline.cycle.transition(PipelineState.CANCELED)
        elif self.cancel_policy == CancelPolicy.CANCEL_PENDING_ONLY:
            for task in pipeline.tasks:
                if task.cycle.state == TaskState.PENDING:
                    task.cycle.transition(TaskState.CANCELED)
                    cancel_reason = f"was cancelable on requested graceful stop"

                if task.on_cancel:
                    task.on_cancel(
                        TaskOutcome(
                            name = str(task.name),
                            status = FinalStatus.CANCELED,
                            error = Exception(f"task canceled : {cancel_reason}")
                        )
                    )