# V30 Controlled Release Readiness Plan

Updated: 2026-06-13

## Purpose

This plan records the controlled release-boundary readiness track after core modules, RBD, and synthetic canonical calibration have entered steady/wait states.

REL-S1 is not external release approval. It is a targeted readiness review that confirms the system can enter a controlled trial boundary while keeping full pytest, full 518K, live LLM, real-env smoke, and pointer promotion explicit-only.

## Principles

- Do not reopen M1-M8 without concrete failed evidence.
- Do not introduce unverifiable real-person Bazi truth labels.
- Do not run full pytest, synthetic all, full 518K, live LLM, or real-env smoke by default.
- Do not promote policy pointers or mutate chart facts.
- Treat external release as a later explicit operator decision.

## Mainline Tasks

### REL-S1 Controlled Release-Boundary Readiness Review

Status: Completed.

Implemented:

- New readiness artifact: `v30.controlled_release_readiness.v1`.
- Aggregates:
  - SCAL-S3-WAIT synthetic canonical trigger status.
  - SCAL-S3 synthetic canonical steady gate.
  - RBD steady-state status.
  - Backend API Bazi journey acceptance.
  - Runtime configuration summary.
- Confirms controlled trial readiness.
- Keeps external release disabled.

Validation:

```text
python3 -m compileall -q v30/validation/controlled_release_readiness.py scripts/run_controlled_release_readiness.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_controlled_release_readiness.py tests/unit/test_synthetic_canonical_await_trigger.py
7 passed

python3 scripts/run_controlled_release_readiness.py
v30.controlled_release_readiness.v1: passed (6/6) rel_s1_controlled_release_readiness_ready
controlled_trial_ready=True external_release_ready=False next=REL-S2
```

REL-S1 verifies:

- Synthetic canonical gate is frozen and waiting without active trigger.
- RBD is steady for current scope.
- Backend API journey can create a reading, project user/admin views, answer a question, preserve interaction state, and expose history.
- Runtime config remains V30-scoped.
- Heavy and live gates are not run by default.
- External release remains false.

### REL-S2 Explicit Release Gate Authorization Decision

Status: Completed.

Implemented:

- New authorization artifact: `v30.explicit_release_gate_authorization.v1`.
- Default decision: `authorize_stage_a`.
- Authorized pending execution:
  - `controlled_release_readiness`
  - `synthetic_all`
  - `518k_sample`
  - `518k_shard`
- Deferred:
  - `full_pytest`
  - `live_llm_smoke`
  - `real_env_smoke`
  - `full_518k`
- No gate is executed by REL-S2.
- External release remains disabled.

Scope:

- Decide whether to explicitly run any major gate:
  - synthetic all
  - 518K sample/shard
  - real-env smoke
  - live LLM smoke
  - full pytest
  - full 518K
- Keep policy pointer promotion as a separate explicit decision.
- Keep external release disabled unless operator approval and required evidence are recorded.

Validation:

```text
python3 -m compileall -q v30/validation/explicit_release_gate_authorization.py scripts/run_explicit_release_gate_authorization.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_explicit_release_gate_authorization.py tests/unit/test_controlled_release_readiness.py
7 passed

python3 scripts/run_explicit_release_gate_authorization.py
v30.explicit_release_gate_authorization.v1: rel_s2_stage_a_gates_authorized_pending_execution
authorized_gate_ids=controlled_release_readiness,synthetic_all,518k_sample,518k_shard
deferred_gate_ids=full_pytest,live_llm_smoke,real_env_smoke,full_518k
runs_triggered=False external_release_allowed=False next=REL-S3
```

### REL-S3 Execute Stage-A Authorized Release Gates

Status: Completed.

Implemented:

- New execution artifact: `v30.stage_a_release_gate_execution.v1`.
- Executes only REL-S2-authorized Stage-A gates.
- Records gate summaries for controlled readiness, synthetic all, 518K sample, and 518K shard.
- Keeps full pytest, live LLM smoke, real-env smoke, full 518K, external release, and pointer promotion disabled.

Scope:

- Execute only gates authorized by REL-S2:
  - `python3 scripts/run_controlled_release_readiness.py`
  - `python3 scripts/run_synthetic_validation.py --tier all`
  - `python3 scripts/run_518k_validation.py --mode sample --limit 8`
  - `python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16`
- Record pass/fail evidence.
- Do not run full pytest, live LLM smoke, real-env smoke, or full 518K in REL-S3.
- Do not promote pointers or authorize external release.

Validation:

