# DeepBazi V50 Current Implementation Roadmap

> Canonical execution order
>
> Updated: 2026-07-20

<!-- V50_EXECUTION_STATE:START -->
## Machine-Synchronized Execution State

> Source: `config/v50_execution_state.yaml` · SHA-256 `2ea6c66d5b97` · Updated `2026-07-20`

```yaml
canonical_product_target: Life Script Case Workspace
current_product_surface: legacy_l5_plus_experience_shell
case_workspace_status: ISOLATED_DESIGN_STUDY_IMPLEMENTED_PRODUCTION_NOT_STARTED
product_model: one_case_workspace
mingli_world: one_canonical_mingli_world
r1_human_product_gate: READY_PENDING_EXECUTION
architecture_consolidation_gate: NOT_PASSED
professional_blind_gate: PENDING
public_professional_release: BLOCKED
full_regression: 446_PASSED
```

Authorized now:

- `R1_HUMAN_REVIEW`: execute_hash_locked_v6_review_only
- `CASE_WORKSPACE_IA`: information_architecture_and_isolated_clickable_prototype
- `MINGLI_LAB_BLUEPRINT`: roles_tasks_permissions_and_scene_requirements

Next architecture slice: `ARCHITECTURE_CONSOLIDATION_SLICE_2` after `r1_human_product_gate_pass`.

Blocked: `relation_atlas_ra1`, `relation_core_v2_implementation`, `path_core_v2_implementation`, `mingli_lab_engineering`, `production_workspace_migration`, `frontend_framework_migration`, `legacy_l5_redesign`, `public_release`.
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
Consolidation is also closed. R1 now truthfully exposes the Solver's zero, one
and many outcomes, and the review build is hash-locked. The only active task is
the v5 unguided human review. Existing visual prototypes are retained but
receive no parallel feature work during this gate.

## 1. Closed — L0 + L1 Closeout

Status: `CLOSED / PASS`

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

## 3. Frozen — Xiangfa Generation V1

Status: `RETAINED ISOLATED ROUTE / WORK PAUSED`

The existing route and evidence are retained. No new Xiangfa work is active
before the R1 human gate. It may never reopen S0, add a Reasoner, create
relations or paths, or write LifeCase state.

## 4. Now — R1 v5 Unguided Human Product Review

Status: `V5 MACHINE PASS / REVIEW BUILD HASH-LOCKED / HUMAN REVIEW PENDING`

Do not execute the superseded v1 protocol. The target-draft, global Chart
Constraint Solver and canonical Temporal / DaYun service pass the machine gate.
Use `product/V50_ONECANVAS_R1_V5_UNGUIDED_REVIEW_PROTOCOL.md` for the human
review against the hash-locked build recorded under
`reports/mingli-onecanvas-r1/review-v6-ready/`.

Review only:

- formal versus Sandbox authority;
- legal pillar selection and linked choices;
- gender and DaYun direction;
- changed, unchanged, and unresolved DaYun states;
- Gregorian annual observation only; annual Jiazi is derived;
- undo, redo, reset;
- desktop and 390px mobile completion.

The order-dependent pillar cascade has been replaced by the global target-draft
solver. The product projection now preserves all three server-owned outcomes:

- `single_solution` applies one resolved complete chart;
- `multiple_solutions` requires explicit selection of a complete variant;
- `no_solution` shows the conflict and only server-provided releasable
  constraints.

No outcome is ranked professionally, the first candidate is never selected
silently, cancellation preserves the current chart, and the browser still owns
no legality rule. The former preparation blocker is closed; professional
analysts and first-time users have not yet executed the human gate.

Do not add Relation Atlas, assisted path drawing, Theater, Xiangfa, or new Mingli modules to R1.

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

### CAG-03 — Scene Contract Convergence Design

Freeze a canonical Scene Compiler contract that can project:

- C1 Inspector view;
- OneCanvas interactive view;
- role-filtered Context Pack;
- later Theater and Xiangfa views.

Exit condition: one semantic identity model, no Renderer inference, and a tested adapter path for both current contracts.

### CAG-04 — Formal Relation and Path Provenance

Define versioned identifiers and historical adapters before changing Graph behavior.

Exit condition:

- a committed LifeCase path survives Relation/Graph implementation upgrades;
- historical cognition is readable without silent rewriting;
- candidate, committed, blocked, and user-draft paths remain distinct.

### CAG-05 — Legacy and Documentation Ownership

Status: `FIRST CLEANUP SLICE COMPLETE / RETIREMENT PENDING`

- retain usage tracking for legacy routes and Agent APIs;
- freeze prototype identities;
- remove old docs from current-authority navigation;
- assign owner and authority level to active modules.

Exit condition: Architecture Consolidation Gate review is explicitly signed `PASS`.

The current cleanup and large-file policy is recorded in
`V50_DEEP_CLEANUP_AND_LARGE_FILE_GOVERNANCE_V1.md`. It does not authorize
Relation Atlas, Path Core V2, route retirement, or production deployment.

## 6. Core V2 Workstream

Blocked until R1 Product Gate and Architecture Consolidation Gate pass.

### RA1 — Relation Ontology and Fixtures

Implement only:

- RelationDefinition;
- BinaryRelation and HyperRelation;
- ContextModifier and TemporalActivation;
- provenance, school profile, stable relation IDs;
- positive, negative, missing-condition, temporal, and coexistence fixtures.

No new ordinary-user UI.

### RA2 — Temporal Relation Activation

Model how DaYun and annual states introduce, activate, reinforce, weaken, block, reopen, or leave relations unchanged. Preserve discrete semantics and reasons; do not create pseudo-precise percentages.

### RA3 — Path Core V2

Implement:

- PathCandidate and PathAssertion;
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
R1_human_product_gate: READY_PENDING_EXECUTION
R1_human_product_blocker: NONE
architecture_audit: COMPLETE
architecture_consolidation_gate: NOT_PASSED
RA1: BLOCKED
RA2_to_RA7: BLOCKED
professional_blind_gate: PENDING
production_release: BLOCKED
```
