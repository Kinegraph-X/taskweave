import os
from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.logging import LogStore
from taskweave.utils import Session, TaskId

attempts = 0

def test_unique_id(tmp_path):
    log_dir = f"{tmp_path}/{constants.log_dir}"
    os.mkdir(log_dir)

    def short_suffix_fn():
        global attempts
        attempts += 1
        return str(attempts)
    
    def make_id_fn(
            task_name : TaskId,
            session_id : TaskId,
            suffix_fn = short_suffix_fn
        ):
        ts = hex(1_000_000)[-8:]
        return task_name.increment(f"_{ts}_{session_id}_{suffix_fn()}")


    session = Session()
    store = LogStore(log_dir = log_dir)
    
    task_id1 = store.register(
        session_id = session.id,
        source_id = TaskId("task_test"),
        make_id_fn = make_id_fn
    )
    task_id2 = store.register(
        session_id = session.id,
        source_id = TaskId("task_test"),
        make_id_fn = make_id_fn
    )

    assert str(task_id1).endswith("_1")
    assert str(task_id2).endswith("_2")
