# V30 M6 Practical Reading Output Completion Plan

Updated: 2026-05-24

## Purpose

M6 is the practical reading output layer. It turns the core calculation spine into customer-readable but evidence-bound readings for career, wealth, relationship, health/stress, and timing/stage review.

M6 consumes M1/M2 chart facts, M3 evidence/rule/structure paths, M4 model-signal bands, and M5 ranked candidates. It must not mutate four pillars, luck/flow facts, chart facts, ranked candidates, or model raw scores.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M6 Practical Reading Output | 85% | 85% | Phase sealed: career, wealth, relationship, health, and timing readings expose customer summaries plus calculation basis, module dependencies, M5 decision links, M4 model-signal bands, evidence ids, explanation units, boundary conditions, blocked claims, and quality contracts. |

## Completion Scope

- `v30.practical_domain_reading.v2` is active for career, wealth, relationship, health, and timing.
- `v30.practical_domain_calculation_basis.v1` records day master, element distribution keys, root/vault boundary, structure state, path score, and timing context.
- `v30.practical_model_signal_context.v1` exposes model-signal bands and alerts, not raw energy/stability/volatility scores.
- Domain readings link to M5 strength, structure, and useful-god ranked decisions.
- Domain readings carry evidence ids, explanation units, boundary conditions, blocked claims, and quality contracts.
- Health remains stress/routine review, not medical advice.
- Timing remains stage review, not fixed event prediction.

## Synthetic And Training

- Existing tier: `practical_reading`.
- New contract tier: `m6_practical_reading_contract`.
- `v30.training_signal.practical_reading_quality` now tracks calculation-basis, ranked-link, model-signal, evidence, blocked-claim, and explanation-unit coverage.
- Training may tune domain ranking, expression strategy, and question strategy.
- Training must not mutate chart facts, deterministic time facts, ranked candidates, or model raw scores.

## Validation 2026-05-24 Final Seal

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier practical_reading
v30.synthetic.practical_reading: passed (1/1)
python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (14/14)
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m6_practical_reading_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
3 passed
pytest -q tests/unit/test_presentation_projection.py
6 passed
pytest -q tests/test_v30_scaffold.py
8 passed
```

## Remaining Gap

M6 is phase sealed for the current runtime contract. Wording and domain emphasis should continue to be calibrated through M7 real-case replay before any broad release gate.

## Next Task

```text
M7 Core Calculation Validation / Real-case Calibration completion toward 90%.
```
