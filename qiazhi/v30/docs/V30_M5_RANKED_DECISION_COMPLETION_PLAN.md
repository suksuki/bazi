# V30 M5 Strength / Structure / Useful-god Ranked Decision Completion Plan

Updated: 2026-06-11

## Purpose

This is the dedicated completion plan for M5, the ranked decision layer. M5 consumes M1/M2 deterministic facts, M3 evidence/rules/structure paths, and M4 model signals to produce bounded candidates for:

- strength.
- structure pattern.
- useful-god.

M5 is not a chart-fact module and not a fixed-verdict module. It must not mutate four pillars, luck/flow facts, hidden factors, or model-signal raw scores. It must rank candidates with evidence, counter-evidence, unresolved requirements, scoring basis, and explicit boundaries.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M5 Ranked Decisions | 88% | 88% | Phase sealed: candidate scores, scoring basis, model-signal fusion, follow/disputed/regulation candidates, real-case fixtures, replay weights, useful-god evidence calibration, M1/M2 root/vault consumption, M4 interface/calibration consumption, and no-raw-score contract are active. |

## A-E Completion Path

### A. Module Content

- Strength candidates: strong, slightly strong, balanced, slightly weak, weak.
- Structure candidates: ordinary, dynamic, follow-structure boundary, special-structure boundary, regulation/climate boundary, disputed structure, mediation path.
- Useful-god candidates: balance, resource/self support, output/wealth release, authority regulation, climate regulation.
- Each decision must expose primary candidate, alternatives, candidate scores, scoring basis, confidence, supporting evidence, weakening evidence, unresolved requirements, and boundary.

### B. Interfaces

- Inputs:
  - M1/M2 chart facts and root/vault presence-only facts.
  - M3 evidence, rule, and structure path signals.
  - M4 `model_signal_summary`, `v30.model_signal_interface_contract.v1`, and `v30.model_signal_calibration_profile.v1`.
- Outputs:
  - `RankedDecision` payloads for strength, structure pattern, and useful-god.
  - No fixed strength verdict, fixed 格局 verdict, fixed 用神 verdict, or raw score exposure.

### C. Synthetic / Replay

- Existing tier: `strength_structure_useful_god`.
- Existing real-case tier: `real_case_calibration_pack`.
- New contract tier: `m5_ranked_decision_contract`.
- Replay validates candidate shape, score floors, basis signals, M4 interface consumption, M1/M2 root/vault consumption, and no raw-score leakage.

### D. Training

- `v30.training_signal.m5_weight_replay` remains the M5 replay signal.
- Training can tune candidate weights and score floors.
- Training cannot promote fixed useful-god, fixed structure, or deterministic chart facts.
- M4 model-signal interface and calibration profile may influence candidate weights only through bounded policy candidates.

### E. Gate

Subtask gate:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
```

## Completed 2026-05-24 Final Seal

- Added `m5_ranked_decision_contract` synthetic tier.
- Extended M5 scoring basis with:
  - M4 model-signal interface version.
  - M4 model-signal allowed consumers.
  - M4 forbidden raw-score fields.
  - M4 calibration profile version and family coverage.
  - M1/M2 root/vault fact summary version, root counts, and root/vault boundary.
- Extended ranked-decision `model_signal_summary` decision input with interface and calibration profile versions.
- Added tests proving M5 consumes M4 interface and M1/M2 root/vault facts while remaining candidate-bound and raw-score-free.

## Validation 2026-05-24 Final Seal

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
v30.synthetic.strength_structure_useful_god: passed (1/1)
python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (14/14)
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (14/14)
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
3 passed
pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
1 passed
```

## 2026-06-11 H1 Evidence Consumption Hardening

After M3-G1 through M3-G6 closed the source-governed M3 evidence flow, M5-H1 verifies that ranked decisions consume the sealed M3 evidence spine.

Added:

- `v30.m5_evidence_consumption_hardening.v1`
- CLI: `python3 scripts/run_m5_evidence_consumption_hardening.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/evidence-consumption-hardening`

H1 checks:

