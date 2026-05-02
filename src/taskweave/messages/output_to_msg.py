from .output_type import OutputType
from .msg_type import MsgType

_OUTPUT_TO_MSG: dict[OutputType, MsgType] = {
    OutputType.PROGRESS :   MsgType.PROGRESS,
    OutputType.LOG_LINE :   MsgType.LOG_LINE,
    OutputType.BANNER :     MsgType.BANNER,
    OutputType.VERBOSE :   MsgType.BANNER
    # DISCARD absent — no LogEvent produced
}