# V60 Executable Product Architecture

Status: `IMPLEMENTED_LOCAL_FOUNDATION_V3`

This document records the architecture that is executable in the V60
repository. It is not a future platform diagram. Each active module below has
Runtime code, an explicit owner boundary and an architecture-registry entry.

## Product definition

V60 is a Mingli-centered Life Intelligence product. Abu Dream is the
priority game breakthrough, not the truth owner:

```text
Mingli Calculation
  -> owns reproducible readings, evidence and explicit uncertainty

Dream World
  -> makes bounded uncertainty, judgment, waiting and consequence playable

Mingli Lab
  -> researches improvements and proposes versioned Knowledge admission

Abu Says
  -> expresses the exact current Mingli Reading without creating another one

Abu Theater
  -> directs approved material into scripts, storyboards, voice and media
```

The first four online units share one Case and one lineage. Theater is a
relatively independent Studio workflow, but it still consumes approved source
packages and cannot create facts, events or Mingli conclusions.

## Executable module graph

```text
Identity Authority
  -> Knowledge Authority
      -> Mingli Cognitive Engine
          -> Cognitive Decision Kernel
              -> World Continuity Engine
                  -> Life Story Engine
                      -> Dream Game Engine

Media Registry --------------------------> presentation
Migration Boundary ----------------------> admitted V60 records

One shared lineage
  -> Experience Context Envelope
  -> Mingli Unit
  -> Dream Unit
  -> Lab Unit
  -> Abu Says Unit

Approved source package
  -> Theater Studio
  -> in-product scene / YouTube / Douyin / other channel package
```

The machine-readable source is
`abu_v60.architecture.registry.RUNTIME_ARCHITECTURE`. Startup validation rejects
duplicate schema owners, unknown module dependencies and product units that
attempt to write canonical state.

## Canonical write owners

| Schema or state | Unique owner | Other modules |
| --- | --- | --- |
| Account, session, profile, consent | Identity | Read through identity ports |
| Admitted knowledge profile identity and content Hash | Knowledge | Read exact immutable profile |
| ChartVersion, facts, LifeCaseRevision, Reading lineage, evidence-preparation receipt | Mingli | Read-only projection or typed request |
| Decision request, gate receipt, formal decision | Cognition | Submit typed requests |
| ClockEpoch, WorldEvent, evidence, actor timeline, outbox | World | Consume typed output |
| QuestionInstance and ScenePlan | Story | Read committed source refs |
| Encounter, organ progress, AnswerSeal, Fruit, Reveal, ReturnAttention selection/application | Dream Game | Issue commands |
| Asset identity, version, hash and Runtime delivery | Media | Resolve by asset ID |
| Import receipt and source lineage | Migration | No Runtime fallback to V50 |

Product units own no database schema and cannot write canonical state.

## Runtime code ownership

Module ownership is reflected in source boundaries instead of accumulating in
one application service:

| Source owner | Responsibility | Explicitly does not own |
| --- | --- | --- |
| `dream.service.DreamService` | legal command orchestration and transaction order | public read projection, raw persistence helpers, reconciliation policy |
| `dream.persistence.DreamRepository` | Encounter/Tree optimistic writes and immutable command receipts | command legality, story content, public copy |
| `dream.projection.DreamSnapshotProjector` | Episode-scoped public read model | canonical writes or state transitions |
| `dream.outcomes.DreamOutcomeCoordinator` | committed WorldEvent to Fruit/Reveal reconciliation | browser commands or World outcomes |
| `dream.encounter_creation.DreamEncounterCreator` | one canonical Encounter creation transaction for Grove and graph continuation | command routing, authored content or public projection |
| `dream.return_attention.DreamReturnAttentionCoordinator` | candidate-bound next-observation selection, replay and same-tree application | Mingli evidence, Knowledge admission, Question/Answer/NPC/outcome mutation |
| `dream.attention_follow_through.DreamAttentionFollowThroughProjector` | revalidated pending, active and returned read-only attention projection | canonical writes, semantic-match decisions or professional evidence |
| `mingli.relation_effect_request.RelationEffectEvidenceRequestStore` | account-private, append-only preparation-request receipt derived from one canonical packet | material intake, professional evidence, review, Knowledge or Decision |
| `mingli.relation_effect_history.MingliRelationEffectHistoricalPacketResolver` | reconstruct one packet from immutable Reading/Quant/Source Review lineage for integrity checks | current-Case selection or receipt mutation |
| `App` | session, navigation and Runtime composition | login layout, companion-unit internals |
| `components/*` | bounded presentation responsibilities | canonical product state |

