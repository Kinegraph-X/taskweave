import os
from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.logging import LogStore, SessionData
from taskweave.utils import Session, TaskId

def test_index_is_populated(tmp_path):
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

    assert isinstance(sessions[str(session.id)], SessionData)
    assert str(task_id1) in sessions[str(session.id)].list