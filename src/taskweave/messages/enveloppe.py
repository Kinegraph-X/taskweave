from dataclasses import dataclass
from .log_event import LogEvent
from taskweave.snapshots import SessionSnapshot

@dataclass
class Enveloppe:
    event : LogEvent
    session_snapshot : SessionSnapshot | None = None