import pytest

from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.snapshots import SessionSnapshot

from taskweave_protocol import LogEvent, SeenSequences

def test_mini_bus_emit(
        event,
        log_events,
        writer,
        has_failed,
        session_snapshot
    ):
    def failure_behavior(event):
        has_failed.set()
        return session_snapshot

    bus = MiniBus(
        writer = writer,
        observability_policy = ObservabilityPolicy.SAFE,
        snapshot_getter = failure_behavior
    )

    bus.emit(event)
    assert len(log_events) == 1
    assert isinstance(log_events[0], LogEvent)

def test_mini_bus_emit_internal(
        source_id,
        failure_event,
        log_enveloppes,
        writer,
        has_failed,
        session_snapshot
    ):
    def failure_behavior(event):
        has_failed.set()
        return session_snapshot

    bus = MiniBus(
        writer = writer,
        observability_policy = ObservabilityPolicy.SAFE,
        snapshot_getter = failure_behavior
    )

    bus.emit_internal(failure_event)
    assert len(log_enveloppes) == 1
    assert isinstance(log_enveloppes[0].event, LogEvent)
    assert has_failed.is_set() # fails if an error doesn't trigger failure_behavior() on MiniBus
    assert isinstance(log_enveloppes[0].session_snapshot, SessionSnapshot)
    assert isinstance(log_enveloppes[0].last_seen_sequences, dict)
    assert log_enveloppes[0].last_seen_sequences[str(source_id)]["sequence_on_failure"] == 1
    assert log_enveloppes[0].last_seen_sequences[str(source_id)]["last_seen"] == 1

def test_mini_bus_emit_internal_best_effort(
        failure_event,
        log_enveloppes,
        writer
    ):

    bus = MiniBus(
        writer = writer,
        observability_policy = ObservabilityPolicy.BEST_EFFORT,
        snapshot_getter = lambda event: None
    )

    bus.emit_internal(failure_event)
    assert len(log_enveloppes) == 1
    assert isinstance(log_enveloppes[0].event, LogEvent)
    assert log_enveloppes[0].session_snapshot is None
    assert log_enveloppes[0].last_seen_sequences is None