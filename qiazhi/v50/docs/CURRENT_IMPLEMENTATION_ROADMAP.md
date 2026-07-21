# DeepBazi V50 Current Implementation Roadmap

> Canonical execution order
>
> Updated: 2026-07-21

<!-- V50_EXECUTION_STATE:START -->
## Machine-Synchronized Execution State

> Source: `config/v50_execution_state.yaml` · SHA-256 `c71426a67806` · Updated `2026-07-21`

```yaml
canonical_product_target: Life Script Case Workspace
current_product_surface: legacy_l5_plus_experience_shell
case_workspace_status: ISOLATED_DESIGN_STUDY_IMPLEMENTED_PRODUCTION_NOT_STARTED
product_model: one_case_workspace
mingli_world: one_canonical_mingli_world
r1_human_product_gate: CANCELED_NO_SCHEDULE
architecture_consolidation_gate: CLOSED_PASS
professional_blind_gate: PENDING
public_professional_release: BLOCKED
full_regression: 559_PASSED_RA1_RELATION_CORE_FINAL
```

Authorized now:

- `RA2_PATH_QUALIFICATION`: qualify_existing_relations_for_paths_with_explicit_evidence_without_changing_relation_existence

Next architecture slice: `RA3_PATH_EVIDENCE_CALIBRATION` after `ra2_path_qualification_pass`.

Blocked: `ra3_uncalibrated_path_scoring_promotion`, `mingli_lab_public_release`, `production_workspace_migration`, `frontend_framework_migration`, `self_healing_platform_or_product_subsystem`, `new_product_ui_animation_or_interaction`, `public_release`.
<!-- V50_EXECUTION_STATE:END -->

## 0. Rule

The roadmap is gate-driven, not feature-count-driven.

```text
machine proof
≠ product proof
≠ professional Mingli proof
≠ production authorization
```

`Abu Actor Pass V1` is `CLOSED / PASS`, and `S0 V1.2` is locked. L2 Authority
Consolidation is also closed. R1 truthfully exposes the Solver's zero, one and
many outcomes; its 20-file V6 manifest remains an immutable regression
reference. The previously assumed seven-person review does not exist and is no
longer an engineering prerequisite. The current phase is limited to integration,
cleanup, slimming and authority convergence. Self-healing and synthetic
validation are evidence disciplines here, not new product or platform work.

## 1. Closed — L0 + L1 Closeout

Status: `CLOSED / PASS / AUTHORITY HARDENED`

Required closeout:

```text
machine Before inventory
→ safe archive and physical deletion
→ runtime/static reference checks
→ full regression
→ machine After inventory
→ one-page Before/After
```

L1 may move or delete only presentation proofs, duplicate media and
regenerable outputs. It may not alter Runtime, Reasoner, LifeCase, relation/path
semantics, or formal state.

## 2. Closed — L2 Authority Consolidation

Status: `CLOSED / PASS`

This slice closed one-owner authority for:

- a canonical Chart Constraint Solver;
- a canonical Temporal / DaYun service;
- removal of browser-side Mingli derivation;
- removal of production dependencies on fixture-builder private helpers.

It was admitted only after the L0/L1 closeout and was closed with failing
fixtures, focused regression and a full authority audit.

## 3. Retained — Xiangfa Generation V1

Status: `RETAINED ISOLATED ROUTE / NON-AUTHORITATIVE`

The existing route and evidence are retained. It may not reopen S0, add a
Reasoner, create relations or paths, or write LifeCase state. Future Xiangfa
work must consume the Canonical Scene projection envelope.

## 4. Retained — R1 V6 Regression Reference

Status: `MACHINE PASS / 20 FILES HASH-LOCKED / HUMAN GATE CANCELED`

The target-draft, global Chart Constraint Solver and canonical Temporal / DaYun
service pass the machine gate. The hash-locked build under
`reports/mingli-onecanvas-r1/review-v6-ready/` remains unchanged and is rerun as
a behavioral baseline after architecture work. No R1-A01 through R1-U05
sessions are scheduled or awaited.

The order-dependent pillar cascade has been replaced by the global target-draft
solver. The product projection now preserves all three server-owned outcomes:

- `single_solution` applies one resolved complete chart;
- `multiple_solutions` requires explicit selection of a complete variant;
- `no_solution` shows the conflict and only server-provided releasable
  constraints.

