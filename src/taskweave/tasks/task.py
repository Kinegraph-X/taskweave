import time
from typing import List, Callable
from dataclasses import dataclass, field

from .task_strategy import ExecutionStrategy, SynchronousStrategy
from .task_runner import TaskRunner, NoOpRunner

from taskweave.persist import PersistBackend
from taskweave.utils import CmdParam, TaskId, ReverseStrAccumulator, StrAccumulator
from taskweave.messages import LogProducer, LogEventProducer

@dataclass(kw_only = True)
class Task:
    name : str | TaskId
    cmd: List[str | CmdParam]
    strategy : ExecutionStrategy = field(default_factory = SynchronousStrategy)
    _runner : TaskRunner = field(default = NoOpRunner(), init = False)
    producer : LogProducer = field(default_factory = LogEventProducer)
    backend : PersistBackend | None = None
    early_exit_on_success : Callable[[], bool] | None = None
    cancellable: bool = True
    on_success : Callable | None = None
    on_failure : Callable | None = None
    on_cancel : Callable | None = None
    on_finally : Callable | None = None

    def __post_init__(self):
        #type guard just for mypy : name is str
        if isinstance(self.name, str):
            self.name = TaskId(self.name)