The executable source-budget audit prevents these boundaries from silently
collapsing back into thousand-line files. It scans Runtime source only; media
post-processing tools and generated outputs are governed by their own pipeline
contracts.

Knowledge currently owns a small code-native Registry rather than a database
schema. It resolves exact `profile_id + profile_version + profile_hash`,
publishes a non-sensitive manifest and exposes immutable lookup views to
Mingli. Unknown or changed profiles fail closed. Admission does not imply
professional review, and the Profile's forbidden-inference boundary remains
part of the hashed content.

Mingli owns rule evaluation against those admitted profiles. A qualification
receipt proves one named evidence dimension and never grants a canonical
write. The initial executable dimension is structure visibility only:

```text
typed relation-membership fact
-> exact Knowledge rule Profile + Hash
-> CandidateQualificationReceipt
-> Lab may display structure evidence
-> effect/capacity/usability/timing/professional admission remain UNRESOLVED
-> Decision candidate remains unqualified
```

This boundary prevents both UI code and an LLM from promoting a visible
relation into effective work.

`ExperienceContextEnvelope` is the executable port between canonical owners
and the five product units. It binds one Encounter/Case/World lineage and
formal facts into a frozen Pydantic contract. Baseline evidence is committed
no later than cutoff and carries no prediction credit. Context v3 has a
separate post-cutoff `revealed_evidence` channel: it remains empty until a
Reveal exists and then accepts only committed World evidence after cutoff and
no later than the current World Tick. The two evidence sets cannot overlap.
The Envelope emits a deterministic SHA-256 plus an explicit disclosure
manifest for each unit. Outcome atoms, sealed outcomes, hidden NPC choices and
pre-Reveal DecisionRefs fail validation instead of relying on projector
convention.

Experience Context v3 also carries the current
`EpisodeNarrativeMoment`. Its phase and disclosure class must agree with
Encounter progress. This gives Dream, Abu Says and Theater one authored story
source while preserving their separate projection boundaries. Theater reads
baseline evidence before Reveal and committed outcome evidence after Reveal.

## Central brain and decision order

`CognitiveDecisionKernel` is the routing authority, not an all-knowing model.
It follows this order:

```text
1. deterministic fact or transition available
   -> system decides

2. admitted versioned rule available
   -> rule qualifies candidates

3. unresolved candidates and an authorized reasoning contract
   -> bounded LLM may compare them

4. consent, preference or irreversible subjective choice
   -> human decides

5. formal record requested
   -> Epistemic Gate validates provenance and commits

insufficient evidence
   -> UNRESOLVED
```

The LLM cannot create chart facts, permissions, world outcomes or global
knowledge. A provider-neutral bounded Reasoner Host and strict structured
output adapter are executable. The managed local profile currently reports
`READY`; an incomplete or disabled provider profile reports `NOT_CONFIGURED`
and cannot substitute a hidden model or generated answer:

```text
multiple qualified candidates
-> LLM_REASONER route
-> exact visible Evidence/Candidate projection
-> provider structured output
-> bounded DecisionProposal
-> EpistemicGate evidence/candidate validation
-> immutable DecisionRecord
```

The Host stamps provider, model, prompt, provider-response and context
identities, and retries first recover an existing immutable record instead of
calling the model again. The Gate receipt permits only the DecisionRecord.
Domain owners must still apply their own typed command. Provider readiness
does not broaden the evidence contract or grant professional rule authority.

The executable decision path is:

```text
typed DecisionRequest
-> CognitiveDecisionKernel
-> CognitiveDecisionCoordinator
-> immutable DecisionRecord
-> owning World or Dream transaction continues
```

World settlement and Reveal reconciliation use this path today. The record
contains the complete routed request and result, SHA-256, authority, method,
correlation and causation. The same decision identity accepts only an exact
replay. `decision.service` is the sole writer to the Cognition schema.

This generic Decision path is not professional Mingli rule admission. In
particular, an LLM proposal followed by the Epistemic Gate can establish only
that a bounded DecisionRequest was answered within its evidence and candidate
contract. It cannot certify a relation-effect rule, source usability or
professional correctness.

