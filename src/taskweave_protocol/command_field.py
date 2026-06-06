from typing import Any
from dataclasses import dataclass, field

from .json_schema import JsonSchema

@dataclass(kw_only = True)
class CommandField:
    schema : JsonSchema
    value : Any