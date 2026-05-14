from typing import Callable, Any

from .seen_sequences import SeenSequences

from taskweave.utils import TaskId
from taskweave.info_stream import StreamWriter
from taskweave.messages import LogEvent
from taskweave.buses import ObservabilityPolicy
from taskweave.snapshots import SessionSnapshot


class MiniBus:
    """
    Light Decoupler between event producers and StreamWriter.
    Producers emit on the bus without knowing their consumers.
    Also handles a stderr channel, allowing to propagate errors
    from the logging stack, and to track dropped events.
    """
    def __init__(
            self,
            *,
            writer: StreamWriter,
            observability_policy : ObservabilityPolicy,
            failure_behavior : Callable
        ):
        self._writer = writer
        self._observability_policy = observability_policy
        self._failure_behavior = failure_behavior
        self._last_seen_sequences : dict[TaskId, SeenSequences] = {}

    def _handle_observability_policy(self, event : LogEvent):
        event.sequence = self._last_seen_sequences[event.source_id].last_seen
        self._last_seen_sequences[event.source_id].sequence_on_failure = event.sequence
        if self._observability_policy == ObservabilityPolicy.SAFE:
            session_snapshot : SessionSnapshot = self._failure_behavior(event)
            self._writer._on_internal_event(event, session_snapshot, self._last_seen_sequences)
            return
        self._writer._on_internal_event(event)
    
    def emit(self, event: LogEvent) -> None:
        if not self._last_seen_sequences[event.source_id]:
            self._last_seen_sequences[event.source_id] = SeenSequences()
        event.sequence = self._last_seen_sequences[event.source_id].last_seen
        self._writer._on_event(event)
        self._last_seen_sequences[event.source_id].last_seen += 1

    def emit_internal(self, event : LogEvent):
        self._handle_observability_policy(event)