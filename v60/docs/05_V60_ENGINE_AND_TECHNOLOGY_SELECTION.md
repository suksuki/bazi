# V60 Engine and Technology Selection

## Product architecture

V60 is a modular monolith first. It uses one deployable backend, one web
client and one PostgreSQL database with explicit module ownership. It may split
only after measured operational pressure proves the need.

## Dream game engine

```text
DreamGameEngine
├── pure encounter state machine
├── legal command derivation
└── semantic organ projection

DreamGameplayDirector
├── versioned Episode Contract verification
├── contract-hash and identity checks
└── scene phase, commands and public organ projection

WorldContinuityEngine
├── integer Tick and append-only ClockEpoch
├── WorldEvent admission compiler and immutable receipt
├── rational wall-clock projection and database-fenced pulse
├── DueSchedule and exactly-once WorldEvent settlement
├── actor timeline and event evidence
└── transactional Outbox

LifeStoryEngine
├── hash-locked Episode + WorldEvent source packages
├── source-bound Episode transition graph
├── fail-closed package binding and admission compiler
├── committed-source Question metadata and admission manifest
├── deterministic ScenePlan
├── versioned Episode narrative moments
└── disclosure-safe story projection

ExperienceContextEnvelope
├── one Case / World / Encounter lineage
├── cutoff and monotonic-progress validation
├── sealed-outcome and hidden-choice exclusion
└── per-product-unit disclosure manifest

React + PixiJS + Media Registry
└── accessible interaction and 2D presentation
```

- **PixiJS** is the 2D rendering engine for trees, fog, scene layers and
  spatial interaction.
- **React** owns accessible controls, text, forms and application composition.
- `DreamGameEngine` cannot write the world outcome.
- `DreamGameplayDirector` cannot own authored content or persistence.
- `WorldContinuityEngine` cannot write an AnswerSeal or invent story copy.
- `WorldEventAdmissionService` rejects answer-owned outcomes, authority drift
  and changed-content identity replay before World scheduling.
- `LifeStoryEngine` can stage only committed semantic objects.
- Product projectors accept one validated `ExperienceContextEnvelope`, not
  independent raw dictionaries or database rows.
- The browser never owns canonical world state or event outcomes.
- The Runtime host may invoke World and Dream typed ports, but it owns no
  schema and cannot bypass either engine's write boundary.
- Seed and import workflows are orchestration only. They call versioned
  Platform, Identity, Mingli, World, Story and Dream admission services; direct
  cross-schema bootstrap SQL is rejected by architecture tests.
- We do not use Unity or Godot for the first web release: V60 is a 2D,
  accessibility-sensitive, UI-integrated experience, and those engines would
  add a second application shell without solving a current product problem.
- We do not hand-roll raster rendering, asset loading or WebGL batching.

## Mingli engine

`MingliCognitiveEngine` is a V60 domain engine, not a third-party fortune
telling package and not an LLM prompt.

```text
birth input
-> deterministic calendar and chart facts
-> typed relation graph
-> versioned knowledge and rule profiles
-> qualified candidate fabric
-> CognitiveDecisionKernel
-> Epistemic Gate
-> LifeCase revision
```

Python 3.12, Pydantic and pure domain services implement deterministic and
rule-governed behavior. PostgreSQL stores versioned facts, evidence and formal
decisions. The LLM may compare already-qualified interpretations only when the
decision contract permits it; it cannot create chart facts, permissions,
world outcomes or global knowledge.

`KnowledgeAuthority` is the executable read boundary for those profiles. It
admits only exact profile ID/version identities, optionally verifies the
expected SHA-256 and fails closed on unknown or altered material. The current
foundation profile is a code-native, immutable registry because it is a small
deterministic table; no knowledge database, question bank or LLM retrieval
layer is introduced yet. Its public manifest keeps
`professionally_reviewed=false` and exposes the Owner-bounded source identity.

`StructuralCandidateCompiler` is the first executable candidate-fabric slice.
It derives stable read-only candidate identities from admitted typed relation
facts and carries their provenance into Lab. It deliberately does not infer
relation effect, usable root, capacity, mechanism success or professional
admission. Candidate existence therefore never implies effective work.

`CandidateQualificationEngine` is the shared rule-execution boundary between
candidate existence and decision routing. It resolves an exact hash-locked
rule profile, evaluates only the named evidence dimension and emits an
immutable receipt. The first profile grants only
`STRUCTURE_EVIDENCE_SATISFIED` for bounded relation-membership facts. Its rule
contract has `selection_authority=false` and names every forbidden conclusion,
so the receipt cannot silently become relation effect, capacity, usability,
professional admission or effective work. Missing rules, altered authority or
source drift fail closed.

The bounded Reasoner now has a provider-neutral Runtime Host and an optional
OpenAI Responses adapter. A `DecisionProposal` may contain only an
already-qualified candidate selection plus request-bound evidence,
counter-evidence, provider/model/prompt/response identity, context Hash and
uncertainty. Strict structured output is revalidated by Pydantic and
`EpistemicGate` before the Decision Ledger can record it. The Gate never grants
a direct domain write. Missing, disabled or unsupported provider configuration
fails closed before a network call.

## Life story engine

`LifeStoryEngine` compiles committed semantic objects into scene plans.

```text
LifeCase / WorldEvent / DecisionRecord
-> StoryOpportunity
-> deterministic StoryBeat plan
-> approved asset and disclosure selection
-> optional bounded wording
-> Dream / Abu Says / Theater projection
```

The Story engine does not invent events. It chooses how an authorized,
already-existing semantic object is experienced. Story beats and assets are
data-driven and versioned; no general screenplay DSL is introduced before
real content demonstrates repeated structure.

