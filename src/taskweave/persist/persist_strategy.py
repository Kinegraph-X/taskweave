from typing import Protocol
from dataclasses import dataclass, field
from .persist_backend import PersistBackend, FileBackend

from taskweave.messages import OutputType

class PersistStrategy(Protocol):
    def write(self, line: str, output_type: OutputType) -> None:
        pass

@dataclass
class PersistAll:
    # écrit toutes les lignes
    backend : PersistBackend = field(default_factory = FileBackend)
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        self.backend.write(source_id, line, output_type)

@dataclass
class PersistDiscarded:
    # only writes OutputType.DISCARD
    backend : PersistBackend = field(default_factory = FileBackend)
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        if output_type == OutputType.DISCARD:
            self.backend.write(source_id, line, output_type)

@dataclass
class Persist_Verbose_And_Discarded:
    # only writes OutputType.VERBOSE and OutputType.DISCARD
    backend : PersistBackend = field(default_factory = FileBackend)
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        if output_type in (OutputType.DISCARD, OutputType.VERBOSE):
            self.backend.write(source_id, line, output_type)

class PersistNone:
    def write(self, line: str, output_type: OutputType) -> None:
        pass

