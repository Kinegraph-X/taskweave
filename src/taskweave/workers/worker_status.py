from typing import List
from dataclasses import dataclass

@dataclass
class WorkerStatus:
    status: str
    message_stack: List[str]