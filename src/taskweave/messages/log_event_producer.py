from typing import Protocol, Callable, Any
from dataclasses import dataclass
from time import time

from taskweave.utils import TaskId, SinkContext

from taskweave_protocol import LogEvent, MsgType, SourceType, RoutingPolicy

@dataclass(kw_only = True)
class LogEventProducer:
    """
    default routing policy is forward & don't persist
    """
    on_line_fn : Callable[[str, str], LogEvent] = lambda source_id, line : (
                LogEvent(
                    msg_type = MsgType.LOG_LINE,
                    source_type = SourceType.TASK,
                    source_id = TaskId(source_id),
                    msg = line,
                    timestamp = time()
                )
            )

    def on_line(self, source_id: str, line: str) -> LogEvent:
        return self._on_line_fn(source_id, line)
    
    def make_sink(self, context : SinkContext) -> None:
        if context.backend:
            self._on_line_fn = lambda source_id, line : (
                LogEvent(
                    msg_type = MsgType.LOG_LINE,
                    source_type = SourceType.TASK,
                    source_id = TaskId(source_id),
                    msg = line,
                    timestamp = time(),
                    routing = RoutingPolicy(
                        forward = True,
                        persist = True
                    )
                )
            )
    