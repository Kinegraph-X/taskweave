from typing import Protocol, TypedDict
from dataclasses import dataclass
from queue import Queue
import types

from .task_runner import TaskRunner

from taskweave.buses import MiniBus
from taskweave.utils import TaskId

class ExecutionContext(Protocol):...

class NeedsSourceId(Protocol):
    source_id : TaskId

class NeedsBus(Protocol):
    event_bus : MiniBus

class NeedsPools(Protocol):
    pools : dict[str, TaskRunner]

class NeedsQueue(Protocol):
    global_completion_queue : Queue

class PoolExecutionContext(
    ExecutionContext,
    NeedsPools,
    Protocol
    ):...
class SynchronousExecutionContext(
    ExecutionContext,
    NeedsSourceId,
    NeedsQueue,
    NeedsBus,
    Protocol
    ):...

@dataclass(kw_only = True)
class ExecutionPool:
    source_id : TaskId
    pools : dict[str, TaskRunner]
    global_completion_queue : Queue
    event_bus : MiniBus