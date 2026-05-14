from typing import Callable, List, Set
import os, sys, multiprocessing, threading, traceback
from multiprocessing import get_context
from queue import Queue
from collections import deque
from time import time, sleep

from .worker_logger import WorkerLogger
from .worker_status import WorkerStatus
from .basic_worker import BasicWorker
from .work_item import WorkItem
from .cancel_intent import CancelIntent
from .completed_task import CompletedTask
from .task_outcome import TaskOutcome
from .final_status import FinalStatus

from taskweave.context import get_app_context
config, constants, cmd_line_args = get_app_context()
from taskweave.states import WorkerState, WorkerContext
from taskweave.messages import LogEvent, LogProducer, MsgType, SourceType
from taskweave.buses import MiniBus, Heartbeat, HeartbeatConfig
from taskweave.utils import TaskId

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        multiprocessing.freeze_support()
        multiprocessing.set_start_method('spawn', force=True)

class WorkerManager:
    """
    May be implemented as a standalone worker manager:
    curl -d "{\"name\" : \"server\"}" -H "Content-Type:application/json" -X POST http://localhost:3001/start_worker
    accepts a shared completion_queue for enforced ordering of messages accross managers
    """
    def __init__(
            self,
            *,
            log_bus : MiniBus,
            max_count : int = 4,
            completion_queue : Queue[CancelIntent | CompletedTask] = Queue()
            ):
        self.workers : dict[str, BasicWorker] = {}
        self._message_queue : multiprocessing.Queue[LogEvent] = multiprocessing.Queue()
        self.worker_ctx : dict[str, WorkerContext] = {}
        self.log_bus = log_bus
        self.on_success_cbs : dict[str, Callable] = {}
        self.on_failure_cbs : dict[str, Callable] = {}
        self.on_cancel_cbs : dict[str, Callable] = {}
        self.completion_threads : dict[str, threading.Thread] = {}
        self.heartbeats : dict[str, Heartbeat] = {}
        self.max_count = max_count
        self._pending: deque[WorkItem] = deque()

        self._completion_queue : Queue[CancelIntent | CompletedTask] = Queue() if completion_queue is None else completion_queue
        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True
        )
        self._dispatch_thread.start()
        self._active = 0
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._done.set()

    def _assert_transition(self, name, required_state):
        worker_ctx = self.worker_ctx.get(name)
        if not worker_ctx:
            raise RuntimeError(f"unknown ctx for worker : {name}")
        if worker_ctx.state != required_state:
            raise RuntimeError(f"worker state mismatch {name} : state {worker_ctx.state.value}, expected {required_state.value}")
            
    def add_worker(
            self,
            *,
            name : str,
            args_list : List[str],
            producer : LogProducer,
            on_success : Callable | None = None,
            on_failure : Callable | None = None,
            on_cancel : Callable | None = None,
            heartbeat_cfg : HeartbeatConfig = HeartbeatConfig()
        ):
        name = str(name)
        if len(self.workers) >= self.max_count:
            self._pending.append(
                WorkItem(
                    name,
                    args_list,
                    on_success,
                    on_failure,
                    producer
                )
            )
            return 
        else:
            self.reset_worker_instance(
                name,
                args_list,
                on_success,
                on_failure,
                on_cancel,
                producer,
                heartbeat_cfg
            )
            
        return self.start_worker(name)

    def reset_worker_instance(
            self,
            name,
            args_list,
            on_success,
            on_failure,
            on_cancel,
            producer,
            heartbeat_cfg
        ):
        self.workers[name] = BasicWorker(
            name = name,
            args_list = args_list,
            print_queue = self._message_queue,
            producer = producer,
            debug = cmd_line_args.debug,
            dist = cmd_line_args.dist
        )
        self.worker_ctx[name] = WorkerContext(name = name)
        self.on_success_cbs[name] = on_success # on_success : None is handled in completion_thread
        self.on_failure_cbs[name] = on_failure # on_failure : None is handled in completion_thread
        self.on_cancel_cbs[name] = on_cancel #  on_cancel : None is handled in _stop_worker
        self.heartbeats[name] = Heartbeat(name, self.log_bus, heartbeat_cfg)
        
        self.completion_threads[name] = threading.Thread(
            target=self._handle_worker_completion, args = (name, ), daemon=True
        )
        self.worker_ctx[name].set_pending("initial state")

    def start_worker(self, name : str):
        self._assert_transition(name, WorkerState.PENDING)
        
        self.workers[name].start()
        self.worker_ctx[name].set_running("start worker")
        self.completion_threads[name].start()
        if self._active == 0:
            with self._lock:
                self._active += 1
                self._done.clear()
                self._collect_results()
        else:
            with self._lock:
                self._active += 1
                self._done.clear()
        return self.format_status(name, f"{self.worker_ctx[name].state.value}")

    def stop_worker(self, name):
        self._completion_queue.put(CancelIntent(name = name))

    def _stop_worker(self, name):
        self._assert_transition(name, WorkerState.RUNNING)
        worker = self.workers[name]
        if worker.is_alive():
            worker.terminate()
        with self._lock:
            self._active -= 1
        self.worker_ctx[name].state = WorkerState.STOPPED

        if self.on_cancel_cbs[name]:
            self._execute_callback(name, self.on_cancel_cbs[name], FinalStatus.STOPPED)
        # no need to kill self.completion_threads[name], it's not a loop
        status_obj = self.format_status(name, f"{name} {self.worker_ctx[name].state.value}")
        # self.reset_worker_instance(name)
        return status_obj
        
    def join_worker(self, name):
        self._assert_transition(name, WorkerState.RUNNING)
        worker = self.workers.get(name)
        
        if not worker:
            raise ValueError(f'join_worker() on non-existing worker. worker name is {name}')
        worker.join()

    def remove_worker(self, name):
        self._assert_transition(name, WorkerState.STOPPED)
        worker = self.workers[name]
        worker.terminate()
        self.worker_ctx[name].set_stopped('worker stopped and removed')
        status_obj = self.format_status(name, f"{name} {self.worker_ctx[name].state.value}")
        self.workers.pop(name)
        return status_obj

    def all_stopped(self):
        return all(ctx.state != WorkerState.RUNNING 
                for ctx in self.worker_ctx.values())

    def get_worker_status(self, name):
        worker = self.workers.get(name)
        if not worker:
            return self.format_status(name, f"ERROR : {name} : No instance available for Worker")

        if self.worker_ctx[name].state == WorkerState.RUNNING and not worker.is_alive():
            self.worker_ctx[name].set_error("Worker wasn't alive when getting status")
        return self.format_status(name, f"{self.worker_ctx[name].state.value}")

    def format_status(self, name, status_string):
        # Get the messages in the queue (non-blocking)
        messages = []
        queue = self._message_queue
        try:
            while not queue.empty():
                messages.append(queue.get_nowait())
        except:
            pass
        return WorkerStatus(f"{status_string}", messages)
    
    def _dispatch_loop(self):
        while True:
            event = self._message_queue.get()
            if event is None:
                return
            self.heartbeats[event.name].beat(event)

    def _collect_results(self):
        completed_tasks : set[str] = Set()
        while self._active > 0:
            result = self._completion_queue.get()
            name = result.name
            worker = self.worker[name]
            if not worker:
                self._completion_queue.put(result)
                sleep(.01)
                continue

            if isinstance(CancelIntent, result) and not name in completed_tasks:
                self._stop_worker(name)
                continue
            elif isinstance(CompletedTask, result):
                completed_tasks.add(name)

            if worker.success_event.is_set() and self.on_success_cbs[name]:
                self._execute_callback(name, self.on_success_cbs[name], FinalStatus.SUCCESS)
            elif self.on_failure_cbs[name]:
                self._execute_callback(name, self.on_failure_cbs[name], FinalStatus.FAILURE)
                
            self._cleanup(name)
            
            try:
                if self._pending:
                    task = self._pending.popleft()
                    self.add_worker(task.name, task.args_list, task.on_success, task.on_failure, task.producer)
            except Exception as e:
                print(f"WorkerManager._handle_worker_completion thread for {name} raised : {e} when starting the '{task.name}' pending task")
                print(traceback.format_exc())
            finally:
                with self._lock:
                    self._active -= 1
                    if self._active == 0:
                        self._done.set()

    def _execute_callback(self, name : str, cb : Callable, final_status : FinalStatus):
        outcome : TaskOutcome = TaskOutcome(
            name = name,
            status = final_status,
            error = None
        )
        try:
            cb(outcome)
        except Exception as e:
            stacktrace = traceback.format_exc()
            event = LogEvent(
                msg_type = MsgType.CALLBACK_ERROR,
                msg = f"{e}\n{stacktrace}",
                source_id = TaskId(name),
                source_type = SourceType.TASK,
                timestamp = time()
            )

            self.log_bus.emit(event)

            print(f"WorkerManager._handle_worker_completion thread for {name} raised : '{e}' when calling completion cbs")
            print(stacktrace)

    def _handle_worker_completion(self, name):
        try:
            worker = self.workers[name]
            self.join_worker(name)
        except Exception as e:
            print(f"WorkerManager._handle_worker_completion thread for {name} raised : '{e}' when joining process")
        
        self._completion_queue.put(CompletedTask(name = name))
    
    def wait_all(self) -> None:
        self._done.wait()

    def _cleanup(self, name):
        # nothing to do
        # self.completion_threads[name].stop()
        # self.completion_threads[name].join()
        pass

    def destroy(self):
        self._message_queue.put(None)  # poison pill
        self._dispatch_thread.join()
