from typing import Any, Pattern
import re, ast
from taskweave_protocol import FieldSchema, OutputType, JsonSchemaType

class Field:
    def __init__(
        self,
        *,
        schema: FieldSchema,
        target : str | Pattern,
        keyword: str = "",      # legacy
        separator: str = "=",   # legacy
        group : int = 1,
        category: OutputType = OutputType.PROGRESS
    ):
        if not target:
            self.rule = re.compile(rf"{keyword}\s*{separator}\s*([^\s]+?)")
        elif isinstance(target, str):
            target = re.sub(r"\s", "\s", target)
            self.rule = re.compile(rf"{target}")
        else:
            self.rule = target

        self.schema = schema
        self.group = group
        self.category = category

    def __post_init__(self) -> None:
        if self.rule.groups == 0:
            raise ValueError(
                f"Pattern '{self.rule.pattern}' must contain a capturing group — use (...)"
            )
        if self.group > self.rule.groups:
            raise ValueError(
                f"Field Definition : target '{self.rule.pattern}' has {self.rule.groups} group(s), "
                f"but group={self.group} was requested"
            )
        # if self.group != 1:
        #     raise ValueError(
        #         "group parameter is only valid for Pattern targets, not str"
        #     )

    def parse(self, line : str) -> Any | None:
        matches = self.rule.findall(line)
        if matches is not None and len(matches) > self.group:
            return self.cast(matches[self.group])
        return None
    
    def cast(self, value : Any) -> Any :
        match type(ast.literal_eval(value)):
            case "<class 'int'>":
                if self.schema.type == JsonSchemaType.INT:
                    return int(value)
                else:
                    raise ValueError(f'literal eval incompatible with declared field type in schema : expected {self.schema.type}, got "int')
            case "<class 'float'>":
                if self.schema.type == JsonSchemaType.NUMBER:
                    return float(value)
                else:
                    raise ValueError(f'literal eval incompatible with declared field type in schema : expected {self.schema.type}, got "number')
            case "<class 'str'>":
                if self.schema.type == JsonSchemaType.STRING:
                    return str(value)
                else:
                    raise ValueError(f'literal eval incompatible with declared field type in schema : expected {self.schema.type}, got "string')
            case _ :
                return str(value)