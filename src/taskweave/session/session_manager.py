from typing import cast, Callable
import os, threading
from queue import Queue
from uuid import uuid4
from time import time, sleep
from .session import Session
from taskweave.context import Config, get_app_context
config, constants, args = get_app_context()
from taskweave.persist import PersistRegistry, FileBackendRunner
from taskweave.snapshots import PipelineFailure
from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.info_stream import StreamWriter, SinkScope
from taskweave.snapshots import SessionSnapshot
from taskweave.pipeline import PipelineOrchestrator, Pipeline
from taskweave.tasks import CancelPolicy, Task, PoolStrategy, PoolTaskRunner, TaskRunner, ExecutionPool
from taskweave.messages import MsgType, LogEvent, SourceType
from taskweave.states import SessionState, TaskState, PipelineState
from taskweave.workers import WorkerPool, WorkerManager, SubProcessManager
from taskweave.logging import LogStore
from taskweave.utils import TaskId

class SessionManager:
    def __init__(
            self,
            *,
            config : Config | None = None,
            on_event : Callable | None = None,
            cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY,
            observability_policy : ObservabilityPolicy = ObservabilityPolicy.RELAXED
        ):
        self.ensure_context_safe()
        self.session = Session(
            # config.media_path,
            # config.keywords,
        )
        self.orchestrator = PipelineOrchestrator(
            str(self.session.id),
            self.log_failure,
            cancel_policy
        )
        self.session.pipelines = self.orchestrator.pipelines
        self._execution_pools : dict[str, TaskRunner] = {}
        self._global_completion_queue : Queue = Queue()
        self.log_store = LogStore(log_dir = constants.log_folder)
        self._observability_policy = observability_policy
        (
            self.stream_writer,
            self._log_bus,
            self._persist_registry
            ) = self._make_broadcast_channel(on_event = on_event)

    def _make_broadcast_channel(
            self,
            on_event : Callable | None
        ) -> tuple[StreamWriter, MiniBus, PersistRegistry]:
        """
        StreamWriter coordonnate external sinks.
        MiniBus decouples internal producers from StreamWriter.
        Together: event-channel of the session
        """
        persist_registry = PersistRegistry()
        writer = StreamWriter(on_event = on_event, persist_registry = persist_registry)
        log_bus = MiniBus(
            writer = writer,
            observability_policy = self._observability_policy,
            failure_behavior = self.stop
        )
        return writer, log_bus, persist_registry

    def start(self) -> None:
        self.log_store.cleanup()
        self.session.started_at = time()
        self.session.state = SessionState.RUNNING
        self.orchestrator.start_all_pipelines()
        for runner in self._execution_pools.values():
            runner.manager.wait_all()

    def stop(self) -> None:
        self.session.state = SessionState.STOPPING
        self.orchestrator.graceful_stop()
        
        # observe ending of "running" tasks via a thread
        threading.Thread(target=self._wait_for_stop, daemon=True).start()

    def cancel_session(self) -> None:
        self.session.state = SessionState.CANCELED
        self.orchestrator.cancel_policy = CancelPolicy.CANCEL_ALL
        for pipeline in self.orchestrator.pipelines:
            self.orchestrator.stop_pipeline(pipeline.id)

    def add_pipeline(self) -> TaskId:
        def on_transition(old: PipelineState, new: PipelineState) -> None:
            self._push_event(LogEvent(
                msg_type=MsgType.STATE_CHANGE,
                source_type=SourceType.PIPELINE,
                source_id=pipeline.id,
                timestamp=time()
            ))
        pipeline = Pipeline(on_transition, str(self.session.id))
        return self.orchestrator.add_pipeline(pipeline)

    def add_task(self, pipeline_id : TaskId, task_spec : Task) -> None:
        def on_transition(old: TaskState, new: TaskState) -> None:
            self._push_event(LogEvent(
                msg_type = MsgType.STATE_CHANGE,
                source_type = SourceType.TASK,
                source_id = task_spec.name,    # safe : Task.name is cast in post_init
                timestamp=time()
            ))
        
        # ensures ordering on disk and unicity on task names
        task_spec.name = self.log_store.register(
            session_id = self.session.id,
            source_id = task_spec.name    # safe : Task.name is cast in post_init
        )

        # synchronize logging and persitance
        on_cleanup = self._handle_task_persitance(task_spec)
        # a task can't run until having acquired an explicit runner
        self._define_runner(task_spec)

        # launch task
        self.orchestrator.add_task(pipeline_id, task_spec, on_transition, on_cleanup)
    
    def add_pool(self, pool_name : str, max_parallel : int = 4) -> PoolStrategy:
        """
        pools subscribe to StreamWriter once
        """
        manager = WorkerManager(
            max_count = max_parallel,
            log_bus = self._log_bus,
            completion_queue = self._global_completion_queue
        )
        self._execution_pools[pool_name] = PoolTaskRunner(manager = manager)
        return PoolStrategy(pool_name = pool_name)

    def _define_runner(self, task : Task) -> None :
        """
        Pool tasks have the same _runner.
        Each synchronous task has a _runner which mimics PoolRunner.
        TaskRunner(Protocol) -> (TaskPoolRunner, SubprocessTaskRunner, NoOpRunner)
        -> get_runner() consumes what's needed 
        global_completion_queue is unique on pools, may be per task on synchronous subprocesses
        but "a unique instance accross all runners" is the pattern for the entire scope of this lib
        """
        context = ExecutionPool(
            source_id = task.name,
            pools = self._execution_pools,
            global_completion_queue = self._global_completion_queue,
            event_bus = self._log_bus
        )
        task._runner = task.strategy.get_runner(
            context = context
        )

    def _handle_task_persitance(self, task_spec : Task) -> Callable | None:
        """
        due to decoupling with BasicWorker, tasks without specific log_producer
        declare persistance mecanism on themselves,
        (Specific producers are in the "dialect" package)
        """
        if task_spec.backend:
            backend_runner = FileBackendRunner(
                source_id = str(task_spec.name),
                backend = task_spec.backend,
                error_sink = self._log_bus.emit_internal
            )
            self.stream_writer.register_sink(
                task_spec.backend.write,
                scope = SinkScope.SCOPED,
                source_id = task_spec.name
            )
            self._persist_registry.add_context(
                task_spec.name,
                backend_runner
            )
            def cleanup(): 
                self.stream_writer.unregister_sink(
                    task_spec.name
                )
                task_spec.backend.close()
            return cleanup 
        
        return None

    def _wait_for_stop(self) -> None:
        while any(
            t.state == TaskState.RUNNING
            for p in self.orchestrator.pipelines
            for t in p.tasks
        ):
            sleep(0.5)

        self.session.state = SessionState.SUCCESS
        self._push_event(
            LogEvent(
                source_id = self.session.id,
                msg_type = MsgType.STATE_CHANGE,
                source_type = SourceType.SESSION,
                timestamp = time()
            )
        )

    def stop_pipeline(self, pipeline_id) -> None:
        self.orchestrator.stop_pipeline(pipeline_id)

    def _push_event(self, event) -> None:
        snapshot = None
        if event.msg_type == MsgType.STATE_CHANGE:
            snapshot = self.snapshot()
        self.stream_writer._on_event(event, snapshot)

    def log_failure(self, pipeline_id : str, reason : str) -> None:
        self.session.failure_reasons.append(
            PipelineFailure(
                pipeline_id,
                reason,
                time()
            )
        )

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            id=str(self.session.id),
            # media_path=self.session.media_path,
            # keywords=self.session.keywords,
            state=self.session.state,
            started_at=self.session.started_at,
            elapsed=time() - self.session.started_at if self.session.started_at else 0,
            pipelines={str(p.id) : p.snapshot() for p in self.orchestrator.pipelines},
            failure_reasons=self.session.failure_reasons
        )
    
    def reset(self, on_event, cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY, persist_registry = PersistRegistry()):
        self.pipelines : dict[str, Pipeline] = {}
        self.session = Session()
        self.stream_writer = StreamWriter(on_event = on_event, persist_registry = persist_registry)
        self.orchestrator = PipelineOrchestrator(
            str(self.session.id),
            self.log_failure,
            cancel_policy
        )
        self.session.pipelines = self.orchestrator.pipelines
        self._execution_pools = {}
        self.log_store = LogStore(log_dir = constants.log_folder)

    def ensure_context_safe(self):
        os.makedirs(constants.log_folder, exist_ok = True)