from dataclasses import dataclass
from .json_schema_type import JsonSchemaType

@dataclass
class FieldSchema:
    name: str
    type: JsonSchemaType
    description: str = ""
    optional: bool = False