from dataclasses import dataclass

from .field_schema import FieldSchema
from .output_type import OutputType

@dataclass(kw_only = True)
class Schema:
    """
    fetch_schema = Schema(
        fields=[
            FieldSchema("status", JsonSchemaType.INT),
            FieldSchema("url",    JsonSchemaType.STRING),
        ],
        output_type=OutputType.PROGRESS
    )
    """
    fields : list[FieldSchema]
    output_type : OutputType


