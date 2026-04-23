from enum import Enum

class MsgType(Enum):
    STATE_CHANGE = "state change"
    ACTIVITY = "activity"
    TASK_DONE = "task done"
    EARLY_EXIT = "early exit"