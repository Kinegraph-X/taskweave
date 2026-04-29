from typing import Generator
from dataclasses import dataclass
from pathlib import Path

@dataclass(kw_only=True)
class LogReader:
    log_path: Path

    def lines(self) -> Generator[str, None, None]:
        # Generator pattern: reads one line at a time — avoids loading
        # the entire file into memory. Appropriate for large log files
        # streamed to a client or processed incrementally.
        with self.log_path.open() as f:
            yield from f

    def tail(self, n: int) -> Generator[str, None, None]:
        # Generator pattern: yields the last n lines without seeking.
        # collections.deque with maxlen acts as a sliding window —
        # only the tail is kept in memory.
        from collections import deque
        with self.log_path.open() as f:
            yield from deque(f, maxlen=n)