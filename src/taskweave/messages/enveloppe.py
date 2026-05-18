from dataclasses import dataclass
from .log_event import LogEvent
from .seen_sequences import SeenSequences
from taskweave.snapshots import SessionSnapshot

@dataclass
class Enveloppe:
    event : LogEvent
    session_snapshot : SessionSnapshot | None = None
    last_seen_sequences : dict[str, SeenSequences] | None = None # useful for post-mortem analysis