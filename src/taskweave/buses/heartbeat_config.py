from dataclasses import dataclass

@dataclass(kw_only = True)
class HeartbeatConfig:
    threashold : int = 5
    max_attempts : int = 5