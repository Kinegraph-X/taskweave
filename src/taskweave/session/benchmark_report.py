from dataclasses import dataclass

@dataclass
class BenchmarkReport:
    heartbeat_threshold: float
    circuit_breaker_threshold: int
    pool_concurrency: dict[str, int]  # par pool
    
    def to_config(self) -> str:
        """Génère le code de configuration correspondant."""
        return f"""
            HeartBeatStrategy(
                threshold={self.heartbeat_threshold:.1f},
                max_threshold={self.heartbeat_threshold * 2:.1f}
            )
            CircuitBreakerConfig(
                threshold={self.circuit_breaker_threshold},
                recovery_timeout=1.0
            )
            """