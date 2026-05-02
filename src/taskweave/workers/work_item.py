from typing import List, Callable
from dataclasses import dataclass
from taskweave.messages import LogProducer

@dataclass
class WorkItem:
    name : str
    args_list : List[str]
    on_success : Callable | None
    on_failure : Callable | None
    producer : LogProducer | None