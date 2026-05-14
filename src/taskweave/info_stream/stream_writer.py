from typing import List, Callable, TypeVar
from .sink_scope import SinkScope

from taskweave.persist import PersistRegistry
from taskweave.buses import SeenSequences
from taskweave.messages import LogEvent, Enveloppe
from taskweave.snapshots import SessionSnapshot
from taskweave.utils import TaskId

from taskweave_protocol import OutputType

# SinkSignature = Callable[[TaskId, str, OutputType], None]
SinkSignature = Callable[[str, str], None]

class StreamWriter:
    def __init__(
            self,
            persist_registry : PersistRegistry,
            on_event : Callable | None = None
            ):
        self._global_sinks : List[Callable] = []
        self._error_sinks : List[Callable] = []
        self._scoped_sinks : dict[TaskId, SinkSignature] = {}          # callables : CLI, WebSocket, files...
        self._persist_registry = persist_registry
        if callable(on_event):
            self._global_sinks.append(on_event)

    # scoped sinks may serve persistance needs
    # SessionManager use it to handle 
    # Tasks with "persist" : PersistStrategy attribute 
    def register_sink(
            self,
            cb: SinkSignature,
            *,
            scope: SinkScope = SinkScope.GLOBAL,
            source_id: TaskId | None = None,
        ) -> int:
        if scope == SinkScope.GLOBAL:
            self._global_sinks.append(cb)
            return len(self._global_sinks) - 1
        elif scope == SinkScope.SCOPED:
            if not source_id:
                raise RuntimeError(f'StreamWriter.register_sink : call with SinkScope.SCOPED must provide a source_id')
            self._scoped_sinks[source_id] = cb
            return len(self._scoped_sinks) - 1

    def register_error_sink(self, cb : Callable):
        self._error_sinks.append(cb)
        
    def unregister_sink(self, source_id : TaskId):
        del self._scoped_sinks[source_id]

    def _on_event(self, event: LogEvent, snapshot : SessionSnapshot | None = None):
        source_id = event.source_id
        if source_id in self._scoped_sinks.keys():
            if event.routing.persist:
                self._persist_registry.persist(event)
            # self._scoped_sinks[source_id](source_id, event.msg, OutputType.DISCARD)
        
        enveloppe = Enveloppe(event=event)
        if snapshot:
            # enriched with current snapshot
            enveloppe.session_snapshot = snapshot
        
        for sink in self._global_sinks:
            sink(enveloppe)

    def _on_internal_event(
            self,
            event : LogEvent,
            snapshot  : SessionSnapshot | None = None,
            last_seen_sequences : dict[TaskId, SeenSequences] | None = None
        ):
        enveloppe = Enveloppe(event=event)
        if snapshot:
            enveloppe.session_snapshot = snapshot
        if last_seen_sequences:
            enveloppe.last_seen_sequences = {str(k) : v for k, v in last_seen_sequences.items()}
        for sink in self._error_sinks:
            sink(enveloppe)