No outcome is ranked professionally, the first candidate is never selected
silently, cancellation preserves the current chart, and the browser still owns
no legality rule. R1 is evidence, not a global stop signal; Relation Atlas still
waits for CAG-03 through CAG-05 and the Architecture Gate.

## 5. Architecture Consolidation Gate

Status: `REQUIRED BEFORE RA1`

### CAG-01 — Authority Closure

Status: `PASS`

```text
prove Graph relation first-look leak with a failing fixture
→ make authority mapping exhaustive
→ rerun authority and full regression suites
```

Exit condition: no experimental observation can become production through an unknown/default authority value.

### CAG-02 — Canonical Calendar and Temporal Services

Status: `PASS`

Extract from prototype scripts into versioned domain/application services:

- Jiazi catalog;
- year→month candidate dependency;
- day→hour candidate dependency;
- real-date reverse lookup;
- DaYun direction and sequence;
- exact/current DaYun resolution;
- changed/unchanged/unresolved result contract.

Migrate World, OneCanvas, and fixtures to consume the same owner.

Exit condition: no production module imports `scripts.*`.

L2 closed the previously listed defects:

- production structural compilation consumes a public compiler;
- OneCanvas timing consumes `CanonicalTemporalService` through a
  presentation-only adapter;
- structural, calendar-resolved and active-DaYun states are explicit;
- supplied formal pillars have strict Jiazi and calendar consistency fixtures;
- no production module imports `scripts.*` or fixture-private helpers.

### CAG-02A — Global Chart Constraint Solver

Status: `PASS`

Define a server-owned target draft and solver that accepts desired pillar
constraints and returns zero, one, or many legal complete variants. Browser
gestures may edit the draft, but may not destructively cascade the compiled
chart or decide legality.

Exit condition:

- operation order does not change the reachable target set;
- year/month and day/hour dependencies are solved globally;
- birth-year anchors are preserved only when compatible;
- formal, hypothetical structural, calendar-resolved, and active-DaYun states
  remain distinct;
- no Sandbox action writes ChartVersion or LifeCase.

### CAG-03 — Canonical Scene Contract Convergence

Status: `CLOSED / PASS`

The canonical Scene Compiler projects one formal case source into:

- OneCanvas;
- Abu;
- Theater;
- Xiangfa;
- Workspace.

`CanonicalSceneOwner` accepts only a server-owned case identity, reads
`ChartWorldInstance + committed LifeCase`, applies role disclosure before
serialization, and issues one shared Scene identity plus projection envelopes.
Theater delegates to this owner; read-only OneCanvas requests its projection
from the same owner; Abu narration no longer reads `record` or invokes a legacy
formal-projection fallback. Graph/Path v1 remains candidate-only behind the
formal CAG-04 assertion boundary.

Exit condition: one semantic identity model, no Renderer inference, no client
formal-fact override, and tested compatibility paths for current contracts.

### CAG-04 — Formal Relation and Path Provenance

Status: `CLOSED / PASS`

Implemented without changing Graph or Path semantics:

- stable `NodeRef`, `RelationKey` and `PathKey` contracts;
- append-only versioned `RelationAssertion` and `PathAssertion` history;
- explicit provenance, lifecycle and supersession;
- exact-only legacy migration with `legacy_unresolved` fallback;
- one formal owner in LifeCase;
- role-filtered assertion projection through Canonical Scene;
- removal of Canvas anonymous path IDs and relation-text matching;
- removal of Theater score-tolerance and signature-based reconnection.

Exit condition:

- a committed LifeCase path survives Relation/Graph implementation upgrades;
- historical cognition is readable without silent rewriting;
- candidate, committed, blocked, and user-draft paths remain distinct.

Machine evidence: `11` focused and `479` full tests passed; R1 remains `20/20`;
V40 is unchanged. Candidate provenance cannot masquerade as formal status, and
invalid supersession history is rejected at the formal source and projection
boundaries.

### CAG-05 — Schema and Module Ownership

Status: `CLOSED / PASS`

- one production authority manifest replaces four split registries;
- one PostgreSQL schema file replaces six runtime DDL owners;
- one command service executes both synchronous and progressive baselines;
- Python response models generate JSON Schema and TypeScript contracts;
- handwritten TypeScript contract declarations are retired;
- Canonical, Transitional and Legacy ownership is frozen without adding a new
  transitional layer.

