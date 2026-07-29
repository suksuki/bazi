# V60 Gameplay and Story Foundation

Status: `IMPLEMENTED_LOCAL`

This is the development contract for adding playable Dream content without
turning content, presentation or an LLM into a second game engine.

## Development order

V60 follows a game-production order:

```text
player promise
-> core loop
-> authored episode
-> rule validation
-> persistent simulation
-> playable scene
-> media and feel
-> content breadth
```

Visual detail cannot compensate for a weak choice or a fake consequence.
Generic infrastructure cannot replace one playable episode. Every new
foundation abstraction must be exercised by a real local slice in the same
iteration.

## Product promise and core loop

Abu Dream World lets a player inspect incomplete evidence, make a judgment
before the outcome is known, wait for the world rather than a browser timer,
and reconcile that judgment with committed evidence.

```text
enter one continuing world
-> observe two independent evidence leaves
-> connect them through one structure branch
-> open one question flower
-> seal one answer
-> wait for a due WorldEvent
-> reveal one fruit
-> reconcile
-> return to the changed world
```

The current five Episodes are content instances of this loop. They are not
special branches inside the engine.

## Four runtime layers

### 1. Authored Episode Definition

`DreamEpisodeDefinition` is the complete authoring package. It contains:

- one versioned Runtime contract;
- prompt and two to four comparable choices;
- pre-decision evidence;
- resolution atoms and no-baseline-credit rule;
- independently sealed future outcome;
- exactly two evidence leaves, one structure branch, one question flower and
  one outcome fruit.

The validator rejects:

- a missing evidence leaf;
- a branch that does not depend on both leaves;
- options that compare different dimensions;
- incomplete future evidence;
- outcome atoms in baseline evidence;
- flower or fruit refs that do not match their canonical Question or
  WorldEvent.

An invalid package never enters the playable Runtime.

### Hash-locked Episode Source Registry

Authored definitions are stored as versioned JSON source packages under:

```text
content/dream/episodes/
├── registry.json
├── yanzhou-old-channel-v1.json
├── yanzhou-wet-bank-v1.json
└── yanzhou-shared-night-water-v1.json
```

The registry binds each language-neutral package identity to one relative
path and SHA-256, and owns the explicit Episode transition graph. A package
contains the complete definition template, its WorldEvent definitions and an
explicit list of authority bindings. The current packages accept only
`structure_fact_ref`; they cannot accept arbitrary authored values from a
caller.

`EpisodeSourceRegistry` rejects:

- registry or package Hash drift;
- duplicate package identities or paths;
- absolute paths, traversal and non-JSON package paths;
- malformed, missing, extra or empty bindings;
- a missing or divergent Episode WorldEvent;
- a transition whose package or Question drifts, or whose optional legacy
  continuation/label disagrees when present;
- any compiled payload that fails `DreamEpisodeDefinition`.

The source registry is an authoring and admission boundary, not a Runtime
content provider. Seed/import orchestration compiles all packages with
canonical bindings, sends events to `WorldEventAdmissionService`, Episodes to
`StoryEpisodeAdmissionService` and edges to
`StoryEpisodeTransitionAdmissionService`. It owns none of those database
tables. The live `DreamEpisodeCatalog` continues to read only admitted
PostgreSQL records. There is no raw-package, Python-constant or legacy
fallback.

Registry edges are authoritative. An immutable source package may leave its
legacy continuation fields empty; it must not be rewritten merely to add a
later chapter. `first_slice.py` and `return_slice.py` exist only as
compatibility views that compile the corresponding Registry package. The
former writer tool has been removed; `tools/audit_episode_source_packages.py`
is read-only and compiles all packages without modifying the Registry.

### 2. Persisted Episode Contract

`DreamEpisodeContract` is the minimal immutable lifecycle contract persisted
with `story.question_instances`:

```text
episode identity and version
runtime admission status
gameplay identity and content key
chapter and entrypoint
actor / tree / question identity
baseline and future WorldEvent refs
cutoff and due Tick
Resolution Rule Hash
typed organ / actor / continuation Runtime metadata
six phase-specific Episode narrative moments
entry transition for a return episode
tree state before and after settlement
```

