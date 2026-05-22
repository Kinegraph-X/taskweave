import time, threading
from typing import Callable, Any, Protocol, IO, Deque
from pathlib import Path
from dataclasses import dataclass, field
from queue import Queue, Full, Empty
from collections import deque

from .backend_exception import BackendTransientFailure, BackendFatalError
from .circuit_breaker import CircuitBreaker

from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.utils import (
    CircuitBreakerConfig,
    PersistConfig,
    TaskId
)

from taskweave_protocol import LogEvent, SourceType, MsgType, BackendErrorKind

class PersistBackend(Protocol):
    config : PersistConfig

@dataclass(kw_only = True)
class FileBackend:
    max_lines : int = 100
    max_files : int = 3
    log_dir: Path = Path(f"{constants.log_dir}")
    config : PersistConfig = field(default_factory = CircuitBreakerConfig.LOCAL.value)
    """ 
    testing implies min_drain_threshold is larger than max_line * max_files
    to avoid triggering the drain on close()
    """
    min_drain_threshold: int | None = None # generally the same as max_lines

    @property
    def _min_drain_threshold(self) -> int:
        return self.min_drain_threshold if self.min_drain_threshold is not None else self.max_lines

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
            error_sink : Callable[[LogEvent], None] # MiniBus.emit_internal, equivalence to stderr
        ):
        self.max_lines = backend.max_lines
        self.max_files = backend.max_files
        self.log_dir = backend.log_dir
        self._min_drain_threshold = backend._min_drain_threshold
        self.source_id = source_id
        self.error_sink = error_sink

        self.file_index : int = 1
        self.buffer : Deque[str] = deque()
        # self.create_dir()
        self.handle : IO[Any] = self._create_handle()
        self._thread_died = False
        self._stop_event = threading.Event()

        self.circuit_breaker = CircuitBreaker(config = backend.config)

        self._queue: Queue = Queue(maxsize=10_000)
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()

    """
    Exemple implementation for short-circuitable backend:
    - depending on CircuitBreakerConfig, we hope for recovery, i.e,
    we may accept timeout, service-unavailable, maybe even several queue_full error, etc.
    - the _write() method should raise: ideal case is it triages
    (distinct logics between disk and network)
    - In network context, _write() maps HTTP error codes to BackendErrorKind
    - Every error is considered transient, and if there's an original exception,
    it is re-raised, encapsulated in a BackendTransientFailure
    - The circuit breaker then triages theses internal exeptions between 
    really transient and fatal, et re-raise as fatal if appropriate, while
    still continuing
    - in disk-access context, the circuit breaker has no other usage than triaging :
    config is threshold = 1, recovery_timeout = 0, so as it definitely opens on 
    the first error, and receives only BackendErrorKinds that it will triage as fatal
    Example : on OSError -> raise BackendTransientFailure.kind = BackendErrorKind.OS_ERROR
      -> prevent further writes -> propagate
      -> backend is forcefully terminated, and the client may forcefully stop the entire task
    """
    def write(self, source_id: str, line: str) -> None:
        if self._thread_died:
            return
        try:
            self.circuit_breaker.call(
                fn = self._write,
                args_list = [source_id, line]
            )
        except BackendFatalError as e:
            exc = BackendFatalError(
                kind = e.kind,
                msg = e.msg
            )
            self._propagate_error(source_id, exc)
            self._cleanup()
        except BackendTransientFailure as e:
            if e.kind == BackendErrorKind.CIRCUIT_OPEN:
                self._propagate_transient_error(source_id, e)
        except:     # non-disk related exceptions in our case (never triggered)
            pass

    def _consume_loop(self):
        try:
            self._loop()
        except Exception as e:
            raise e

    def _loop(self):
        while True and not self._stop_event.is_set():
            line = self._queue.get()
            if line is None:    # poison pill
                break
            try:
                self._append(self.source_id, line)
            except (OSError, IOError) as e: # here we could re-put the message in the queue, to replay
                self._thread_died = True
                exc = BackendTransientFailure(
                    kind = BackendErrorKind.OS_ERROR,
                    msg = e.msg
                )
                self._propagate_error(self.source_id, exc)
                self._cleanup()

    def _write(self, source_id : str, line : str):
        if self._thread_died:
            raise BackendTransientFailure(
                kind = BackendErrorKind.THREAD_DIED,  # risk of double messaging -> test
                msg = f"task {self.source_id} FileBackend : consumer thread died"
            )
        try:
            self._queue.put_nowait(line)
        except Full as e:
            raise BackendTransientFailure(
                kind = BackendErrorKind.QUEUE_FULL,
                msg = "backend dispatch queue full"
            )

    def _append(self, source_id : str, line : str):
        buffer = self._get_buffer()
        buffer.append(line)
        if len(buffer) >= self.max_lines:
            self._rotate()
        self._queue.task_done()

    def _propagate_error(self, source_id : str, e : BackendFatalError):
        self.error_sink(
            LogEvent(
                source_id = TaskId(source_id),
                source_type = SourceType.TASK,
                msg = f"Backend Fatal error : {e.kind} / {e.msg}",
                msg_type = MsgType.BACKEND_FAILURE,
                timestamp = time.time()
            )
        )

    def _propagate_transient_error(self, source_id : str, e : BackendTransientFailure):
        self.error_sink(
            LogEvent(
                source_id = TaskId(source_id),
                source_type = SourceType.TASK,
                msg = f"Backend open : {e.kind} / {e.msg}",
                msg_type = MsgType.BACKEND_OPEN,
                timestamp = time.time()
            )
        )

    def _rotate(self) -> None:
        self.handle.close()
        handle = self._get_handle()
        
        for line in self.buffer:
            handle.write(line) # newline handled by PersistRegistry
        handle.flush()
        self.buffer.clear()
        self._get_file_index()

    def _get_buffer(self) -> Deque[str]:
        return self.buffer
    
    # called by _rotate(): so we start at 0, write 001 the first time
    def _get_file_index(self) -> int:
        if self.file_index >= self.max_files:
            self.file_index = 1
            return 1
        else:
            self.file_index += 1
            return self.file_index

    def create_dir(self):
        path = Path.joinpath(
            self.log_dir,
            str(self.source_id)
        )
        path.mkdir(parents=True, exist_ok=True)

    def _create_handle(self) -> IO[Any] :
        path = Path.joinpath(
            self.log_dir,
            # str(self.source_id),
            f"{self.source_id}_{self.file_index:03d}{constants.log_file_extension}"
        )
        handle = open(path, "w")
        return handle

    def _get_handle(self) -> IO[Any] :
        self.handle = self._create_handle()
        return self.handle

    # case of exit on failure
    def _cleanup(self) -> None :
        # ensure no more messages are added to the queue
        self._thread_died = True

        # empty the queue : we are in degradated mode
        # -> best-effort : keep last 3 in case of queue full
        last_messages = self._drain_last_messages()
        self._thread.join()

        self.buffer.extend(last_messages)
        self._conclude_rotation()

    def _drain_last_messages(self, keep: int = 3) -> list:
        last_messages : Deque[str] = deque(maxlen=keep)

        while True:
            try:
                msg = self._queue.get_nowait()
            except Empty:
                # poison pill the thread
                self._queue.put(None)
                break
            except Exception as e:
                # crash on any edge case (thread dead, race condition with drain, etc.)
                raise e

            last_messages.append(f"[LAST_RESORT] : {msg}")

        return list(last_messages)

    def _conclude_rotation(self):
        try:
            for line in self.buffer:
                self.handle.write(line)
            self.handle.flush()
            self.buffer.clear()
            self.handle.close()
        except OSError:
            pass  # best-effort, we're on cleanup

    def close(self) -> None:
        last_messages = None
        if not self._thread_died and self._queue.qsize() < self._min_drain_threshold:
            self._queue.join()  # clean drain
        else:
            self._stop_event.set()
            last_messages = self._drain_last_messages()

        self._thread_died = True    
        self._queue.put(None)
        self._thread.join()

        if last_messages is not None:
            self.buffer.extend(last_messages)
            self._conclude_rotation()

# future implems
@dataclass
class InMemoryBackend:
    def write(self, source_id: str, line: str) -> None:...
    def close(self) -> None:...

@dataclass
class NullBackend:
    def write(self, source_id: str, line: str) -> None:...
    def close(self) -> None:...