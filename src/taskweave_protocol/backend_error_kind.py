from enum import Enum

class BackendErrorKind(Enum):
    # Transient — circuit breaker waits for recovery
    RATE_LIMITED    = "rate_limited"     # HTTP 429
    UNAVAILABLE     = "unavailable"      # HTTP 503, ConnectionError
    TIMEOUT         = "timeout"          # socket timeout, HTTP 504
    CIRCUIT_OPEN    = "circuit breaker transient error"
    
    # Permanent — circuit breaker raiss immediadelty BACKEND_FATAL_ERROR
    BAD_REQUEST     = "bad_request"      # HTTP 400, malformed doc
    UNAUTHORIZED    = "unauthorized"     # HTTP 401/403, config error

    OS_ERROR        = "os error"         # disk related fatal failures
    QUEUE_FULL      = "backend dispatch queue full"
    THREAD_DIED     = "backend dispatch thread died"
    
    # conservatory behavior : always signal
    UNKNOWN         = "unknown"