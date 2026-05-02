from typing import cast, Callable
from time import time_ns

from taskweave.utils import StrSerializable

def make_log_id(task_name: str | StrSerializable) ->  str | StrSerializable:
    ts = hex(time_ns() // 1_000_000)[-8:]  # ms, 8 chars, 2038-proof on 34 years more
    if isinstance(task_name, StrSerializable):
        return cast(Callable, task_name)(f"_{ts}")
    
    return f"{task_name}_{ts}"