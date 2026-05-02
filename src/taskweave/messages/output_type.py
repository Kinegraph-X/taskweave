from enum import Enum

class OutputType(Enum):
    PROGRESS = "progress"   # → LogEvent(MsgType.PROGRESS) + parsed
    LOG_LINE = "log_line"   # → LogEvent(MsgType.LOG_LINE)
    BANNER = "banner" # → LogEvent(MsgType.LOG_HEADER)
    VERBOSE = "verbose"
    DISCARD = "discard"    # → disk only, pas d'event