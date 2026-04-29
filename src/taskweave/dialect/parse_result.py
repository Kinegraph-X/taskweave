from typing import Any
from dataclasses import dataclass

@dataclass
class ParseResult:
    matched: bool
    content: dict[str, Any] | None = None