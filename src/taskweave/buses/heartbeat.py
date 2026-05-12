from dataclasses import dataclass
import threading, time

from .heartbeat_config import HeartbeatConfig

from taskweave.messages import MsgType, LogEvent, SourceType
from taskweave.buses import MiniBus
from taskweave.utils import TaskId

class Heartbeat:
    def __init__(
        self,
        *,
        task_id : str,
        log_bus : MiniBus,
        config : HeartbeatConfig = HeartbeatConfig()
    ):
        self.task_id = task_id
        self._log_bus = log_bus
        self._config = config
        self._attempts = 0
        self._heartbeat_thread = threading.Thread(
            target = self._heartbeat_loop,
            daemon = True
        )
        self._heartbeat_thread.start()

    def beat(
            self,
            event : LogEvent
        ):
        if event.msg_type in (MsgType.PROGRESS, MsgType.EVENT, MsgType.LOG_LINE, MsgType.BANNER, MsgType.ERROR):
            if self._attempts < self._config.max_attempts:
                self._attempts = 0

        self._log_bus.emit(event)

    def _heartbeat_loop(
            self
    ):
        while self._attempts < self._config.max_attempts:
            time.sleep(
                self._config.threshold ** self._attempts
            )
            self._attempts += 1

        self._log_bus.emit(
            LogEvent(
                source_id = TaskId(self.task_id),
                msg_type = MsgType.HEARTBEAT_ERROR,
                msg = "silent task",
                timestamp = time.time(),
                source_type = SourceType.TASK
            )
        )

    def exit(self):
        self._heartbeat_thread.stop()