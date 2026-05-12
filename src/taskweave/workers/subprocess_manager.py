import traceback
from dataclasses import dataclass, field
from threading import Thread
from subprocess import Popen, PIPE, STDOUT
from typing import Callable
from queue import Queue
from time import time, sleep

from .worker_pool import WorkerPool
from .task_outcome import TaskOutcome
from .final_status import FinalStatus
from .cancel_intent import CancelIntent
from .completed_task import CompletedTask

from taskweave.utils import TaskId
from taskweave.messages import LogEvent, LogProducer, LogEventProducer, MsgType, SourceType
from taskweave.buses import MiniBus, Heartbeat, HeartbeatConfig


@dataclass(kw_only=True)
class SubProcessManager:
    # Minimal single-process manager — no pool, no queue.
    # Contrast with WorkerManager which handles concurrent workers via max_count.
    # Both implement WorkerPool
    log_bus : MiniBus
    source_id: str = field(default_factory=str)
    producer: LogProducer = field(default_factory=LogEventProducer)
    heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
    _completion_queue: Queue = field(default_factory=Queue)
    # _on_log_cb: Callable[[LogEvent], None] = field(default=lambda evt: None)
    _process: Popen | None = field(init=False, default=None)
    _stdout_thread: Thread | None = field(init=False, default=None)
    _completion_thread: Thread | None = field(init=False, default=None)

    def __post_init__(self):
        self._heartbeat = Heartbeat(
            task_id = self.source_if,
            log_bus = self.log_bus,
            config = self.heartbeat_cfg
        )

    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        on_cancel: Callable | None = None,
        # on_log: Callable | None = None,
        producer: LogProducer | None
    ) -> None:
        self.source_id = name
        self.on_cancel = on_cancel
        
        # name discarded — single process, this mimics Pool[WorkItem], so no WorkItem.name
        self._start(args_list, on_success, on_failure)

    def stop_worker(self, name: str) -> None:
        # name discarded
        if self._process:
            self._process.terminate()
        if self.on_cancel:
            self._execute_callback(self.source_id, self.on_cancel, FinalStatus.STOPPED)

    def remove_worker(self, name: str) -> None:
        pass  # noop

    def _start(
        self,
        args_list: list[str],
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
    ) -> None:
        # allow passing serializable objects references
        cmd = [str(instr) for instr in args_list]
        self._process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True)
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
            self._heartbeat.beat(event)

        self._process.wait()
        self._completion_queue.put(CompletedTask(name=self.source_id))

    # Handles the need for global synchronization
    # on state-snapshots in the main thread
    def _completion_loop(
        self,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
    ):
        assert self._process is not None
        while True:
            result = self._completion_queue.get()
            name = result.name
            if not name == self.source_id:
                self._completion_queue.put(result)
                sleep(.01)
                continue

            if isinstance(CancelIntent, result):
                self.stop_worker(name)
                break
            elif isinstance(CompletedTask, result):
                if self._process.returncode == 0 and on_success:
                    self._execute_callback(
                        self.source_id, on_success, FinalStatus.SUCCESS)
                elif on_failure:
                    self._execute_callback(
                        self.source_id, on_failure, FinalStatus.FAILURE)
                break

    def _execute_callback(self, name: str, cb: Callable, final_status: FinalStatus):
        outcome: TaskOutcome = TaskOutcome(
            name=name,
            status=final_status,
            error=None
        )
        try:
            cb(outcome)
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

    def wait_all(self) -> None: ...
