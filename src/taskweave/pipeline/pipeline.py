import time
from uuid import uuid4
from typing import List, Set, Callable
from dataclasses import dataclass, field

from taskweave.snapshots import PipelineSnapshot
from taskweave.tasks import PipelineTask, Task
from taskweave.states import PipelineState
from taskweave.utils import TaskId

@dataclass(kw_only = True)
class Pipeline():
    id : TaskId = field(default_factory = lambda: TaskId(uuid4().hex))
    tasks : List[Task] = field(default_factory = list)