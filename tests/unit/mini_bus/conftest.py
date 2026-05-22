import pytest
import threading
from time import time

from taskweave.persist import PersistRegistry
from taskweave.info_stream import StreamWriter, SinkScope
from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.utils import TaskId
from taskweave.snapshots import SessionSnapshot

from taskweave_protocol import LogEvent, MsgType

@pytest.fixture
def source_id():
    return TaskId("task_test")

@pytest.fixture
def registry():
    registry = PersistRegistry()
    yield registry
    registry = PersistRegistry()

@pytest.fixture
def log_events():
    log_events = []
    yield log_events
    log_events.clear()

@pytest.fixture
def log_enveloppes():
    log_events = []
    yield log_events
    log_events.clear()

@pytest.fixture
def has_failed():
    has_failed : threading.Event = threading.Event()
    yield has_failed
    has_failed.clear()

@pytest.fixture
def on_event(log_events):
    on_event = lambda enveloppe: log_events.append(enveloppe.event)
    yield on_event

@pytest.fixture
def on_internal_event(log_enveloppes):
    on_event = lambda enveloppe: log_enveloppes.append(enveloppe)
    yield on_event

@pytest.fixture
def writer(
        on_event,
        on_internal_event,
        registry
    ):
    writer = StreamWriter(
        persist_registry = registry
    )
    writer.register_sink(
        cb = on_event
    )
    writer.register_error_sink(
        cb = on_internal_event
    )
    yield writer
    writer = StreamWriter(
        persist_registry = registry
    )
    writer.register_sink(
        cb = on_event
    )
    writer.register_error_sink(
        cb = on_internal_event
    )

@pytest.fixture
def event(source_id):
    event = LogEvent(
        msg_type = MsgType.LOG_LINE,
        source_id = source_id,
        timestamp = time()
    )
    return event

@pytest.fixture
def failure_event(source_id):
    event = LogEvent(
        msg_type = MsgType.BACKEND_FAILURE,
        source_id = source_id,
        timestamp = time()
    )
    return event

@pytest.fixture
def session_snapshot():
    return SessionSnapshot(
            id = "",
            state = "",
            started_at = 0.0,
            elapsed = 0.0,
            pipelines = {},
            failure_reasons = []
        )