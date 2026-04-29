from typing import Protocol
from dataclasses import dataclass
from .output_type import OutputType
from .persist_backend import PersistBackend, FileBackend

class PersistStrategy(Protocol):
    def write(self, line: str, output_type: OutputType) -> None:
        pass

@dataclass
class PersistAll:
    # écrit toutes les lignes
    backend : PersistBackend = FileBackend()
    def write(self, line: str, output_type: OutputType) -> None:
        self.backend.write(output_type, line)

@dataclass
class PersistDiscarded:
    # only writes OutputType.DISCARD
    backend : PersistBackend = FileBackend()
    def write(self, line: str, output_type: OutputType) -> None:
        if output_type == OutputType.DISCARDED:
            self.backend.write(output_type, line)

@dataclass
class Persist_Verbose_And_Discarded:
    # only writes OutputType.VERBOSE and OutputType.DISCARD
    backend : PersistBackend = FileBackend()
    def write(self, line: str, output_type: OutputType) -> None:
        if output_type in (OutputType.DISCARDED, OutputType.VERBOSE):
            self.backend.write(output_type, line)

class PersistNone:
    def write(self, line: str, output_type: OutputType) -> None:
        pass

