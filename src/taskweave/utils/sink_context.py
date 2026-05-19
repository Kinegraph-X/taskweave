from typing import Protocol, Any
from dataclasses import dataclass

@dataclass(kw_only = True)
class SinkContext():
    backend : Any = None
    source_id : str