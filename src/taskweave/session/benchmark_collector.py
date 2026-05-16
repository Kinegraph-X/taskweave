from dataclasses import dataclass
from time import time
from .benchmark_report import BenchmarkReport

from taskweave.messages import LogEvent, MsgType
from taskweave.utils import TaskId

@dataclass(kw_only = True)
class HeartbeatGap:
    timestamp : float
    gap : float

@dataclass(kw_only = True)
class BackendFailure:
    timestamp : float

class BenchmarkCollector:
    """
    Observe une session réelle et recommande des seuils.
    Branché comme backend de logging — zéro impact sur l'orchestrateur.
    """
    def __init__(self):
        self._task_durations: dict[TaskId, list[float]] = {}
        self._heartbeat_gaps: dict[TaskId, list[HeartbeatGap]] = {}
        self._backend_failures: dict[TaskId, BackendFailure] = {}
    
    def __call__(self, event: LogEvent) -> None:
        # collecte silencieuse
        match event.msg_type:
            case MsgType.STATE_CHANGE:
                self._record_duration(event)
            case (
                MsgType.LOG_LINE
                | MsgType.PROGRESS
                | MsgType.BANNER
                | MsgType.VERBOSE
            ):
                self._record_heartbeat_gap(event)
            case MsgType.BACKEND_FAILURE:
                self._record_failure(event)
    
    def recommend(self) -> BenchmarkReport:
        return BenchmarkReport(
            # heartbeat_threshold=self._p99(self._heartbeat_gaps),
            heartbeat_threshold = {k : max([b.gap for b in v]) for k, v in self._heartbeat_gaps.items()},
            circuit_breaker_threshold=self._recommend_cb_threshold(),
            pool_concurrency=self._recommend_concurrency()
        )
    
    def _record_heartbeat_gap(self, event):
        source_id = event.source_id
        if not self._heartbeat_gaps[source_id]:
            self._heartbeat_gaps[source_id] = [
                HeartbeatGap(
                    timestamp = time(),
                    gap = 0.0
                )
            ]
        else:
            evt_list = self._heartbeat_gaps[source_id]
            length = len(evt_list)
            last = evt_list[length - 1].timestamp
            current = time()
            evt_list.append(
                HeartbeatGap(
                    timestamp = current,
                    gap = current - last
                )
            )

    def _record_failure(self, event):
        source_id = event.source_id
        if not self._backend_failures[source_id]:
            self._backend_failures[source_id] = [
                BackendFailure(
                    timestamp = time()
                )
            ]
        else:
            evt_list = self._backend_failures[source_id]
            evt_list.append(
                BackendFailure(
                    timestamp = time()
                )
            )

    def _record_duration(self, event):
        source_id = event.source_id
        if event.msg_type == MsgType.STATE_CHANGE:  # can't detect RUNNING here, but assume state machine prevents illegal transitions
            if not self._task_durations[source_id]:
                self._task_durations[source_id] = [
                    HeartbeatGap(
                        start = time(),
                        duration = -1.0
                    )
                ]
            else:
                task_data = self._task_durations[source_id]
                task_data.duration = time() - task_data.start