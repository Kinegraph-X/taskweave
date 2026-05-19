from typing import Protocol
from dataclasses import dataclass
from taskweave_protocol import BackendErrorKind

class BackendException(Exception):
    kind: BackendErrorKind
    msg: str

@dataclass(kw_only= True)
class BackendTransientFailure(BackendException):
    kind: BackendErrorKind
    msg: str
    http_status: int | None = None
    retryable: bool = True  # may be derived from kind

@dataclass(kw_only = True)
class BackendFatalError(BackendException):
    kind: BackendErrorKind
    msg: str