from typing import Pattern
from enum import Enum
from dataclasses import dataclass

class DialectErrorKind(Enum):
    INVALID_ESCPE = "invalid escape in log parser declaration"
    BAD_REPETITION = "bad repetition in log parser declaration"
    UNTERMINATED_GROUP = "unterminated group in log parser declaration"

    MISSING_GROUP = "missing group in log parser declaration"
    OUT_OF_BOUND_GROUP = "out of bound group"
    INCOMPATIBLE_JSON_TYPE = "incompatible json type between schema and actual output"

    PARTIAL_MATCH = "partial match on log parser"
    MULTIPLE_MATCHES = "multiples matches on log parser"
    TEST_FAILED = "log extractor test failed"

    UNKNOWN = "unknown"

MSG_TO_ERROR : dict[str, DialectErrorKind] = {
    "invalid escape" : DialectErrorKind.INVALID_ESCPE,
    "bad repetition" : DialectErrorKind.BAD_REPETITION,
    "unterminated group" : DialectErrorKind.UNTERMINATED_GROUP,

    "missing group" : DialectErrorKind.MISSING_GROUP,
    "out of bound group" : DialectErrorKind.OUT_OF_BOUND_GROUP,
    "incompatible json type" : DialectErrorKind.INCOMPATIBLE_JSON_TYPE,
    
    "partial match" : DialectErrorKind.PARTIAL_MATCH,
    "multiples matches" : DialectErrorKind.MULTIPLE_MATCHES,
    "extractor test failed" : DialectErrorKind.TEST_FAILED
}

@dataclass(kw_only = True)
class DialectError(Exception):
    kind : DialectErrorKind
    pattern : Pattern | None = None
    pos : int | None = None
    msg : str