The canonical JSON and SHA-256 are stored together. Runtime loading validates
the Pydantic contract, its Hash, the duplicated relational columns and the
persisted Resolution Rule Hash. Flower/fruit names and the hidden NPC choice
come from typed Episode Runtime metadata. Titles, status copy, Theater beats
and Abu lines come from `EpisodeNarrativeContract`, not a Question-ID or
frontend fallback. A tampered or mismatched contract fails closed.

The first two historical Episode contracts retain their original optional
continuation fields so their persisted Hashes remain valid. Those fields are
read-only compatibility data. New graph growth does not modify them and
Runtime does not derive active transitions from them.

The persisted Resolution Rule is intentionally narrow. It contains only:

```text
rule version
comparable proposition atoms
no-baseline-credit policy
exact-match policy
mixed-match policy
no-match policy
```

Baseline presentation, organ copy, hidden NPC choice, fruit metadata and
narrative moments are separate versioned contracts. They must not be mixed
into the formal rule payload.

### Episode Admission Compiler

`EpisodeAdmissionCompiler` converts one complete authored definition into a
deterministic admission package. It resolves the canonical LifeCase revision,
structure Fact and WorldEvent and checks:

- Actor, Tree, Case and Chart lineage agree;
- pre-decision evidence exists no later than the cutoff;
- the continuation entry event is the only allowed same-cutoff baseline;
- WorldEvent type, due Tick, summary and outcome match the authored contract;
- Question, organ, contract and formal Resolution Rule Hashes are stable.

The resulting `EpisodeAdmissionManifest` binds every authority identity and
Hash plus the compiler version. `StoryEpisodeAdmissionService` is the only SQL
writer for playable Story content. Exact replay is idempotent; changed content
under the same Question identity raises an admission conflict. Seed code and
Dream Runtime cannot bypass this path.

### Episode Transition Admission

`EpisodeTransitionContract` is a separate immutable Story object:

```text
transition identity and version
source Question identity
target Question identity
visible continuation label
ACTIVE or RETIRED Runtime status
canonical JSON and SHA-256
```

`StoryEpisodeTransitionAdmissionService` is its only writer. It requires both
Questions to be admitted, the same Actor and LifeTree on both endpoints, a
non-entrypoint target and non-overlapping time windows. Exact replay is
idempotent. Reusing a transition identity with changed content fails closed.
Migration `0014_episode_transitions` backfilled the existing first-to-return
edge without rewriting either Episode.

### Episode Narrative Contract

Every active Episode defines exactly six moments:

```text
OBSERVING       -> BASELINE_ONLY
QUESTION_OPEN   -> BASELINE_ONLY
WAITING_FOR_WORLD -> SEALED_NO_OUTCOME
REVEAL_READY    -> WORLD_COMMITTED_HIDDEN
REVEALED        -> OUTCOME_REVEALED
COMPLETED       -> OUTCOME_REVEALED
```

Each moment owns a stable content key, title, status line, Theater beat and
Abu line. All five Episodes therefore share mechanics while remaining
meaningfully different stories. Exact future-event and evidence summaries
are invalid in pre-Reveal moments. Experience Context v3 revalidates the
phase/disclosure pair before any product projector receives it, keeps
post-cutoff outcome evidence out of every pre-Reveal projection and gives
Theater a separate committed evidence channel after Reveal.

### 3. Gameplay Director

`DreamGameplayDirector` combines a validated Episode Contract with the pure
`DreamGameEngine`. It emits a `GameplayScene`:

- stable Scene ID, version and layout identity from `DreamSceneRegistry`;
- current chapter and phase;
- legal commands;
- public organ states;
- continuation availability;
- stable content identity.

It does not choose an outcome, write a Seal, invent story facts or select
media. React and PixiJS render this scene; they do not derive legal state.

