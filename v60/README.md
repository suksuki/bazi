# Abu Knows V60

V60 has two product outcomes: Mingli Calculation must reach
advanced-practitioner-grade destiny reading, and Abu Dream World must become
a complete Mingli story game with a real question system, mature game engine
and controlled AI NPC participation. Lab, Abu Says and Theater support these
two outcomes rather than forming separate product roadmaps.

## Product spine

```text
Chart facts
-> LifeCase
-> Canonical Scene
-> Case Workspace
   -> Mingli Calculation
   -> Dream World
   -> Mingli Lab / OneCanvas
   -> Abu Says

Approved source package
-> Abu Theater Studio
   -> in-product scene / YouTube / Douyin / other channel
```

## Authority spine

```text
Fact Authority
-> Knowledge and Rule Authority
-> Candidate Fabric
-> LLM Cognitive Reasoner when allowed
-> Epistemic Gate
-> Decision Ledger
```

The system owns facts, permissions, state transitions and commits. The LLM is
a bounded reasoning organ; it never writes canonical facts or world outcomes.
The Proposal/Gate contract and provider-neutral Reasoner Host are executable.
The managed local Runtime uses the dblife-hosted `gemma4:latest` expression
candidate through an explicit, hash-locked structured-decision profile. The
Host sends only admitted candidate/evidence projections, requires strict
structured output, records provider/model/profile/prompt/context identity and
never grants a model a domain write. Partial or unsupported provider
configuration remains fail-closed.

Knowledge Authority is also executable rather than implied by imports. Mingli
resolves an exact profile ID, version and SHA-256 from a read-only registry.
The current foundation profile preserves its Owner-bounded source identity and
explicitly remains `professionally_reviewed=false`; a missing or mismatched
profile fails closed.

Candidate qualification is a separate executable boundary. The first admitted
rule profile can prove only that a typed relation-membership fact is valid
structure evidence. Its immutable receipt explicitly forbids conclusions about
effect, root usability, capacity, timing, professional admission or effective
work. Lab can show this proof; the Decision Kernel still receives the candidate
as unqualified.

Every product projection is built from one immutable
`ExperienceContextEnvelope`. Before Reveal, its cutoff guard rejects
post-cutoff evidence, sealed outcomes and hidden NPC choices. After Reveal,
Context v3 admits only committed post-cutoff World evidence through a
separate `revealed_evidence` channel. Theater therefore stages the actual
outcome without reusing baseline clues or weakening the pre-Reveal boundary.

Each playable Episode also owns one versioned `EpisodeNarrativeContract`.
Its six phase-specific moments provide the shared title, status, Theater beat
and Abu line for the current scene. The Experience Context validates the
corresponding disclosure class, so a committed world outcome can remain
hidden until Reveal without relying on frontend convention.

Playable content has one write path:
`StoryEpisodeAdmissionService`. It recompiles the full Episode definition,
binds the exact LifeCase revision, structure fact, WorldEvent, cutoff and
outcome Hash, then persists a deterministic admission manifest. Exact replay
is idempotent; changed content under an existing Question identity is a hard
conflict. Dream Runtime has no unadmitted-content fallback.

Episode authoring now starts from the hash-locked packages under
`content/dream/episodes/`. Each package binds one complete Episode to its
authored WorldEvent definitions, while the Registry binds the explicit
Episode transition graph. The compiler permits only declared authority
bindings and fails closed on path escape, file drift, missing bindings, event
drift or transition drift. Seed only coordinates these compiled contracts
through the existing World and Story owners. The files are admission inputs,
not live content: the running game still reads only admitted PostgreSQL
contracts.

Episode order has a separate append-only Story owner.
`StoryEpisodeTransitionAdmissionService` persists versioned transitions
between immutable Question/Episode identities. Adding a later chapter does
not rewrite the preceding Episode contract. Runtime requires the admitted
transition graph and never reconstructs it from legacy continuation fields.

The current canonical source registry contains five authored Episodes and
four explicit transitions. The third chapter tests an Actor promise and later
public action; the fourth binds the same LifeCase's frozen Dayun, annual and
monthly coordinates beside an already-committed world fact without allowing
those coordinates to decide the Actor's action. The fifth grows from the
fourth chapter's committed public record and asks which bounded career-duty
effect appears next. Its answer remains independent from the player and is
resolved only by the later WorldEvent. Legacy
`first_slice.py` and `return_slice.py` modules are read-only compatibility
views over the Registry; they no longer author content. Source verification is
read-only through `tools/audit_episode_source_packages.py`.

