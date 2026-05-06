
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
