# V60 Domain and Data Model

## Architecture style

V60 starts as a modular monolith with one PostgreSQL database and explicit
schema ownership. Modules communicate through typed services and ports, not
cross-schema writes.

```text
Identity
Mingli
Knowledge
Cognition
World
Story
Dream
Abu
Theater
Lab
Media
```

## Core aggregates

### CaseAggregate

Long-lived identity for a human or an explicitly synthetic subject.

```text
Case
├── Profile
├── ChartVersion
├── LifeCaseRevision
├── RealityEvidence
└── RevisionLedger
```

### DecisionAggregate

Owns requests, proposals, gate receipts and immutable committed decisions.

### WorldAggregate

Owns integer world time, epochs, actors, due events, event settlement and
world projections.

Every authored WorldEvent carries a deterministic
`WorldEventAdmissionManifest` that binds:

```text
World / Actor / Case / branch
event type + due Tick
immutable event payload Hash
sealed outcome Hash
initial evidence Ref + committed Tick + Hash
definition Hash + compiler version
```

The initial admission state is distinct from the current lifecycle state. A
scheduled event may later be settled without changing its definition Hash.
World Continuity validates the receipt before settlement, so a changed payload
or outcome cannot be accepted merely because the row identity still exists.

### DreamVisitAggregate

Owns entry, encounter, navigation, recovery, departure and disclosure state.

### LifeTreeAggregate

Projects one authorized Case into stable organs and visible phenotype. It is
not a Mingli truth owner.

Its canonical state is limited to stable phenotype and growth caused by
committed WorldEvents. A viewer observing a leaf, opening a question or sealing
an answer must never mutate the canonical LifeTree.

### StoryAggregate

Owns StoryOpportunity, ScenePlan, BeatSequence and presentation cues. It never
owns the world outcome or chart interpretation it presents.

Each immutable `QuestionInstance` owns the organ projection used for that
question version. The projection contains stable leaf, branch, flower and fruit
IDs plus their source refs and hash. This prevents one viewer's later encounter
from replacing another viewer's earlier question organs.

Every playable `QuestionInstance` also carries an immutable
`EpisodeAdmissionManifest`. The Story owner compiles it from the complete
Episode definition and canonical source snapshot. It binds:

```text
Question / Episode / Organ / Contract Hashes
LifeCaseRevision + revision Hash
Structure Fact + Fact Hash
WorldEvent + outcome Hash
cutoff Tick + due Tick
admission compiler version
```

The manifest is not authored presentation metadata. It is the proof that the
content was checked against the same Case, Tree, Actor, World and time window
before admission. Exact replay returns the existing record; identity reuse
with different content fails closed.

### Encounter projection boundary

```text
Canonical LifeTree
  -> stable phenotype + committed world growth

QuestionInstance
  -> immutable organ projection for one question/cutoff

Encounter
  -> viewer-private observation, Seal, Reveal and reconciliation progress

URL view/focus
  -> disposable navigation state only
```

Dream, Mingli Calculation, Abu Says, Theater and Lab derive their visible focus
from the same QuestionInstance organ and server-owned source refs. None of
these projections may create facts or rewrite another projection's evidence.

### Experience context boundary

One immutable `ExperienceContextEnvelope` is assembled from the current
Encounter and canonical owners before any product-unit projector runs:

```text
Encounter + Actor + World + Question
+ LifeCaseRevision + ChartVersion + formal Facts
+ pre-cutoff committed evidence
+ post-Reveal DecisionRefs only
-> ExperienceContextEnvelope + Hash
-> per-unit disclosure manifest
-> five read-only projections
```

The contract rejects evidence observed after the Question cutoff, outcome
atoms in baseline evidence, DecisionRefs before Reveal, duplicate source refs
and non-monotonic Encounter progress. It never carries the sealed outcome or
the hidden NPC choice. Every projection returns the same `context_ref`; a
divergent projector fails before the response is emitted.

The Envelope also carries one validated Episode narrative moment. Its
disclosure lifecycle is explicit:

```text
OBSERVING / QUESTION_OPEN
-> BASELINE_ONLY

WAITING_FOR_WORLD
-> SEALED_NO_OUTCOME

REVEAL_READY
-> WORLD_COMMITTED_HIDDEN

REVEALED / COMPLETED
-> OUTCOME_REVEALED
```