```text
python3 -m compileall -q v30/validation/stage_a_release_gate_execution.py scripts/run_stage_a_release_gate_execution.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_stage_a_release_gate_execution.py tests/unit/test_explicit_release_gate_authorization.py
7 passed

python3 scripts/run_stage_a_release_gate_execution.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.stage_a_release_gate_execution.v1: rel_s3_stage_a_gates_passed
passed=4/4
controlled_release_readiness=completed
synthetic_all=passed
518k_sample=eligible
518k_shard=eligible
external_release_allowed=False next=REL-S4
```

### REL-S4 Stage-A Evidence Review And External-Release Hold

Status: Completed.

Implemented:

- New evidence review artifact: `v30.stage_a_evidence_review.v1`.
- Reviews REL-S3 Stage-A pass evidence.
- Confirms controlled trial readiness only.
- Keeps external release on hold.
- Selects return to core-module mainline selection instead of expanding release gates.

Scope:

- Review REL-S3 pass evidence.
- Keep external release on hold.
- Decide whether to return to core-module targeted work or explicitly authorize additional heavy/live gates.
- Keep full pytest, live LLM smoke, real-env smoke, full 518K, and pointer promotion deferred unless separately authorized.

Validation:

```text
python3 -m compileall -q v30/validation/stage_a_evidence_review.py scripts/run_stage_a_evidence_review.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_stage_a_evidence_review.py tests/unit/test_stage_a_release_gate_execution.py
6 passed

python3 scripts/run_stage_a_evidence_review.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.stage_a_evidence_review.v1: rel_s4_stage_a_evidence_review_complete_external_release_held
reviewed_gate_ids=controlled_release_readiness,synthetic_all,518k_sample,518k_shard
blockers=none
external_release_allowed=False
return_to_core_module_mainline=True
next=MCR3
```

### MCR3 Return To Core Module Mainline Selection

Status: Completed.

Implemented:

- New selector artifact: `v30.core_mainline_selection_after_release_hold.v1`.
- Uses REL-S4 release-hold evidence without rerunning Stage-A by default.
- Rechecks main-module readiness.
- Selects the next core business module task by direct Bazi measurement impact.
- Keeps external release and heavy/live gates deferred.

Scope:

- Return from controlled-release boundary to core-module targeted work.
- Use REL-S4 evidence as the current release hold baseline.
- Select the next core business module task by impact on Bazi measurement quality.
- Keep full pytest, live LLM smoke, real-env smoke, full 518K, external release, and pointer promotion deferred unless separately authorized.

Validation:

```text
python3 -m compileall -q v30/validation/core_mainline_selection_after_release_hold.py scripts/run_core_mainline_selection_after_release_hold.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_core_mainline_selection_after_release_hold.py tests/unit/test_stage_a_evidence_review.py
7 passed

python3 scripts/run_core_mainline_selection_after_release_hold.py
v30.core_mainline_selection_after_release_hold.v1: mcr3_core_mainline_selected
selected=SYN-CAL1 Synthetic Archetype Rule-Claim Calibration
track=m3_m5_m6_measurement_quality
blockers=none
external_release_allowed=False
full_pytest_run_now=False
```

### SYN-CAL1 Synthetic Archetype Rule-Claim Calibration

Status: Completed.

Implemented:

- New calibration artifact: `v30.synthetic_archetype_rule_claim_calibration.v1`.
- Four synthetic archetypes cover metal/resource pressure, wood/output conflict, fire/resource review, and water/timing balance.
- Each archetype validates:
  - M3 claim domains and dynamic mechanisms.
  - M5 strength and useful-god ranked candidates.
  - M6 practical domain claims and Bazi-specific summaries.
  - RBD graph/claim trace and overclaim boundaries.

Scope:

- Build verifiable synthetic typical Bazi archetypes instead of unverifiable real-person truth labels.
- Validate M3 rules, portraits, features, dynamic paths, M5 ranked decisions, and M6 practical claims together.
- Route failures to calibration queues without chart-fact mutation, real-person labels, auto-apply training, or pointer promotion.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_archetype_rule_claim_calibration.py scripts/run_synthetic_archetype_rule_claim_calibration.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_archetype_rule_claim_calibration.py tests/unit/test_core_mainline_selection_after_release_hold.py
7 passed

