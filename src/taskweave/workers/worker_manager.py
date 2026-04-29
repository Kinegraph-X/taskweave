from typing import Callable, List
import sys, multiprocessing, threading
from multiprocessing import get_context, Queue
from collections import deque

from .worker_logger import WorkerLogger
from .worker_status import WorkerStatus
from .basic_worker import BasicWorker

from taskweave.tasks import PendingTask
from taskweave.context import get_app_context
config, constants, cmd_line_args = get_app_context()
from taskweave.states import WorkerState
from taskweave.messages import LogProducer
# if getattr(sys, 'frozen', False):

# ctx = get_context('spawn')  # Explicitly get a new context with 'spawn'
if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)

# curl -d "{\"name\" : \"server\"}" -H "Content-Type:application/json" -X POST http://localhost:3001/start_worker

class WorkerManager:
    def __init__(self, max_count = 4):
        self.workers = {}
        # self.message_queues = {}
        self._message_queue : Queue = multiprocessing.Queue()
        self.on_log_cbs = {}
        self.on_success_cbs = {}
        self.on_failure_cbs = {}
        self.completion_threads = {}
        self.max_count = max_count
        self._pending: deque[PendingTask] = deque()
        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True
        )
        self._dispatch_thread.start()

    def _assert_transition(self, name, required_state):
        worker = self.workers.get(name)
        if not worker:
            raise RuntimeError(f"unknown worker : {name}")
        if worker.context.state != required_state:
            raise RuntimeError(f"worker state mismatch {name} : state {worker.context.state.value}, expected {required_state.value}")
            
    def add_worker(
            self,
            *,
            name : str,
            args_list : List[str],
            on_success : Callable | None = None,
            on_failure : Callable | None = None,
            on_log : Callable | None = None,
            producer : LogProducer | None
        ):
        if len(self.workers) >= self.max_count:
            self._pending.append(PendingTask(name, args_list, on_success, on_failure))
            return 
        else:
            self.reset_worker_instance(name, args_list, on_success, on_failure, on_log, producer)
            
        return self.start_worker(name)

    def reset_worker_instance(self, name, args_list, on_success, on_failure, on_log, producer):
        # allow passing serializable objects references
        args_list = [str(part) for part in args_list]
        self.workers[name] = BasicWorker(
            name,
            args_list,
            self._message_queue,
            producer = producer,
            debug = cmd_line_args.debug,
            dist = cmd_line_args.dist
        )
        self.on_success_cbs[name] = on_success # None is handled in completion_thread
        self.on_failure_cbs[name] = on_failure # None is handled in completion_thread
        if on_log:
                self.on_log_cbs[name] = on_log
        self.completion_threads[name] = threading.Thread(
            target=self.completion_loop, args = (name, ), daemon=True
        )
        self.workers[name].ctx.set_stopped("initial state")

    def subscribe_to_logs(self, cb, name : str | None = None):
        self.on_log_cbs['central_queue'] = cb

    def start_worker(self, name):
        self._assert_transition(name, WorkerState.STOPPED)
        self.workers[name].start()
        self.workers[name].ctx.set_started("start worker")
        return self.format_status(name, f"{self.workers[name].state.value}")

    def stop_worker(self, name):
        self._assert_transition(name, WorkerState.RUNNING)
        worker = self.workers[name]
        worker.terminate()
        worker.state = WorkerState.STOPPED
        status_obj = self.format_status(name, f"{name} {worker.state.value}")
        # self.reset_worker_instance(name)
        return status_obj
        
    def join_worker(self, name):
        self._assert_transition(name, WorkerState.RUNNING)
        worker = self.workers.get(name)
        if not worker:
            raise ValueError(f'join_worker() on non-existing worker. worker name is {name}')
        worker.join()
        if worker.is_alive():
            raise RuntimeError(f"{name} still alive after join")

    def remove_worker(self, name):
        self._assert_transition(name, WorkerState.STOPPED)
        worker = self.workers[name]
        worker.terminate()
        worker.ctx.set_stopped('worker sopped and removed')
        status_obj = self.format_status(name, f"{name} {worker.state.value}")
        self.workers.pop(name)
        return status_obj

    def all_stopped(self):
        return all(w.ctx.state != WorkerState.RUNNING 
                for w in self.workers.values())

    def get_worker_status(self, name):
        worker = self.workers.get(name)
        if not worker:
            return self.format_status(name, f"ERROR : {name} : No instance available for Worker")

        if worker.ctx.state == WorkerState.RUNNING and not worker.is_alive():
            worker.ctx.set_error("Worker wasn't alive when getting status")
        return self.format_status(name, f"{worker.state.value}")

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
            for worker, cb in self.on_log_cbs.items():
                if event.worker == worker:
                    cb(event)
            self.on_log_cbs["central_queue"](event)

    def completion_loop(self, name):
        worker = self.workers[name]
        self.join_worker(name)
        if worker.ctx.success_event.is_set() and self.on_success_cbs[name]:
            self.on_success_cbs[name]()
        elif self.on_failure_cbs[name]:
            self.on_failure_cbs[name]()
        self._cleanup(name)
        if self._pending:
            task = self._pending.popleft()
            self.start_worker(task.name, task.args_list, task.on_success, task.on_failure)

    def _cleanup(self, name):
        self.completion_threads[name].stop()
        self.completion_threads[name].join()

    def destroy(self):
        self._message_queue.put(None)  # poison pill
        self._dispatch_thread.join()
