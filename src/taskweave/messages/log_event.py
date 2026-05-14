import json, time
from typing import Any
from dataclasses import dataclass
from .msg_type import MsgType
from .source_type import SourceType
from .routing_policy import RoutingPolicy
from taskweave.utils import TaskId

@dataclass
class LogEvent:
    msg_type: MsgType
    source_id: TaskId
    source_type: SourceType   # enum : WORKER | PIPELINE | SESSION
    timestamp: float
    routing: RoutingPolicy = RoutingPolicy(forward=True, persist=False)
    sequence : int = 0        # allow post-mortem reading of logs
    msg: str = ""             # always the raw line
    parsed: Any | None = None # result of dialect classifier, opaque for the lib

    def format(self):
        return json.dumps(
            {
                "source_type" : self.source_type,
                "time" : time.locale_time(self.timestamp),
                "source_id" : self.source_id,
                "sequence" : self.sequence,
                "msg_type" : self.msg_type,
                "msg" : self.msg
            }
        )