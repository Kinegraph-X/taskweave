from enum import Enum

class CancelPolicy(Enum):
    CANCEL_ALL = "cancel all"
    CANCEL_PENDING_ONLY = "cancel pending only"
    DRAIN = "drain"