Playable interaction also has one API write path. Every action is a strict
`DreamCommandEnvelope` binding the Encounter, expected version, idempotency
identity and exact target. The Game Engine validates phase and organ role
before the Dream owner writes. Every accepted command atomically creates an
immutable `DreamCommandReceipt`; stale fresh commands fail closed, exact
receipt-backed replays return the already-committed state, and reuse of an
idempotency key with changed content is rejected.

Waiting is not a client command. After an AnswerSeal, the canonical Dream
surface exposes no world-advance action. PostgreSQL wall time and the World
Runtime settle due events; the browser only polls the read model until the
Dream projection becomes revealable.

Public snapshots are Episode-scoped rather than copies of the latest mutable
Actor and LifeTree rows. Later timeline events, Actor state and tree chapters
remain hidden until the current Episode disclosure contract permits them.

Authored WorldEvents follow the same rule through
`WorldEventAdmissionService`. The World owner binds Actor/Case/branch,
immutable event payload, sealed outcome and each initial evidence
Ref/Tick/Hash before an event can be scheduled or committed. World settlement
revalidates that receipt and fails closed on drift; player input and
presentation still cannot own an outcome.

Bootstrap and migration code are coordinators, not database owners. Seed and
V50 import call typed admission ports owned by Platform, Identity, Mingli,
World, Story and Dream. Actor and LifeTree admission manifests bind stable
identity without resetting an evolved timeline or tree. Static architecture
tests reject direct cross-schema writes from coordinators.

## Repository boundary

- `v60/` is a new system with its own runtime, database and migrations.
- `v50/` is a read-only migration source. V60 runtime code must not import it.
- Only assets and domain behavior admitted by an explicit migration manifest
  may cross the boundary.
- Old Dream visits, synthetic Forest Factory populations, preview routes and
  fixture product data are not V60 runtime inputs.

## Local baseline

```bash
cd /Users/liujin/DEV/AIProjects/bazi/v60
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev]'
npm --prefix web install

createdb qiazhi_v60
.venv/bin/alembic upgrade head
.venv/bin/python tools/sync_asset_registry.py
npm --prefix web run build
.venv/bin/python tools/audit_source_maintainability.py
.venv/bin/python tools/local_runtime.py start
```

Open `http://127.0.0.1:8060/experience`.

After login, V60 opens the viewer's private LifeTree. Entering Abu Dream World
is an explicit action from that scene; returning Home does not reset the
continuing Dream world.

Use `tools/local_runtime.py check|status|restart|stop` for subsequent local
service operations. The manager refuses stale engine versions and does not
terminate unowned processes.

The managed local product uses the existing dblife-hosted Ollama service:

```bash
V60_REASONER_PROVIDER=ollama-generate
V60_REASONER_MODEL=gemma4:latest
V60_REASONER_PROFILE_REF=v60.model-serving.gemma4-structured-decision.001
V60_REASONER_BASE_URL=http://dblife.com:11888
V60_REASONER_THINK=false
V60_REASONER_TEMPERATURE=0
V60_REASONER_TOP_P=0.95
V60_REASONER_TOP_K=64
V60_REASONER_NUM_CTX=32768
V60_REASONER_NUM_PREDICT=1200
V60_REASONER_KEEP_ALIVE=30m
```

`tools/local_runtime.py` supplies these defaults to the child Runtime. Explicit
environment values can override them. The adapter reuses the proven V50
Ollama protocol without importing V50 code or data at Runtime. Partial or
unsupported configuration remains fail-closed, and provider credentials are
never included in the public system manifest.

This is a bounded product-decision profile rather than Gemma's unrestricted
creative default: `temperature=0` keeps JSON-Schema comparison deterministic,
while the selected model's `top_p=0.95` and `top_k=64` remain explicit. Qwen
models retain their historical Research/Teacher role; the earlier
`qwen3.5:35b` DecisionRecord remains append-only trial evidence and is not the
active V60 product model.

