from typing import Protocol, Any, Pattern
from dataclasses import dataclass
import ast, re

from .field import FieldExtractor
from .json_schema import JsonSchema
from .json_schema_type import JsonSchemaType

@dataclass(kw_only=True)
class LineExtractor(Protocol):
    extractors : list[FieldExtractor]

    def parse(self, line: str) -> dict[str, Any] | None:
        pass
    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.field for e in self.extractors])

@dataclass(kw_only=True)
class RExtractor:
    extractors : list[FieldExtractor]
    
    def parse(self, line: str) -> dict[str, Any] | None:
        results: dict[str, Any] = {}

        for extractor in self.extractors:
            value = extractor.parse(line)
            if value is None:
                return None
            results[extractor.field.name] = value

        return results
    
        # results = {}
        # for extractor in self.extractors:
        #     results[extractor.field.name] = extractor.parse(line)

        # return results if all(v is not None for v in results.values()) else None
    
    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.field for e in self.extractors])
    
    

# future logics
@dataclass(kw_only=True)
class JsonFieldParser:
    pass

@dataclass(kw_only=True)
class CsvFieldParser:
    pass