from typing import Any, Pattern
import re, ast
from dataclasses import dataclass
from .field_schema import FieldSchema

from taskweave.messages import MsgType

class Field:
    def __init__(
        self,
        *,
        schema: FieldSchema,
        target : str | Pattern,
        keyword: str,
        separator: str = "=",
        group : int = 1,
        category: MsgType = MsgType.PROGRESS
    ):
        if not target:
            self.rule = re.compile(rf"{keyword}\s*{separator}\s*([^\s]+?)")
        else:
            target = re.sub(r"\s", "\s", target)
            self.rule = re.compile(rf"{target}")

    def __post_init__(self) -> None:
        if isinstance(self.rule, re.Pattern):
            if self.rule.groups == 0:
                raise ValueError(
                    f"Pattern '{self.rule.pattern}' must contain a capturing group — use (...)"
                )
            if self.group > self.rule.groups:
                raise ValueError(
                    f"Pattern '{self.rule.pattern}' has {self.rule.groups} group(s), "
                    f"but group={self.group} was requested"
                )
        elif self.group != 1:
            raise ValueError(
                "group parameter is only valid for Pattern targets, not str"
            )

    def parse(self, line : str) -> Any | None:
        matches = self.rule.match(line)
        if matches is not None and len(matches) > self.group:
                return self.cast(matches[self.group])
    
    def cast(self, value : Any) -> Any :
        match type(ast.literal_eval(value)):
            case "<class 'int'>":
                return int(value)
            case "<class 'float'>":
                return float(value)
            case "<class 'str'>":
                return str(value)
            case _ :
                return str(value)