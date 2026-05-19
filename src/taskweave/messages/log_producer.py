from typing import Protocol, Callable, Any
from dataclasses import dataclass
from time import time

from taskweave.utils import SinkContext

from taskweave_protocol import LogEvent


class LogProducer(Protocol):
    def on_line(self, source_id: str, line: str) -> LogEvent:...
    def make_sink(self, context : SinkContext) -> None :...