Every player action is submitted as one `DreamCommandEnvelope` through
`POST /api/v60/dream/command`. The envelope contains:

```text
command
encounter_ref
expected_version
idempotency_key
target_ref or choice_id when required
```

Payloads are command-specific and strict. The Game Engine rechecks both the
current legal-command set and organ role, so a presentation bug cannot use a
leaf action against a branch or flower. Dream Service owns dispatch and the
single Encounter transaction; there are no parallel mutable API routes.
Each accepted envelope writes one immutable `DreamCommandReceipt` in that
same transaction.

### Active Episode Catalog

`DreamEpisodeCatalog` is the only Runtime reader for persisted Episode
contracts. Before an Encounter is created or resumed it verifies the complete
catalog:

- every persisted contract, contract Hash and duplicated relational identity;
- every admission manifest and canonical authority/outcome Hash;
- every explicit Transition Contract, duplicated column and Hash;
- exactly one active entrypoint;
- unique Episode, Question and content identities;
- every active transition endpoint exists;
- no continuation cycle or unreachable active Episode;
- one Actor and LifeTree remain continuous across a continuation;
- the next cutoff does not overlap the previous Episode's due window.

Retired Episodes remain readable for replay, but cannot enter the active
content graph. If the active graph is invalid, Dream fails closed; it never
falls back to a hard-coded question, legacy continuation field or older scene.

### Versioned Scene Registry

`DreamSceneRegistry` maps each legal `DreamPhase` to a stable presentation
identity. The current registry contains one scene for each of:

```text
OBSERVING
QUESTION_OPEN
WAITING_FOR_WORLD
REVEAL_READY
REVEALED
COMPLETED
```

Scene identity is presentation metadata, not canonical progress. Changing a
layout or approved asset requires a new Scene version; playback still cannot
advance the Encounter by itself.

### 4. Simulation and consequence

`WorldContinuityEngine` alone advances integer Tick and settles due events.
`LifeStoryEngine` projects already committed semantic material. Dream owns
Encounter progress, AnswerSeal, Fruit, Reveal and reconciliation, but it may
not manufacture the WorldEvent it later reveals.

The canonical Gameplay Director exposes no `ADVANCE_WORLD` action. After Seal,
the visible state is read-only until the Runtime host settles the due event
from PostgreSQL wall time and Dream performs its idempotent projection
catch-up. Client polling observes that transition; it does not cause it.

The application Runtime continuously pulses this existing owner from
PostgreSQL wall time. It does not add another clock: one append-only
ClockEpoch defines the current rational mapping, and an advisory transaction
lock prevents concurrent processes from double advancing. Dream projection
catch-up is separately idempotent, so process failure cannot strand a settled
WorldEvent behind a waiting fruit.

The public Encounter snapshot applies an Episode disclosure horizon. Before
Reveal it exposes only that Episode's baseline Actor event and Episode-local
tree state. At Reveal it may add only that Episode's outcome; later Actor
timeline entries, mutable state and later LifeTree chapters remain excluded
even when the canonical world has already advanced beyond them.

Authored events first pass `WorldEventAdmissionCompiler`. The resulting
receipt binds Actor/Case/branch, event payload, due Tick, sealed outcome and
each initial evidence Ref/Tick/Hash. Settlement revalidates the receipt and
persisted evidence under row lock. A
historical event replay is idempotent and does not advance the Actor version a
second time.

Before a scheduled event can settle, its immutable outcome is routed as a
deterministic `WORLD_OUTCOME` decision. Reveal atom reconciliation is routed
separately as `DOMAIN_INFERENCE`. Both are system decisions recorded by the
same Cognition owner; neither answer choice nor presentation can alter the
world outcome.

## Canonical execution chain

