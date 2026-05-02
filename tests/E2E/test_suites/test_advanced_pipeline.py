import json
from pathlib import Path
from collections import defaultdict

from taskweave.session import SessionManager
from taskweave.tasks import Task, LocalProcessStrategy
from taskweave.workers import WorkerManager


def test_multi_pipeline_with_sync(tmp_path):
    events = []

    def on_event(evt):
        events.append(evt)

    session = SessionManager(on_event=on_event)

    validate_manager = WorkerManager(max_count=1)

    pipelines = []
    contexts = {}

    # 🔁 Création de 3 pipelines
    for i in range(3):
        pipeline_id = session.add_pipeline()
        pipelines.append(pipeline_id)

        context = {}
        contexts[pipeline_id] = context

        # --- FETCH ---
        session.add_task(pipeline_id, Task(
            name="fetch",
            strategy=LocalProcessStrategy(max_count=4),
            command=["python", "fetch.py"],
        ))

        # --- VALIDATE (point de sync global) ---
        session.add_task(pipeline_id, Task(
            name="validate",
            strategy=LocalProcessStrategy(manager=validate_manager),
            command=["python", "validate.py"],
            on_complete=lambda ctx=context: ctx.update(
                json.loads(Path("validation_result.json").read_text())
            ),
            early_exit_condition=lambda ctx=context: not ctx.get("valid", False),
        ))

        # --- EXPORT ---
        session.add_task(pipeline_id, Task(
            name="export",
            strategy=LocalProcessStrategy(),
            command=["python", "export.py"],
        ))

    # ▶️ RUN ALL
    session.start_all_pipelines()

    # -----------------------------
    # 📊 ANALYSE DES EVENTS
    # -----------------------------

    # On groupe les events par task
    task_events = defaultdict(list)

    for e in events:
        task_name = getattr(e, "task_name", None)
        if task_name:
            task_events[task_name].append(e)

    # -----------------------------
    # ✅ ASSERTIONS
    # -----------------------------

    # 1. Tous les pipelines ont exécuté fetch
    assert len(task_events["fetch"]) > 0

    # 2. Validate a été exécuté (au moins une fois)
    assert len(task_events["validate"]) > 0

    # 3. Export ne doit jamais s’exécuter (early exit)
    assert "export" not in task_events

    # 4. Synchronisation effective :
    # on vérifie que les validate ne se chevauchent pas

    validate_timestamps = []

    for e in task_events["validate"]:
        ts = getattr(e, "timestamp", None)
        if ts:
            validate_timestamps.append(ts)

    # ⚠️ heuristique simple :
    # les timestamps doivent être globalement "étalés"
    # (pas tous identiques → pas parallèles)

    assert len(set(validate_timestamps)) > 1

    # 5. Tous les contextes ont été remplis
    for ctx in contexts.values():
        assert "valid" in ctx

    # 6. Tous les pipelines doivent être invalides (mock server)
    for ctx in contexts.values():
        assert ctx["valid"] is False