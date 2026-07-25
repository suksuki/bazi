# DREAM-BRIDGE-01 Repository Map

Status: `READ_ONLY_AUDIT_COMPLETE`

Audit date: `2026-07-22`

This document records the first read-only repository audit for
`DREAM-BRIDGE-01`. It is not an implementation authorization and does not
define the wider NPC world, synthetic population, 六爻 layer, question
flowers, fruit reveal, or evidence game loop.

## 1. Audit Baseline

```yaml
authoritative_environment: mac_local
authoritative_worktree: ${REPO_ROOT}
v50_root: ${REPO_ROOT}/qiazhi/v50
branch: codex/cag04-ra0-reconciliation
head: 06efac64df38f0003943fe31e17f6d7278cd416a
working_tree: dirty_before_audit
repository_agents_file: absent
global_agents_file: ${CODEX_HOME}/AGENTS.md
global_agents_file_size: 0
remote_sync: not_run
server_13_access: not_run
database_writes: none
product_source_changes: none
```

The working tree already contained a large set of modified and untracked
local changes before this audit. This audit did not clean, revert, stage, or
commit any of them.

The named handoff file
`CODEX_HANDOFF_ABU_DREAM_WORLD_PHASE_A_V1.md` was not available in the local
repository, Downloads, or the supplied attachment directories. The audit was
therefore executed strictly from the scope stated in the owner's message. The
handoff body must be supplied or imported before implementation authorization
is evaluated.

## 2. Current Truth Chain

```text
Authenticated user session
  -> AgentCaseStore / LifeCase
  -> CanonicalSceneOwner
  -> ReadOnlySixPillarCanvasService
  -> Experience API
  -> Experience Shell / OneCanvas
```

The existing chain already provides the correct authority boundary for a
future read-only Dream projection:

| Responsibility | Current owner | Repository location | Audit result |
| --- | --- | --- | --- |
| User and session | ProductStore | `apps/product/product_store_memory.py`, `apps/product/product_store_postgres.py` | Present |
| Case persistence | AgentCaseStore | `apps/product/agent_case_store_memory.py`, `apps/product/agent_case_store_postgres.py` | Present |
| Formal case history | LifeCase | `packages/core/life_case/contracts.py` | Present |
| Relation/path history | LifeCase services | `packages/core/life_case/relation_path.py` | Present |
| Stable relation/path contracts | Graph provenance | `packages/core/graph/provenance.py` | Present |
| Canonical scene issuance | CanonicalSceneOwner | `apps/product/canonical_scene.py` | Present; owner-scoped |
| Canonical scene contracts/compiler | Experience package | `packages/experience/canonical_scene.py` | Present |
| Six-pillar projection | ReadOnlySixPillarCanvasService | `apps/product/canvas_projection.py` | Present; read-only |
| Path projection diagnostics | Experience projection | `packages/experience/product_projection.py` | Present |
| Workspace bootstrap | WorkspaceBootstrapService | `apps/product/workspace_bootstrap.py` | Present |
| Workspace contract | Experience workspace | `packages/experience/workspace.py` | Present |
| Product API composition | FastAPI app | `apps/product/app.py` | Present |
| Browser rendering | Experience shell | `apps/product/experience_shell/src/` | Present |

### Authority observations

1. `CanonicalSceneOwner` reads the Case through the authenticated participant
   identity. It does not currently issue projections for curated anonymous
   encounters outside that ownership model.
2. `ReadOnlySixPillarCanvasService` consumes the canonical scene and does not
   write formal state, invoke an LLM, or mutate a Sandbox.
3. `WorkspaceSurface` currently supports `overview`, `onecanvas`, `xiangfa`,
   `theater`, and `mingli_lab`. Dream is not an existing surface or route.
4. No `DreamVisit`, `DreamProjection`, `EncounterSet`, `KnowledgeSeed`,
   `DreamCase`, `TreeGraph`, or `DreamLedger` implementation exists.
5. The current repository therefore has no second Dream truth owner. This is
   a useful clean starting condition and must be preserved.

## 3. OneCanvas Real State

```yaml
canonical_six_pillar_scene: implemented
stable_4_5_6_pillar_layout: tested
single_coordinate_system: tested
six_lens_projection: tested
role_projection: tested
lab_potential_relation_isolation: tested
frontend_natural_language_path_inference: forbidden_and_tested
committed_path_rendering: implemented_and_tested
```

The browser renders path availability from the server projection. It displays
`正式主路径正在形成` only when a real path task is running; otherwise it displays
`当前暂无已确认主路径`. Internal diagnostic codes are restricted by role.

This means OneCanvas is suitable for embedding or reusing in a future Dream
container. It must not be copied into a separate Dream implementation.

## 4. PathAssertion Real State

### Contract and pipeline capability

The current local working tree contains:

- stable `RelationAssertion` and `PathAssertion` contracts;
- LifeCase-owned relation/path commit and history services;
- a deterministic `path_bridge.py` that binds only system-enumerated node and
  relation identities;
- segment-level validation and rejection;
- tests proving that an invalid middle segment cannot be skipped to fabricate
  a continuous path;
- tests proving that narration is derived from the validated structure rather
  than used by the browser to guess a path.

Important source-integrity boundary: `path_bridge.py`, its tests, and the
LOCAL-GATE-04 test files are currently untracked local files. Their passing
state is real in this working tree, but they are not yet protected by the
current Git HEAD.

### Current local database state

The read-only PostgreSQL audit found:

```yaml
agent_case_rows: 44
rows_with_life_case_object: 10
relation_assertion_total: 0
path_assertion_total: 2
renderable_committed_path_assertions: 0
legacy_unresolved_path_assertions: 2
```

