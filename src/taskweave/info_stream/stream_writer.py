from typing import List, Callable
from whisper_infer.messages import LogEvent, Enveloppe
from whisper_infer.workers import WorkerManager
from whisper_infer.snapshots import SessionSnapshot

class StreamManager:
    def __init__(self):
        self._sinks : List[Callable] = []          # callables : CLI, WebSocket, fichier...

    def attach_orchestrator(self, orchestrator):
        self._orchestrator = orchestrator

    def subscribe(self, manager: WorkerManager):
        manager.subscribe_to_logs(self._on_event)

    def add_sink(self, fn: Callable):
        self._sinks.append(fn)

    def _on_event(self, event: LogEvent, snapshot : SessionSnapshot | None = None):
        envelope = Enveloppe(event=event)
        if snapshot:
            # enriched with current snapshot
            envelope.session_snapshot = snapshot
        
        for sink in self._sinks:
            sink(envelope)