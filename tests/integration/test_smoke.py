from taskweave.tasks import Task, LocalProcessStrategy, SubprocessStrategy
from taskweave.session import SessionManager
from taskweave.messages import MsgType, LogEvent, Enveloppe
from taskweave.workers import WorkerManager

import threading
# import pytest

import sys
import os
# print("PID:", os.getpid())
import multiprocessing as mp
# print("Process name:", mp.current_process().name)
if __name__ == "__main__":
    mp.freeze_support()
    mp.set_start_method('spawn', force=True)

class DebugStdout:
    def write(self, data):
        import traceback
        traceback.print_stack()
        return sys.__stdout__.write(data)

    def flush(self):
        return sys.__stdout__.flush()

# sys.stdout = DebugStdout()

def main():
    log_events = []
    activity_events = []
    def on_event(env : Enveloppe):
        event = env.event
        if event.msg_type == MsgType.LOG_LINE:
            log_events.append(event)
        elif event.msg_type == MsgType.STATE_CHANGE:
            activity_events.append(event)

    def after_complete(task_name : str):
        # pass
        print(f"Task completed with {len(log_events)} log events and {len(activity_events)}")

    manager = WorkerManager()

    task = Task(
        name = "smoke",
        strategy = LocalProcessStrategy(manager = manager),
        cmd = ["python", "--version"],
        after_complete = after_complete
    )

    session = SessionManager(on_event = on_event)
    pipeline_id = session.add_pipeline()
    session.add_task(pipeline_id, task)
    session.start()

    # for t in threading.enumerate():
    #     print(t, t.daemon)

if __name__ == "__main__":
    main()