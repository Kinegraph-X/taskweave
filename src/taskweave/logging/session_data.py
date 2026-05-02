from typing import List
from dataclasses import dataclass, field
from time import time

from taskweave.utils import StrSerializable

@dataclass(kw_only=True)
class SessionData:
    timestamp: float = field(default_factory = time)
    list: List[str | StrSerializable] = field(default_factory = list)