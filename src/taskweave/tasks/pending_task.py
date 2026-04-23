from typing import List, Callable
from dataclasses import dataclass

@dataclass
class PendingTask:
    name : str
    args_list : List[str]
    on_success : Callable | None
    on_failure : Callable | None