from enum import Enum

class ObservabilityPolicy(Enum):
    """
    Defines system behavior when the logging backend becomes unavailable.
    In both cases, the client to the orchestrator is notified and may suspend the worker

    BEST_EFFORT — Declares that Log loss is accepted.
              Use when task completion matters more than full observability.
              Risk: silent failures become harder to diagnose post-hoc.

    SAFE    — Declares log integrity is required (audit, compliance, debugging).
              The client to the orchestrator receives a complete snapshot, 
              and may decide to crash and resume on a new session
              Risk: a logging failure can halt a long-running computation.

    The choice is a trade-off between availability and observability,
    not a quality setting. Neither is "better" by default,
    and slow backends may still lost logs : min_drain_threshold is more effecive
    on log less than ObservabilityPolicy.
    """
    SAFE = "safe"
    BEST_EFFORT = "best effort"