No personal case content was printed. The two path records have no usable node
or relation references and are explicitly `legacy_unresolved`.

Therefore:

> The code can validate and render a formal path, but the current local Case
> population still contains no renderable committed PathAssertion.

Dream Phase A must preserve this truth. A tree or embedded OneCanvas must show
`当前暂无已确认主路径` when the selected Case has no formal path. It must not add
decorative work-path light or infer one from prose.

## 5. LOCAL-GATE-04 Real State

```yaml
LOCAL_GATE_03:
  canvas_acceptance: pass
  professional_content: fail

PATH_BRIDGE_01:
  deterministic_contract_and_tests: pass_in_dirty_worktree
  current_git_head_protection: absent

LOCAL_GATE_04:
  mechanical_path_pipeline: pass_in_tests
  professional_path_quality: not_proven

LOCAL_GATE_04A:
  assertion_integrity: pass_local
  professional_release_isolation: pass_local
  reasoner_quality_repaired: false

LOCAL_GATE_04B:
  status: not_entered
```

`tests/test_v50_local_gate_04.py` uses a mechanical gate model that selects an
allowed system candidate. It proves the structure and projection pipeline; it
is not professional Mingli approval.

The current local status also records five real-model baselines as `0/5` safe
for professional submission. LOCAL-GATE-04A blocks known bad assertions from
formal release, but it does not improve the Reasoner that generated them.

Dream readiness must therefore be stated narrowly:

- canonical facts and a path-empty OneCanvas can be projected now;
- professionally trusted work paths cannot be assumed;
- absence of a path is a valid state, not a Dream implementation failure.

## 6. DREAM-BRIDGE-01 Missing Capabilities

No Dream implementation exists yet. A future first read-only vertical slice
would need the following capabilities, each consuming existing authorities:

| Capability | Existing reusable authority | Missing work |
| --- | --- | --- |
| Entry and resume | Product session and Case context | Feature flag plus Dream visit state |
| Curated three-tree encounter | AgentCaseStore and CanonicalSceneOwner | Explicit authorization/grant model for anonymized curated Cases |
| Tree semantics | CanonicalScene and assertions | Read-only DreamProjection contract/adapter |
| Journey API | Existing FastAPI composition | Dream-specific read-only router/service |
| Browser scene | Existing Experience shell | One Dream route and responsive three-tree scene |
| Tree detail | Existing OneCanvas API/component | Reuse or embed; do not copy the renderer |
| Path-empty disclosure | Existing PathProjectionDiagnostic | Preserve current user-safe message |
| Resume | Existing authenticated product context | Minimal DreamVisit persistence, only if separately authorized |

### Provisional repository landing map

These are candidate landing zones for later review, not files authorized by
this audit:

```text
packages/experience/
  Dream projection contracts only; no Dream truth owner

apps/product/
  Truth adapter, journey service/router, and optional visit store

apps/product/experience_shell/src/
  Feature-flagged entry and Dream scene presentation

tests/
  Authority, privacy, resume, no-path, and OneCanvas-reuse tests
```

Before implementation, the final handoff must decide whether `DreamVisit`
requires persistence in the first slice. If it does, an explicit schema and
migration decision is required; startup DDL is forbidden.

## 7. Phase A Boundaries

The first slice must not introduce:

- Canonical NPC identity or NPC life simulation;
- synthetic population generation;
- NPC Mind, memory, world clock, attention leases, or encounters;
- 六爻 question mechanics;
- question flowers, judgments, fruit, reveal, or KnowledgeSeed promotion;
- a second Case, relation, path, scene, or ledger owner;
- frontend inference from natural-language cognition;
- copied OneCanvas logic;
- automatic LLM, TTS, topic generation, or baseline recomputation;
- production deployment or remote synchronization.

The later constitutions for NPC life, evidence, capacity, causal firewall, and
encounter orchestration remain design dependencies for later phases. They are
not implementation dependencies for a strictly read-only three-tree
projection, provided that no object is represented as a living Canonical NPC.

## 8. Baseline Evidence

All commands ran against the authoritative Mac worktree with bytecode and
pytest cache writes disabled.

```yaml
targeted_canvas_path_gate_tests:
  files: 5
  result: 47_passed

targeted_scene_workspace_tests:
  files: 4
  result: 24_passed

experience_typescript_typecheck:
  command: npm_run_typecheck_experience
  result: pass

full_v50_regression:
  result: 641_passed
  duration_seconds: 21.80

working_tree_fingerprint:
  before: 880f67441365c716d0c8a645d0cb15da0e95fee832424e09cca16a0e8f7861cd
  after: 880f67441365c716d0c8a645d0cb15da0e95fee832424e09cca16a0e8f7861cd
  unchanged: true

local_runtime:
  health: ok
  experience_http: 200
  port: 8053
```

The first test attempt failed during collection because the repository's test
helpers require `tests/` on `PYTHONPATH`. It made no source change. The suite
was rerun with the repository's actual test module path and passed.

## 9. Audit Decision

```yaml
DREAM_BRIDGE_01_REPO_MAP: complete
DREAM_BRIDGE_01_IMPLEMENTATION: not_started
read_only_three_tree_feasibility: feasible_with_explicit_case_grants
existing_onecanvas_reuse: feasible
formal_path_dependency: optional_for_phase_a_and_currently_empty
professional_cognition_dependency: not_satisfied
authorization_to_implement: absent
```

The repository can support a read-only Dream vertical slice without creating a
second Mingli system. The first implementation authorization must remain
limited to authenticated journey state, authorized anonymous Case projection,
three static tree projections, and reuse of the current OneCanvas. No wider
Dream World or NPC architecture should be inferred from that authorization.

Audit stops here pending the exact owner instruction:

```text
授权实施 DREAM-BRIDGE-01
```