The executable relation-effect boundary therefore stops at a versioned
evidence-readiness packet today:

```text
deterministic relation membership and source coordinate
-> research Frontier
-> shortcut pre-admission Review
-> professional evidence readiness packet
-> optional account-private preparation-request receipt
   (0 materials / 0 professional evidence / 0 ready dimensions)
-> optional account-private bibliography-coordinate candidate
   (unverified metadata / requested artifact still unsatisfied)
-> effect and source usability remain UNRESOLVED
```

Runtime facts, coordinate refs, Policy and Proposal refs in that packet are
`RUNTIME_CONTEXT_ONLY_NOT_PROFESSIONAL_EVIDENCE`. They identify the precise
question and missing dimensions; they do not satisfy those dimensions.

The preparation receipt is the only new canonical write in this slice. It
records that one account asked to preserve the server-owned gap checklist; it
does not accept or generate evidence. The client sends only the current packet
Ref/Hash, request version and idempotency key. Mingli derives the exact demand
and six slots, persists the receipt append-only, and restores the same identity
after refresh or process restart.

The later bibliography-candidate writer does not reopen or rewrite that
receipt. It accepts four bounded structured coordinates and persists a
separate `BIBLIOGRAPHIC_COORDINATE_CANDIDATE`. The
`PROFESSIONAL_SOURCE_MANIFEST` value is only the requested future artifact,
not the type or status of the candidate. A server-derived bibliography Hash
prevents changed-key duplicates; request item, demand Ref/Hash and provenance
slot are exact-bound because a slot Ref may repeat across future demands.

Active-Case admission, mechanism comparison and preparation-request creation
share one account-scoped PostgreSQL transaction lock. Each write path also
revalidates that its Case belongs to the same active `HUMAN_OWNER`. Runtime
Integrity reconstructs the historical packet from the persisted Reading and
its immutable Quant and Source Review vectors rather than accepting a
self-consistent receipt as proof.

Any future professional relation-effect Decision requires a separate
authority chain:

```text
complete professional evidence packet
-> Owner professional review approves exact proposition and scope
-> Knowledge admits a new immutable rule Profile
-> a new Reading binds that exact Profile Ref + Hash
-> Mingli applies the admitted deterministic rule
-> typed effect result, or still UNRESOLVED
```

The current packet, preparation receipt and bibliography candidates do not
execute this chain. They create no DecisionRequest, Gate receipt,
DecisionRecord, Knowledge promotion request, professional material or
effect/usability write. Existing Readings cannot acquire a newly admitted
Profile retroactively.

Player gestures follow an equally explicit path:

```text
product gesture
-> DreamCommandEnvelope
-> Dream command router
   -> Encounter command: DreamGameEngine phase and target validation
   -> SELECT_NEXT_ATTENTION: DreamReturnAttentionCoordinator validation
-> Dream owner transaction
-> immutable DreamCommandReceipt
-> committed Encounter or ReturnAttention identity
-> shared Experience Context
```

The envelope binds the Encounter identity, expected version, idempotency
identity and exact command payload. Presentation cannot call domain mutators
directly. The accepted envelope and its result are atomically preserved in an
immutable `DreamCommandReceipt`. An unrecorded stale version fails closed; an
exact receipt-backed retry returns the already committed state, while changed
reuse of the idempotency key conflicts.

`WAITING_FOR_WORLD` deliberately has no canonical client command. The browser
cannot advance World Tick or settle an event. It polls the read-only Encounter
projection while the Runtime host invokes the World owner from authoritative
database time.

Mutable canonical objects are not copied directly into that projection.
`EpisodePublicProjection` applies the current Episode's disclosure horizon:

```text
before Reveal
  -> baseline Actor event only
  -> mutable Actor state withheld
  -> Episode-local LifeTree state

after Reveal
  -> baseline + this Episode's outcome event
  -> later Episode events remain excluded
  -> current Actor state only when provably inside the same horizon
```

This prevents a late-arriving viewer from learning a future chapter merely
because the canonical Actor or LifeTree has already advanced.

## Game engine split

V60 does not put all game behavior in a single scene component.

### Dream Game Engine

Code:

- `abu_v60.game.engine.DreamGameEngine`
- `abu_v60.game.contracts`
- `abu_v60.game.director.DreamGameplayDirector`

Owns the pure encounter state machine:

