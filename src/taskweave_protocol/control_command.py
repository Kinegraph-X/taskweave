from dataclasses import dataclass, field

from .json_schema import JsonSchema
from .command_field import CommandField

@dataclass(kw_only = True)
class ControlCommand:
    schema : JsonSchema
    fields : list[CommandField]

    def serialize(self):...