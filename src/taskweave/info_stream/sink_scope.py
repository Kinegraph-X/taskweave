from enum import Enum

class SinkScope(Enum):
    GLOBAL = "global"    # receives all — Flask, CLI
    SCOPED = "scoped"  # filters by source_id — PersistSink