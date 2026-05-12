from typing import Any
from dataclasses import dataclass
from .msg_type import MsgType
from .source_type import SourceType
from taskweave.utils import TaskId

@dataclass
class LogEvent:
    msg_type: MsgType
    source_id: TaskId
    source_type: SourceType   # enum : WORKER | PIPELINE | SESSION
    timestamp: float
    sequence : int = 0        # allow post-mortem reading of logs
    msg: str = ""             # always the raw line
    parsed: Any | None = None # result of dialect classifier, opaque for the lib