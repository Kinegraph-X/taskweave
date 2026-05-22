from typing import Protocol, Any, Pattern, Callable, runtime_checkable
from dataclasses import dataclass, field
from time import time
import ast, re, traceback

from .field import Field
from .dialect_error import DialectErrorKind, DialectError

from taskweave.buses import MiniBus
from taskweave.utils import TaskId

from taskweave_protocol import JsonSchema, LogEvent, MsgType

class LineExtractor(Protocol):
    extractors : list[Field]

    def parse(self, line: str, is_test : bool = False) -> dict[str, Any] | None:
        pass
    def test(self, line : str, excepted : dict | None):
        pass
    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.schema for e in self.extractors])

@runtime_checkable
class LineExtractorRunner(Protocol):
    extractors : list[Field]

    def parse(self, line: str, is_test : bool = False) -> dict[str, Any] | None:
        pass
    



class RExtractor:
    extractors : list[Field]
    _runner : LineExtractorRunner = field(init = False)

    def parse(self, line: str, is_test : bool = False) -> dict[str, Any] | None:
        if isinstance(self._runner, LineExtractorRunner):
            return self._runner.parse(line, is_test)
        else:
            raise RuntimeError('uninitialized type : RExtractor must host a MiniBus for logging')

    def make_runner(self, source_id : str, log_bus : MiniBus):
        self._runner = RExtractorRunner(
            extractors = self.extractors,
            _source_id = source_id,
            _log_bus = log_bus
        )

    def schema(self) -> JsonSchema:
        return JsonSchema(fields=[e.schema for e in self.extractors])

    def test(self, line : str, excepted : dict | None):
        self._runner.parse(line = line, is_test = True)


@dataclass(kw_only=True)
class RExtractorRunner:
    extractors : list[Field]
    _log_bus : MiniBus
    _source_id : str
    
    def parse(self, line: str, is_test : bool = False) -> dict[str, Any] | None:
        results: dict[str, Any] = {}
        failures : list = []

        for extractor in self.extractors:
            try:
                value = extractor.parse(line, is_test)
            except Exception as e:
                failures.append(extractor.parser._rule.pattern)
                self._log_bus.emit_internal(
                    LogEvent(
                        source_id = TaskId(self._source_id),
                        msg_type = MsgType.MULTIPLE_MATCHES,
                        msg = f"partial match on dialect: extractor has the following rule : {str(extractor.parser._rule.pattern)}",
                        timestamp = time()
                    )
                )
                if is_test:
                    traceback.print_exception(e)

            if value is None:
                continue
            results[extractor.schema.name] = value

        if len(results) != len(self.extractors):
            if is_test:
                traceback.print_exception(
                    DialectError(
                        kind = DialectErrorKind.TEST_FAILED,
                        msg = f"not every fields matched on test case (might be by design). The following failed : {str(failures)}"
                    )
                )
            return None

        return results
    
    

# future logics
@dataclass(kw_only=True)
class JsonFieldParser:
    pass

@dataclass(kw_only=True)
class CsvFieldParser:
    pass