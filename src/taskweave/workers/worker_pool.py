from typing import Callable, Protocol
from taskweave.messages import LogEvent, LogProducer

class WorkerPool(Protocol):
    def subscribe_to_log(self, cb: Callable[[LogEvent], None]) -> None: ...
    
    def add_worker(
        self,
        *,
        name: str,
        args_list: list[str],
        on_success: Callable | None = None,
        on_failure: Callable | None = None,
        producer : LogProducer | None
    ) -> None: ...
    
    def stop_worker(self, name: str) -> None: ...
    def remove_worker(self, name: str) -> None: ...