Machine evidence: `10` focused and `483` full tests passed; TypeScript typecheck
and production bundle passed; the rebuilt bundle is byte-identical; R1 remains
`20/20`. Implementation commit: `2078e3a1`.

The Architecture Gate now waits only for `CAL-01 Late-Zi Five-Rats
Consistency`; CAG-05 did not adopt RA0 audit normalization silently.

The current cleanup and large-file policy is recorded in
`V50_DEEP_CLEANUP_AND_LARGE_FILE_GOVERNANCE_V1.md`. It does not authorize
Relation Atlas, Path Core V2, route retirement, or production deployment.

## 6. Core V2 Workstream

Blocked until the Architecture Consolidation Gate passes.

### RA1 — Relation Ontology and Fixtures

Implement only:

- RelationDefinition;
- BinaryRelation and HyperRelation;
- ContextModifier and TemporalActivation;
- school profile and semantic definitions bound to the existing CAG-04 keys
  and assertion provenance;
- no second relation or path identity system;
- positive, negative, missing-condition, temporal, and coexistence fixtures.

No new ordinary-user UI.

### RA2 — Temporal Relation Activation

Model how DaYun and annual states introduce, activate, reinforce, weaken, block, reopen, or leave relations unchanged. Preserve discrete semantics and reasons; do not create pseudo-precise percentages.

### RA3 — Path Core V2

Implement:

- PathCandidate semantics and extensions to the existing `PathAssertion`;
- ordered PathSegment references;
- segment eligibility;
- whole-path continuity and blockers;
- typed evidence/counter-evidence;
- temporal path state;
- versioned provenance.

LLM comparative reasoning remains the professional synthesis authority.

## 7. Migration and Authority Workstream

### RA4 — World and Reasoner Adapters

Expose V2 relations and path candidates to the Context Compiler without allowing them to dominate the independent first look. Preserve challenge-pack separation.

### RA5 — LifeCase Provenance Migration

Write new typed assertions for future commits and provide read adapters for historical LifeCases. Never mass-rewrite old cognition silently.

### RA6 — Graph/Path v1 Quarantine and Retirement Audit

Track every remaining consumer. Keep v1 as a versioned experimental adapter until parity fixtures and usage evidence permit retirement.

## 8. Product Adoption Workstream

### RA7 — OneCanvas Adoption

After Core V2 and migration gates:

- render all approved relation lenses from one Scene Compiler;
- assist PathDraft using server-authorized relation/path eligibility;
- compare system, candidate, and user paths in one node space;
- expose local root/reveal and temporal activation progressively;
- preserve Li, Xiang, and Time identity;
- keep ordinary-user complexity below professional views.

Theater, classes, video export, and Live consume the same Scene State later. They do not create a second relation or path system.

## 9. Legacy Retirement

Legacy retirement happens last, by evidence:

```text
usage observed
→ replacement parity proven
→ data migration verified
→ route decision recorded
→ rollback available
→ retire
```

Candidates include:

- the L5 root shell;
- legacy Agent read APIs;
- fixture-script production dependencies;
- duplicate timing helpers;
- independent C1R/C2A product evolution;
- Graph/Path v1 authority claims.

## 10. Verification Loop

Every slice follows:

```text
contract
→ failing fixture
→ minimal implementation
→ focused regression
→ full regression
→ authority audit
→ product/professional review where applicable
→ explicit gate decision
```

No gate is inferred from code volume or test count alone.

## 11. Current Status

```yaml
lean_l0_inventory: COMPLETE
lean_l1_physical_slimming: COMPLETE
lean_l1_machine_gate: PASS
lean_l1_full_regression: 413_PASSED
lean_l2_authority_consolidation: CLOSED
lean_l2_machine_gate: PASS
lean_l2_full_regression: 434_PASSED
R1_v5_machine_gate: PASS
R1_legacy_machine_gate: SUPERSEDED
R1_review_build: V6_HASH_LOCKED
R1_projection_regression: 30_PASSED
R1_full_regression: 438_PASSED
R1_human_product_gate: CANCELED_NO_SCHEDULE
R1_regression_reference: 20_OF_20_HASH_LOCKED
git_source_baseline: PASS
CAG_03_canonical_scene: CLOSED_PASS
architecture_audit: COMPLETE
architecture_consolidation_gate: NOT_PASSED
RA1: BLOCKED
RA2_to_RA7: BLOCKED
professional_blind_gate: PENDING
production_release: BLOCKED
```
