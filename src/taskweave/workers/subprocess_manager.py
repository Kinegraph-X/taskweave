from dataclasses import dataclass, field
from threading import Thread
from subprocess import Popen, PIPE, STDOUT
from typing import Callable

from taskweave.messages import LogEvent, LogProducer, LogEventProducer
from .worker_pool import WorkerPool


@dataclass(kw_only=True)
class SubProcessManager:
    # Minimal single-process manager — no pool, no queue.
    # Contrast with WorkerManager which handles concurrent workers via max_count.
    # Both implement WorkerPool 
    source_id : str
    producer: LogProducer = field(default_factory=LogEventProducer)
    _on_log_cb: Callable[[LogEvent], None] | None = field(init=False, default=None)
    _process: Popen | None = field(init=False, default=None)
    _thread: Thread | None = field(init=False, default=None)

    def subscribe_to_log(self, cb: Callable[[LogEvent], None]) -> None:
        self._on_log_cb = cb

    def add_worker(
            self,
            *,
            name: str,
            args_list: list[str],
            on_success: Callable | None = None,
            on_failure: Callable | None = None,
            producer : LogProducer | None
        ) -> None:
        # name discarded — single process, no pool to register to
        self._start(args_list, on_success, on_failure)

    def stop_worker(self, name: str) -> None:
        # name discarded
        if self._process:
            self._process.terminate()

    def remove_worker(self, name: str) -> None:
        pass  # noop

    def _start(
            self,
            args_list : list[str],
            on_success: Callable | None = None,
            on_failure: Callable | None = None,
        ) -> None:
        self._process = Popen(args_list, stdout=PIPE, stderr=STDOUT, text=True)
        self._thread = Thread(
            target=self._poll_stdout,
            args=(on_success, on_failure),
            daemon=True,
        )
        self._thread.start()

    def _poll_stdout(
            self,
            on_success: Callable | None = None,
            on_failure: Callable | None = None,
        ) -> None:
        assert self._process is not None
        assert self._process.stdout is not None

        for line in self._process.stdout:
            self.producer.on_line(source_id = self.source_id, line=line.rstrip())

        self._process.wait()
        if self._process.returncode == 0 and on_success:
            on_success()
        elif on_failure:
            on_failure()