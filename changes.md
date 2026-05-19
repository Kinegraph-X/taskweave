Voilà le bilan structuré.

---

## TODO — Implémentation

**Architecture**
- [*] Extraire `FieldSchema`, `OutputType`, `MsgType`, `LogEvent`, `TaskOutcome` dans `taskweave-protocol`
- [*] Créer `taskweave-transport` avec `ControlTransport`, `StdinTransport`, `SocketTransport`
- [*] Implémenter `PersistRegistry` owned by `SessionManager`
- [*] Implémenter `RoutingPolicy` sur `LogEvent`
- [ ] Supprimer `Task.producer.persist` — option 2, `SessionManager` seul responsable
- [*] Enrichir `ExecutionContext` avec `MiniBus` et `PersistRegistry`
- [*] Implémenter `make_sink(context)` sur `LogProducer` — symétrique de `make_runner()`
- [*] Implémenter `_wire_event_channel()` sur `SessionManager`
- [*] Implémenter `_completion_dispatch` thread dans `WorkerManager`
- [*] Implémenter `MsgType.ERROR` et `MsgType.HEARTBEAT_TIMEOUT` et `MsgType.BACKEND_FAILURE`
- [*] Implémenter `OutputType.ERROR` dans le dialect
- [*] Implémenter `CircuitBreaker` sur `PersistStrategy` avec `write_internal()` pour éviter la boucle
- [*] Implémenter `ObservabilityPolicy` (`BEST_EFFORT` / `SAFE`) avec `register_failure_behavior(cb)`
- [ ] Implémenter `ObservabilityFailureContext` avec `last_emitted`, `last_persisted`, `missing_count`
- [ ] Implémenter `ErrorChannel` sur socket séparé
- [ ] Implémenter `ControlChannel` avec `ControlDialect` et `CommandSerializer`
- [*] Ajouter `control: ControlDialect | None` sur `Task` (nullable, opt-in)

**Tests**
- [ ] Machine à états — transitions illégales
- [ ] Snapshot immutabilité — muter la source ne mute pas le snapshot
- [ ] Routage callbacks — `on_success` / `on_failure` / `on_finally` exclusifs et indépendants
- [ ] Exception dans callback — les autres callbacks continuent
- [ ] Backend timeout — non bloquant pour l'orchestrateur
- [ ] Race condition completion/cancel — via `_completion_dispatch`
- [ ] `HeartBeat` — avec `FakeClock` et `FakeSleep` injectés
- [*] `CircuitBreaker` — ouverture après threshold, recovery après timeout
- [ ] `PersistRegistry` — routing correct selon `RoutingPolicy`
- [*] Unicité des IDs — collision détectée dans `LogStore`

**Prospectif — à poser sans implémenter**
- [ ] `EventDispatcher` côté client — symétrique de `Classifier`
- [ ] `ControlDialect` dans `taskweave-protocol`
- [ ] `BenchmarkCollector` comme backend de logging
- [ ] `replay_since(cursor)` sur `StreamWriter` pour reconnexion client

---

## API Changes

**`Task`**
```python
# avant
name: str
persist: PersistStrategy | None
producer: LogProducer

# après
name: TaskId                           # plus de conversion dans __post_init__
persist: PersistStrategy | None        # inchangé — mais géré par SessionManager
persist_config: CircuitBreakerConfig   # nouveau
timeout_profile: TimeoutProfile        # nouveau, default NORMAL
control: ControlDialect | None         # nouveau, opt-in
# producer.persist supprimé
```

**`LogEvent`**
```python
# avant
parsed: Any

# après
parsed: Any                            # inchangé — assumé et documenté
routing: RoutingPolicy                 # nouveau — forward + persist
sequence: int                          # à vérifier si déjà présent
```

**`SessionManager`**
```python
# nouveaux paramètres de construction
observability_policy: ObservabilityPolicy = ObservabilityPolicy.BEST_EFFORT
backend_config: CircuitBreakerConfig | None = None

# nouvelles méthodes
def add_pool(pool: ExecutionPool) -> None
def register_failure_behavior(cb: Callable[[ObservabilityFailureContext], None]) -> None
```

**`WorkerManager`**
```python
# paramètre de construction ajouté
_completion_queue: Queue | None = None  # underscore — usage interne
_event_bus: MiniBus | None = None       # underscore — usage interne
```

**`HeartBeatStrategy`**
```python
threshold: float
max_threshold: float                   # borne explicite
max_attempts: int
clock: Callable[[], float]             # injectable pour tests
sleep: Callable[[float], None]         # injectable pour tests
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