```text
OBSERVING
-> QUESTION_OPEN
-> WAITING_FOR_WORLD
-> REVEAL_READY
-> REVEALED
-> COMPLETED
```

It validates commands, derives legal actions and projects organ visibility. It
does not own the world clock or outcome.

All Dream mutations enter through the single
`POST /api/v60/dream/command` boundary. The Dream command router sends
Encounter commands to the engine, which validates the current phase and organ
semantic role, and sends `SELECT_NEXT_ATTENTION` to the Return Attention
coordinator. React, accessibility controls and later media cues therefore
remain on one authoritative Dream command path without pretending that an
Echo observation is an Encounter phase transition.

The Dream schema also owns the command receipt ledger. It records no new
story fact: it proves exactly which command envelope caused which committed
Encounter version and state Hash. This is the replay boundary for double
clicks, delayed requests and process recovery.

The same schema owns two separate append-only Return Attention ledgers:

```text
candidate-backed committed Return Echo
-> deterministic server observation options
-> account-private selection + immutable command receipt
-> other-tree visit: no application
-> Grove marks the exact source tree
-> source-tree visit: one opening application
-> read-only 0/3 through 3/3 progress across the full Encounter
-> pre-Reveal world response withheld
-> post-Reveal committed materials, semantic match not evaluated
-> unassessed returned summary in the Grove
```

Selection binds the exact source Encounter/version, Echo Ref/Hash, Grove
candidate Ref/Hash, tree and option. Application binds the selection Ref/Hash
to one later Encounter on the same tree. Runtime integrity revalidates both
stored payload Hashes and their column, account, candidate and tree lineage.
Every pending or follow-through projection additionally rebuilds the source
Encounter's exact Echo and revalidates its candidate, actor, question, tree
and server-issued observation. Target progress is an exact ordered subset of
the two leaves and one branch. World response is absent before Reveal and,
after Reveal, contains only the actual event plus stable committed evidence.
It remains `SEMANTIC_MATCH_NOT_EVALUATED`, including after reconciliation and
Grove return.

The records and projections are `NOT_EVIDENCE`: they cannot change a Question,
Answer, NPC choice, outcome, owner Reading, Cognition Decision or Knowledge
object. They do not decide whether the remembered observation semantically
matches the later material.

Authored content enters through a complete `DreamEpisodeDefinition`. Runtime
persists the narrower `DreamEpisodeContract`, its Hash and a separately
compiled admission manifest beside the QuestionInstance. The Director rejects
tampering or identity disagreement before producing scene commands. All
three active visits use this same path; Dream Service has no authored
Question-ID branches.

The complete definition is compiled from a hash-locked source package owned by
Story. `content/dream/episodes/registry.json` binds each package identity,
relative path, SHA-256 and explicit transition graph. Each package also carries
the WorldEvent definitions required by its Episode. Package compilation proves
the event Actor, type, due Tick, summary and sealed outcome match the Episode,
then Seed submits the resulting contracts to the existing World and Story
owners. Package templates accept only declared canonical bindings and are
validated as a full `DreamEpisodeDefinition` before admission. These files are
never a Runtime fallback: after admission, `DreamEpisodeCatalog` reads only
PostgreSQL contracts and admission manifests.

Episode ordering is not mutable Episode content. Story persists an independent
`EpisodeTransitionContract` in `story.episode_transitions`. The active graph
requires these explicit, hash-checked edges; legacy continuation fields remain
read-only historical payload and are not a Runtime fallback.

The source Registry is also the only authoring truth. Legacy Python slice
modules resolve compatibility values by compiling the Registry package; they
contain no authored prompts, outcomes or transitions. Seed derives navigation
from Registry edges, and the repository exposes only a non-writing source
audit tool.

The persisted contract also owns exactly one narrative moment for every legal
Dream phase. Application headings, status copy, Abu speech and Theater beats
come from this contract through the shared context. React and product
projectors do not infer narrative from chapter or status.

### World Continuity Engine

Code:

- `abu_v60.world.admission.WorldEventAdmissionService`
- `abu_v60.world.service.WorldContinuityEngine`

The Admission Service is the only World write path for authored event
definitions and initial evidence. It persists a deterministic authority
receipt and rejects changed-content identity replay. `WorldContinuityEngine`
owns integer Tick, append-only epochs, due-event settlement, actor timeline,
later event evidence and transactional outbox. The current ClockEpoch projects
database wall time at a rational rate; a transaction-scoped PostgreSQL
advisory lock fences each Runtime pulse. Browser time never determines facts.

