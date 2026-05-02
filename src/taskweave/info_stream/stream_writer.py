from typing import List, Callable, TypeVar
from .sink_scope import SinkScope
from taskweave.messages import LogEvent, Enveloppe, OutputType
from taskweave.snapshots import SessionSnapshot
from taskweave.utils import StrSerializable

SinkSignature = Callable[[str | StrSerializable, str, OutputType], None]

class StreamWriter:
    def __init__(self, on_event : Callable | None = None):
        self._global_sinks : List[Callable] = []
        self._scoped_sinks : dict[str | StrSerializable, SinkSignature] = {}          # callables : CLI, WebSocket, files...
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
            source_id: str | StrSerializable | None = None,
        ) -> int:
        if scope == SinkScope.GLOBAL:
            self._global_sinks.append(cb)
            return len(self._global_sinks) - 1
        elif scope == SinkScope.SCOPED:
            if not source_id:
                raise RuntimeError(f'StreamWriter.register_sink : call with SinkScope.SCOPED must provide a source ID')
            self._scoped_sinks[source_id] = cb
            return len(self._scoped_sinks) - 1
        
    def unregister_sink(self, source_id : str | StrSerializable):
        del self._scoped_sinks[source_id]

    def _on_event(self, event: LogEvent, snapshot : SessionSnapshot | None = None):
        source_id = event.source_id
        if source_id in self._scoped_sinks.keys():
            self._scoped_sinks[source_id](source_id, event.msg, OutputType.DISCARD)
        
        envelope = Enveloppe(event=event)
        if snapshot:
            # enriched with current snapshot
            envelope.session_snapshot = snapshot
        
        for sink in self._global_sinks:
            sink(envelope)