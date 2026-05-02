# taskweave

Orchestration engine for long-running process pipelines. Orchestrates processes that talk to each other : sequencing tasks, 
managing concurrency, and streaming structured events to any sink (CLI, WebSocket, file).

Three execution models, combinable within the same session:

**Sequential pipeline** — tasks declared within a pipeline run in order. 
Multiple pipelines run in parallel with each other.

**Shared worker pool** — a `WorkerManager` instance controls concurrency across any task assigned to it, regardless of which pipeline it belongs to. 
A shared instance placed mid-pipeline becomes a synchronisation point 
across all pipelines that reach it.

**External sync** — when synchronisation is managed outside taskweave, 
implement `ExternalStrategy` and taskweave defers entirely to it.

All events produced by tasks (state changes, progress, logs) flow through a structured output declared via a **dialect** : a set of rules that classify process stdout into typed events, ready to serialize. 
The streams may feed two WebSocket channels : low-frequency state changes and high-frequency activity. See the default implementation of the server.

## How it works

### Sequential pipeline

Tasks declared within the same pipeline run in order. Multiple pipelines run in parallel with each other.

```python
pipeline_a = session.add_pipeline()
session.add_task(pipeline_a, fetch_task)    # runs first
session.add_task(pipeline_a, validate_task) # runs after fetch completes

pipeline_b = session.add_pipeline()
session.add_task(pipeline_b, other_task)    # runs in parallel with pipeline_a

session.start_all_pipelines()
```

### Cross-pipeline sync

Tasks may run many workers of the same type concurrently. `WorkerManager` handles concurrency and overflow via `max_count`.

```python
# Up to 4 fetch workers running at once
Task(name="fetch", strategy=LocalProcessStrategy(max_count=4), ...)
```

A shared `WorkerManager` instance creates a synchronisation point across pipelines — any task assigned to it will not start until a slot is available, regardless of which pipeline it belongs to. The manager can be assigned at any step of a pipeline.

```python
# Task 1 runs freely across all pipelines.
# Task 2 uses a shared manager — only one pipeline proceeds,
# the others wait for a slot. First pipeline to reach Task 2 wins.
validate_manager = WorkerManager(max_count=1)

for source in sources:
    pipeline_id = session.add_pipeline()
    session.add_task(pipeline_id, Task(name="fetch", ...))
    session.add_task(pipeline_id, Task(
        name="validate",
        strategy=LocalProcessStrategy(manager=validate_manager),
        ...
    ))
```

### External sync

When synchronisation is managed outside taskweave — a message queue, a database lock, an external scheduler — taskweave defers to the `ExternalStrategy` you implement.

```python
class MyQueueStrategy(ExternalStrategy):
    def run(self, task: Task, on_success: Callable, on_failure: Callable) -> None:
        queue.consume(task, on_success=on_success, on_failure=on_failure)
```

---

## Hello world

```python
from taskweave.session import SessionManager
from taskweave.tasks import Task
from taskweave.workers import LocalProcessStrategy

session = SessionManager(on_event=print)
pipeline_id = session.add_pipeline()

session.add_task(pipeline_id, Task(
    name="fetch",
    strategy=LocalProcessStrategy(),
    command=["python", "fetch.py", "--source", SOURCE_URL],
))

session.start_pipeline(pipeline_id)
```

Events flow to `on_event` as `LogEvent` instances wrapped in `Enveloppe`. No configuration required.

---

## Dialect

A dialect tells taskweave how to read a process's stdout. Without one, all lines are emitted as `MsgType.LOG_LINE`.

### Declaring fields

```python
from taskweave.dialect import RExtractor, Field, FieldSchema, JsonSchemaType

status_extractor = RExtractor(fields=[
    Field(schema=FieldSchema("status", JsonSchemaType.INT),    target="status="),
    Field(schema=FieldSchema("url",    JsonSchemaType.STRING), target="url="),
])
```

### Classifying lines

Each line is parsed according to cascading rules, first match wins.
`Persist_Verbose_And_Discarded` is the most common strategy — it keeps unmatched lines (typed as DISCARD internally) and known noise (lines identified and declared as VERBOSE) on disk, while structured output flows to the client. `Persist_Discarded` skips `VERBOSE` from logging to disk.

