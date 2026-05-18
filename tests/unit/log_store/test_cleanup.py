import os, json
from time import time, sleep
from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.logging import LogStore, SessionData, Encoder
from taskweave.utils import Session, TaskId

def test_cleanup(tmp_path):
    log_dir = f"{tmp_path}/{constants.log_dir}"
    os.mkdir(log_dir)

    session = Session()
    store = LogStore(log_dir = log_dir)
    
    task_id1 = store.register(
        session_id = session.id,
        source_id = TaskId("task_test")
    )

    index_path = os.path.join(log_dir, store.log_index)
    sessions = store._get_index(index_path)

    assert isinstance(sessions, dict)
    assert isinstance(sessions[str(session.id)], SessionData)
    assert str(task_id1) in sessions[str(session.id)].list

    # artificially increase age
    sessions[str(session.id)].timestamp = time() - store.max_age - 1.0
    with open(index_path, "w") as f:
            json.dump(sessions, f, cls = Encoder)

    store.cleanup()
    sessions = store._get_index(index_path)
    assert isinstance(sessions, dict)
    assert len(sessions) == 0