The engine and framework choices are recorded in
[`docs/05_V60_ENGINE_AND_TECHNOLOGY_SELECTION.md`](docs/05_V60_ENGINE_AND_TECHNOLOGY_SELECTION.md).

Migration decisions and source-lineage rules are recorded in
[`docs/06_V60_MIGRATION_AND_PROVENANCE_POLICY.md`](docs/06_V60_MIGRATION_AND_PROVENANCE_POLICY.md).
The reproducible evidence for the first playable slice is recorded in
[`docs/07_V60_FIRST_SLICE_EVIDENCE.md`](docs/07_V60_FIRST_SLICE_EVIDENCE.md).
The versioned Gemini-to-Runtime media workflow is recorded in
[`docs/08_V60_MEDIA_LIBRARY_AND_PRODUCTION_PIPELINE.md`](docs/08_V60_MEDIA_LIBRARY_AND_PRODUCTION_PIPELINE.md).
The accepted Eastern fairy-tale picture-book direction and cinematic handoff
rules are recorded in
[`docs/09_V60_VISUAL_DIRECTION_AND_CINEMATIC_LANGUAGE.md`](docs/09_V60_VISUAL_DIRECTION_AND_CINEMATIC_LANGUAGE.md).
The same-world second-visit product and runtime contract is recorded in
[`docs/10_V60_RETURN_ENCOUNTER_SLICE.md`](docs/10_V60_RETURN_ENCOUNTER_SLICE.md).
The frozen history of previously delivered product slices is preserved in
[`docs/11_V60_ACTIVE_PRODUCT_DELIVERY.md`](docs/11_V60_ACTIVE_PRODUCT_DELIVERY.md).
The executable module graph, unique write owners, game-engine split and five
product-unit boundaries are recorded in
[`docs/12_V60_EXECUTABLE_PRODUCT_ARCHITECTURE.md`](docs/12_V60_EXECUTABLE_PRODUCT_ARCHITECTURE.md).
The gameplay package, Episode contract, Director, story-authoring and replay
rules are recorded in
[`docs/13_V60_GAMEPLAY_STORY_FOUNDATION.md`](docs/13_V60_GAMEPLAY_STORY_FOUNDATION.md).
The private Home LifeTree, explicit Dream threshold and cross-scope authority
rules are recorded in
[`docs/14_V60_PRIVATE_HOME_TREE_AND_DREAM_THRESHOLD.md`](docs/14_V60_PRIVATE_HOME_TREE_AND_DREAM_THRESHOLD.md).
The authoritative two-line direction, honest Mingli and Dream reviews,
explicit stop list and pre-merge product work are recorded in
[`docs/15_V60_TWO_PRODUCT_LINES_AND_PRE_MERGE_PLAN.md`](docs/15_V60_TWO_PRODUCT_LINES_AND_PRE_MERGE_PLAN.md).
The Mingli capability inventory, central decision hierarchy, V50 reuse
boundary and quantitative/statistical model are recorded in
[`docs/16_V60_MINGLI_CORE_AND_QUANTITATIVE_MODEL.md`](docs/16_V60_MINGLI_CORE_AND_QUANTITATIVE_MODEL.md).
The implemented four/six-pillar stage, synthetic character fixtures, Dylan
narration authority, audio-clock state machine and real Desktop/in-app iPad
viewport evidence are recorded in
[`docs/17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md`](docs/17_V60_MINGLI_STAGE_AND_SYNCHRONIZED_NARRATION.md).
The Owner-approved specialist Mingli Agent decision, implemented one-call
Reading path, typed semantic guards and current local-model qualification
failure are recorded in
[`docs/18_V60_MINGLI_AGENT_DECISION_AND_BUILD.md`](docs/18_V60_MINGLI_AGENT_DECISION_AND_BUILD.md).
The Owner-approved cognitive-system constitution, shared Reading Claim Graph,
blind/reconciliation boundary and functional delivery sequence are recorded in
[`docs/19_V60_MINGLI_COGNITIVE_SYSTEM_CONSTITUTION_V1.md`](docs/19_V60_MINGLI_COGNITIVE_SYSTEM_CONSTITUTION_V1.md).
The running implementation history is kept in
[`docs/CHANGELOG.md`](docs/CHANGELOG.md).
