from typing import Callable, Protocol
from dataclasses import dataclass

from taskweave.messages import LogProducer
from taskweave.utils import StrSerializable
from taskweave.buses import HeartbeatConfig

from taskweave_protocol import LogEvent

@dataclass
class WorkerPool(Protocol):
    max_count : int = 1
    
    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        producer: LogProducer,
        on_start : Callable,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        on_cancel: Callable | None = None,
        heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
    ) -> None: ...
    
    def stop_worker(self, name: str) -> None: ...
    def remove_worker(self, name: str) -> None: ...
    def wait_all(self) -> None: ...

@dataclass
class NoOpPool:
    max_count = 1
    # def subscribe_to_logs(self, cb: Callable[[LogEvent], None]) -> None: ...
    
    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        producer: LogProducer,
        on_start : Callable,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        on_cancel: Callable | None = None,
        heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
    ) -> None: ...
    
    def stop_worker(self, name: str) -> None: ...
    def remove_worker(self, name: str) -> None: ...
    def wait_all(self) -> None: ...