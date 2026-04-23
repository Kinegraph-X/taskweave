from dataclasses import dataclass

@dataclass
class MsgEvent:
    worker : str = ''
    msg : str = ''