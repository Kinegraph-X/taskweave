import time
from typing import List, Callable
from dataclasses import dataclass, field

from .task_strategy import ExecutionStrategy, SynchronousStrategy, TaskRunner, NoOpRunner

from taskweave.persist import PersistStrategy, PersistConfig
from taskweave.workers import WorkerManager, WorkerPool
from taskweave.utils import CmdParam, TaskId, ReverseStrAccumulator, StrAccumulator
from taskweave.messages import LogProducer, LogEventProducer

@dataclass(kw_only = True)
class Task:
    name : str
    cmd: List[str | CmdParam]
    strategy : ExecutionStrategy = field(default_factory = SynchronousStrategy)
    _runner : TaskRunner = field(default = NoOpRunner(), init = False)
    producer : LogProducer = field(default_factory = LogEventProducer)
    persist : PersistStrategy | None = None
    config : PersistConfig | None = None
    early_exit_on_success : Callable | None = None
    cancellable: bool = True
    on_success : Callable | None = None
    on_failure : Callable | None = None
    on_cancel : Callable | None = None
    on_finally : Callable | None = None

    def __post_init__(self):
        self.name = TaskId(self.name)
        if self.config:
            self.persist.config = self.config
