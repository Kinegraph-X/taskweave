from typing import Any, Protocol, IO, TextIO, Deque
from pathlib import Path
from dataclasses import dataclass

from taskweave.messages import OutputType
from taskweave.context import get_app_context
config, constants, args = get_app_context()

class PersistBackend(Protocol):
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        pass

@dataclass(kw_only = True)
class FileBackend:
    # base_folder : str = "logs/",
    max_lines : int = 100
    max_files : int = 3
    log_dir: Path = Path(f"{constants.log_folder}")

    def __post_init__(self):
        self.handles : dict[str, IO[Any]] = {}
        self.buffers : dict[str, Deque[str]] = {}
        self.file_indices : dict[str, int] = {}

    # one file per worker, named on source_id, rotated
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        buffer = self._get_buffer(source_id)
        buffer.append(line)
        if len(buffer) >= self.max_lines:
            self._rotate(source_id)

    def _rotate(self, source_id : str) -> None:
        self._get_handle(source_id).close()
        self._get_file_index(source_id)
        handle = self._get_handle(source_id)
        
        for line in self.buffers[source_id]:
            handle.write(line + '\n')
        handle.flush()
        self.buffers[source_id].clear()

    def _get_buffer(self, source_id : str) -> Deque[str]:
        return self.buffers[source_id]
    
    def _get_file_index(self, source_id : str) -> int:
        if self.file_indices[source_id]:
            if self.file_indices[source_id] >= self.max_files:
                self.file_indices[source_id] = 0
                return 0
            else:
                return ++self.file_indices[source_id]
        else:
            self.file_indices[source_id] = 0
            return 0

    def _get_handle(self, source_id : str) -> IO[Any] :
        if self.handles[source_id] and not self.handles[source_id].closed:
            return self.handles[source_id]
        else:
            path = Path.joinpath(
                self.log_dir,
                source_id,
                f"{source_id}_{self.file_indices[source_id]:03d}.log"
            )
            self.handles[source_id] = open(path, "w")
            return self.handles[source_id]

    def _cleanup(self) -> None :
        for id, buffer in self.buffers.items():
            self._rotate(id)

        for id, handle in self.handles.items():
            handle.close()

    def close(self) -> None:
        self._cleanup()

# future implems
@dataclass
class InMemoryBackend:
    max_lines: int = 100
    # ring buffer per source_id
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        pass

@dataclass
class NullBackend:
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        pass