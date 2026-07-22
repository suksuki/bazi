# DREAM-BRIDGE-01 Gate Report

## Decision

```yaml
DREAM_BRIDGE_01_CODE_COMPLETE: PASS
DREAM_BRIDGE_01_REAL_THREE_TREE_GATE: BLOCKED_EXPECTED
DREAM_BRIDGE_01_RELEASE: NOT_AUTHORIZED
PATH_QUALIFICATION_01_DIAGNOSTIC: COMPLETE
PROFESSIONAL_PATH_QUALIFICATION: BLOCKED
LOCAL_GATE_04: NOT_PASSED
committed_PathAssertion: 0
```

The read-only bridge, eligibility gate, state machine, persistence, projection, API, and responsive scene are implemented. The real three-tree product gate is correctly closed because the local source of truth currently contains zero eligible Dream grants. No existing Case was auto-authorized, copied, mocked, or hardcoded to make the gate pass.

## Repository Landing Points

The pre-implementation repository map remains `docs/product/DREAM_BRIDGE_01_REPO_MAP.md`; the table below records the implemented landing points.

| Responsibility | Owner |
| --- | --- |
| Dream contracts and state machine | `packages/experience/dream.py` |
| Feature admission | `apps/product/dream_feature.py` |
| Eligibility, visits, selection, and resume | `apps/product/dream_service.py` |
| Disposable read-only projection | `apps/product/dream_projection.py` |
| Persistence contract and stores | `apps/product/dream_store_contracts.py`, `apps/product/dream_store_memory.py`, `apps/product/dream_store_postgres.py` |
| Authenticated journey API | `apps/product/dream_api.py` |
| Existing formal scene authority | `apps/product/canonical_scene.py` |
| Existing OneCanvas compiler | `apps/product/canvas_projection.py` |
| Dream web runtime and localization | `apps/product/experience_shell/src/dream_runtime.ts`, `apps/product/experience_shell/src/dream_i18n.ts` |

## Data And State

- New persistent objects: `DreamSceneGrant`, `DreamVisit`, and immutable `EncounterSet` selection data.
- State flow: `HOME_GROVE → PATH_OFFERED → DREAM_ENTERING → ENCOUNTER_READY → TREE_SELECTED → TREE_OBSERVING → MIRROR_OPEN`.
- Exactly three eligible scenes are selected deterministically; one tree may be selected once.
- Visits are owner-scoped, resumable, idempotent, and protected by row-version checks.
- Revoked grants and changed source versions invalidate subsequent projection access.
- The explicit local migration raised the schema from `v50.consolidated.002` to `v50.consolidated.003`; service startup only checks the version.
- Local production-like data after migration: `0` Dream grants and `0` Dream visits.

## Feature And Eligibility

The server-side feature is off by default and requires both:

```text
V50_DREAM_BRIDGE_V1_ENABLED
V50_DREAM_BRIDGE_V1_USER_IDS
```

The client cannot enable it. Eligibility requires a real Canonical Scene plus an active, explicit, anonymized, revocable grant, a stable source version, a unique public scene reference, and complete canonical facts. Fewer than three eligible grants returns a closed gate and does not expose the entry.

## OneCanvas And Disclosure

Dream uses the existing Canonical Scene owner and the existing OneCanvas compiler; it does not copy chart facts or create a second renderer. Public scene references are opaque and mapped server-side.

For Guest and Member projections:

- all `potential` relations are omitted;
- raw Case and authorization references are omitted;
- uncommitted, rejected, and `legacy_unresolved` paths are omitted;
- committed path count is currently `0`;
- the only work-path message is `当前暂无已确认主路径`;
- Dream and the browser never parse natural language to create a line.

## Verification

- Dream Bridge and Path Qualification focused tests: `10 passed`.
- Broader owner/projection/API focused suite: `43 passed`.
- TypeScript typecheck and Experience build: passed.
- Desktop and 390 px mechanism fixtures: no horizontal overflow; three trees remain visible; tree selection, mirror opening, and the shared six-pillar canvas work without console errors.
- `zh`, `en`, and `ko` strings are centralized; reduced-motion behavior is present.
- Fixture screenshots under `.runtime/dream-bridge-01` verify rendering only. They are not eligible Canonical Scenes and do not count toward the real three-tree gate.

## Rollback And Remaining Work

Rollback is limited to this isolated Dream module, its router/frontend registration, and the explicit `v50.consolidated.003` Dream tables. No production rollback or deployment was performed.

The bridge can open only after three real scenes receive explicit grants. Path cognition remains a separate blocked gate: 44 records yield 37 `no_candidate`, 5 `segment_rejected`, 2 `legacy_unresolved`, and 0 `committed`. No repair was attempted.

## Scope Declaration

This change did **not** implement NPCs, synthetic populations, Mind Wake, problem flowers, judgments, fruit, reveal, Liuyao/Q0 Runtime, new Mingli algorithms, Prompt or knowledge changes, GitHub synchronization, server deployment, or production opening.
