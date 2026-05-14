from .msg_type import MsgType

from taskweave_dialect import OutputType

_OUTPUT_TO_MSG: dict[OutputType, MsgType] = {
    OutputType.PROGRESS :   MsgType.PROGRESS,
    OutputType.LOG_LINE :   MsgType.LOG_LINE,
    OutputType.BANNER :     MsgType.BANNER,
    OutputType.VERBOSE :   MsgType.BANNER,
    OutputType.ERROR :      MsgType.ERROR,
    OutputType.DISCARD :   MsgType.LOG_LINE
}