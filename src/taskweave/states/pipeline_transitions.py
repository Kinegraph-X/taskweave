from .pipeline_state import PipelineState

pipeline_transitions = {
    PipelineState.PENDING : {
        PipelineState.RUNNING,
        PipelineState.STOPPED
    },
    PipelineState.RUNNING : {
        PipelineState.SUCCESS,
        PipelineState.FAILED,
        PipelineState.STOPPED
    }
}