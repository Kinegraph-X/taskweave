import json
from typing import Pattern
from enum import Enum
from dataclasses import dataclass

class DialectErrorKind(str, Enum):
    UNTERMINATED_CHARACTER_CLASS = "unterminated character class in log parser declaration"
    QUANTIFIER_WITHOUT_TARGET = "quantifier without target in log parser declaration"
    MULTIPLE_QUANTIFIERS = "multiple quantifiers in log parser declaration"
    INVALID_ESCPE = "invalid escape in log parser declaration"
    UNTERMINATED_GROUP = "unterminated group in log parser declaration"
    INVALID_NAMED_GROUP = "invalid named group in log parser declaration"
    INVALID_GROUP_REFERENCE = "invalide group reference in log parser declaration"
    INVALID_LOOK_BEHIND = "invalid look-behind in log parser declaration"

    MISSING_GROUP = "missing group in log parser declaration"
    OUT_OF_BOUND_GROUP = "out of bound group in log parser declaration"
    NAMED_GROUP_FORBIDDEN = "named groups are forbidden in log parser declaration"
    UNION_FORBIDDEN = "unions are considered bad practice"
    INCOMPATIBLE_JSON_TYPE = "incompatible json type between schema and actual output"

    PARTIAL_MATCH = "partial match on log parser"
    MULTIPLE_MATCHES = "multiples matches on log parser"
    NO_MATCH = "no match"
    TEST_FAILED = "log extractor test failed"

    UNKNOWN = "unknown"

MSG_TO_ERROR : dict[str, DialectErrorKind] = {
    "unterminated character set" : DialectErrorKind.UNTERMINATED_CHARACTER_CLASS,
    "nothing to repeat" : DialectErrorKind.QUANTIFIER_WITHOUT_TARGET,
    "multiple repeat" : DialectErrorKind.MULTIPLE_QUANTIFIERS,
    "bad escape" : DialectErrorKind.INVALID_ESCPE,
    "bad character" : DialectErrorKind.INVALID_NAMED_GROUP,
    "unterminated subpattern" : DialectErrorKind.UNTERMINATED_GROUP,
    "invalid group reference" : DialectErrorKind.INVALID_GROUP_REFERENCE,
    "look-behind" : DialectErrorKind.INVALID_LOOK_BEHIND,

    "missing group" : DialectErrorKind.MISSING_GROUP,
    "out of bound group" : DialectErrorKind.OUT_OF_BOUND_GROUP,
    "incompatible json type" : DialectErrorKind.INCOMPATIBLE_JSON_TYPE,
    
    "partial match" : DialectErrorKind.PARTIAL_MATCH,
    "multiples matches" : DialectErrorKind.MULTIPLE_MATCHES,
    "no match" : DialectErrorKind.NO_MATCH,
    "extractor test failed" : DialectErrorKind.TEST_FAILED
}

@dataclass(kw_only = True)
class DialectError(Exception):
    kind : DialectErrorKind
    pattern : Pattern | None = None
    pos : int | None = None
    msg : str
    failures : list[tuple[str, Pattern, DialectErrorKind]] | None = None

    def __str__(self):
        data = {
            "kind": self.kind,
            "pattern": self.pattern,
            "pos": self.pos,
            "msg" : self.msg,
            "failures" : self.failures
        }

        return (
            "DialectError\n"
            + json.dumps(data, indent=2, ensure_ascii=False)
        )