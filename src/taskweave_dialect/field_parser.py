from typing import Any, Pattern, Protocol
import re, ast
from dataclasses import dataclass, field

from .dialect_error import DialectErrorKind, MSG_TO_ERROR, DialectError

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
    _rule : Pattern = field(default_factory = lambda: re.compile(""))
    def compile(self):
        if isinstance(self.target, str):
            self.target = re.sub(r"\s", r"\\s", self.target)

        try:
            self._rule = re.compile(self.target)
        except re.error as e:
            error = self.get_error(
                msg = e.msg,
                pos = e.pos
            )
            raise error
        
        if self._rule.groups == 0:
            raise DialectError(
                kind = DialectErrorKind.MISSING_GROUP,
                pattern = self._rule,
                msg = f"Pattern '{self._rule.pattern}' must contain a capturing group — use (...)"
            )

    def parse(self, line : str, group : int, is_test : bool = False):
        m = self._rule.search(line)
        if m:
            return m.group(group)
        
        return None

    def get_error(self, msg : str, pos : int | None):
        if not msg in MSG_TO_ERROR:
            kind = DialectErrorKind.UNKNOWN
        else:
            kind = MSG_TO_ERROR[msg]

        return DialectError(
            kind = kind,
            pattern = self._rule,
            pos = pos,
            msg = msg
        )