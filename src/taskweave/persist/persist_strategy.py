import time
from typing import Callable, Protocol
from dataclasses import dataclass, field
from .persist_backend import PersistBackend, FileBackend
from .circuit_breaker_config import PersistConfig, CircuitBreakerConfig
from .circuit_breaker import CircuitBreaker

from taskweave.buses import MiniBus
from taskweave.utils import TaskId
from taskweave.messages import LogEvent, MsgType, SourceType, RoutingPolicy

from taskweave_protocol import OutputType

class PersistStrategy(Protocol):
    # def write(self, source_id: TaskId, line: str) -> None:...
    def specialize_event(self, event : LogEvent, output_type: OutputType) -> LogEvent:...
    # def register_error_sink(self, sink : MiniBus) -> None:...

@dataclass(kw_only = True)
class PersistAll:
    """writes all lines"""
    # backend : PersistBackend = field(default_factory = FileBackend)
    # config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)

    # def __post_init__(self):
    #     self.circuit_breaker = CircuitBreaker(self.config)
    #     self._error_sinks : list[MiniBus] = []

    # def register_error_sink(self, sink : MiniBus):
    #     self._error_sinks.append(sink)
    
    # def write(self, event : LogEvent, output_type: OutputType) -> None:
    #     try:
    #         self.circuit_breaker.call(
    #             fn = self.backend.write,
    #             args_list = [str(source_id), line]
    #         )
    #     except Exception as e:
    #         self._propagate_error(source_id, e)

    def specialize_event(self, event : LogEvent, output_type: OutputType) -> LogEvent:
        event.routing = RoutingPolicy(
            persist = True,
            forward = True
        )
        return event

    # def _propagate_error(self, source_id : TaskId, e : Exception):
    #     for sink in self._error_sinks:
    #         sink.emit_internal(
    #             LogEvent(
    #                 source_id = source_id,
    #                 source_type = SourceType.TASK,
    #                 msg = str(e),
    #                 msg_type = MsgType.BACKEND_FAILURE,
    #                 timestamp = time.time()
    #             )
    #         )

        

@dataclass(kw_only = True)
class PersistDiscarded:
    """only writes OutputType.DISCARD and OutputType.ERROR"""
    # backend : PersistBackend = field(default_factory = FileBackend)
    config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)

    # def __post_init__(self):
    #     self.circuit_breaker = CircuitBreaker(self.config)
    #     self._error_sinks : list[MiniBus] = []

    # def register_error_sink(self, sink : MiniBus):
    #     self._error_sinks.append(sink)

    # def write(self, source_id: TaskId, line: str, output_type: OutputType) -> None:
    #     if output_type in (OutputType.DISCARD, OutputType.ERROR):
    #         try:
    #             self.circuit_breaker.call(
    #                 fn = self.backend.write,
    #                 args_list = [str(source_id), line]
    #             )
    #         except Exception as e:
    #             self._propagate_error(source_id, e)

    def specialize_event(self, event : LogEvent, output_type: OutputType) -> LogEvent:
        if output_type in (OutputType.DISCARD, OutputType.ERROR):
            event.routing = RoutingPolicy(
                persist = True,
                forward = False
            )
        return event

    # def _propagate_error(self, source_id : TaskId, e : Exception):
    #     for sink in self._error_sinks:
    #         sink.emit_internal(
    #             LogEvent(
    #                 source_id = source_id,
    #                 source_type = SourceType.TASK,
    #                 msg = str(e),
    #                 msg_type = MsgType.BACKEND_FAILURE,
    #                 timestamp = time.time()
    #             )
    #         )

@dataclass(kw_only = True)
class Persist_Verbose_And_Discarded:
    """only writes OutputType.VERBOSE, OutputType.DISCARD and OutputType.ERROR"""
    # backend : PersistBackend = field(default_factory = FileBackend)
    # config : PersistConfig = field(default = CircuitBreakerConfig.LOCAL.value)

    # def __post_init__(self):
    #     self.circuit_breaker = CircuitBreaker(self.config)
    #     self._error_sinks : list[MiniBus] = []

    # def register_error_sink(self, sink : MiniBus):
    #     self._error_sinks.append(sink)

    # def write(self, source_id: TaskId, line: str, output_type: OutputType) -> None:
    #     if output_type in (OutputType.DISCARD, OutputType.VERBOSE, OutputType.ERROR):
    #         try:
    #             self.circuit_breaker.call(
    #                 fn = self.backend.write,
    #                 args_list = [str(source_id), line]
    #             )
    #         except Exception as e:
    #             self._propagate_error(source_id, e)

    def specialize_event(self, event : LogEvent, output_type: OutputType) -> LogEvent:
        if output_type in (OutputType.DISCARD, OutputType.VERBOSE, OutputType.ERROR):
            event.routing = RoutingPolicy(
                persist = True,
                forward = False
            )
        return event

    # def _propagate_error(self, source_id : TaskId, e : Exception):
    #     for sink in self._error_sinks:
    #         sink.emit_internal(
    #             LogEvent(
    #                 source_id = source_id,
    #                 source_type = SourceType.TASK,
    #                 msg = str(e),
    #                 msg_type = MsgType.BACKEND_FAILURE,
    #                 timestamp = time.time()
    #             )
    #         )

@dataclass(kw_only = True)
class PersistNone:
    # def write(self, line: str, output_type: OutputType) -> None:...
    # def register_error_sink(self, sink : MiniBus) -> None:...
    def specialize_event(self, event : LogEvent, output_type: OutputType) -> LogEvent:
        event.routing = RoutingPolicy(
            persist = False,
            forward = True
        )
        return event
