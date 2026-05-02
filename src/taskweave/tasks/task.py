import time
from typing import List, Callable
from dataclasses import dataclass, field

from .task_strategy import ExecutionStrategy, LocalProcessStrategy, SubprocessStrategy

from taskweave.persist import PersistStrategy
from taskweave.workers import WorkerManager, WorkerPool
from taskweave.utils import StrSerializable, ReverseStrAccumulator, StrAccumulator
from taskweave.messages import LogProducer, LogEventProducer

@dataclass(kw_only = True)
class Task:
    # def __init__(
    #         self,
    #         *,
    #         name: str,
    #         # manager: WorkerPool | None,     # execution mecanic
    #         cmd: List[str | StrSerializable],
    #         strategy : ExecutionStrategy = SubprocessStrategy(),
    #         producer : LogProducer = LogEventProducer(),
    #         after_complete : Callable | None = None,
    #         early_exit_on_success : bool | Callable = False,
    #         cancellable: bool = True
    #     ):
        # self.name = ReverseStrAccumulator()
        # self.name(name)
        # # self.manager: WorkerPool | None = manager
        # self.cmd: List[str | StrSerializable] = cmd
        # self.strategy : ExecutionStrategy = strategy
        # self.producer = producer
        # self.after_complete : Callable | None = after_complete
        # self.early_exit_on_success : bool | Callable = early_exit_on_success
        # self.cancellable: bool = cancellable
    name : str | StrSerializable
    cmd: List[str | StrSerializable]
    strategy : ExecutionStrategy
    producer : LogProducer = field(default_factory = LogEventProducer)
    persist : PersistStrategy | None = None
    after_complete : Callable | None = None
    early_exit_on_success : Callable | None = None
    cancellable: bool = True

    def __post_init__(self):
        self.name = StrAccumulator(value = self.name)
