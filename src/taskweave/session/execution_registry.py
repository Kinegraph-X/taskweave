from typing import Any
from dataclasses import dataclass

from taskweave.tasks import PoolStrategy, Task, SynchronousStrategy
from taskweave.pipeline import ExecutionPlan, Pipeline
from taskweave.workers import WorkerPool

class ParseError(Exception):...

@dataclass(kw_only = True)
class ParsedPlan:
    plan: ExecutionPlan             # pipelines avec Task.strategy déjà affectées
    pools: dict[str, PoolStrategy]              # ref gardée pour SessionGateway



@dataclass(kw_only = True)
class ExecutionRegistry:
    # TODO : ensure cancel_policy & observability_policy are enums in plan
    @staticmethod
    def parse_plan(self, payload: dict) -> ParsedPlan | ParseError:
        """
        Reconstruit un ExecutionPlan typé depuis un payload sérialisé.
        Valide que chaque task.pool référence un pool déclaré.
        pools est consommé ici uniquement — pas propagé dans ExecutionPlan.
        """
        # 1. parse les pools
        pools = self._parse_pools(payload.get("pools", []))
        
        # 2. parse les pipelines, valide les refs, affecte Task.strategy
        pipelines = self._parse_pipelines(payload.get("pipelines", []), pools)
        if isinstance(pipelines, ParseError):
            return pipelines
        
        return ParsedPlan(
            plan = ExecutionPlan(pipelines=pipelines),
            pools = pools
        )
    
    @staticmethod
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

    @staticmethod
    def _parse_pipelines(self, pipelines : list[Any], pools : dict[str, PoolStrategy]):
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
        Reconstruit le plan sérialisable depuis l'état runtime.
        pools est reconstruit depuis PoolProvider — pas stocké dans ExecutionPlan.
        """
        pools_list = [
            {
            "name": name,
            "max_parallel": manager.max_count
            }
            for name, manager in pools.items()
        ]
        return {
            **self._stored_plan,  # pipelines, cancel_policy, etc.
            "pools": pools        # reconstruit dynamiquement
        }