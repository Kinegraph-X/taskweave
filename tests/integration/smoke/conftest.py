import pytest
from threading import Event
from time import time

from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.messages import LogEvent, MsgType, Enveloppe, SourceType
from taskweave.tasks import Task, LocalProcessStrategy, SubprocessStrategy
from taskweave.workers import WorkerManager
from taskweave.session import SessionManager

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
    monkeypatch.setattr(constants, "log_folder", tmp_path / "logs")
    session = SessionManager(on_event = on_event)
    yield session
    session.reset(on_event = on_event)

@pytest.fixture
def task(after_complete):
    return Task(
        name = "smoke",
        strategy = LocalProcessStrategy(manager =  WorkerManager()),
        cmd = ["python", "--version"],
        after_complete = after_complete
    )

@pytest.fixture(autouse=True)
def pipeline(session, task):
    pipeline_id = session.add_pipeline()
    session.add_task(pipeline_id, task)
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