from typing import Any, Pattern, Protocol
import re, traceback
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
        except re.error as e: # re.error, re.PatternError python >= 3.13
            error = self.get_error(
                msg = e.msg,
                pos = e.pos
            )
            raise error.with_traceback(None) from None
        
        if self._rule.groups == 0:
            raise DialectError(
                kind = DialectErrorKind.MISSING_GROUP,
                pattern = self._rule,
                msg = f"Pattern '{self._rule.pattern}' must contain a capturing group — use (...)"
            ).with_traceback(None) from None

    def parse(self, line : str, group : int, is_test : bool = False):
        m = self._rule.search(line)
        if m:
            return m.group(group)
        
        return None

    def get_error(self, msg : str, pos : int | None):
        for error in MSG_TO_ERROR.keys():
            if error in msg:
                kind = MSG_TO_ERROR[error]
                break
            else:
                kind = DialectErrorKind.UNKNOWN

        return DialectError(
            kind = kind,
            pattern = self._rule,
            pos = pos,
            msg = msg
        )