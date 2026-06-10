from taskweave.states import SessionState

session_transitions = {
    SessionState.PENDING : {
        SessionState.RUNNING,
        SessionState.CANCELED
    },
    SessionState.RUNNING : {
        SessionState.SUCCESS,
        SessionState.FAILED,
        SessionState.CANCELED
    }
}