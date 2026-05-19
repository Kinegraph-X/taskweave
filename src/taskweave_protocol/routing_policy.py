from dataclasses import dataclass

@dataclass(frozen=True)
class RoutingPolicy:
    forward: bool   # send to client Monitor
    persist: bool   # persist on disk