python3 scripts/run_synthetic_archetype_rule_claim_calibration.py
v30.synthetic_archetype_rule_claim_calibration.v1: syn_cal1_archetype_rule_claim_calibration_ready
cases=4/4
failed_case_ids=none
queue_items=0
external_release_allowed=False
next=SYN-CAL2
```

### SYN-CAL2 Synthetic Archetype Calibration Queue And Tier Registration

Status: Completed.

Implemented:

- Registered `synthetic_archetype_rule_claim` in `SYNTHETIC_SUITES`.
- New registration artifact: `v30.synthetic_archetype_tier_registration.v1`.
- New CLI: `python3 scripts/run_synthetic_archetype_tier_registration.py`.
- The tier remains targeted and is not a default full/release gate.

Scope:

- Register SYN-CAL1 as a targeted synthetic tier.
- Connect failed archetype rows to read-only calibration queues.
- Keep real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release forbidden.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_case.py v30/validation/synthetic_archetype_tier_registration.py scripts/run_synthetic_archetype_tier_registration.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_archetype_tier_registration.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py
7 passed

python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim
v30.synthetic.synthetic_archetype_rule_claim: passed (4/4)

python3 scripts/run_synthetic_archetype_tier_registration.py
v30.synthetic_archetype_tier_registration.v1: syn_cal2_tier_registration_ready
passed=6/6
queue_items=0
external_release_allowed=False
next=SYN-CAL3
```

### SYN-CAL3 Synthetic Archetype Training Signal Review

Status: Completed.

Implemented:

- New training signal review artifact: `v30.synthetic_archetype_training_signal_review.v1`.
- New CLI: `python3 scripts/run_synthetic_archetype_training_signal_review.py`.
- Produces four review-only training signals:
  - M3 archetype rule/claim coverage.
  - M5 ranked candidate alignment.
  - M6 practical claim specificity.
  - M3/M5/M6 boundary safety.

Scope:

- Derive review-only training signals from archetype outcomes.
- Route signal targets to M3/M5/M6 calibration only.
- Keep chart facts, auto-apply training, pointer promotion, real-person truth labels, and external release disabled.

Validation:

```text
python3 -m compileall -q v30/validation/synthetic_archetype_training_signal_review.py scripts/run_synthetic_archetype_training_signal_review.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_archetype_training_signal_review.py tests/unit/test_synthetic_archetype_tier_registration.py
6 passed

python3 scripts/run_synthetic_archetype_training_signal_review.py
v30.synthetic_archetype_training_signal_review.v1: passed (6/6) syn_cal3_training_signal_review_ready
signals=4
queue_items=0
auto_apply=False
next=SYN-CAL4
```

### SYN-CAL4 Synthetic Archetype Calibration Closeout

Status: Complete.

Scope:

- Freeze SYN-CAL1 to SYN-CAL3 evidence into mainline docs.
- Define routine cadence for `synthetic_archetype_rule_claim` and SYN-CAL3 signal review.
- Keep queue items review-only until explicit calibration work is selected.

Latest result:

```text
python3 -m compileall -q v30/validation/synthetic_archetype_calibration_closeout.py scripts/run_synthetic_archetype_calibration_closeout.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_archetype_calibration_closeout.py tests/unit/test_synthetic_archetype_training_signal_review.py tests/unit/test_synthetic_archetype_tier_registration.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py
11 passed

python3 scripts/run_synthetic_archetype_calibration_closeout.py
v30.synthetic_archetype_calibration_closeout.v1: passed (6/6) syn_cal4_synthetic_archetype_calibration_closed
signals=4 queue_items=0 auto_apply=False full_pytest=False
next=CORE-CAL-S0
```

Routine cadence:

- `python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim`
- `python3 scripts/run_synthetic_archetype_training_signal_review.py`
- `python3 scripts/run_synthetic_archetype_calibration_closeout.py`

Next:

```text
CORE-CAL-S0 Core Calibration Steady-State Queue
```

### CORE-CAL-S0 Core Calibration Steady-State Queue

Status: Complete.

Scope:

- Add `v30.core_calibration_steady_state_queue.v1`.
- Bind SYN-CAL4 closeout and W-S1 await-evidence status into the current mainline gate.
- Define steady-state cadence and focused-evidence-only module reopen policy.
- Keep heavy gates and live provider checks explicit-only.

Latest result:

```text
python3 -m compileall -q v30/validation/core_calibration_steady_state_queue.py scripts/run_core_calibration_steady_state_queue.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_core_calibration_steady_state_queue.py
3 passed

pytest -q tests/unit/test_core_calibration_steady_state_queue.py tests/unit/test_synthetic_archetype_calibration_closeout.py tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_ready tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_blocks_candidates_or_queue_gap tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_blocks_missing_sources_or_heavy_gate tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_ready tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_reports_focused_candidates tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_blocks_core_or_queue_gap tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_blocks_heavy_default_gate
12 passed
```

Next:

```text
CORE-CAL-WAIT Await Focused Calibration Evidence Or Explicit Major Validation
```

## Boundary

REL-S1 permits controlled trial readiness only. REL-S2 authorizes Stage-A gate execution only. REL-S3 records Stage-A pass evidence only. REL-S4 holds external release and returns to core-module mainline selection. None of these steps authorize external release, live provider calls, chart-fact mutation, automatic training, full pytest, full 518K, or pointer promotion.
