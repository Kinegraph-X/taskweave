from typing import Callable, Protocol
from taskweave.messages import LogEvent, LogProducer
from taskweave.utils import StrSerializable
from taskweave.buses import HeartbeatConfig

class WorkerPool(Protocol):
    # def subscribe_to_logs(self, cb: Callable[[LogEvent], None]) -> None: ...
    
    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        producer: LogProducer,
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        on_cancel: Callable | None = None,
        heartbeat_cfg : HeartbeatConfig = HeartbeatConfig(),
        producer : LogProducer | None
    ) -> None: ...
    
    def stop_worker(self, name: str) -> None: ...
    def remove_worker(self, name: str) -> None: ...
    def wait_all(self) -> None: ...