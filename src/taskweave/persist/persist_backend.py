import time, threading
from typing import Callable, Any, Protocol, IO, TextIO, Deque
from pathlib import Path
from dataclasses import dataclass, field
from queue import Queue, Full

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

class BackendFailure(Exception):...

class PersistBackend(Protocol):
    max_lines : int
    max_files : int
    log_dir: Path
    config : PersistConfig

@dataclass(kw_only = True)
class FileBackend:
    max_lines : int = 100
    max_files : int = 3
    log_dir: Path = Path(f"{constants.log_folder}")
    config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)

class PersistBackendRunner(Protocol):
    def write(self, source_id: str, line: str) -> None:...
    def close(self) -> None:...

class NoOpBackendRunner:
    def write(self, source_id: str, line: str) -> None:...
    def close(self) -> None:...

class FileBackendRunner:
    """
    one file per worker, named on source_id, rotated
    (old implem was shared accross tasks)
    """
    def __init__(
            self,
            *,
            source_id : str,
            backend : FileBackend,
            error_sink : Callable[[LogEvent], None] # MiniBus.emit_internal
        ):
        self.max_lines = backend.max_lines
        self.max_files = backend.max_files
        self.log_dir = backend.log_dir
        self.source_id = source_id
        self.error_sink = error_sink
        self.config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)
        self._queue: Queue = Queue(maxsize=10_000)
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()

    def __post_init__(self):
        self.handles : dict[str, IO[Any]] = {}
        self.buffers : dict[str, Deque[str]] = {self.source_id : Deque()}
        self.file_indices : dict[str, int] = {}

        self.circuit_breaker = CircuitBreaker(self.config)

    # circuit_breaker accepts multiple "queue full" errors,
    # depending on config, and we hope for recovery
    # on OSError -> thread exits -> propagate -> prevent further writes
    def write(self, source_id: str, line: str) -> None:
        if self._thread_died:
            return
        try:
            self.circuit_breaker.call(
                fn = self._write,
                args_list = [source_id, line]
            )
        except Exception as e:
            self._propagate_error(source_id, e)
            self._cleanup()

    def _consume_loop(self):
        try:
            self._loop()
        except (OSError, IOError) as e:
            self._thread_died = True
            self._propagate_error(self.source_id, e)
            self._cleanup()

    def loop(self):
        while True:
            line = self._queue.get()
            if line is None:    # poison pill
                break
            self._append(self.source_id, line)

    def _write(self, source_id : str, line : str):
        if self._thread_died:
            raise BackendFailure(f"task {self.source_id} FileBackend : consumer thread died")
        try:
            self._queue.put_nowait(line)
        except Full as e:
            raise e

    def _append(self, source_id : str, line : str):
        buffer = self._get_buffer(source_id)
        buffer.append(line)
        if len(buffer) >= self.max_lines:
            self._rotate(source_id)

    def _propagate_error(self, source_id : str, e : Exception):
        self.error_sink(
            LogEvent(
                source_id = TaskId(source_id),
                source_type = SourceType.TASK,
                msg = f"Backend thread died : {str(e)}",
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

        self._queue.put_nowait(None)
        self._thread.join()

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