`WORLD_COMMITTED_HIDDEN` is intentionally distinct from both waiting and
revealed: the World owner has committed an outcome, but Dream, Abu and Theater
must not disclose it until the Reveal transition. Phase/disclosure drift is a
contract error, not a presentation choice.

## Shared identity vocabulary

All cross-module references use stable typed IDs:

```text
CaseRef
ChartVersionRef
LifeCaseRevisionRef
AssertionRef
EvidenceRef
DecisionRef
WorldRef
WorldEventRef
ActorRef
DreamVisitRef
EncounterRef
LifeTreeRef
StoryRef
SceneRef
AssetRef
```

## Persistence rules

- Relational columns carry identity, status, ownership, time and version.
- JSONB may carry immutable typed payloads and traces, not hidden ownership.
- Story content may enter `story.question_instances` only through
  `StoryEpisodeAdmissionService`; seed and Dream code have no direct Story
  write path.
- Authored events and their initial evidence may enter `world.events` only
  through `WorldEventAdmissionService`; settlement and actor continuity remain
  owned by `WorldContinuityEngine`.
- Seed and migration modules are coordinators. They may read source material
  and call typed admission ports, but may not write Identity, Mingli, World,
  Story or Dream tables directly.
- Platform migration receipts enter only through
  `MigrationBatchAdmissionService`; Identity lineage through
  `IdentityAdmissionService`; compiled Case lineage through
  `MingliCaseAdmissionService`; Actor identity through
  `WorldActorAdmissionService`; and persistent tree identity through
  `LifeTreeAdmissionService`.
- Actor admission binds stable identity but never rewinds its timeline or
  current state. LifeTree admission binds stable Tree/Actor/Scene identity and
  the initial organ set for newly admitted trees, but never resets an evolved
  tree. Existing trees backfilled by migration `0012` are explicitly marked
  as backfills rather than falsely claiming knowledge of their historical
  initial organ set.
- Dream/world state uses event ledger plus snapshots where replay is valuable.
- The current ClockEpoch maps database wall time to integer Tick at a rational
  rate. Epoch history is append-only; a process restart never resets time.
- LifeCase and knowledge remain versioned relational records, not a universal
  event-sourcing experiment.
- Every external command has an idempotency key.
- Dream writes enter through one `DreamCommandEnvelope` containing the
  Encounter Ref, expected Encounter version, command, idempotency key and
  command-specific target. A stale command cannot mutate a later state.
- Every accepted command atomically persists one immutable
  `DreamCommandReceipt`, including the complete envelope Hash and committed
  result Encounter/version/state Hash.
- Observation, Reveal, reconciliation and continuation implement
  receipt-backed semantic replay. Only the exact envelope under the same
  idempotency key returns committed state without another version increment;
  changed reuse conflicts and an unrecorded stale command fails closed.
  AnswerSeal keeps its stronger immutable answer contract inside the same
  command transaction.
- World settlement is not a Dream command. The World Runtime owns due-time
  progression and settlement; the canonical client receives a read-only
  waiting state and polls the committed Encounter projection.
- Outbox delivery is atomic with the state commit.
- Presentation focus may live in the URL for refresh/back recovery, but it is
  not canonical product state and creates no database write.

## Language-ready identity boundary

V60 currently authors and renders `zh-CN` copy only. It does not yet include a
locale preference, translation catalogue, language switcher, automatic
translation or localized routing.

Future localization is reserved through language-neutral IDs and stable
`contentKey` values:

```text
QuestionRef / OrganRef / EvidenceRef / FactRef
contentKey
-> future locale-specific presentation copy
```

Locale must never be embedded in canonical IDs, hashes, evidence lineage or
world state. Adding another language later changes presentation resources, not
the Case, QuestionInstance, AnswerSeal, WorldEvent or Reveal identity.

## V50 migration policy

| Data | V60 disposition |
| --- | --- |
| Accounts and profiles | Whitelist import |
| Birth inputs | Import, then recompute |
| Deterministic chart facts | Recompute and compare |
| Provenance-complete committed LifeCase | Selective import |
| Approved assets | Hash-locked import |
| Dream visits and preview runs | Archive only |
| Forest Factory synthetic population | Do not import |
| P0/P1/demo/scenario records | Do not import |
| Legacy heuristic strength values | Do not import as professional evidence |

