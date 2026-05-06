

def test_log_line(
        done,
        activity_events,
        session,
        state_change_event
    ):
    session.start()
    done.wait()
    assert len(activity_events) > 0 # no events received
    assert activity_events[0].msg_type == state_change_event.msg_type # msg_type should be STATE_CHANGE
