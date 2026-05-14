from typing import Callable
import threading, time

from .heartbeat_config import HeartbeatConfig

from taskweave.messages import MsgType, LogEvent, SourceType
from taskweave.buses import MiniBus
from taskweave.utils import TaskId

"""
class FakeClock:
    def __init__(self):
        self._time = 0.0
    
    def tick(self, seconds: float) -> None:
        self._time += seconds
    
    def __call__(self) -> float:
        return self._time

class FakeSleep:
    def __init__(self, clock: FakeClock):
        self._clock = clock
    
    def __call__(self, seconds: float) -> None:
        self._clock.tick(seconds)  # avance le temps sans attendre

# dans le test
clock = FakeClock()
sleep = FakeSleep(clock)
hb = HeartBeat(threshold=5, max_attempts=3, clock=clock, sleep=sleep)

hb.beat(event)       # reset attempts
sleep(6.0)           # avance le temps fictif
assert not hb.is_timed_out()

sleep(20.0)          # avance encore
assert hb.is_timed_out()
"""

class Heartbeat:
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
        if event.msg_type in (MsgType.PROGRESS, MsgType.EVENT, MsgType.LOG_LINE, MsgType.BANNER, MsgType.ERROR):
            self._attempts = 0

        self._log_bus.emit(event)

    def _heartbeat_loop(
            self
    ):
        while self._attempts < self._config.max_attempts:
            delay = min(
                self._config.threshold * self._attempts,
                self._config.max_threshold
            )
            self._sleep(delay)
            self._attempts += 1

        self._log_bus.emit(
            LogEvent(
                source_id = TaskId(self.source_id),
                msg_type = MsgType.HEARTBEAT_ERROR,
                msg = "silent task",
                timestamp = time.time(),
                source_type = SourceType.TASK
            )
        )

    def exit(self):
        self._heartbeat_thread.stop()