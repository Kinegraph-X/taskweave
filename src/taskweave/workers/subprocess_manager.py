import traceback
from dataclasses import dataclass, field
from threading import Thread, Event, Lock
from subprocess import Popen, PIPE, STDOUT
from typing import Callable
from queue import Queue
from time import time, sleep

from .worker_pool import WorkerPool
from .task_outcome import TaskOutcome
from .cancel_intent import CancelIntent
from .completed_task import CompletedTask

from taskweave.messages import LogProducer, LogEventProducer
from taskweave.states import FinalStatus

from taskweave.utils import TaskId
from taskweave_protocol import LogEvent, MsgType, SourceType
from taskweave.buses import MiniBus, Heartbeat, HeartbeatConfig


@dataclass(kw_only=True)
class SubProcessManager:
    """
    Minimal single-process manager — no pool, and potentially no shared queue.
    Mimics WorkerManager which handles concurrent workers, but is pure one-shot
    Both implement WorkerPool as a minimal generic
    """
    log_bus : MiniBus
    source_id: str
    producer: LogProducer = field(default_factory=LogEventProducer)
    _process: Popen | None = field(init=False, default=None)
    _stdout_thread: Thread | None = field(init=False, default=None)
    _completion_thread: Thread | None = field(init=False, default=None)
    _done : Event = Event()
    _init : Event = Event()
    max_count : int = 1

    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        on_start: Callable,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        on_cancel: Callable | None = None,
        heartbeat_cfg : HeartbeatConfig = HeartbeatConfig(),
        producer: LogProducer | None        # not used
    ) -> None:
        if self._done.is_set() or self._init.is_set(): # prevent multiple calls to add_worker
            return
        self.source_id = name
        self.on_cancel = on_cancel

        self._heartbeat = Heartbeat(
                source_id = self.source_id,
                log_bus = self.log_bus,
                config = heartbeat_cfg
            )
        
        # name discarded — single process, this mimics Pool[WorkItem], so no WorkItem.name
        self._start(args_list, on_start, on_success, on_failure)
        self._init.set()

    def stop_worker(self, name: str) -> None:   # name discarded
        if self._process:
            self._process.terminate()
        if self.on_cancel:
            self._execute_callback(self.source_id, self.on_cancel, FinalStatus.CANCELED)
        self._done.set()

    def remove_worker(self, name: str) -> None:
        pass  # noop

    def _start(
        self,
        args_list: list[str],
        on_start: Callable,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
    ) -> None:
        self._process = Popen(args_list, stdout=PIPE, stderr=STDOUT, text=True)
        self._stdout_thread = Thread(
            target=self._poll_stdout,
            daemon=True,
        )
        self._stdout_thread.start()
        self._completion_thread = Thread(
            target=self._completion_loop,
            args=(on_success, on_failure),
            daemon=True,
        )

        on_start()
        self._completion_thread.start()

    def _poll_stdout(
        self
    ) -> None:
        assert self._process is not None
        assert self._process.stdout is not None

        for line in self._process.stdout:
            event = self.producer.on_line(
                source_id=self.source_id,
                line=line.rstrip()
            )
            self._heartbeat.beat(event) # log_bus is called by heartbeat

        self._process.wait()

    # Handles the need for global synchronization
    # on state-snapshots in the main thread
    def _completion_loop(
        self,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
    ):
        assert self._process is not None
        self._process.wait()

        if self._process.returncode == 0 and on_success:
            self._execute_callback(
                self.source_id, on_success, FinalStatus.SUCCESS)
        elif on_failure:
            self._execute_callback(
                self.source_id, on_failure, FinalStatus.FAILURE)
            
        self._done.set()
            
    def _execute_callback(self, name: str, cb: Callable, final_status: FinalStatus):
        # enforce no race condition between FAILED/CANCELED or SUCCESS/CANCELED
        if self._done.is_set():
            return
        
        try:
            cb()
        except Exception as e:
            stacktrace = traceback.format_exc()
            event = LogEvent(
                msg_type=MsgType.ERROR,
                msg=f"{e}\n{stacktrace}",
                source_id= TaskId(name),
                source_type=SourceType.TASK,
                timestamp=time()
            )
            self.log_bus.emit(event)

            print(
                f"SubProcessManager._completion_thread thread for {name} raised : '{e}' when calling completion cbs")
            print(stacktrace)

    def wait_all(self) -> None:
        self._done.wait()
