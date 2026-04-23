import time, threading
from uuid import uuid4
from .session import Session
from whisper_infer.info_stream import StreamManager
from whisper_infer.snapshots import SessionSnapshot
from whisper_infer.pipeline import PipelineOrchestrator
from whisper_infer.tasks import CancelPolicy
from whisper_infer.messages import MsgType, LogEvent
from whisper_infer.states import SessionState, TaskState

class SessionManager:
    def __init__(self, config, cancel_policy = CancelPolicy.CANCEL_PENDING_ONLY):
        self.session = Session(
            uuid4().hex,
            config.media_path,
            config.keywords,
            time.time()
        )
        self.stream_manager = StreamManager()
        self.orchestrator = PipelineOrchestrator(self, self.stream_manager, cancel_policy)
        return self.session

    # def create_session(self, config) -> Session:
    #     self.session = Session(
    #         uuid4().hex,
    #         config.media_path,
    #         config.keywords,
    #         time.time()
    #     )
    #     return self.session

    def stop_session(self):
        self.session.state = SessionState.STOPPING
        self.orchestrator._propagate_state_change(None, None, MsgType.STATE_CHANGE)
        
        # ccnecancel pendings, keep runnings
        for pipeline in self.orchestrator.pipelines:
            for task in pipeline.tasks:
                if task.state == TaskState.PENDING and task.cancellable:
                    task.state = TaskState.CANCELED
        
        # observe ending of "running" tasks via a thread
        threading.Thread(target=self._wait_for_stop, daemon=True).start()

    def _wait_for_stop(self):
        while any(
            t.state == TaskState.RUNNING
            for p in self.orchestrator.pipelines
            for t in p.tasks
        ):
            time.sleep(0.5)
        self.session.state = SessionState.SUCCESS
        self.orchestrator._propagate_state_change(None, None, MsgType.STATE_CHANGE)

    def cancel_session(self):
        self.orchestrator.cancel_policy = CancelPolicy.CANCEL_ALL
        for pipeline in self.orchestrator.pipelines:
            self.orchestrator.stop_pipeline(pipeline.id)

    def stop_pipeline(self, pipeline_id):
        self.orchestrator.stop_pipeline(pipeline_id)

    def _push_event(self, event : LogEvent):
        if event.msg_type in (MsgType.STATE_CHANGE, MsgType.TASK_DONE, MsgType.EARLY_EXIT):
            snapshot = self.snapshot()
        self.stream_manager._on_event(event, snapshot)

    def snapshot(self) -> SessionSnapshot:
        return SessionSnapshot(
            id=self.session.id,
            media_path=self.session.media_path,
            keywords=self.session.keywords,
            state=self.session.state,
            started_at=self.session.started_at,
            elapsed=time.time() - self.session.started_at if self.session.started_at else 0,
            pipelines={p.id : p.snapshot() for p in self.orchestrator.pipelines},
            failure_reasons=self.session.failure_reasons
        )
    