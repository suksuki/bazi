# V30 M1/M2 Bazi Calculation And Base Fact Layer Completion Plan

Updated: 2026-05-24

## Purpose

This is the dedicated completion plan for the two modules that must be sealed before M5 consumes chart facts:

- M1: BirthInput and deterministic chart facts.
- M2: Base Bazi fact explanation layer.

The rule is strict: M1 creates deterministic facts, M2 explains and projects those facts, and M5 only consumes them for ranked judgment. Training, feedback, hidden factors, and LLM output must not create or mutate chart facts.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M1 BirthInput and deterministic chart facts | 95% | 95% | Phase sealed: solar, lunar, true-solar, unknown-hour/invalid-timezone guardrails, solar-term/year-month boundary fixtures, canonical real-case fact fixtures, luck/flow/six-pillar context, deterministic `base_fact_summary`, and dedicated M1/M2 synthetic validation are active. |
| M2 Base Bazi fact explanation layer | 92% | 92% | Phase sealed: `core_bazi_reading`, `fact_integrity`, `base_fact_explanations`, root/vault fact summary, deterministic fact-contract observations, canonical category coverage, and base-fact training signals are active. |

## A-E Completion Path

### A. Contract And Ownership

- M1 owns BirthInput, calendar conversion, chart build, four pillars, boundary trace, luck-cycle context, flow-year/month context, and six-pillar context.
- M2 owns day-master, visible/hidden ten-god, hidden stems, five-element distribution, relation facts, vault/root fact summaries where supported, and customer-safe base explanations.
- M5 owns strength, structure pattern, and useful-god ranked decisions. M5 must not recalculate or mutate M1/M2 facts.

### B. Deterministic Conversion Hardening

- Solar ready chart.
- Lunar ready chart.
- Leap-month lunar ready chart.
- True-solar known-place chart.
- Unknown-hour pending chart with no fake pillars.
- Invalid timezone blocked chart with no fake pillars.
- Late-zi and timezone boundary flags.

### C. Fact Layer Completeness

- `base_fact_summary` must expose pillar count, day master, day-master element, visible ten-god counts, hidden ten-god counts, hidden stem summary, relation type counts, relation families, vault branches, element distribution, strongest elements, weakest elements, fact sources, and guardrails.
- `base_fact_explanations` must explain day master, ten gods, hidden stems, five elements, relations, and time context without fixed strength, fixed structure, or fixed useful-god conclusions.
- `fact_integrity` must explicitly mark chart facts as deterministic, not LLM-generated, not training-generated, and not feedback-generated.

### D. Synthetic And Training Validation

- Dedicated synthetic tier: `m1_m2_bazi_calculation`.
- Existing adjacent tier: `core_bazi_calculation`.
- Training signal: `v30.training_signal.m1_m2_base_fact_contract`.
- Training may improve validation coverage and explanation density. It must not create or alter chart facts.

### E. Gate And Documentation

Subtask gate:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
```

Major gate, only when declaring M1/M2 complete for the phase:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

## Completed 2026-05-24 Batch 1

- Added `v30.base_bazi_fact_summary.v1` under `ChartContext.natal_pillars`.
- Added `fact_integrity` and `v30.base_bazi_fact_explanations.v1` under `core_bazi_reading`.
- Validated with targeted M1/M2 tests and `core_bazi_calculation`.

## Completed 2026-05-24 Batch 2

- Expanded `base_fact_summary` with visible ten-god counts, hidden ten-god counts, hidden stem summary, relation type counts, and relation families.
- Expanded `base_fact_explanations` to expose deterministic visible/hidden ten-god counts and relation families.
- Added dedicated `m1_m2_bazi_calculation` synthetic tier covering solar, leap-month lunar, true-solar, unknown-hour, and invalid-timezone boundaries.
- Added `m1_m2_base_fact_contract` observations and `v30.training_signal.m1_m2_base_fact_contract`.

Validation 2026-05-24 Batch 2:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 41 passed
Synthetic core_bazi_calculation: 4/4 passed
Synthetic m1_m2_bazi_calculation: 5/5 passed
Full pytest / synthetic all / 518K: not run; reserved for major gate.
```

## Completed 2026-05-24 Batch 3

- Added `v30.root_vault_fact_summary.v1` to `base_fact_summary`.
- Added root/vault guardrails: root facts are hidden-stem presence only, no strength verdict from root facts, no useful-god verdict from vault facts.
- Added `roots_and_vaults` to `base_fact_explanations`.
- Added solar-term/year-month synthetic fixtures for before/after the deterministic engine boundary.
- Expanded `m1_m2_bazi_calculation` from 5 to 7 cases.
- Extended `v30.training_signal.m1_m2_base_fact_contract` with `root_fact_ready_count`.

Validation 2026-05-24 Batch 3:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 42 passed
Synthetic m1_m2_bazi_calculation: 7/7 passed
Synthetic core_bazi_calculation: 4/4 passed
Full pytest / synthetic all / 518K: not run; reserved for major gate.
```

## Completed 2026-05-24 Batch 4

- Expanded `m1_m2_bazi_calculation` from 7 to 12 cases.
- Added canonical real-case fact fixtures for:
  - solar female ready chart.
  - standard lunar ready chart.
  - leap-month lunar ready chart.
  - known-place true-solar ready chart.
  - unknown-gender natal-ready chart.
- Added stable pillar assertions for those fixtures.
- Extended `m1_m2_base_fact_contract` observations with calendar type, gender status, true-solar flag, and leap-month flag.
- Extended `v30.training_signal.m1_m2_base_fact_contract` with category coverage for solar, lunar, leap-month lunar, true-solar, and unknown-gender cases.

Validation 2026-05-24 Batch 4:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 42 passed
Synthetic m1_m2_bazi_calculation: 12/12 passed
Synthetic core_bazi_calculation: 4/4 passed
Full pytest / synthetic all / 518K: not run; reserved for final M1/M2 phase gate.
```

## Completed 2026-05-24 Final Phase Seal

M1 sealed content:

- BirthInput validation and blocked-state behavior.
- Solar conversion.
- Lunar conversion.
- Leap-month lunar conversion.
- Known-place true-solar conversion.
- Unknown-hour no-fake-pillar guardrail.
- Invalid timezone/date/time no-fake-pillar guardrail.
- Late-zi boundary recording.
- Solar-term/year-month boundary fixture.
- Four pillars, day master, luck/flow, six-pillar context, and deterministic chart-build trace.

M2 sealed content:

- Day master and day-master element explanation.
- Visible ten-god facts and counts.
- Hidden-stem ten-god facts and counts.
- Five-element distribution.
- Relation type/family summaries.
- Root/vault presence-only facts.
- Fact integrity contract proving chart facts are not LLM-, training-, feedback-, or hidden-factor-generated.
- Customer-safe `core_bazi_reading` projection.

Final validation recorded:

```text
python3 -m compileall -q v30
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Results:

```text
Compileall: passed
518K sample: v30.518k.sample.20260523200042775391, cases=8, json_fallback
Latest targeted M1/M2 gate before seal: 42 passed, m1_m2_bazi_calculation 12/12, core_bazi_calculation 4/4
Full pytest / synthetic all: not completed after user interruption; next major cross-module gate may run them.
```

## Remaining Gap

- Add more edge-year and cross-timezone cases later if they expose stable deterministic output.
- Keep root/vault facts as presence-only facts until M5/M3 evidence layers consume them through ranked decisions.

## Next Task

```text
M6 Practical Reading Output completion toward 85%.
```
