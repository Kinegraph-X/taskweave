from dataclasses import dataclass, field

from .persist_backend import PersistBackendRunner

from taskweave.messages import LogEvent
from taskweave.utils import TaskId

@dataclass(kw_only = True)
class PersistRegistry:
    """
    Mapping Task.name → PersistBackendRunner.
    Owned by SessionManager, passed to StreamWriter.
    """

    _contexts : dict[TaskId, PersistBackendRunner] = field(default_factory = dict)

    def add_context(self, task_id : TaskId, backend : PersistBackendRunner):
        self._contexts[task_id] = backend

    def persist(self, event: LogEvent) -> None:
        ctx = self._contexts.get(event.source_id)
        if ctx:
            ctx.write(str(event.source_id), f"{event.format()}\n")