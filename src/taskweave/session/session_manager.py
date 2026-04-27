import threading
from uuid import uuid4
from time import time, sleep
from .session import Session
from taskweave.context import Config
from taskweave.snapshots import PipelineFailure
from taskweave.info_stream import StreamWriter
from taskweave.snapshots import SessionSnapshot
from taskweave.pipeline import PipelineOrchestrator, Pipeline
from taskweave.tasks import CancelPolicy, Task
from taskweave.messages import MsgType, LogEvent, SourceType
from taskweave.states import SessionState, TaskState, PipelineState

class SessionManager:
    def __init__(
            self,
            config : Config,
            cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY
            ):
        self.session = Session(
            # config.media_path,
            # config.keywords,
        )
        self.stream_manager = StreamWriter()
        self.orchestrator = PipelineOrchestrator(
            self.session.id,
            self.log_failure,
            cancel_policy
        )
        self.session.pipelines = self.orchestrator.pipelines

    def start_session(self) -> None:
        self.session.started_at = time()
        self.session.state = SessionState.RUNNING
        self.orchestrator.start_all_pipelines()

    def stop_session(self) -> None:
        self.session.state = SessionState.STOPPING
        self.orchestrator.graceful_stop()
        
        # observe ending of "running" tasks via a thread
        threading.Thread(target=self._wait_for_stop, daemon=True).start()

    def cancel_session(self) -> None:
        self.session.state = SessionState.CANCELED
        self.orchestrator.cancel_policy = CancelPolicy.CANCEL_ALL
        for pipeline in self.orchestrator.pipelines:
            self.orchestrator.stop_pipeline(pipeline.id)

    def add_pipeline(self) -> str:
        def on_transition(old: PipelineState, new: PipelineState) -> None:
            self._push_event(LogEvent(
                msg_type=MsgType.STATE_CHANGE,
                source_type=SourceType.PIPELINE,
                source_id=pipeline.id,
                timestamp=time()
            ))
        pipeline = Pipeline(on_transition, self.session.id)
        return self.orchestrator.add_pipeline(pipeline)

    def add_task(self, pipeline_id : str, task_spec : Task) -> None:
        def on_transition(old: TaskState, new: TaskState) -> None:
            self._push_event(LogEvent(
                msg_type = MsgType.STATE_CHANGE,
                source_type = SourceType.TASK,
                source_id = task_spec.name,
                timestamp=time()
            ))
        self.orchestrator.add_task(pipeline_id, task_spec, on_transition)

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
        self.stream_manager._on_event(event, snapshot)

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
            id=self.session.id,
            # media_path=self.session.media_path,
            # keywords=self.session.keywords,
            state=self.session.state,
            started_at=self.session.started_at,
            elapsed=time() - self.session.started_at if self.session.started_at else 0,
            pipelines={p.id : p.snapshot() for p in self.orchestrator.pipelines},
            failure_reasons=self.session.failure_reasons
        )
    