import pytest
from threading import Event
from time import time

from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave_protocol import LogEvent, MsgType, Enveloppe, SourceType
from taskweave.tasks import Task, SynchronousStrategy, PoolTaskRunner, SubprocessTaskRunner
from taskweave.workers import WorkerManager
from taskweave.session import SessionManager, SessionControl
from taskweave.pipeline import Pipeline

@pytest.fixture
def done():
    done = Event()
    yield done
    done.clear()

@pytest.fixture
def log_events():
    log_events = []
    yield log_events
    log_events.clear()

@pytest.fixture
def activity_events():
    activity_events = []
    yield activity_events
    activity_events.clear()

@pytest.fixture
def on_event(log_events, activity_events):
    def func(env : Enveloppe):
        event = env.event
        if event.msg_type == MsgType.LOG_LINE:
            log_events.append(event)
        elif event.msg_type == MsgType.STATE_CHANGE:
            activity_events.append(event)
    return func

@pytest.fixture
def after_complete(done):
    def func(task_name : str):
        done.set()
    return func

@pytest.fixture
def session(tmp_path, monkeypatch, on_event):
    monkeypatch.setattr(constants, "log_dir", tmp_path / "logs")
    session = SessionControl(on_event = on_event)
    yield session
    session.reset()

@pytest.fixture
def task(after_complete):
    return Task(
        name = "smoke",
        strategy = SynchronousStrategy(),
        cmd = ["python", "--version"],
        on_finally = after_complete
    )

@pytest.fixture(autouse=True)
def pipeline(session, task):
    p = Pipeline(
        tasks = [task]
    )
    pipeline_id = session.orchestrator._hydrate_pipeline(
        session_id = session.session.id,
        pipeline = p
    )
    return session

@pytest.fixture
def log_line_event():
    return LogEvent(
        msg_type = MsgType.LOG_LINE,
        source_id = "",
        source_type = SourceType.TASK,
        timestamp = time(),
        msg = "",
        parsed = None
    )

@pytest.fixture
def state_change_event():
    return LogEvent(
        msg_type = MsgType.STATE_CHANGE,
        source_id = "",
        source_type = SourceType.TASK,
        timestamp = time(),
        msg = "",
        parsed = None
    )