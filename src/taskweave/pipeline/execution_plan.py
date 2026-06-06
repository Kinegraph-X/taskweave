from dataclasses import dataclass, field

from taskweave.tasks import CancelPolicy, Task, PoolStrategy
from taskweave.pipeline import Pipeline
from taskweave.utils import TaskId
from taskweave.buses import ObservabilityPolicy

@dataclass(kw_only = True)
class ExecutionPlan:
    cancel_policy : CancelPolicy = CancelPolicy.CANCEL_PENDING_ONLY
    observability_policy : ObservabilityPolicy = ObservabilityPolicy.SAFE
    pools : list[PoolStrategy] = field(default_factory = list)
    pipelines : list[Pipeline] = field(default_factory = list)