import time
from typing import List, Callable
from dataclasses import dataclass
from taskweave.tasks import ExecutionStrategy, LocalProcessStrategy
from taskweave.workers import WorkerManager
from taskweave.utils import StrSerializable, ReverseStrAccumulator

class Task:
    def __init__(
            self,
            name: str,
            manager: WorkerManager | None,     # execution mecanic
            cmd: List[str | StrSerializable],
            strategy : ExecutionStrategy = LocalProcessStrategy(),
            after_complete : Callable | None = None,
            early_exit_on_success : bool | Callable = False,
            cancellable: bool = True,
        ):
        self.name = ReverseStrAccumulator()
        self.name(name)
        self.manager: WorkerManager | None = manager
        self.cmd: List[str | StrSerializable] = cmd
        self.strategy : ExecutionStrategy = strategy
        self.after_complete : Callable | None = after_complete
        self.early_exit_on_success : bool | Callable = early_exit_on_success
        self.cancellable: bool = cancellable
