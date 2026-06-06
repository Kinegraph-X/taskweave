from typing import Protocol, Any, Pattern, Callable, runtime_checkable
from dataclasses import dataclass, field
from time import time
import ast, re, traceback, json

from .field import Field
from .dialect_error import DialectErrorKind, DialectError
from .diagnostics import Diagnostics
from .static_diagnostics import StaticDiagnostics
from .diagnostic_info import DiagnosticInfo
from .extraction_result import ExtractionResult

from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.info_stream import StreamWriter
from taskweave.persist import PersistRegistry
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

    def parse(self, line: str, is_test : bool = False) -> ExtractionResult:
        pass
    


@dataclass(kw_only=True)
class RExtractor:
    extractors : list[Field]
    _runner : LineExtractorRunner = field(init = False)
    valid : list[DiagnosticInfo] = field(init = False)

    def __post_init__(self):
        static_diagnostics = StaticDiagnostics(
            extractors = self.extractors
        )
        self.valid = static_diagnostics.analyze()

    def parse(self, line: str, is_test : bool = False) -> ExtractionResult:
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

    def test(self, line : str, expected : dict | None = None):
        diagnostics = Diagnostics(extractors = self.extractors)
        print(
            json.dumps(
                [info.to_json() for info in self._test(line, expected, diagnostics)],
                indent = 4
            )
        )

    def return_test(self, line : str, expected : dict | None = None):
        diagnostics = Diagnostics(extractors = self.extractors)
        return self._test(line, expected, diagnostics)

    def _test(self, line : str, expected : dict | None, diagnostics : Diagnostics):
        return diagnostics.analyze(
            lambda: self._runner.parse(line = line, is_test = True)
        )



@dataclass(kw_only=True)
class RExtractorRunner:
    extractors : list[Field]
    _log_bus : MiniBus
    _source_id : str
    
    def parse(self, line: str, is_test : bool = False) -> ExtractionResult:
        result = ExtractionResult()

        for extractor in self.extractors:
            try:
                value = extractor.parse(line, is_test)
                if value is None:
                    result.failures.append(
                        (
                            extractor.schema.name,
                            extractor.parser._rule.pattern,
                            DialectErrorKind.NO_MATCH
                        )
                    )
                    continue
                result.results[extractor.schema.name] = value

            except DialectError as e:
                # don't raise here, test mode prints later
                result.failures.append(
                    (
                        extractor.schema.name,
                        extractor.parser._rule.pattern,
                        e.kind  # should be cast error
                    )
                )
                
                self._log_bus.emit_internal(
                    LogEvent(
                        source_id = TaskId(self._source_id),
                        msg_type = MsgType.DIALECT_ERROR,
                        msg = f"{e.kind} - {e.msg}: extractor has the following rule : {str(extractor.parser._rule.pattern)}",
                        timestamp = time()
                    )
                )

        # if is_test and len(failures):
        #     raise DialectError(
        #         kind = DialectErrorKind.TEST_FAILED,
        #         msg = f"Test failed (might be by design). Read the report",
        #         failures = failures
        #     ).with_traceback(None) from None

        return result
    
    

# future logics
@dataclass(kw_only=True)
class JsonFieldParser:
    pass

@dataclass(kw_only=True)
class CsvFieldParser:
    pass