from .task_state import TaskState

task_transitions = {
    TaskState.PENDING : {
        TaskState.RUNNING,
        TaskState.CANCELED
    },
    TaskState.RUNNING : {
        TaskState.SUCCESS,
        TaskState.FAILED,
        TaskState.CANCELED
    }
}