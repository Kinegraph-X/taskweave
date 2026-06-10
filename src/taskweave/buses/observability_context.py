from typing import Callable

from taskweave.context import Config, get_app_context
config, constants, args = get_app_context()

from .observability_policy import ObservabilityPolicy
from .mini_bus import MiniBus

from taskweave.persist import PersistRegistry
from taskweave.info_stream import StreamWriter
from taskweave.logging import LogStore

from taskweave_protocol import LogEvent

class ObservabilityContext:

    def __init__(
            self,
            on_event : Callable,
            snapshot_getter : Callable,
            observability_policy : ObservabilityPolicy = ObservabilityPolicy.SAFE
        ):
        """
        Minibus coordinates loggging.
        It decouples internal producers from StreamWriter.
        Client sinks are opaque to StreamWriter.
        PersistRegistry abstracts the two directions in StreamWriter:
        monitoring & persistance.
        Together they're the event-channel of the session
        """
        self.log_store = LogStore(log_dir = constants.log_dir)
        self._persist_registry = PersistRegistry()
        self._writer = StreamWriter(persist_registry = self._persist_registry)
        self.log_bus = MiniBus(
            writer = self._writer,
            observability_policy = observability_policy,
            snapshot_getter = snapshot_getter
        )
        self._writer.register_sink(cb = on_event)

    def emit(self, event: LogEvent) -> None:
        self._writer._on_event(event)

    