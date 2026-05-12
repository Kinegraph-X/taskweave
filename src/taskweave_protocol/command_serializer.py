from typing import Protocol

class CommandSerializer(Protocol):...

class LineSerializer:...    # "pause\n", "seek position=1.75\n" — simple, debuggable
class JsonSerializer:...    # {"cmd": "seek", "position": 1.75} — structuré