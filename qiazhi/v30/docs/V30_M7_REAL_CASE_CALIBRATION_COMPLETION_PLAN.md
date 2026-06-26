# V30 M7 Core Calculation Validation / Real-case Calibration Completion Plan

Updated: 2026-05-24

## Purpose

M7 is the cross-module validation and calibration layer for the core Bazi calculation chain. It verifies that M1 through M6 work together on canonical real-case fixtures without hard-coding final fortune conclusions.

M7 validates:

- BirthInput and deterministic chart facts.
- base Bazi fact explanation and root/vault boundaries.
- luck-cycle, flow-year/month, and six-pillar context.
- M4 ten-god model-signal bands and no raw-score exposure.
- M5 strength, structure, and useful-god ranked candidates.
- M6 practical reading output boundaries.
- no fake pillars for pending or blocked inputs.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M7 Core Calculation Validation / Real-case Calibration | 90% | 90% | Phase sealed: `real_case_calibration_pack` now has 30 canonical fixtures and validates chart facts, timing context, model signals, ranked decisions, practical reading contracts, blocked/pending guardrails, training extraction, synthetic all, and 518K sample distribution gate. |

## Fixture Coverage

- solar ready cases.
- lunar ready cases.
- leap-month lunar cases.
- true-solar known-place cases.
- unknown-hour pending cases.
- unknown-gender natal-only cases.
- invalid date/time blocked cases.
- solar-term and year-edge boundary cases.
- M5 weak, slightly weak, balanced, strong, follow-structure, disputed-structure, late-zi, and disputed useful-god cases.
- M6 career, wealth, relationship, health, and timing output-boundary cases.

## Training And Validation Contract

- `v30.training_signal.real_case_calibration_pack` now observes 30 canonical fixtures.
- The signal tracks category coverage, ready/pending/blocked counts, no-fake-fact count, model-signal readiness, ranked-decision readiness, score-floor readiness, ranked-basis signals, six-pillar readiness, M6 practical contract readiness, M6 practical domain contract count, and raw-score leak count.
- Training may tune validation priorities, replay emphasis, reading expression, and candidate scoring review thresholds.
- Training must not mutate deterministic chart facts, luck/flow facts, pillars, ranked candidates, or model raw scores.

## Validation 2026-05-24 Final Seal

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (30/30)
python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (30/30)
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_synthetic_validation.py::test_synthetic_m6_practical_reading_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
4 passed
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260524025228337725: eligible, cases=8, json_fallback
```

## Remaining Gap

M7 is phase sealed for the current canonical pack. Future work should add real production replay metadata when available, but current runtime and training gates now have enough canonical coverage for the next module.

## Next Task

```text
M8 User Presentation / API Projection completion toward 90%.
```
