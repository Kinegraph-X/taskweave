from enum import Enum

class MsgType(Enum):
    STATE_CHANGE = "state change"
    ACTIVITY = "activity"     # legacy
    TASK_DONE = "task done"
    EARLY_EXIT = "early exit"

    # Workers
    PROGRESS = "progress"     # avancement quantifiable (ex: frame=, time= chez ffmpeg)
    EVENT = "event"           # warnings et logs d'un module (ex: [m3u8], [ts] chez ffmpeg)
    LOG_LINE = "log_line"     # ligne stdout classifiée, non structurée
    BANNER = "banner" # métadonnées initiales du process (ex: version ffmpeg, codec)