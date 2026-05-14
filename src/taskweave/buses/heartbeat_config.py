from dataclasses import dataclass

@dataclass(kw_only = True)
class HeartbeatConfig:
    threashold : int = 5
    max_threshold : int = 15