Playable content is admitted as a validated `DreamEpisodeDefinition`. Runtime
uses its smaller persisted `DreamEpisodeContract`, verifies the SHA-256 and
passes it through `DreamGameplayDirector`. Story never imports Dream content,
and Dream services never branch on authored Question IDs.

Authoring packages live in `content/dream/episodes/` behind one versioned
registry Hash. Their only variable fields are explicit authority bindings such
as the admitted structure Fact Ref. Each package carries the matching
WorldEvent definitions, and the Registry carries the transition graph.
Compilation proves event identity, Actor, due Tick, summary and sealed outcome
agree with the Episode. Loading rejects undeclared bindings, missing bindings,
path traversal, content drift and transition drift. The live Runtime never
reads these source files; it reads only admitted PostgreSQL contracts and
manifests.

`StoryEpisodeAdmissionService` is the only Story writer for playable content.
Its compiler resolves canonical LifeCase, structure-fact and WorldEvent
authority, rejects cutoff or outcome drift, and persists a deterministic
admission manifest. Exact replay is idempotent; a changed definition under the
same Question identity is rejected instead of silently ignored.

The active registry currently contains three Episodes and two transitions.
Registry transitions are authoritative even when an immutable older package
has no embedded continuation pointer. The old Python slice modules compile
their compatibility constants from this Registry and cannot overwrite JSON
packages; the former exporter has been replaced by a read-only audit command.

The formal persisted resolution rule contains only comparable proposition
atoms and the exact/mixed/no-match policy. Organ names, baseline presentation,
NPC choice, fruit copy and six narrative moments remain separate versioned
contracts. They cannot change the formal rule Hash by accidental JSON mixing.

The Episode contract owns a six-moment `EpisodeNarrativeContract`. Each moment
binds the phase to a stable content key, title, status, Theater beat, Abu line
and disclosure class. `LifeStoryEngine`, Abu Says, Theater and the React shell
consume that same moment through `ExperienceContextEnvelope`; none of them
reconstruct authored narrative from chapter names, Question IDs or local
status branches.

Experience Context v3 keeps baseline and revealed evidence in separate typed
channels. Baseline evidence remains cutoff-bounded and carries no prediction
credit. Committed post-cutoff World evidence becomes projectable only after a
Reveal exists; Theater then uses that outcome channel instead of replaying the
baseline clues.

## Central brain

`CognitiveDecisionKernel` is the single routing authority:

1. The deterministic system proves facts, policies, transitions and outcomes.
2. Rules filter and qualify candidates.
3. A bounded LLM Reasoner compares remaining candidates when authorized.
4. Humans own consent and irreversible subjective choices.
5. The Epistemic Gate alone creates formal records.
6. Insufficient evidence remains `UNRESOLVED`.

`CognitiveDecisionLedger` makes this authority executable. Deterministic world
outcomes and Reveal reconciliation now route through the Kernel and append one
immutable record in the same transaction as their canonical result. Exact
retry is idempotent; a changed payload under the same decision identity is a
hard conflict. The active identity is
`v60.cognitive-decision-kernel.004`.

`EvidenceReconciliationEngine` compares sealed proposition atoms with later
committed evidence. Pre-seal baseline facts receive no prediction credit, and
missing required atoms fail closed.

## Foundation stack

| Layer | Selection |
| --- | --- |
| Runtime | Python 3.12 |
| API | FastAPI |
| Contracts | Pydantic |
| Persistence | PostgreSQL + SQLAlchemy |
| Migrations | Alembic |
| Web shell | React + TypeScript |
| 2D rendering | PixiJS |
| Browser QA | Playwright against installed Chrome |
| Python QA | Pytest + Ruff |
| Asset authority | Versioned manifest + SHA-256 |
| Media production | Immutable sources + postprocess lineage + Cue Bundles |

## Source modularity and size budgets

V60 treats a very large source file as an ownership warning, not as a normal
end state. Runtime code is split by transaction owner and reason to change:

```text
DreamService
  -> command dispatch and transaction orchestration

DreamRepository
  -> Encounter, Tree and command-receipt persistence

DreamSnapshotProjector
  -> read-only public snapshot composition

DreamOutcomeCoordinator
  -> World settlement, Fruit maturity and Reveal reconciliation
```

React follows the same rule: `App` composes Runtime state and navigation;
login, brand and companion presentation are independent components. CSS is
ordered through small imports for foundation, tree scene, product units,
system/auth and responsive behavior.

`abu_v60.architecture.source_budget` enforces hard safety ceilings:

| Runtime source | Hard maximum |
| --- | ---: |
| Python module | 850 lines |
| TypeScript / TSX module | 500 lines |
| CSS module | 600 lines |

These are emergency ceilings, not preferred sizes. A cohesive module should
usually remain well below them. The repair for an over-budget file is to
separate owners or responsibilities; blanket exemptions and arbitrary
line-slicing are not accepted.

The executable architecture registry is
`abu_v60.architecture.registry.RUNTIME_ARCHITECTURE`. It validates module
dependencies, unique schema ownership and read-only product units at startup.

The current owner-admission boundary is:

```text
Seed / V50 import coordinator
-> MigrationBatchAdmissionService
-> IdentityAdmissionService
-> MingliCaseAdmissionService
-> WorldActorAdmissionService
-> WorldEventAdmissionService
-> StoryEpisodeAdmissionService
-> LifeTreeAdmissionService
```

Each port owns only its schema, validates exact replay and rejects identity or
provenance drift. Mutable Actor and LifeTree state is never reset by replay.

## Deferred until justified

- Redis, Kafka and a service mesh.
- A second database or graph database.
- A general NPC mind framework.
- Unbounded LLM agents.
- A custom visual editor or story DSL.
- Runtime model training or automatic rule promotion.
