# V50 L2 Authority Consolidation Closeout

```yaml
status: CLOSED
gate: PASS
date: 2026-07-20
R1_v5_machine_gate: PASS
R1_human_product_gate: PENDING_EXECUTION
production_deployment: false
```

L2 removes duplicate cognitive authority. It does not add a new Mingli
capability and does not authorize Relation Atlas, Path Core V2, Reasoner,
LifeCase schema, full C2 or production work.

## 1. Authority Before / After

| Fact or decision | Before | After |
|---|---|---|
| Supplied pillars | Length checks and mixed trust conventions | Strict stems, branches, Jiazi, Five Tigers, Five Rats, timezone and calendar consistency |
| Chart editing | Local dependent cascade plus server compile | One global `PillarTargetDraft → ChartResolution` solver |
| Solver result | UI-oriented unique result | Explicit no / single / multiple solution contract; no silent multi-candidate commit |
| DaYun | Core functions plus local projections and local ownership fragments | One application-facing `CanonicalTemporalService` |
| OneCanvas timing | Local projection and fixture-derived helpers | Canonical service plus presentation-only adapter |
| Structural variant | Production depended on fixture-private implementation | Public `structural_variant_compiler` |
| Browser | Server catalogs plus local interaction preview | TargetDraft/display state only; final variant only from server response |
| Legacy invalid research charts | Could accidentally enter timing calculation | Read-only world material; temporal derivation explicitly rejected |

Authority counts after L2:

```yaml
canonical_chart_constraint_solver_count: 1
canonical_temporal_service_count: 1
production_private_fixture_imports: 0
browser_side_mingli_derivation: 0
duplicate_dayun_direction_implementations: 0
order_dependent_chart_results: 0
malformed_supplied_pillars_accepted: 0
stale_temporal_results_reused: 0
sandbox_formal_writes: 0
```

## 2. Dependency Direction

```text
Birth intake ───────────────→ Pillar Fact Authority
OneCanvas target intent ────→ Global Chart Constraint Solver

World ──────────────────────┐
OneCanvas ──────────────────┤
Fixture Builder ────────────┼→ CanonicalTemporalService
Personal Timing ────────────┘

Canonical facts
  → OneCanvas timing adapter
  → public structural variant compiler
  → Renderer / static review fixture
```

The adapter formats known facts. It does not import the temporal service,
calculate DaYun, infer relations or repair missing semantics.

## 3. Deleted Old Owners

Deleted rather than renamed:

```text
dayun.current_timing_material
OneCanvas._onecanvas_timing_projection
OneCanvas._luck_direction
Fixture._structural_timing_projection
Fixture._onecanvas_structural_variant
Fixture._prepare_variant_for_canvas
Fixture._pillar_nodes
production → fixture-builder private helper dependency
```

`dayun.py` remains a low-level algorithm module. Only
`CanonicalTemporalService` may call it from the application layer.

## 4. Contract Evidence

### L2-A Pillar fact rejection

Fixtures reject:

```text
invalid stem
invalid branch
invalid Jiazi / parity
illegal year-month dependency
illegal day-hour dependency
calendar mismatch
invalid timezone
partial supplied pillars
```

Every accepted birth input carries one explicit source:

```text
calendar_derived_formal
calendar_verified_supplied
structurally_legal_hypothetical
unverified_legacy
```

There is no silent repair. Historical invalid research charts may remain
readable, but return `pillar_facts_rejected` and no DaYun.

### L2-B 0 / 1 / many

`ChartResolution` exposes:

```text
no_solution       conflicts + releasable_constraints
single_solution   one selected complete ChartVariant
multiple_solutions candidates + selected_variant = null
```

Order independence, deterministic candidates, monotonic constraint relaxation,
anchor invalidation and incomplete-draft non-selection have machine fixtures.

### L2-C three temporal levels

```text
structural_valid       direction and sequence only
calendar_resolved      real datetime candidate set exists
active_dayun_resolved  active DaYun and year/age range are resolved
```

Changed, unchanged and unresolved are explicit. The Ding-Si fixture
`丁巳 乙巳 乙丑 乙酉`, male, 1977, observed in 2026 resolves to:

```text
direction: reverse
active_dayun: 庚子
year_range: 2018–2027
```

Every result carries a derivation fingerprint over pillars, gender, analysis
year, timezone, birth anchor, calendar profile and rule profile. Changing
gender invalidates the prior result in the stale-derivation fixture.

## 5. R1 v5 Machine Evidence

R1 now proves:

- the browser contains no Five Tigers, Five Rats, Jiazi, relation or DaYun algorithm;
- UI interaction may prepare a TargetDraft using server-provided catalogs;
- every effective chart mutation calls `/onecanvas/target-compile`;
- only `payload.variant` may replace `workingSnapshot.variant`;
- multiple candidates cannot be silently selected;
- DaYun is derived and never directly edited;
- Gregorian year is the annual input; annual Jiazi is derived;
- unknown gender never reuses stale DaYun;
- target compile writes neither ChartVersion nor LifeCase.

Evidence: `reports/v50-lean-consolidation/l2/authority_evidence.json`.

## 6. Verification

```text
focused authority + OneCanvas: 67 passed
full regression:                 434 passed
authority audit:                PASS
production deployment:          NOT PERFORMED
```

The first full run exposed 29 old fixtures that treated malformed pillars as
valid timing input. Formal product tests were corrected to re-derive all four
pillars after a birth-date change. Historical research fixtures were not
silently rewritten; the temporal service now refuses to derive DaYun from
them while preserving read-only benchmark access.

## 7. Next Gate

Only the revised R1 v5 unguided human review is authorized next:

```text
2 professional analysts
5 first-time users
desktop all tasks
390px mobile core tasks
no oral guidance
```

RA1, Path Core V2, full C2 and production release remain blocked.
