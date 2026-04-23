from dataclasses import dataclass
from .msg_type import MsgType

@dataclass
class LogEvent:
    worker : str = ''
    msg : str = ''
    pipelline : str = ''
    msg_type : MsgType = MsgType.ACTIVITY