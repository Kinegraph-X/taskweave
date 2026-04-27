from typing import Any
from dataclasses import dataclass, field
from .output_type import OutputType
from .line_extractor import RExtractor
from .persist_strategy import PersistStrategy, PersistNone

@dataclass(kw_only=True)
class Classifier:
    rules: dict[RExtractor, OutputType]
    persist: PersistStrategy = field(default_factory = PersistNone)

    def classify(self, line: str) -> tuple[OutputType, dict[str, Any] | None]:
        for parser, output_type in self.rules.items():
            result = parser.parse(line)
            if result is not None:
                self.persist.write(line, output_type)
                return output_type, result
        self.persist.write(line, OutputType.LOG_LINE)
        return OutputType.LOG_LINE, None