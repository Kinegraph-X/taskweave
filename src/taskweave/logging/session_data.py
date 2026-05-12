from typing import List
from dataclasses import dataclass, field
from time import time

from taskweave.utils import TaskId

@dataclass(kw_only=True)
class SessionData:
    timestamp: float = field(default_factory = time)
    list: List[TaskId] = field(default_factory = list)