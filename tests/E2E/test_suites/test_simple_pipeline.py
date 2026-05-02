import json
from pathlib import Path

import pytest

from taskweave.session import SessionManager
from taskweave.tasks import Task, LocalProcessStrategy


VALIDATION_FILE = Path("validation_result.json")


def test_pipeline_early_exit(tmp_path):
    # 📁 Isoler les fichiers
    validation_file = tmp_path / "validation_result.json"

    events = []

    def on_event(evt):
        events.append(evt)

    session = SessionManager(on_event=on_event)

    pipeline_id = session.add_pipeline()

    context = {}

    # --- FETCH ---
    session.add_task(pipeline_id, Task(
        name="fetch",
        strategy=LocalProcessStrategy(),
        command=["python", "fetch.py"],
    ))

    # --- VALIDATE ---
    session.add_task(pipeline_id, Task(
        name="validate",
        strategy=LocalProcessStrategy(),
        command=["python", "validate.py"],
        on_complete=lambda: context.update(
            json.loads(Path("validation_result.json").read_text())
        ),
        early_exit_condition=lambda: not context.get("valid", False),
    ))

    # --- EXPORT (ne doit PAS s'exécuter) ---
    session.add_task(pipeline_id, Task(
        name="export",
        strategy=LocalProcessStrategy(),
        command=["python", "export.py"],
    ))

    # ▶️ RUN
    session.start_pipeline(pipeline_id)

    # --- ASSERTIONS ---

    # 1. Le fichier de validation existe
    assert Path("validation_result.json").exists()

    data = json.loads(Path("validation_result.json").read_text())

    # 2. On s'attend à un échec global (mock server → b.com, error.com, slow.com)
    assert data["valid"] is False

    # 3. Early exit → export ne doit pas apparaître dans les events
    task_names = [getattr(e, "task_name", None) for e in events if hasattr(e, "task_name")]

    assert "export" not in task_names

    # 4. Validate a bien tourné
    assert "validate" in task_names

    # 5. On a bien des events de progression
    progress_events = [e for e in events if getattr(e, "msg_type", None) == "PROGRESS"]
    assert len(progress_events) > 0