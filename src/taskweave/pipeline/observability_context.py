from typing import Callable

from taskweave.context import Config, get_app_context
config, constants, args = get_app_context()

from taskweave.tasks import Task
from taskweave.persist import PersistRegistry, FileBackendRunner
from taskweave.snapshots import SessionSnapshot, PipelineFailure
from taskweave.buses import MiniBus, ObservabilityPolicy
from taskweave.info_stream import StreamWriter, SinkScope
from taskweave.utils import TaskId, Session, SinkContext
from taskweave.logging import LogStore

from taskweave_protocol import LogEvent

class ObservabilityContext:

    def __init__(
            self,
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

    def emit(self, event: LogEvent) -> None:
        self._writer._on_event(event)

    def handle_task_persistence(self, task_spec: Task) -> Callable:
        """
        This method connects LogProducer, RoutingPolicy and PersistBackend
        (Due to decoupling with the "workers" package, 
        tasks without specific producer are defaulted to LogEventProducer.
        Specific producers are in the "dialect" package)
        """
        if task_spec.backend:
            backend_runner = task_spec.backend.make_runner(
                source_id = str(task_spec.name),
                error_sink = self.log_bus.emit_internal
            )
            task_spec.producer.make_sink(
                context = SinkContext(
                    source_id = str(task_spec.name),
                    backend = task_spec.backend
                )
            )
            self._persist_registry.add_context(
                task_spec.name,
                backend_runner
            )
            def cleanup(): 
                self.stream_writer.unregister_sink(
                    task_spec.name
                )
                task_spec.backend.close()
            return cleanup
        
        return lambda: None