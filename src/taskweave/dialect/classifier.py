from typing import Any, Generator
from dataclasses import dataclass, field
from .output_type import OutputType
from .line_extractor import RExtractor
from .persist_strategy import PersistStrategy, PersistNone
from .json_schema import JsonSchema
from .parse_result import ParseResult

@dataclass(kw_only=True)
class Classifier:
    rules: dict[RExtractor, OutputType]
    persist: PersistStrategy = field(default_factory = PersistNone)
    _names : dict[RExtractor, str] = {}

    def __post_init__(self):
        for extractor in self.rules.keys():
            name = "_".join([e.name for e in extractor])
            if name in self.names.values():
                raise ValueError(
                    f"Two extractors share a field name '{name}' — "
                    f"provide a unique combination of 'name's on each RExtractor to disambiguate"
                )
            self._names[extractor] = name
        # self.names = {(k, "_".join([e.name for e in k])) for k in self.extractors.keys()}

    def classify(self, line: str) -> Generator[tuple[str, OutputType, ParseResult], None, None]:
        # Generator pattern: yields one entry per extractor — first match wins,
        # remaining extractors yield matched=False without calling parse().
        # Note: a simple loop constructing a dict would work here,
        # but the generator naturally models the "produce all, short-circuit on match" contract.
        matched = False
        for extractor, output_type in self.rules.items():
            if not matched:
                result = extractor.parse(line)
                if result is not None:
                    yield self._names[extractor], output_type, ParseResult(matched = True, content = result)
                else:
                    yield self._names[extractor], output_type, ParseResult(matched = False)
        if not matched:
            self.persist.write(line, OutputType.DISCARD)
        else:
            self.persist.write(line, output_type)

    def schema(self) -> dict[str, JsonSchema]:
        schema : dict[str, JsonSchema] = {}
        for extractor in self.rules.keys():
            schema[self._names[extractor]] = extractor.schema()

        return schema
