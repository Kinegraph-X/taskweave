from typing import Any, TypedDict, Literal
from dataclasses import dataclass, field, asdict
from .field_schema import FieldSchema

JsonTypeProperty = TypedDict("JsonTypeProperty", {
        "type": Literal["string", "number", "boolean"],
    })

@dataclass
class JsonSchemaType(dict):
    type : str = "object"
    properties : dict[str, JsonTypeProperty] = field(default_factory = dict)
    required : list = field(default_factory = list)
    schema_ : str = "http://json-schema.org/draft-07/schema#"

    def to_dict(self):
        d = asdict(self)
        d["$schema"] = d.pop("schema_")

@dataclass  
class JsonSchema:
    fields: list[FieldSchema]
    
    def to_dict(self) -> dict[str, Any]:
        schema = JsonSchemaType().to_dict()
        for field in self.fields:
            schema.properties[field.name] = {type : str(field.type)}
            schema.required.append(field.name)
        
        return schema