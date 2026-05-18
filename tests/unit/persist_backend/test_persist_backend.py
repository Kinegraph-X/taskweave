import os
from time import sleep
from pathlib import Path

from taskweave.context import get_app_context
config, constants, args = get_app_context()
from taskweave.persist import FileBackend, FileBackendRunner

class persist_config:
    threshold = 5
    recovery_timeout = 1.0

def test_file_backend_nominal(tmp_path):
    os.mkdir(f"{tmp_path}/{constants.log_dir}")

    backend = FileBackend(
        max_lines = 10,
        max_files = 2,
        log_dir = Path(tmp_path),
        config = persist_config,
        min_drain_threshold = 100 # config forced to avoid race condition in test
    )

    backend_runner = FileBackendRunner(
        source_id = "test_task",
        backend = backend,
        error_sink = lambda : None
    )

    for i in range(0, backend.max_lines * backend.max_files):
        backend_runner.write("test_task", f"line {i}\n")
    
    backend_runner.close()

    files = sorted(tmp_path.glob("**/*.log"))
    all_lines = [l for f in files for l in f.read_text().splitlines()]
    assert len(all_lines) == backend.max_lines * backend.max_files
    