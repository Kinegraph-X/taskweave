from typing import Callable
import threading, time

from .heartbeat_config import HeartbeatConfig

from taskweave_protocol import MsgType, LogEvent, SourceType
from taskweave.buses import MiniBus
from taskweave.utils import TaskId

class Heartbeat:
    """
    config.max_attempts could be a tool for small adjustments, but
    is not meant to be documented.
    The smaller the ratio between threshold & max_threshold is, 
    the littler the timing threads loops.
    """
    def __init__(
        self,
        *,
        source_id : str,
        log_bus : MiniBus,
        config : HeartbeatConfig = HeartbeatConfig(),
        sleep : Callable = time.sleep
    ):
        self.source_id = source_id
        self._log_bus = log_bus
        self._config = config
        self._sleep = sleep
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
        if event.msg_type in (
            MsgType.PROGRESS,
            MsgType.EVENT,
            MsgType.LOG_LINE,
            MsgType.BANNER,
            MsgType.ERROR
        ):
            self._attempts = 0

        self._log_bus.emit(event)

    def _heartbeat_loop(
            self
    ):
        while self._attempts < self._config.max_attempts:
            delay = self._config.threshold * self._attempts
            if delay < self._config.max_threshold:
                self._sleep(delay)
                self._attempts += 1
            else:
                break

        self._log_bus.emit(
            LogEvent(
                source_id = TaskId(self.source_id),
                msg_type = MsgType.HEARTBEAT_TIMEOUT,
                msg = "silent task",
                timestamp = time.time(),
                source_type = SourceType.TASK
            )
        )

    def exit(self):
        self._heartbeat_thread.stop()