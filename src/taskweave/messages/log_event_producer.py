from typing import Protocol, Callable
from dataclasses import dataclass
from time import time

from .log_event import LogEvent
from .msg_type import MsgType
from .source_type import SourceType

from taskweave.utils import TaskId

class LogProducer(Protocol):
    def on_line(self, source_id: str, line: str) -> LogEvent:
        pass

@dataclass(kw_only = True)
class LogEventProducer:

    def on_line(self, source_id: str, line: str) -> LogEvent:
        return LogEvent(
            msg_type = MsgType.LOG_LINE,
            source_type = SourceType.TASK,
            source_id = TaskId(source_id),
            msg = line,
            timestamp = time()
        )