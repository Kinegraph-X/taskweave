from typing import Any, Pattern
from dataclasses import dataclass, field

from .dialect_error import DialectErrorKind

@dataclass(kw_only = True)
class ExtractionResult:
    results : dict[str, Any] = field(default_factory = dict)
    failures : list[tuple[str, Pattern, DialectErrorKind]] = field(default_factory = list)