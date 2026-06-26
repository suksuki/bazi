# V30 Synthetic Canonical Bazi Calibration Plan

Updated: 2026-06-13

## Purpose

This plan replaces unverifiable "real Bazi truth" calibration with synthetic canonical Bazi structures.

The goal is to validate whether the current M3/M4/M5/M6/IQ/RBD spine can recognize typical Bazi structures, generate traceable paths and claims, and surface useful question strategy without polluting the system with unprovable biography labels.

## Principles

- Do not use real-person life outcomes as truth labels.
- Do not write fixed destiny verdicts into cases.
- Do not mutate four pillars, luck cycles, flow-year/month, or deterministic chart facts.
- Do not auto-apply training or promote policy pointers from synthetic failures.
- Validate structure expectations only: domains, RBD paths, rules, portraits, claims, traceability, safety, and question readiness.

## Mainline Tasks

### SCAL-S1 Synthetic Canonical Bazi Case Pack And Calibration Review

Status: Completed.

Implemented:

- New synthetic tier: `synthetic_canonical_bazi_calibration`.
- Six canonical synthetic cases:
  - wealth/timing flow over 庚 day master
  - career/officer-pressure over 甲 day master
  - resource/fire balance over 丁 day master
  - earth/structure over 戊 day master
  - water/timing over 壬 day master
  - hidden-factor feedback over 庚 day master
- New review artifact: `v30.synthetic_canonical_bazi_calibration_review.v1`.
- Failed canonical expectations become read-only calibration queue items.
- No real-person truth, no chart-fact mutation, no auto-apply training, no pointer promotion.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_case.py v30/validation/synthetic_canonical_bazi_calibration_review.py scripts/run_synthetic_canonical_bazi_calibration_review.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_canonical_bazi_calibration_review.py tests/unit/test_synthetic_validation.py::test_synthetic_real_bazi_diagnosis_tier_passes
4 passed

python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
v30.synthetic.synthetic_canonical_bazi_calibration: passed (6/6)

python3 scripts/run_synthetic_canonical_bazi_calibration_review.py
v30.synthetic_canonical_bazi_calibration_review.v1: passed (6/6) scal_s1_synthetic_canonical_calibration_ready
cases=6/6 queue_items=0 next=SCAL-S2
```

### SCAL-S2 Synthetic Canonical Pack Expansion Or Cadence Decision

Status: Completed.

Implemented:

- Expanded canonical pack from 6 to 16 synthetic cases.
- Added 10 structural expansion families:
  - 财多身弱
  - 食伤生财
  - 官杀混杂
  - 印比过重
  - 财官印相生
  - 寒热燥湿偏枯
  - 刑冲合害明显
  - 从强/从弱候选边界
  - 大运触发结构变化
  - 流年触发领域主题
- New decision artifact: `v30.synthetic_canonical_pack_decision.v1`.
- Failed expectations remain read-only calibration candidates.
- Full pytest, synthetic all, full 518K, chart-fact mutation, auto-apply training, and pointer promotion remain explicit/non-default.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_case.py v30/validation/synthetic_canonical_pack_decision.py scripts/run_synthetic_canonical_pack_decision.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_canonical_pack_decision.py tests/unit/test_synthetic_canonical_bazi_calibration_review.py
6 passed

python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
v30.synthetic.synthetic_canonical_bazi_calibration: passed (16/16)

python3 scripts/run_synthetic_canonical_pack_decision.py
v30.synthetic_canonical_pack_decision.v1: passed (6/6) scal_s2_expanded_canonical_pack_cadence_ready
cases=16 families=10 next=SCAL-S3
```

### SCAL-S3 Synthetic Canonical Calibration Steady State

Status: Completed.

Implemented:

- Freeze the expanded 16-case canonical pack as the routine calibration gate.
- Define when to run it:
  - after RBD rule/path/portrait/claim changes
  - after M3 knowledge/rule/portrait changes
  - after M5 ranked-decision scoring changes
  - after IQ question-strategy changes
  - before release-boundary validation
- Route failures to read-only calibration review.
- Do not introduce real-person truth labels.
- New steady-state artifact: `v30.synthetic_canonical_steady_state.v1`.
- Next state is `SCAL-S3-WAIT`.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_canonical_steady_state.py scripts/run_synthetic_canonical_steady_state.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_canonical_steady_state.py tests/unit/test_synthetic_canonical_pack_decision.py
5 passed

python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
v30.synthetic.synthetic_canonical_bazi_calibration: passed (16/16)

python3 scripts/run_synthetic_canonical_steady_state.py
v30.synthetic_canonical_steady_state.v1: passed (6/6) scal_s3_synthetic_canonical_steady_state_ready
cases=16 families=10 next=SCAL-S3-WAIT
```

### SCAL-S3-WAIT Synthetic Canonical Calibration Await Trigger

Status: Active wait state recorded.

Run the frozen gate after:

- RBD rule/path/portrait/claim changes
- M3 knowledge/rule/portrait changes
- M5 ranked-decision scoring changes
- IQ question-strategy changes
- before release-boundary validation

Default validation:

```text
python3 scripts/run_synthetic_canonical_await_trigger.py
python3 scripts/run_synthetic_canonical_steady_state.py
python3 scripts/run_synthetic_canonical_pack_decision.py
python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
pytest -q tests/unit/test_synthetic_canonical_await_trigger.py
```

Latest result:

```text
python3 -m compileall -q v30/validation/synthetic_canonical_await_trigger.py scripts/run_synthetic_canonical_await_trigger.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_canonical_await_trigger.py tests/unit/test_synthetic_canonical_steady_state.py
6 passed

python3 scripts/run_synthetic_canonical_await_trigger.py
v30.synthetic_canonical_await_trigger.v1: passed (4/4) scal_s3_await_trigger_ready waiting=True run_required=False next=Await Synthetic Canonical Trigger
```

## Routine Cadence

Run SCAL tier:

```text
python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
python3 scripts/run_synthetic_canonical_await_trigger.py
python3 scripts/run_synthetic_canonical_steady_state.py
python3 scripts/run_synthetic_canonical_pack_decision.py
python3 scripts/run_synthetic_canonical_bazi_calibration_review.py
```

Major-node explicit-only:

```text
python3 scripts/run_synthetic_validation.py --tier all
pytest -q
python3 scripts/run_518k_validation.py --mode full --confirm-full
```

## Boundary

Synthetic canonical calibration validates the diagnosis engine, not life truth. It can surface rule/path/portrait/question gaps, but it cannot directly alter deterministic chart facts or promote runtime policy.
