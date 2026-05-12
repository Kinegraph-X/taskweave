from subprocess import Popen

class StdinTransport:
    def __init__(self, process: Popen):
        self._stdin = process.stdin
    
    def send_raw(self, payload: bytes) -> None:
        self._stdin.write(payload + b"\n")
        self._stdin.flush()

class SocketTransport:...
class NamedPipeTransport:...