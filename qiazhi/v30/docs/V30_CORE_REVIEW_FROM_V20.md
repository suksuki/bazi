# V30 Core Review From V20

Updated: 2026-05-20

## Purpose

This document reviews V20 `core/` before implementing real V30 core context.

Goal:

- Identify direct reuse candidates.
- Identify modules that need reimplementation.
- Define V30 core contracts.
- Define the first fixture and test plan.

## Reviewed V20 Files

```text
core/schemas.py
core/chart.py
core/constants.py
core/ten_gods.py
core/relations.py
core/elements.py
core/time_context.py
core/strength.py
core/useful_god.py
core/context_frame.py
core/calendar.py
```

## Summary Decision

| V20 file | Decision | Reason |
|---|---|---|
| `core/constants.py` | Direct reuse candidate | Static stems, branches, hidden stems, element maps, relations. |
| `core/ten_gods.py` | Direct reuse candidate | Small deterministic ten-god mapping. |
| `core/relations.py` | Direct reuse candidate with cleanup | Deterministic branch relation extraction. |
| `core/elements.py` | Direct reuse candidate with cleanup | Deterministic element distribution. |
| `core/schemas.py` | Reimplement as V30 contracts | Good ideas, but V20 names and dataclass shape should become V30 typed contract. |
| `core/chart.py` | Light reimplementation | Good deterministic logic, but imports and version names are V20. |
| `core/time_context.py` | Light reimplementation | Good explicit pillar model, but V30 needs richer time layer contract. |
| `core/strength.py` | Reimplement from idea | Current scoring is useful as baseline but too simple and parameter constants are not policy-backed. |
| `core/useful_god.py` | Reimplement from idea | Good guardrails, but useful-god must be evidence/path candidate, not core verdict. |
| `core/context_frame.py` | Reimplement from idea | Strong binding concept, but V30 should model it in `ChartContext` and module bindings. |
| `core/calendar.py` | Reimplement carefully | Useful profile-to-pillar behavior, but approximate fallback and optional dependency need explicit status. |

## Reusable Ideas

### Deterministic Chart Facts

V20 already separates deterministic chart facts from conclusions:

```text
ChartInput
-> ChartFacts
```

V30 should keep this principle.

### Guardrails

V20 core guardrails are good and should become V30 contract rules:

- No LLM fact generation.
- No fortune conclusion in core.
- Time layer requires explicit pillar.
- No timing prediction without evidence.
- Useful-god is candidate path, not verdict.

### Time Context Explicitness

V20 `time_context.py` only builds time layers when explicit pillars are supplied.

V30 should preserve this but represent:

- Luck cycle.
- Annual flow.
- Monthly/current flow.
- Missing time state.
- Source and confidence.

### Context Binding

V20 `context_frame.py` created a strong idea:

```text
one current Bazi context ID
-> module outputs must bind to it
```

V30 should absorb this into:

- `ChartContext.context_id`
- module-level `context_id`
- evidence IDs
- trace alignment reports

## V30 Core Target

V30 core should produce:

```text
ChartContext
TimeLayer[]
PillarSet
TenGodPosition[]
RelationHit[]
ElementDistribution
CoreFeatureSeed[]
```

Core should not produce:

- Final useful-god verdict.
- Domain conclusions.
- Question recommendations.
- Portrait claims.
- LLM prompt text.

## Proposed V30 Core Modules

```text
v30/core/constants.py
v30/core/pillars.py
v30/core/ten_gods.py
v30/core/relations.py
v30/core/elements.py
v30/core/chart_context.py
v30/core/time_context.py
v30/core/calendar.py
```

Feature and interpretation logic should live outside core:

```text
v30/evidence/features.py
v30/evidence/strength.py
v30/evidence/useful_god_candidates.py
```

## Contract Changes From V20

### V20

```text
ChartFacts
TimeContext
CoreInference
UsefulGodCandidate
```

### V30

```text
ChartContext
FeatureEvidence
StructureState
MainlineState
AnswerContext
```

V30 should avoid `CoreInference` as a verdict-like object in core. Strength and useful-god should become evidence candidates.

## Direct Reuse Requirements

Before copying any V20 core logic into V30:

- Replace `v20.*` imports with V30 modules.
- Replace version strings.
- Add V30 tests.
- Confirm no runtime pointer, Redis, DB, or V20 runtime file dependency.
- Keep code deterministic and pure.

## First Core Fixture Set

Initial fixtures should cover:

1. Valid four explicit pillars.
2. Invalid stem.
3. Invalid branch.
4. Ten-god visible mapping.
5. Hidden stem extraction.
6. Branch clash.
7. Branch harmony.
8. Three harmony.
9. Explicit luck pillar.
10. Missing time context.

## First Core Tests

Default fast tests:

```text
tests/unit/test_core_pillars.py
tests/unit/test_core_ten_gods.py
tests/unit/test_core_relations.py
tests/unit/test_core_time_context.py
tests/unit/test_core_chart_context.py
```

These should not require:

- Postgres.
- Redis.
- V20 imports.
- LLM.
- 518K corpus.
- Running service.

## Implementation Order

1. Add V30 constants. Completed.
2. Add V30 pillar model and parser. Completed.
3. Add V30 ten-god mapping. Completed.
4. Add V30 branch relations. Completed.
5. Add V30 element distribution. Completed.
6. Add V30 chart context builder. Completed.
7. Add V30 explicit time context builder. Completed.
8. Add core unit tests. Completed.
9. Convert first V20 core cases into fixtures.

## Risks

- Copying V20 import paths by accident.
- Letting useful-god verdicts enter core.
- Treating approximate calendar fallback as high-confidence truth.
- Making time context implicit.
- Reintroducing domain conclusions before evidence layer.

## Acceptance

- V30 core facts are deterministic.
- V30 core has no `v20.*` imports.
- Missing time context is explicit.
- Core tests are fast.
- Strength/useful-god remain evidence candidates, not core truth.
- Downstream modules can bind to `ChartContext.context_id`.
