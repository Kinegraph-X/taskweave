from typing import Protocol
from time import time

from .log_event import LogEvent
from .msg_type import MsgType
from .source_type import SourceType

class LogEventProducer(Protocol):
    def on_line(self, source_id: str, line: str) -> LogEvent:
        return LogEvent(
            msg_type = MsgType.LOG_LINE,
            source_type = SourceType.TASK,
            source_id = source_id,
            msg = line,
            timestamp = time()
        )