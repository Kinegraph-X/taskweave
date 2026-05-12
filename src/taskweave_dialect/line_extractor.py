from typing import Protocol, Any, Pattern
from dataclasses import dataclass
import ast, re

from .field import Field
from taskweave_protocol import JsonSchema

class LineExtractor(Protocol):
    extractors : list[Field]

    def parse(self, line: str) -> dict[str, Any] | None:
        pass
    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.schema for e in self.extractors])

@dataclass(kw_only=True)
class RExtractor:
    extractors : list[Field]
    
    def parse(self, line: str) -> dict[str, Any] | None:
        results: dict[str, Any] = {}

        for extractor in self.extractors:
            value = extractor.parse(line)
            if value is None:
                return None
            results[extractor.schema.name] = value

        return results
    
    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.schema for e in self.extractors])
    
    

# future logics
@dataclass(kw_only=True)
class JsonFieldParser:
    pass

@dataclass(kw_only=True)
class CsvFieldParser:
    pass