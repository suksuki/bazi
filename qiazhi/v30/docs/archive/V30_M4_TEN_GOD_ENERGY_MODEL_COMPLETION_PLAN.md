# V30 M4 Ten-god Energy Model Completion Plan

Updated: 2026-05-24

## Purpose

This is the dedicated completion plan for M4, the Ten-god Energy Model. M4 converts deterministic M1/M2 chart facts into bounded model signals for M5 ranked decisions, M6 practical readings, answer context, diagnostics, synthetic validation, and training.

M4 is not a chart-fact module and not a verdict module. It must not create four pillars, mutate chart facts, or output fixed strength, fixed structure pattern, fixed useful-god, personality, event, wealth, career, relationship, or health conclusions.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M4 Ten-god Energy Model | 88% | 88% | Phase sealed: energy/stability/volatility model, bounded `model_signal_summary`, interface contract, calibration profile, M5 fusion, calibration tier, real-case replay tier, training signal, and auto-training weights are active. |

## A-E Completion Path

### A. Module Content

- Compute ten-god energy from deterministic visible stems, hidden stems, luck, flow year, and flow month.
- Track energy, stability, volatility, confidence, source IDs, modifiers, dominant ten gods, high-volatility ten gods, low-stability ten gods, and interaction matrix.
- Keep raw scores internal to diagnostics/training; customer and ranked-decision interfaces receive bands and alerts only.

### B. Interface Contract

- `TenGodEnergyModel` remains the internal full diagnostic object.
- `ten_god_energy_summary` is the bounded runtime summary.
- `model_signal_summary` is the stable consumer interface.
- Allowed consumers: structure selector, ranked decisions, answer context, training signals, and admin diagnostics.
- Forbidden in consumer-facing summary: raw weight, raw score, numeric energy, numeric stability, numeric volatility.

### C. Calibration And Replay

- Dedicated synthetic calibration tier: `ten_god_energy_calibration`.
- Dedicated real-case replay tier: `m4_ten_god_real_case_replay`.
- Replay categories: solar, lunar, leap-month lunar, true-solar, output/wealth/authority, resource/authority, self/resource, and mixed-family cases.
- Replay validates distribution and interface readiness only; it does not promote production threshold changes.

### D. Training

- `v30.training_signal.ten_god_energy_fusion` must include family coverage, band counts, calibration case count, real-case replay count, interface readiness, and replay family coverage.
- Auto-training may emit conservative structure-policy weights for model-signal fusion, family coverage, energy-band calibration, stability review, and volatility review.
- M4 training cannot mutate chart facts or produce fixed decisions.

### E. Gate

Subtask gate:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
python3 scripts/run_synthetic_validation.py --tier m4_ten_god_real_case_replay
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py tests/unit/test_synthetic_validation.py
```

Major cross-module gate is deferred to the next module milestone.

## Completed 2026-05-24 Batch 1

- Added `v30.model_signal_interface_contract.v1` to `model_signal_summary`.
- Added `v30.model_signal_calibration_profile.v1` with family coverage and band counts.
- Added `m4_ten_god_real_case_replay` synthetic tier with five canonical replay cases.
- Added `m4_ten_god_real_case_replay` observations that validate status, consumer interface, raw-score hiding, forbidden-field leakage, and ranked-decision domain readiness.
- Extended `v30.training_signal.ten_god_energy_fusion` with real-case replay count, interface-ready count, and replay family coverage.
- Extended conservative auto-training model-signal weights to account for replay coverage.

Validation 2026-05-24 Batch 1:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
python3 scripts/run_synthetic_validation.py --tier m4_ten_god_real_case_replay
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py::test_synthetic_m4_ten_god_real_case_replay_tier_passes
pytest -q tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
```

Results:

```text
Compileall: passed
Synthetic ten_god_energy_calibration: 5/5 passed
Synthetic m4_ten_god_real_case_replay: 5/5 passed
M4 interface/unit synthetic tests: 7 passed
Training signal extraction test: 1 passed
Auto-apply structure policy test: 1 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the next cross-module major gate.
```

## Remaining Gap

- Do not change production thresholds until more non-synthetic replay evidence is available.
- Keep `model_signal_policy` as a future split decision; current tuning remains under `structure_policy.weights`.

## Next Task

```text
M5 Strength / Structure / Useful-god Ranked Decisions final seal toward 88%.
```