V60 runtime has no import dependency on V50 source code or database tables.

## Implemented foundation as of 2026-07-28

The first playable slice uses the following real PostgreSQL ownership:

| Owner | Implemented records |
| --- | --- |
| Identity | Account, session, profile and identity admission |
| Knowledge | Read-only, versioned and SHA-256-locked foundation profiles |
| Mingli | Case, ChartVersion, bounded Fact, LifeCaseRevision, CanonicalScene and compiled-case admission |
| World | World, ClockEpoch, admitted Actor, admitted WorldEvent, EventEvidence and Outbox |
| Story | Immutable QuestionInstance and deterministic ScenePlan |
| Dream Game | Admitted LifeTree, Encounter, AnswerSeal, StoryFruit and Reveal |
| Media | Hash-locked Asset registry |
| Platform | Immutable migration and seed batch receipts |

Knowledge profiles are immutable Pydantic values resolved by exact
`profile_id`, `profile_version` and optional expected Hash. Derived lookup
tables are read-only views of the admitted profile, not parallel constants.
The current Bazi foundation profile owns only bounded deterministic mappings:
ten stems, twelve branches, hidden-stem membership and the six clash/harmony
memberships. It explicitly forbids inferring relation effect, root usability,
capacity, professional confidence or mechanism success. Its admission status
does not imply professional review.

The currently visible Dream, Mingli, Abu, Theater and Lab views are read-only
product projections of the same first-slice lineage. Mingli and Lab are now
separate surfaces: Mingli shows the formal chart and source; Lab exposes
bounded research facts and structural relation candidates.

A `MingliCandidatePath` is a read model, not a PathAssertion. V1 candidates
may be compiled only from admitted `six_harmony_membership` or
`six_clash_membership` facts whose payload explicitly says membership-only and
effect-not-inferred. Each candidate preserves the relation FactRef,
participants, source and missing requirements. Effect, usable root, capacity,
time activation and professional admission remain `UNRESOLVED`.

The Lab routes these candidates through the central Decision Kernel with
`selection_qualified=false` and LLM disabled. The resulting
`UNRESOLVED / NONE` route is visible in the product; neither Mingli nor Lab
writes a DecisionRecord or LifeCase revision merely because a structural
candidate exists.

When a later rule profile qualifies multiple candidates, a bounded
`DecisionProposal` must preserve request, provider, model, prompt, reviewed
candidate, selected candidate, evidence and counter-evidence identity.
`EpistemicGateReceipt` records admission or rejection and never grants
canonical domain write permission. Only an admitted proposal may enter the
Decision Ledger; the owning domain remains responsible for any later state
transition.

Question organ projections are now bound immutably to `QuestionInstance`.
Encounter progress is viewer-private, while the canonical LifeTree advances
only through committed world actions. The five visible perspectives share a
URL-restorable semantic focus without duplicating facts or writing navigation
state to PostgreSQL.

The latest mutable Actor and LifeTree rows are not public read models.
`EpisodePublicProjection` filters Actor events to the current Episode
baseline and authorized Reveal horizon, withholds unsafe mutable Actor state,
and derives an Episode-local LifeTree state and projection Hash. Canonical
continuity therefore remains global without leaking a later chapter into an
earlier viewer Encounter.

The Runtime now validates a machine-readable architecture registry with unique
schema owners. Dream encounter rules, world continuity and story projection
are separate executable engines, while the five product units own no schema
and cannot write canonical state.

The Runtime host now pulses the existing World owner continuously. PostgreSQL
provides both authoritative wall time and a transaction-scoped advisory lock,
so multiple application processes cannot advance the same Tick concurrently.
Committed World results are projected into waiting Dream encounters by the
Dream owner on the next pulse; a crash between those transactions is repaired
by deterministic catch-up.

The first slice deliberately does not introduce a universal event bus, graph
database, generic question engine, screenplay DSL or autonomous agent
framework. Repeated product behavior must be observed before those
abstractions may be justified.
