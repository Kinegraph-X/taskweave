import re
from typing import Deque
from collections import deque

EVENT_RE = re.compile(r'^\[\w+ @ 0x[0-9a-f]+\]')

class WorkerLogger:
    def __init__(self, name, base_folder = "logs/", max_lines=100, max_files=3):
        self.name = name
        self.base_folder = base_folder
        self.max_lines = max_lines
        self.max_files = max_files
        self.event_buffer : Deque[str] = deque()
        self.progress_buffer : Deque[str] = deque()
        self.event_count = 0
        self.file_index = 0

        self.summary_handle = open(f"{base_folder}{name}_summary.log", 'w')
        self.progress_handle = open(f"{base_folder}{name}_progress.log", 'w')
        self.event_handle = self._open_event_file()

    def _open_event_file(self):
        return open(f"{self.base_folder}{self.name}_events.{self.file_index % self.max_files}.log", 'w')

    def classify(self, line):
        if EVENT_RE.match(line):
            return 'event', False
        elif line.startswith('size='):
            return 'progress', False
        else:
            return 'summary', True

    def push(self, line):
        category, should_print = self.classify(line)
        if category == 'event':
            self._push_event(line)
        elif category == 'progress':
            self._push_progress(line)
        else:
            self._push_summary(line)
        return should_print

    def _push_summary(self, line):
        self.summary_handle.write(line + '\n')
        self.summary_handle.flush()

    def _push_event(self, line):
        self.event_buffer.append(line)
        self.event_count += 1
        if self.event_count >= self.max_lines:
            self._rotate()

    def _rotate(self):
        self.event_handle.close()
        self.file_index += 1
        self.event_handle = self._open_event_file()
        for line in self.event_buffer:
            self.event_handle.write(line + '\n')
        self.event_handle.flush()
        self.event_buffer.clear()
        self.event_count = 0

    def _push_progress(self, line):
        self.progress_buffer.append(line)

    def close(self):
        if self.event_buffer:
            self._rotate()
        for line in self.progress_buffer:
            self.progress_handle.write(line + '\n')
        self.progress_buffer.clear()
        
        self.summary_handle.close()
        self.progress_handle.close()
        self.event_handle.close()