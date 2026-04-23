import time
from typing import List, Callable
from dataclasses import dataclass
from whisper_infer.tasks import ExecutionStrategy, LocalProcessStrategy
from whisper_infer.workers import WorkerManager
from whisper_infer.utils import StrSerializable

@dataclass
class Task:
    name: str
    manager: WorkerManager | None     # mécanique d'exécution
    cmd: List[str | StrSerializable]
    strategy : ExecutionStrategy = LocalProcessStrategy()
    after_complete : Callable | None = None
    early_exit_on_success : bool | Callable = False
    cancellable: bool = True
