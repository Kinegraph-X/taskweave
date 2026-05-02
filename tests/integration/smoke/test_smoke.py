from taskweave.tasks import Task, LocalProcessStrategy, SubprocessStrategy
from taskweave.session import SessionManager
from taskweave.messages import MsgType, LogEvent, Enveloppe
from taskweave.workers import WorkerManager

# import pytest


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
        print(f"Task completed with {len(log_events)} log events and {len(activity_events)} activity events")

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

def test_log_line(
        done,
        log_events,
        session,
        log_line_event
    ):
    session.start()
    done.wait()
    assert len(log_events) > 0 # no events received
    assert log_events[0].msg_type == log_line_event.msg_type # msg_type should be LOG_LINE
