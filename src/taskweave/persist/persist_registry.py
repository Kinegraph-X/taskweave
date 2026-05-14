from dataclasses import dataclass

from .persist_strategy import PersistStrategy
from .persist_backend import PersistBackend

from taskweave.messages import LogEvent
from taskweave.utils import TaskId

@dataclass(kw_only = True)
class PersistRegistry:
    """Mapping task_id → PersistContext. Owned by SessionManager."""

    _contexts : dict[TaskId, PersistBackend] = {}

    def add_context(self, task_id : TaskId, backend : PersistBackend):
        self._contexts[task_id] = backend

    def persist(self, event: LogEvent) -> None:
        ctx = self._contexts.get(event.source_id)
        if ctx:
            ctx.write(str(event.source_id), event.format())