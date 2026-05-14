import time
from typing import Any, Protocol, IO, TextIO, Deque
from pathlib import Path
from dataclasses import dataclass, field

from .circuit_breaker import CircuitBreaker
from .circuit_breaker_config import CircuitBreakerConfig, PersistConfig

from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.utils import TaskId
from taskweave.messages import LogEvent, SourceType, MsgType
from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.info_stream import StreamWriter
from taskweave.persist import PersistRegistry

from taskweave_protocol import OutputType

class PersistBackend(Protocol):
    def register_error_sink(self, sink : MiniBus) -> None:...
    def write(self, source_id: str, line: str) -> None:...

@dataclass(kw_only = True)
class NoOpBackend:
    def register_error_sink(self, sink : MiniBus) -> None:...
    def write(self, source_id: str, line: str) -> None:...

@dataclass(kw_only = True)
class FileBackend:
    # base_folder : str = "logs/",
    max_lines : int = 100
    max_files : int = 3
    log_dir: Path = Path(f"{constants.log_folder}")
    # late initialized : default constructed, although required for error handling
    error_sink : MiniBus = MiniBus(writer = StreamWriter(persist_registry = PersistRegistry()), observability_policy = ObservabilityPolicy.RELAXED, failure_behavior = lambda: None)
    config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)

    def __post_init__(self):
        self.handles : dict[str, IO[Any]] = {}
        self.buffers : dict[str, Deque[str]] = {}
        self.file_indices : dict[str, int] = {}

        self.circuit_breaker = CircuitBreaker(self.config)

    def register_error_sink(self, sink : MiniBus):
        self.error_sink = sink

    # one file per worker, named on source_id, rotated
    def write(self, source_id: str, line: str) -> None:
        try:
            self.circuit_breaker.call(
                fn = self._write,
                args_list = [source_id, line]
            )
        except Exception as e:
            self._propagate_error(source_id, e)

    def _write(self, source_id : str, line : str):
        buffer = self._get_buffer(source_id)
        buffer.append(line)
        if len(buffer) >= self.max_lines:
            self._rotate(source_id)

    def _propagate_error(self, source_id : str, e : Exception):
        self.error_sink.emit_internal(
            LogEvent(
                source_id = TaskId(source_id),
                source_type = SourceType.TASK,
                msg = str(e),
                msg_type = MsgType.BACKEND_FAILURE,
                timestamp = time.time()
            )
        )

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
                str(source_id),
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
    def write(self, source_id: str, line: str) -> None:
        pass

@dataclass
class NullBackend:
    def write(self, source_id: str, line: str) -> None:
        pass