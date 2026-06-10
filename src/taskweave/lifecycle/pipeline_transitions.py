from taskweave.states import PipelineState

pipeline_transitions = {
    PipelineState.PENDING : {
        PipelineState.RUNNING,
        PipelineState.CANCELED
    },
    PipelineState.RUNNING : {
        PipelineState.SUCCESS,
        PipelineState.FAILED,
        PipelineState.CANCELED
    }
}