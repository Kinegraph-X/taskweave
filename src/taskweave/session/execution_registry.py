from typing import Any
import json
from dataclasses import dataclass

from taskweave.buses import ObservabilityPolicy
from taskweave.tasks import PoolStrategy, Task, SynchronousStrategy, CancelPolicy
from taskweave.pipeline import ExecutionPlan, Pipeline
from taskweave.workers import WorkerPool
from taskweave.utils import jsonSerialize, parse_enum

class ParseError(Exception):...

@dataclass(kw_only = True)
class ParsedPlan:
    plan: ExecutionPlan                         # pipelines with Task.strategy already assignated
    pools: dict[str, PoolStrategy]              # ref kept for SessionGateway
    cancel_policy: CancelPolicy | None          # None is absent from payload
    observability_policy: ObservabilityPolicy | None  # idem


@dataclass(kw_only = True)
class ExecutionRegistry:
    
    def parse_plan(self, payload: dict) -> ParsedPlan | ParseError:
        """
        Reconstructs a typed ExecutionPlan from a serialized payload.
        Validates that each task.pool references a declared pool.
        "pools" is consummed only here : not propagated in ExecutionPlan.
        """
        # 1. parse les pools
        pools = self._parse_pools(payload.get("pools", []))
        
        # 2. parse les pipelines, valide les refs, affecte Task.strategy
        pipelines = self._parse_pipelines(payload.get("pipelines", []), pools)
        if isinstance(pipelines, ParseError):
            return pipelines
        
        cancel_policy = parse_enum(
            CancelPolicy,
            payload.get("cancel_policy")
        )
        observability_policy = parse_enum(
            ObservabilityPolicy,
            payload.get("observability_policy")
        )
 
        return ParsedPlan(
            plan = ExecutionPlan(pipelines=pipelines),
            pools = pools,
            cancel_policy = cancel_policy,
            observability_policy = observability_policy,
        )
    
    def _parse_pools(self, payload) -> dict[str, PoolStrategy]:
        # 1. reconstruit les PoolStrategy depuis le payload
        pools: dict[str, PoolStrategy] = {
            p["name"]: PoolStrategy(
                pool_name=p["name"],
                max_parallel=p.get("max_parallel", 4)
            )
            for p in payload.get("pools", [])
        }
        return pools

    def _parse_pipelines(
        self,
        pipelines : list[Any],
        pools : dict[str, PoolStrategy]
    ):
        # 2. reconstruit les pipelines
        pipelines = []
        for pipeline_payload in pipelines:
            tasks = []
            for task_payload in pipeline_payload.get("tasks", []):

                # valide la référence pool
                pool_name = task_payload.get("pool")
                if pool_name and pool_name not in pools:
                    return ParseError(
                        f"task '{task_payload['name']}' "
                        f"references unknown pool '{pool_name}'"
                    )

                tasks.append(Task(
                    name=task_payload["name"],
                    cmd=task_payload["cmd"],
                    strategy=pools[pool_name] if pool_name else SynchronousStrategy(),
                    # on_finally non supporté en full-web — cf. doc
                ))

            pipelines.append(Pipeline(tasks=tasks))

        return pipelines

    def get_plan(
        self,
        plan : ExecutionPlan,
        pools : dict[str, WorkerPool]
    ) -> dict:
        """
        Constructs a serialized plan from the runtime plan.
        "pools" is constructed from PoolProvider.
        """
        serialized = jsonSerialize(plan)
        
        serialized["pools"] = [
            {
                "name": name,
                "max_parallel": runner.manager.max_count
            }
            for name, runner in pools.items()
        ]
 
        return serialized
    
    def get_json_plan(
        self,
        plan : ExecutionPlan,
        pools : dict[str, WorkerPool]
    ) -> str:
        return json.dumps(self.get_plan(plan, pools), indent=4)