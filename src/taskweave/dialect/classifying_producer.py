from dataclasses import dataclass
from time import time

from taskweave.messages import LogEvent, MsgType, SourceType
from .classifier import Classifier
from .output_type import OutputType

_OUTPUT_TO_MSG: dict[OutputType, MsgType] = {
    OutputType.PROGRESS :   MsgType.PROGRESS,
    OutputType.LOG_LINE :   MsgType.LOG_LINE,
    OutputType.BANNER :     MsgType.BANNER,
    OutputType.VERBBOSE :   MsgType.LOG_LINE
    # DISCARD absent — no LogEvent produced
}

@dataclass
class ClassifyingProducer:
    classifier : Classifier

    def on_line(self, source_id: str, line: str) -> LogEvent:
        output_type, parsed = self.classifier.classify()
        if output_type == output_type.DISCARD:
            return
        return LogEvent(
            msg_type = _OUTPUT_TO_MSG.get(output_type),
            source_type = SourceType.TASK,
            source_id = source_id,
            msg = line,
            parsed = parsed,
            timestamp = time()
        )