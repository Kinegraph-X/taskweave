from typing import Callable
from multiprocessing.synchronize import Event as MpEvent
from dataclasses import dataclass
from time import time
import multiprocessing
from .worker_state import WorkerState


class WorkerContext:
    def __init__(self, name):
        self.name = name
        self.state: WorkerState = WorkerState.PENDING
        self.last_action: str = ""
        self.last_error: str = ""
        self.timestamp: float = 0.0
        # self.success_event : MpEvent = multiprocessing.Event()
        # self.failure_event : MpEvent = multiprocessing.Event()
    def set_running(self, action: str):
        self.state = WorkerState.RUNNING
        self.last_action = f'{self.name} : {action}'
        self.timestamp = time()
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