### Bootstrap owner ports

Code:

- `abu_v60.migration.admission.MigrationBatchAdmissionService`
- `abu_v60.identity.admission.IdentityAdmissionService`
- `abu_v60.mingli.admission.MingliCaseAdmissionService`
- `abu_v60.world.actor_admission.WorldActorAdmissionService`
- `abu_v60.dream.tree_admission.LifeTreeAdmissionService`

Seed and V50 migration workflows coordinate these ports but own none of their
tables. Exact replay verifies stable identity, source and Hashes. Actor
timeline/state and LifeTree lifecycle state are intentionally excluded from
bootstrap rewrites, so a restart or Seed replay cannot rewind the world.
Migration-backfilled LifeTrees are marked as such because their historical
initial organ set cannot be reconstructed honestly.

### Runtime host

Code:

- `abu_v60.runtime.service.WorldRuntimeCoordinator`
- `abu_v60.runtime.service.WorldRuntimeWorker`

The host owns process lifecycle only. It periodically invokes the existing
World write port, then asks the Dream owner to catch up waiting projections.
It owns no schema. A failed second transaction cannot lose the World result:
the next pulse finds settled events whose Encounter projection is still
pending and applies it idempotently.

### Life Story Engine

Code:

- `abu_v60.story.admission.StoryEpisodeAdmissionService`
- `abu_v60.story.admission.StoryEpisodeTransitionAdmissionService`
- `abu_v60.story.service.LifeStoryEngine`

The Admission Service is the only Story write owner for playable
QuestionInstances. It recompiles and validates the Episode, resolves canonical
authority, persists the immutable admission manifest and rejects identity
conflicts. `LifeStoryEngine` then compiles already committed semantic objects
into deterministic question metadata and ScenePlans. The Transition Admission
Service is the only writer for append-only Episode graph edges. It validates
endpoint identity and time order, supports exact idempotent replay and rejects
changed-content identity reuse. None may invent a LifeEvent or world result.

### Presentation engine

React owns application composition and accessible interaction. PixiJS remains
the selected 2D scene engine for spatial layers and animated scene-native
interaction. Video and audio are resolved through the Media Registry and never
advance canonical state by playback completion alone.

The Media Runtime Resolver validates the production catalogue and asset
registry, then exposes only named Runtime bindings through Bootstrap. Client
components receive versioned URL/hash projections and have no direct asset
paths. Cue admission, reduced-motion fallback and cross-identity fallback are
therefore server-verifiable rather than component conventions.

## Mingli and research boundary

`MingliWorkspaceProjector` renders the formal chart workspace:

- chart version;
- four pillars;
- typed admitted facts;
- source references;
- read-only LifeCase lineage.

`LabProjector` renders a separate research boundary:

- available formal facts;
- structural candidates compiled from admitted relation facts;
- effect, capacity and professional-admission status;
- no canonical write.

A relationship fact is not automatically effective work. Unknown capacity or
professional status remains visibly `UNRESOLVED`.

For the current narrow Zi-Wu question, Lab also projects a six-dimensional
professional evidence readiness contract: applicability context, effect
direction, completion conditions, blocking conditions, counter-evidence and
professional provenance. Existing runtime basis refs remain separate from
the empty professional-evidence channel. Mingli Calculation shows only the
readiness summary. Lab may persist one preparation request and inspect its
server-derived checklist, but neither unit may accept materials, conduct the
professional review or publish a rule.

The executable candidate chain is:

```text
Mingli Fact
-> StructuralCandidateCompiler
-> MingliCandidatePath(selection_qualified=false)
-> CognitiveDecisionKernel(llm_allowed=false)
-> UNRESOLVED / NONE
-> LabProjector
```

Only bounded membership facts are accepted. The compiler rejects generated,
malformed or effect-claiming inputs. Stable candidate IDs include the compiler
version, ChartVersionRef, relation FactRef and participants. Lab cannot write
Mingli truth. It may produce a versioned research proposal; only Knowledge
Authority admission can publish a new immutable Profile for later
calculations. Existing Readings remain pinned to their original Profile.

## Five product units

