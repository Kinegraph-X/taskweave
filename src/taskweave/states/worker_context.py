from typing import Callable
from multiprocessing.synchronize import Event as MpEvent
from dataclasses import dataclass
from time import time
import multiprocessing

from .worker_state import WorkerState
from .worker_to_task import WORKER_TO_TASK

from taskweave.utils import TaskId

from taskweave_protocol import LogEvent, SourceType, MsgType

class WorkerContext:
    def __init__(self, name):
        self.name = name
        # self.sink = sink
        self.state: WorkerState = WorkerState.PENDING
        self.last_action: str = ""
        self.last_error: str = ""
        self.timestamp: float = 0.0
    def set_running(self, action: str):
        self.state = WorkerState.RUNNING
        self.last_action = f'{self.name} : {action}'
        self.timestamp = time()
        # self.emit()
    def set_stopped(self, action: str):
        self.state = WorkerState.STOPPED
        self.last_action = f'{self.name} : {action}'
        self.timestamp = time()
    def set_pending(self, action: str):
        self.state = WorkerState.PENDING
        self.last_action = f'{self.name} : {action}'
        self.timestamp = time()
    def set_action(self, action: str, state: WorkerState):
        self.state = state
        self.last_action = f'{self.name} : {action}'
        self.timestamp = time()
    def set_error(self, error: str):
        self.state = WorkerState.ERROR
        self.last_error = f'{self.name} : {error}'
        self.timestamp = time()
    def set_success(self):
        self.state = WorkerState.SUCCESS
        self.timestamp = time()

    # def emit(self):
    #     self.sink(
    #         LogEvent(
    #             source_id = TaskId(self.name),
    #             msg_type = MsgType.STATE_CHANGE,
    #             source_type = SourceType.TASK,
    #             timestamp = time(),
    #             msg = ""
    #         )
    #     )