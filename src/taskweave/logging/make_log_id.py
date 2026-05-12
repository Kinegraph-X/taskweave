from typing import cast, Callable
import random
import string
from time import time_ns

from taskweave.utils import TaskId

_ALPHABET = string.digits + string.ascii_letters           # base62

def make_log_id(task_name: TaskId, session_id : str) ->  TaskId:
    ts = hex(time_ns() // 1_000_000)[-8:]  # ms, 8 chars, 2038-proof on 34 years more
    return task_name.increment(f"_{ts}_{session_id}_{_short_suffix()}")

def _short_suffix(length=4) -> str:
    return ''.join(random.choices(_ALPHABET, k=length))