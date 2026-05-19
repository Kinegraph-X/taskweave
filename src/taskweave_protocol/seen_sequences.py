from dataclasses import dataclass

@dataclass(kw_only = True)
class SeenSequences:
    sequence_on_failure : int = 0
    last_seen : int = 0