```text
Mingli facts + committed world evidence
-> domain-owned bootstrap admission ports
-> hash-locked Episode source package + explicit authority bindings
-> validated DreamEpisodeDefinition
-> EpisodeAdmissionCompiler + authority manifest
-> persisted DreamEpisodeContract + Hash
-> admitted EpisodeTransitionContract + Hash
-> DreamGameplayDirector
-> DreamGameEngine command
-> Encounter write
-> admitted WorldEvent definition + immutable authority receipt
-> CognitiveDecisionLedger + WorldContinuityEngine settlement
-> CognitiveDecisionLedger + Reveal reconciliation
-> ExperienceContextEnvelope
-> LifeStoryEngine / product projections
-> React + PixiJS + Media Registry
```

Dependencies only point forward. Story does not import Dream episode content.
Dream Service does not branch on authored Question IDs. Presentation receives
safe public projections only. All five projectors accept the same immutable
Context Envelope; a cutoff guard and per-unit disclosure manifest make this a
machine-checked boundary rather than a presentation convention.

## Gameplay identity versus content identity

`gameplay_id` identifies a reusable rule loop. `episode_ref` identifies one
authored chapter. `content_key` reserves language-neutral copy identity.

New content that uses the same mechanics creates a new Episode Definition,
Contract and, when it follows another chapter, a new append-only Transition.
It never mutates the preceding Episode. A genuinely different loop requires a
new gameplay implementation and version; it must not be smuggled in as
optional fields or a growing set of Question-ID conditions.

V60 deliberately has no general gameplay DSL or story editor yet.

## Story authoring rules

Every playable episode must answer:

1. What changed in the world before the player arrived?
2. Why are both evidence leaves necessary?
3. What comparison does the branch establish without revealing the answer?
4. What uncertain proposition does the flower ask?
5. Which future event can distinguish the options?
6. What changes in the persistent world after settlement?
7. Why would a player care to return?

Dialogue and media express these answers; they cannot replace them.

## Replay and recovery

- PostgreSQL is the fact source.
- World time advances without an open page; browser timers are presentation
  only.
- Episode Contract Hashes survive process restart.
- The active Episode graph, including admitted transition payloads, has its
  own deterministic SHA-256.
- Existing AnswerSeal, Fruit, Reveal and Question Hashes are not rewritten by
  Episode-contract migration.
- A fresh command carrying a stale Encounter version fails closed.
- An exact receipt-backed retry of an already visible observation, Reveal,
  reconciliation or continuation returns the committed state without
  another version increment. AnswerSeal retains its persisted idempotency and
  conflicting-choice rejection. Reusing an idempotency key for a changed
  envelope is always a conflict.
- Browser URL and session storage are presentation aids only.
- A return chapter commits its entry WorldEvent before creating its Encounter.

## Content and media boundary

Media assets are referenced by registered asset identity and Cue Bundle.
Playback completion may request a command but cannot assert that the command
succeeded. Missing media falls back only to an approved static or reduced
motion delivery of the same asset identity, never to old V50 art or another
game state. The Bootstrap Media Runtime projection is the only frontend asset
source; presentation code may not embed registered delivery paths.

## Multilingual reservation

Episode, Question, organ, event, atom and asset identities are
language-neutral. `content_key` is persisted now, but V60 remains `zh-CN`
only. Translation catalogues, language switches and automatic translation are
not implemented.

## Gate before detail work

Before broad content or visual polish, a gameplay foundation is acceptable
only when:

- at least two authored episodes run through the same engine;
- changing an Episode Contract does not require editing Dream Service;
- future evidence is absent before Seal;
- world settlement is independent from answer choice;
- refresh and process restart recover the same chapter;
- the complete active Episode graph and Scene registry report `READY`;
- the player can understand one meaningful choice and its consequence;
- the next content slice can be added as data plus bounded presentation.

The current five Episodes satisfy the structural and append-only continuity
parts of this gate. The third chapter proves that an Actor promise and later
public action can use the same loop. The fourth proves that a frozen Mingli
timing vector and an already-committed world fact can become two independent
evidence leaves without letting timing coordinates dictate the outcome. The
fifth proves that one committed Episode outcome can become the historical
baseline for a new bounded career-duty proposition without reusing the old
settled event as a new unknown. Product-unit depth, scene-native interaction
and final media remain the next product work.
