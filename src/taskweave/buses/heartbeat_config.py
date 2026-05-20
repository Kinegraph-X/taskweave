from dataclasses import dataclass

@dataclass(kw_only = True)
class HeartbeatConfig:
    """
    max_attempts could be a tool for small adjustments, but
    is not meant to be documented.
    The smaller the ratio between threshold & max_threshold is, 
    the littler the timing threads loops (see HeartBeat).
    """
    threshold : float = 5
    max_threshold : float = 15
    max_attempts : int = 5