- M3-G6 closeout is ready before M5 hardening.
- `strength`, `structure_pattern`, and `useful_god` ranked domains are complete and primary candidates are scored.
- M5 scoring basis consumes M1/M2 root/vault facts and M4 model-signal interface.
- M5 sees M3 source family coverage, K/R/P domain coverage, rule evidence, dynamic path evidence, and M3 completion support.
- Each decision has supporting evidence and fixed-verdict counter-evidence guards.
- M5 remains candidate-bound and raw-score-free.
- M5 contract and strength/structure/useful-god synthetic tiers pass.

Validation 2026-06-11:

```text
python3 -m compileall -q v30 scripts/run_m5_evidence_consumption_hardening.py
passed

pytest -q tests/unit/test_m5_evidence_consumption_hardening.py tests/unit/test_m3_source_backlog_closeout.py tests/unit/test_practical_reading_context.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
10 passed

python3 scripts/run_m5_evidence_consumption_hardening.py --sample-limit 8
v30.m5_evidence_consumption_hardening.v1: passed (7/7) m5_evidence_consumption_hardening_ready domains=3 scores=17

python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (30/30)

python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
v30.synthetic.strength_structure_useful_god: passed (1/1)
```

## 2026-06-11 H2 Calibration Replay Review

M5-H2 verifies calibration replay as a read-only review layer before any threshold, score floor, or policy-weight change.

Added:

- `v30.m5_calibration_replay_review.v1`
- CLI: `python3 scripts/run_m5_calibration_replay_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/calibration-replay-review`

H2 checks:

- M5-H1 evidence consumption is ready before replay review.
- M5 contract, strength/structure/useful-god, and real-case calibration tiers pass.
- Replay has enough ranked observations across strength, structure-pattern, and useful-god.
- Candidate score distribution and close-candidate cases are reviewable.
- `v30.training_signal.m5_weight_replay` is present and trains candidate weights only.
- M5 replay remains read-only: no threshold change, no pointer promotion, no fixed verdict, no chart-fact mutation.

Validation 2026-06-11:

```text
python3 -m compileall -q v30 scripts/run_m5_calibration_replay_review.py
passed

pytest -q tests/unit/test_m5_calibration_replay_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

python3 scripts/run_m5_calibration_replay_review.py --sample-limit 8
v30.m5_calibration_replay_review.v1: passed (6/6) m5_calibration_replay_review_ready cases=51 complete=51 close_candidates=51

python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (30/30)

python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
v30.synthetic.strength_structure_useful_god: passed (1/1)

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

## Remaining Gap

- Production threshold changes remain deferred until broader replay evidence exists.
- M5 may later receive more canonical non-synthetic replay, but this is not a blocker for current phase target.
- M5-H3 has closed calibration replay and returned M5 to steady-state support.
- Future threshold review remains explicit-only and is not part of the current mainline.

## 2026-06-11 H3 Calibration Replay Closeout

M5-H3 closes M5 as a ranked-candidate support module for M6, IQ, and training.

Added:

- `v30.m5_calibration_replay_closeout.v1`
- CLI: `python3 scripts/run_m5_calibration_replay_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/calibration-replay-closeout`

H3 checks:

- M5-H2 replay review is ready for closeout.
- M5-H1/H2 lineage is complete.
- Strength, structure-pattern, and useful-god ranked domains have steady replay coverage.
- `v30.training_signal.m5_weight_replay` boundary remains candidate-weight-only.
- Close-candidate monitoring is ready while threshold changes remain deferred.
- No pointer, threshold, fixed-verdict, or chart-fact write occurred.

Validation 2026-06-11:

```text
python3 -m compileall -q v30 scripts/run_m5_calibration_replay_closeout.py
passed

pytest -q tests/unit/test_m5_calibration_replay_closeout.py tests/unit/test_m5_calibration_replay_review.py tests/unit/test_m5_evidence_consumption_hardening.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
15 passed

python3 scripts/run_m5_calibration_replay_closeout.py --sample-limit 8
v30.m5_calibration_replay_closeout.v1: passed (6/6) m5_calibration_replay_closed cases=51 complete=51 close_candidates=51 next=M6 Practical Reading Consumption Hardening

python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (30/30)

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

## Next Task

```text
M6 Practical Reading Consumption Hardening
```
