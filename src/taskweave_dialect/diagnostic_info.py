import json
from enum import Enum
from  dataclasses import dataclass, asdict

class DiagnosticInfoKind(str, Enum):
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"

@dataclass(kw_only = True)
class DiagnosticInfo:
    kind : DiagnosticInfoKind
    msg : str

    def __str__(self):
        return str(asdict(self))

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(asdict(self))