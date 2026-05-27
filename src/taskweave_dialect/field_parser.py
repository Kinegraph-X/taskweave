from typing import Any, Pattern, Protocol
import re, traceback
from dataclasses import dataclass, field

from .dialect_error import DialectErrorKind, MSG_TO_ERROR, DialectError
from .validate_rule import ValidateRule

class DialectParser(Protocol):
    def __init__(self, target : Pattern | str = ""):...
    def compile(self):...
    def parse(self, line : str, group : int, is_test : bool = False):...

@dataclass(kw_only = True)
class FieldParser:
    """
    Compile & Parsing step
    """
    target : Pattern | str
    group : int = 1
    _rule : Pattern = field(default_factory = lambda: re.compile(""))
    def compile(self):
        if isinstance(self.target, str):
            self.target = re.sub(r"\s", r"\\s", self.target)

        # may raise, and is expected behavior
        self._rule = ValidateRule.validate(self.target, self.group).rule
        

    def parse(self, line : str, group : int, is_test : bool = False):
        m = self._rule.search(line)
        if m:
            return m.group(group)
        
        return None