| Unit | Reads | May do | Must never do |
| --- | --- | --- | --- |
| Mingli | Mingli, Knowledge, Cognition | Produce a reproducible Reading and provenance | Turn an unresolved candidate into fact |
| Dream | Dream, World, Story, Media | Play a bounded proposition and show consequence | Invent outcome or overwrite a Reading |
| Lab | Mingli, Knowledge, Cognition | Inspect evidence, test candidates and propose admission | Write LifeCase or self-publish a rule |
| Abu Says | Mingli Reading, Story, Media | Explain, listen and navigate in the current Reading | Create a second analysis or decide for user |
| Theater | Approved source package, Story, World, Media | Direct, voice, compose and distribute disclosed material | Quietly rewrite canon or act as truth source |

`ExperienceProjectionComposer` produces these read models from one validated
`ExperienceContextEnvelope`. Every unit returns its shared `context_ref`; a
divergence is rejected before the API response. URL `view` and `focus` remain
disposable navigation state.

The in-product Theater projection is the disclosed preview surface. Full
Theater Studio production is a separate workflow with versioned Director
Brief, script, storyboard, voice, asset, render and channel-package records.
Its outputs must declare whether they are canonical replay, authorized
adaptation, simulation branch or fictional education.

## Persistence and recovery

- PostgreSQL is the fact source.
- Every external command uses an idempotency key where duplication is
  possible.
- World settlement commits event, evidence, state and outbox atomically.
- World settlement first validates the immutable WorldEvent admission
  manifest under lock.
- Bootstrap replay first validates immutable Platform, Identity, Mingli,
  Actor and LifeTree admission boundaries and never resets evolved state.
- World Tick continues while no browser is open and survives process restart.
- No canonical product command can advance the World Clock. Waiting surfaces
  may refresh read models but cannot write time or outcomes.
- Encounter state survives refresh and process restart.
- TreeProjection is rebuilt from committed state through the current Episode
  horizon; the latest canonical tree version is not exposed as an earlier
  chapter's public state.
- URL state may restore a view or focus but cannot restore or alter facts.
- Runtime status is read-only at `/api/v60/system/runtime-status`.
- The same endpoint verifies the complete active Episode graph and publishes
  its deterministic graph Hash plus the versioned Scene registry.
- Catalog validation rechecks every admission manifest, authority binding and
  outcome Hash; an unadmitted or drifted QuestionInstance makes Runtime
  integrity fail closed.

## Migration and legacy isolation

V60 has no V50 Runtime import. Data or assets cross only through a versioned
migration or media manifest. There is no old Provider, fixture, scenario or
visual fallback in the canonical V60 path.

The architecture audit command is:

```bash
.venv/bin/python tools/audit_runtime_architecture.py
```

It reports migration head, module owners, world clock, record counts and
integrity defects without mutating product data.

The supported local process owner is:

```bash
.venv/bin/python tools/local_runtime.py start
```

It writes only under `.runtime/`, verifies every expected core-engine version
and full Runtime integrity before reporting ready, and refuses to terminate a
process it did not start.

## Language reservation

The current product is authored in `zh-CN`.

```yaml
default_locale: zh-CN
localization_status: RESERVED
```

IDs, hashes, evidence refs, Seals and world outcomes are language-neutral.
V60 does not yet ship locale preferences, translation catalogues, switches or
automatic translation.

## Current honest boundary

The executable architecture is ready; the content breadth is not:

- one canonical authored world;
- one canonical synthetic actor;
- one persistent LifeTree;
- three completed question encounters;
- three hash-locked Episode source packages and two transitions that compile
  to the admitted Runtime identities;
- one bounded Mingli fact in the current slice;
- one executable, Hash-locked Bazi foundation profile that is not yet
  professionally reviewed;
- one versioned relation-effect professional evidence packet with six empty
  readiness dimensions and no effect or source-usability verdict;
- one account-private append-only preparation-request receipt over that packet,
  with no material intake, automatic executor or professional evidence;
- a separate account-private append-only bibliography-candidate ledger whose
  structured metadata satisfies no requested artifact or evidence dimension;
- no production LLM orchestration;
- no large NPC population or content factory;
- desktop composition validated; mobile visual design deferred;
- further designer media still pending admission.

The next work must deepen one visible playable experience through these owners,
not add a parallel engine or another architecture layer.

The game-production and episode-authoring contract is maintained in
`docs/13_V60_GAMEPLAY_STORY_FOUNDATION.md`.
