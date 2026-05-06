from typing import Any
from dataclasses import dataclass

from .final_status import FinalStatus

@dataclass(kw_only = True, frozen=True)
class TaskOutcome:
    name: str
    status: FinalStatus      # SUCCESS | FAILURE | CANCELLED
    # result: Any | None       # not implemented: returned value if success
    error: Exception | None  # exception if failure
    # duration: float         # not implemented