```python
from taskweave.dialect import (
    Classifier, OutputType,
    PersistStrategy, PersistPolicy, FileBackend,
)
from taskweave.context import constants

fetch_classifier = Classifier(
    rules={
        status_extractor: OutputType.PROGRESS,  # status=200 url=https://... → client
        RExtractor(fields=[
            Field(schema=FieldSchema("total", JsonSchemaType.INT), target="urls_count="),
        ]): OutputType.BANNER,                  # urls_count=142 → client, once
    },
    # taskweave does not handle retry — unmatched lines (connection errors, warnings)
    # are kept on disk. Recovery logic belongs to the app.
    persist=Persist_Verbose_and_Discarded(
        backend=FileBackend(log_dir=constants.log_folder),
    )
)
```

`OutputType` values:

| Value | Sent to client | Persisted to disk |
|---|---|---|
| `PROGRESS` | yes | no |
| `BANNER` | yes | no |
| `LOG_LINE` | yes | no |
| `VERBOSE` | yes | yes |
| `DISCARD` | no | yes |

### Attaching a dialect to a task

`Task` accepts any `LogProducer` — `ClassifyingProducer` is the implementation provided by `dialect`, wrapping a `Classifier` into the expected interface. 

```python
from taskweave.workers import ClassifyingProducer

session.add_task(pipeline_id, Task(
    name="fetch",
    strategy=LocalProcessStrategy(max_count=4),
    command=["python", "fetch.py", "--source", SOURCE_URL],
    producer=ClassifyingProducer(classifier=fetch_classifier),
))
```

---

## Use case — fetch, validate, export

A pipeline that fetches URLs from a CSV, validates each response, and exports results.

```python
from pathlib import Path
import json

context = {}
validation_result = Path("validation_result.json")
matches_path      = Path("matches.json")

session = SessionManager(on_event=print, cancel_policy=CancelPolicy.CANCEL_ALL)
pipeline_id = session.add_pipeline()

session.add_task(pipeline_id, Task(
    name="fetch",
    strategy=LocalProcessStrategy(max_count=4),
    command=["python", "fetch.py", "--source", SOURCE_URL],
    producer=ClassifyingProducer(classifier=fetch_classifier),
    on_complete=lambda: context.update(json.loads(validation_result.read_text())),
))

session.add_task(pipeline_id, Task(
    name="validate",
    strategy=LocalProcessStrategy(),
    command=["python", "validate.py"],
    on_complete=lambda: context.update(json.loads(validation_result.read_text())),
    # exit early on failure — no point exporting invalid data
    early_exit_condition=lambda: not context["valid"],
))

session.add_task(pipeline_id, Task(
    name="match_keywords",
    strategy=LocalProcessStrategy(),
    command=["python", "match_keywords.py"],
    on_complete=lambda: context.update(json.loads(matches_path.read_text())),
    # exit early on success — results found, no need to continue
    early_exit_condition=lambda: len(context["matches"]) > 0,
))

session.add_task(pipeline_id, Task(
    name="export",
    strategy=LocalProcessStrategy(),
    command=["python", "export.py", "--output", "results.csv"],
))

session.start_pipeline(pipeline_id) # or session.start() for "all pipelines"
```

`on_complete` is always called after a task finishes — use it to pass data between tasks via shared context. `early_exit_condition` is evaluated after `on_complete` — taskweave stays blind to the business logic.

---

## Advanced

### Cancel policy

```python
CancelPolicy.CANCEL_ALL   # stop running workers immediately on early_exit
CancelPolicy.GRACEFUL     # let running workers finish
```

### Persist backend — custom sink

Implement `PersistBackend` to route logs to any storage:

```python
from taskweave.dialect import PersistBackend, OutputType

class ElasticBackend:
    def write(self, source_id: str, line: str, output_type: OutputType) -> None:
        elastic_client.index(
            index=source_id,
            body={"line": line, "type": output_type.value}
        )

classifier = Classifier(
    rules={...},
    persist=PersistStrategy(backend=ElasticBackend(), policy=PersistPolicy.ALL),
)
```

### WebSocket sinks (Flask)

`StreamManager` dispatches to two channels — low-frequency state changes, high-frequency activity:

```python
@sock.route('/session/<id>/state')
def ws_state(ws, id):
    queue = session_manager.subscribe_state(id)
    while True:
        ws.send(json.dumps(queue.get()))

@sock.route('/session/<id>/activity')
def ws_activity(ws, id):
    queue = session_manager.subscribe_activity(id)
    while True:
        ws.send(json.dumps(queue.get()))
```

`subscribe_state` — `MsgType.STATE_CHANGE` with snapshots, low frequency.
`subscribe_activity` — `MsgType.PROGRESS`, `MsgType.LOG_LINE`, `MsgType.BANNER`, full frequency.

The `parsed` field on `PROGRESS` events matches the `JsonSchema` declared by the task's `RExtractor`. Use it to drive a dashboard or generate API documentation automatically.