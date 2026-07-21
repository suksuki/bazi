# V50 Framework and Mingli Lab Convergence Closeout V1

Date: 2026-07-21  
Implementation commit: `5468f856`

## Result

The product framework now has one owner per responsibility:

```text
LifeCase                         formal case cognition
CanonicalSceneOwner             role-filtered scene identity
CaseBeliefState                 case-local cognitive deliberation
CaseWorkspaceState              non-cognitive product interaction state
MingliLabSession                non-authoritative experiment lifecycle
AbuNarrationService             narration of approved scene content
```

Workspace, Abu, Theater and Lab consume the same Canonical Scene source identity.
None of them can create chart facts, commit Mingli cognition, or promote a candidate.

## Consolidation and Slimming

- Removed `WorkspaceState` and its builders from `core.life_case`.
- Renamed cognitive `CaseCognitiveWorkspace` to `CaseBeliefState`.
- Renamed the narration owner and module to `AbuNarrationService` / `abu_narration.py`.
- Replaced separate temporal and mechanism sandbox lifecycle identities with one
  `MingliLabSession`.
- Removed Theater's legacy cognitive-record fallback and fuzzy competing-path rematch.
- Moved two fixture builders, 875 lines in total, out of the product runtime namespace.
- Kept old persisted Workspace and Sandbox payloads readable through explicit upgrade
  adapters; adapters cannot become formal owners.
- Added six generated JSON Schemas and matching generated TypeScript contracts from the
  Python models. No handwritten TypeScript contract owner was introduced.

Product runtime module count: `-2`.  
Duplicate Workspace meanings under one name: `3 -> 0`.  
Lab lifecycle owners: `2 -> 1`.  
Fixture builders under the product runtime: `2 -> 0`.

## Verification

```yaml
framework_alignment: CLOSED_PASS
framework_invariants: 10_of_10
framework_gaps: 0
mingli_lab_foundation: CLOSED_PASS
mingli_lab_invariants: 10_of_10
mingli_lab_gaps: 0
full_regression: 578_passed
typescript_strict: passed
architecture_gate: 17_of_17_pass
r1_regression_reference: 20_of_20_ok
universe_hash: 05c97a1518ff840ef3d4955f92dd0a22de9c4729ef7ff2ec8601efbcb14a454c
formal_state_writes: 0
production_migration: false
llm_used: false
```

## Next

The next active slice is Workspace Projection Alignment: connect the latest Case Workspace
reference to the shared Canonical Scene and existing product shell without production data
migration or a frontend framework migration.
