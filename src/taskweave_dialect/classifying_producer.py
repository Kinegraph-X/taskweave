from dataclasses import dataclass, field
from time import time

from .classifier import Classifier

from taskweave.messages import _OUTPUT_TO_MSG, LogEvent, MsgType, SourceType
from taskweave.utils import TaskId
from taskweave.persist import PersistStrategy, PersistNone
from taskweave_protocol import OutputType


@dataclass
class ClassifyingProducer:
    """
    This type is meant to be compatible with LogEventProducer:
    the "dialect" package must not be coupled to the "workers" package
    """
    classifier : Classifier
    strategy : PersistStrategy = field(default_factory = PersistNone)

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
        
        assert msg_type is not None
        
        parsed = {name: pr for name, (_, pr) in results.items()}

        return self.strategy.specialize_event(
            LogEvent(
                msg_type = msg_type,
                source_type = SourceType.TASK,
                source_id = TaskId(source_id),
                msg = line,
                parsed = parsed,
                timestamp = time()
            ),
            matched_type
        )