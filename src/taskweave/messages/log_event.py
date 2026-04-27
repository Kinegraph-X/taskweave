from typing import Any
from dataclasses import dataclass
from .msg_type import MsgType
from .source_type import SourceType
from taskweave.utils import StrSerializable

@dataclass
class LogEvent:
    msg_type: MsgType
    source_id: str | StrSerializable
    source_type: SourceType   # enum : WORKER | PIPELINE | SESSION
    timestamp: float
    msg: str = ""             # always the raw line
    parsed: Any | None = None # result of dialect classifier, opaque for the lib