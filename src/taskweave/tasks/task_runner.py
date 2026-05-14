from typing import Callable, Protocol
from dataclasses import dataclass, field
from taskweave.utils import TaskId, CmdParam
from taskweave.workers import WorkerPool, WorkerManager, SubProcessManager
from taskweave.messages import LogProducer
from taskweave.buses import MiniBus, ObservabilityPolicy, HeartbeatConfig
from taskweave.info_stream import StreamWriter


class TaskRunner(Protocol):
    manager : WorkerPool
    def __post_init__(self):
        raise NotImplementedError
    def run(
            self,
            *,
            task_name: TaskId,
            task_cmd : list[CmdParam],
            log_producer : LogProducer,
            on_success: Callable,
            on_failure: Callable,
            on_cancel : Callable
        ):
        raise NotImplementedError
    def cleanup(self, task_name: TaskId) -> None:
        raise NotImplementedError

@dataclass(kw_only = True)
class PoolTaskRunner:
    max_parallel: int = field(default = 4)
    # default manager for static type checking : not meant to be instanciated by default
    manager: WorkerPool = field(default_factory= lambda : WorkerManager(log_bus = MiniBus(writer= StreamWriter(), observability_policy=ObservabilityPolicy.RELAXED, failure_behavior = lambda: None)))

    def __post_init__(self):
        self.manager.max_count = self.max_parallel

    def run(
            self,
            *,
            task_name : TaskId,
            task_cmd : list[CmdParam],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable,
            heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
        ):
        self.manager.add_worker(
            name = str(task_name),
            args_list = [str(cmd) for cmd in task_cmd], # WorkerPool is scope barrier
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure,
            on_cancel = on_cancel,
            heartbeat_cfg = heartbeat_cfg
        )

    def cleanup(
            self,
            task_name: TaskId
        ) -> None:
        self.manager.stop_worker(str(task_name))
        self.manager.remove_worker(str(task_name))

@dataclass(kw_only = True)
class SubprocessTaskRunner:
    # default manager for static type checking : not meant to be instanciated by default
    manager : WorkerPool = field(default_factory = lambda : SubProcessManager(source_id = "", log_bus = MiniBus(writer= StreamWriter(), observability_policy=ObservabilityPolicy.RELAXED, failure_behavior = lambda : None)))

    def __post_init__(self):...

    def run(
            self,
            *,
            task_name : TaskId,
            task_cmd : list[CmdParam],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable,
            heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
        ):
        self.manager.add_worker(
            name = str(task_name),
            args_list = [str(cmd) for cmd in task_cmd], # WorkerPool is scope barrier
            producer = log_producer,
            on_success = on_success,
            on_failure = on_failure,
            on_cancel  = on_cancel,
            heartbeat_cfg = heartbeat_cfg
        )

    def cleanup(
            self,
            task_name: TaskId
        ) -> None:
        self.manager.stop_worker(str(task_name))

@dataclass
class NoOpRunner:
    manager : WorkerPool = field(default_factory = WorkerPool)

    def __post_init__(self):...

    def run(
            self,
            *,
            task_name : TaskId,
            task_cmd : list[CmdParam],
            log_producer : LogProducer,
            on_success : Callable,
            on_failure : Callable,
            on_cancel : Callable,
            heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
        ):
        raise NotImplementedError(
            "Task must be submitted to a SessionManager/Orchestrator before execution"
        )

    def cleanup(
            self,
            task_name: TaskId
        ) -> None:
        raise NotImplementedError(
            "Task must be submitted to a SessionManager/Orchestrator before execution"
        )


class ExternalRunner:
    """
    This could be implemented depending on your syncing strategy:
    progress file on disk, distant queue, socket synchronisation...
    """
    def run(self, task, on_success, on_failure):
        raise NotImplementedError