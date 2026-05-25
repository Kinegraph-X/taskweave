import pytest
from itertools import cycle

from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.info_stream import StreamWriter
from taskweave.persist import PersistRegistry

@pytest.fixture
def source_id():
    return "task_test"

@pytest.fixture
def log_events():
    log_events = []
    yield log_events
    log_events.clear()

@pytest.fixture
def on_event(log_events):
    return lambda enveloppe: log_events.append(enveloppe.event)

@pytest.fixture
def get_line():
    lines = [
        "status = 200 url = http://example.com",
        "status = 404 url = http://example.com/fail"
    ]
    lines_iter = cycle(lines)

    yield lambda: next(lines_iter)
    lines_iter = cycle(lines)

@pytest.fixture
def log_bus(on_event):
    writer = StreamWriter(
        persist_registry = PersistRegistry(),
        on_event = on_event
    )
    writer.register_error_sink(on_event)
    bus = MiniBus(
        writer = writer,
        observability_policy = ObservabilityPolicy.SAFE,
        snapshot_getter = lambda event: None
    )
    return bus