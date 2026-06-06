from.worker_state import WorkerState
from .task_state import TaskState

WORKER_TO_TASK = {
    WorkerState.PENDING : TaskState.PENDING,
    WorkerState.RUNNING : TaskState.RUNNING,
    WorkerState.STOPPED : TaskState.CANCELED,
    WorkerState.SUCCESS : TaskState.SUCCESS,
    WorkerState.ERROR : TaskState.FAILED,
}