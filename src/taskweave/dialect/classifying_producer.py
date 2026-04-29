from dataclasses import dataclass
from time import time

from taskweave.messages import LogEvent, MsgType, SourceType
from .classifier import Classifier
from .output_type import OutputType

_OUTPUT_TO_MSG: dict[OutputType, MsgType] = {
    OutputType.PROGRESS :   MsgType.PROGRESS,
    OutputType.LOG_LINE :   MsgType.LOG_LINE,
    OutputType.BANNER :     MsgType.BANNER,
    OutputType.VERBOSE :   MsgType.BANNER
    # DISCARD absent — no LogEvent produced
}


"""
This type is meant to be compatible with LogEventProducer:
the "dialect" package must not be coupled to the "workers" package
"""
@dataclass
class ClassifyingProducer:
    classifier : Classifier

    def on_line(self, source_id: str, line: str) -> LogEvent | None:
        # Generator consumed eagerly here
        # dict() because we need random access by name to build parsed.
        # but using a generator in classify() is just for practice purpose
        results = dict(
            (name, (output_type, parse_result))
            for name, output_type, parse_result in self.classifier.classify(line)
        )
        matched_type = next(
            (ot for _, (ot, pr) in results.items() if pr.matched),
            OutputType.LOG_LINE
        )
        msg_type = _OUTPUT_TO_MSG.get(matched_type)
        if msg_type is None:
            return None # DISCARD
        parsed = {name: pr for name, (_, pr) in results.items()}

        return LogEvent(
            msg_type = msg_type,
            source_type = SourceType.TASK,
            source_id = source_id,
            msg = line,
            parsed = parsed,
            timestamp = time()
        )