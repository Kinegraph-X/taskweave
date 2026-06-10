Voilà le bilan structuré.

---

## TODO — Implémentation

**Architecture**
- [*] Extraire `FieldSchema`, `OutputType`, `MsgType`, `LogEvent`, `TaskOutcome` dans `taskweave-protocol`
- [*] Créer `taskweave-transport` avec `ControlTransport`, `StdinTransport`, `SocketTransport`
- [*] Implémenter `PersistRegistry` owned by `SessionManager`
- [*] Implémenter `RoutingPolicy` sur `LogEvent`
- [*] Supprimer `Task.producer.persist` — option 2, `SessionManager` seul responsable
- [*] Enrichir `ExecutionContext` avec `MiniBus` et `PersistRegistry`
- [*] Implémenter `make_sink(context)` sur `LogProducer` — symétrique de `make_runner()`
- [*] Implémenter `_wire_event_channel()` sur `SessionManager`
- [*] Implémenter `_completion_dispatch` thread dans `WorkerManager`
- [*] Implémenter `MsgType.ERROR` et `MsgType.HEARTBEAT_TIMEOUT` et `MsgType.BACKEND_FAILURE`
- [*] Implémenter `OutputType.ERROR` dans le dialect
- [*] Implémenter `CircuitBreaker` sur `PersistStrategy` avec `write_internal()` pour éviter la boucle
- [*] Implémenter `ObservabilityPolicy` (`BEST_EFFORT` / `SAFE`) avec `register_failure_behavior(cb)`
- [ ] Implémenter `ObservabilityFailureContext` avec `last_emitted`, `last_persisted`, `missing_count`
- [*] Implémenter `ErrorChannel` (destiné à socket/Flask séparé)
- [ ] Implémenter `ControlChannel` avec `ControlDialect` et `CommandSerializer`
- [*] Ajouter `control: ControlDialect | None` sur `Task` (nullable, opt-in)
- [*] Implémenter `HeartBeat`
- [implem partiellle] `BenchmarkCollector` comme backend de logging alternatif (permet de lancer une session à blanc et d'observer les seuils de heartbeat pour chaque tâche)

**Tests**
- [ ] Machine à états — transitions illégales
- [*] Snapshot immutabilité — muter la source ne mute pas le snapshot
- [*] Routage callbacks — `on_success` / `on_failure` / `on_finally` exclusifs et indépendants
- [ ] Exception dans callback — les autres callbacks continuent
- [*] Backend timeout — non bloquant pour l'orchestrateur
- [ ] Race condition completion/cancel — via `_completion_done`
- [*] `HeartBeat` — avec `FakeClock` et `FakeSleep` injectés
- [*] `CircuitBreaker` — ouverture après threshold, recovery après timeout
- [ ] `PersistRegistry` — routing correct selon `RoutingPolicy`
- [*] Unicité des IDs — collision détectée dans `LogStore`

**Prospectif — à poser sans implémenter**
- [ ] `EventDispatcher` côté client — symétrique de `Classifier`
- [ ] `ControlDialect` dans `taskweave-dialect`
- [ ] `replay_since(snapshot)` sur `SessionManager` pour reconnexion client

---

## API Changes

**`Task`**
```python
# avant
name: str
persist: PersistStrategy | None
producer: LogProducer | None
strategy : WorkerPool

# après
name: src | TaskId           # conversion vers TaskId dans __post_init__
producer: LogProducer        # defaulted to LogEventProducer
# ClassifyingProducer.strategy defines RoutingPolicy on LogEvent
backend : PersistBackend    # un seul point de définition de la persistance, pour gérer classified or default
# avec PersistBackend.config: CircuitBreakerConfig   # nouveau
control: ControlDialect | None         # nouveau, opt-in
strategy : PoolStrategy | None        # utile uniquement si choix d'un pool synchronisé inter-tâches (WorkerManager maintenant caché dans la lib) 
```

**`LogEvent`**
```python
# réflexion sur l'ancien
parsed: Any                         # pourrait être dict | None

# ajouts
routing: RoutingPolicy                 # nouveau — forward + persist, le message est maintenant le seul à connaître le routing
sequence: int                          # provides minimal continuity proof in logs
```

**`SessionManager`**
```python
# nouveaux paramètres de construction
# déclaration d'intention de l'utilisateur (code un peu + self-documenting)
observability_policy: ObservabilityPolicy = ObservabilityPolicy.BEST_EFFORT
# définit si le canal d'erreur (StreamWriter.emit_internal()) reçoit un snapshot de l'orchestrateur. La vraie policy est surtout le min_drain_threshold sur PersistBackend, en cas de backend qui accumule dans sa queue (queue non-bloquante sur les writes et min_drain_threshold. Utiles pour être capable de raise et d'ouvrir le circuit, et pour la testabilité : min_drain_threshold surdimmensionné si on lance un backend et qu'on le clôt immédiatement garantit le clean drain. Si trop de messages en queue, race-condition, mais on accepte, et on garantit le log uniquement pour les 3 derniers)

# nouvelles méthodes
def add_pool(pool: ExecutionPool) -> PoolStrategy       # PoolStrategy est une déclaration, SessionManager abstrait le branchement sur le worker via le TaskRunner (ancienne idée de TaskStrategy rationnalisée : le runner est indépendant de la déclaration d'intention)

# restructurées
def add_task() # délègue a _define_runner(self, task : Task) -> None et _handle_task_persitance(self, task_spec : Task) -> Callable | None: return def cleanup() if task_spec.backend (cleanup pour LifeCycle)
```

** MiniBus **
```python
def __init__()
    self._writer = writer
    self._observability_policy = observability_policy
    self._last_seen_sequences : dict[TaskId, SeenSequences] = {} # du fait d'un canal d'erreur indépendant du logging (pour propager l'échec du logging), branchement entre MiniBus.emit_internal et StreamWriter._on_internal_event, fait par ObservabilityContext
def emit(self, event: LogEvent) -> None:
def emit_internal(self, event : LogEvent) -> None:
    self._handle_observability_policy(event)
```

** TaskStrategy devient ExecutionStrategy**
```python
class ExecutionStrategy(Protocol):
    def _get__runner(self, context : ExecutionPool) -> TaskRunner
# avec ExecutionPool(
        #     source_id = task.name,
        #     pools = self._execution_pools,
        #     event_bus = self._log_bus
        # )
# juste un contexte, consommé ou pas : fonctionne quel que soit l'implem
```

**`WorkerManager`**
```python
_event_bus: MiniBus | None = None       # underscore — usage interne, pensé instance unique, point de branchement unique avec StreamWriter, mais découplage quand-même sur le package "workers"
```

**`HeartBeatConfig`**
```python
threshold: float
max_threshold: float                   # borne explicite
max_attempts: int
clock: Callable[[], float]             # injectable pour tests
sleep: Callable[[float], None]         # injectable pour tests

# mécanisme de détecion de process stale ou lent : 
# implémenté sur WorkerPool : là où on poll l'event_queue
class Heartbeat:
    config : HeartBeatConfig
    def beat(): if event in ACTIVITY_EVENTS : attempts = 0 # sinon la durée de battement croît jusqu'à max_threshold, puis on propage HEARTBEAT_TIMEOUT
```

**`MsgType`**
```python
ERROR              = "error"           # nouveau
HEARTBEAT_TIMEOUT  = "heartbeat_timeout"  # nouveau
BACKEND_FAILURE    = "backend_failure" # nouveau
```

**`OutputType`**
```python
ERROR = "error"                        # nouveau
```

**`ObservabilityPolicy`**
```python
class ObservabilityPolicy(Enum):
    BEST_EFFORT = "best_effort"
    SAFE        = "safe"
```

---

## Technical Takeaways

**Sur le design**

- *La douleur du mapping inverse révèle un product type mal encodé dans un sum type* — `OutputType` → `RoutingPolicy`
- *Un point de branchement unique vaut mieux que deux chemins vers la même fonctionnalité* — `PersistStrategy` owned une seule fois
- *Le canal d'erreur ne doit pas dépendre de ce qu'il surveille* — `write_internal()` comme `stderr`, boucle infinie évitée
- *Nommer la tension plutôt que la cacher* — `Any` assumé sur `LogEvent.parsed`, documenté honnêtement
- *`ExecutionContext` comme Context Object* — binding au moment de `submit()`, zéro late-initialization

**Sur Python**

- `frozen=True` protège l'objet, pas le contenu de ses champs mutables — combiner avec types immuables natifs (`tuple`, `str`)
- `id()` unique seulement à un instant donné — dangereux pour détecter le partage si les objets ont un cycle de vie court
- `queue.Queue` pour inter-thread, `multiprocessing.Queue` pour inter-process
- `itertools.count()` thread-safe sous CPython via le GIL
- `__post_init__` ne narrowe pas les types pour Mypy — utiliser `InitVar` ou factory `create()`
- Injecter `clock` et `sleep` pour rendre le temps testable — `FakeClock` + `FakeSleep`
- `propagate = False` sur les loggers pour éviter les remontées involontaires
- `@classmethod` existe indépendamment des instances — appelable depuis `__init__`

**Sur les systèmes**

- *Tout système qui s'observe lui-même doit répondre à trois questions* — chemin normal, chemin d'erreur, canal de dernier recours
- *Le Circuit Breaker distingue les erreurs transitoires des erreurs permanentes* — `TransientBackendError` vs `PermanentBackendError`
- *La reconnexion sur snapshot plutôt que replay* — l'état stable est plus fiable que l'historique complet
- *Le jitter dans le backoff casse la synchronisation des clients* — sans lui, tous retraient ensemble
- *`ObservabilityPolicy` comme contrat explicite* — `BEST_EFFORT` vs `SAFE`, documenté, pas implicite
- *`BenchmarkCollector` comme backend* — l'orchestrateur s'observe lui-même sans modification

**Sur l'architecture**

- *Trois packages, trois intentions* — `taskweave-transport` (médium), `taskweave-protocol` (vocabulaire), `taskweave` (orchestration)
- *SemVer strict sur `taskweave-protocol`* — range pinning dans les dépendances (`>=1.2,<2.0`)
- *Protocol partiel + Context Object* — chaque composant déclare ce qu'il consomme, `ExecutionContext` satisfait tout structurellement
- *Two-phase construction* — phase déclarative à la définition, phase opérationnelle à `submit()`
- *`_completion_dispatch` comme seul arbitre du statut final* — `CancelIntent` et `CompletionResult` dans la même queue, premier arrivé décide

---

on_finally : saga in-process uniquement. Pour une saga distante, observez task.succeeded et envoyez une commande via SessionGateway