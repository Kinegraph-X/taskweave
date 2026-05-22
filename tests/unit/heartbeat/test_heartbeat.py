from taskweave.info_stream import StreamWriter
from taskweave.persist import PersistRegistry
from taskweave.buses import Heartbeat, HeartbeatConfig, MiniBus, ObservabilityPolicy
from taskweave.utils import TaskId

from taskweave_protocol import LogEvent, MsgType

class FakeClock:
    def __init__(self):
        self._time = 0.0
    
    def tick(self, seconds: float) -> None:
        self._time += seconds
    
    def __call__(self) -> float:
        return self._time

class FakeSleep:
    def __init__(self, clock: FakeClock):
        self._clock = clock
    
    def __call__(self, seconds: float) -> None:
        self._clock.tick(seconds)  # unroll time without waiting


def test_heartbeat_forwarding():
    events : list[LogEvent] = []
    source_id = TaskId("task_test")
    config = HeartbeatConfig(
        threshold = 5.0,
        max_threshold = 15.0
    )
    event_sink = lambda enveloppe: events.append(enveloppe.event)

    hb = Heartbeat(
        source_id = source_id,
        log_bus = MiniBus(
            writer = StreamWriter(
                persist_registry = PersistRegistry(),
                on_event = event_sink
            ), 
            observability_policy = ObservabilityPolicy.SAFE,
            snapshot_getter = lambda : None
        ),
        config = config
    )

    hb.beat(
        LogEvent(
            source_id = source_id,
            timestamp = 0.0
        )
    )
    
    assert len(events) == 1
    assert events[0].msg_type == MsgType.LOG_LINE


def test_heartbeat_timeout():
    events : list[LogEvent] = []
    source_id = TaskId("task_test")
    config = HeartbeatConfig(
        threshold = 5.0,
        max_threshold = 15.0
    )
    event_sink = lambda enveloppe: events.append(enveloppe.event)

    clock = FakeClock()
    sleep = FakeSleep(clock)
    hb = Heartbeat(
        source_id = source_id,
        log_bus = MiniBus(
            writer = StreamWriter(
                persist_registry = PersistRegistry(),
                on_event = event_sink
            ), 
            observability_policy = ObservabilityPolicy.SAFE,
            snapshot_getter = lambda : None
        ),
        config = config,
        sleep=sleep
    )
    
    # FakeSleep immediately sleeps beyond timeout 
    assert len(events) == 1
    assert events[0].msg_type == MsgType.HEARTBEAT_TIMEOUT