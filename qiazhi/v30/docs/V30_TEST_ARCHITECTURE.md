# V30 Test Architecture

Updated: 2026-06-10

## Purpose

V30 needs a lighter, more modular, more independent test system than V20.

The goal is not fewer checks. The goal is correct test tiering:

- Fast checks run constantly.
- Integration checks run when the touched module needs them.
- Synthetic validation runs explicitly.
- 518K validation runs in sample, shard, and full modes.
- Release gates compose the tiers without making every local test slow.

## Core Principles

- Default `pytest` must stay fast.
- Tests must not depend on V20 runtime, V20 Redis, V20 DB, or V20 pointer files.
- Unit tests use pure functions and fixtures.
- Integration tests may use local temporary storage.
- Service tests start V30 only.
- Training tests use small deterministic fixtures.
- Synthetic and 518K validation are separate commands.
- Every heavy test needs a tier marker and a reason.

Current BT10 support-system closeout:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_brain_training_synthetic_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_brain_training_synthetic_closeout_endpoint_is_read_only
5 passed in 21.11s
python3 scripts/run_brain_training_synthetic_closeout.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.brain_training_synthetic_closeout.v1: passed (6/6) bt10_support_systems_steady_state_ready
```

BT10 did not run full `pytest -q`, synthetic all, or full 518K. Those remain major-node, release, pointer-promotion, or explicit full-freeze gates.

## Test Tiers

### Tier 0: Guards

Purpose: catch isolation and contract violations.

Examples:

- No runtime import from `v20.*`.
- API prefix is `/api/v30`.
- UI prefix is `/v30/ui`.
- Redis keys start with `v30:`.
- DB tables start with `v30_`.
- Runtime directory is V30-local.

Expected speed: under 1 second.

Default: yes.

### Tier 1: Unit

Purpose: validate pure module behavior.

Examples:

- Ten gods.
- Element relationships.
- Time context expansion.
- Feature evidence construction.
- Rule condition matching.
- Graph scoring helpers.

Expected speed: seconds.

Default: yes.

### Tier 2: Module Integration

Purpose: validate contracts between adjacent modules.

Examples:

- Chart context to feature evidence.
- Feature evidence to structure state.
- Structure state to mainline state.
- Question anchor from mainline state.
- Answer context from selected anchor.

Expected speed: seconds to low tens of seconds.

Default: selective.

### Tier 3: Runtime Smoke

Purpose: validate V30 service and basic loop.

Examples:

- `POST /api/v30/readings`.
- `GET /api/v30/readings/{id}`.
- `GET /api/v30/readings/{id}/view`.
- UI receives `ClientPresentationModel`.

Expected speed: low tens of seconds.

Default: no for pure module work, yes before service changes land.

### Tier 4: Synthetic Smoke

Purpose: validate a small converted synthetic set.

Examples:

- 10 core chart cases.
- 10 structure dynamics cases.
- 10 question anchor cases.
- 10 answer boundary cases.

Expected speed: under a few minutes.

Default: no.

### Tier 5: Training Promotion Validation

Purpose: validate that training candidates can be generated, scored, promoted, auto-applied, and rolled back.

Examples:

- Feature policy promotion.
- Rule policy promotion.
- Structure policy promotion.
- Portrait policy promotion.
- Question policy promotion.
- Answer policy promotion.
- Presentation policy promotion.

Expected speed: minutes.

Default: no.

### Tier 6: 518K Validation

Purpose: validate broad corpus behavior.

Modes:

- `sample`: small representative sample.
- `shard`: one or more selected shards.
- `full`: full 518K validation.

Expected speed: variable.

Default: never.

### Tier 7: Release Gate

Purpose: compose required checks for release or active development target switch.

Includes:

- Tier 0.
- Tier 1.
- Tier 2 selected.
- Runtime smoke.
- Synthetic smoke.
- Training promotion smoke.
- 518K sample.

Default: explicit only.

## Proposed Directory Layout

```text
tests/
  unit/
  integration/
  runtime/
  synthetic/
  training/
  release/
  fixtures/
scripts/
  test_fast.sh
  test_runtime.sh
  run_synthetic_validation.py
  run_training_validation.py
  run_518k_validation.py
  run_release_gate.py
```

## Proposed Commands

Fast local development:

```bash
pytest tests/unit tests/test_v30_scaffold.py
```

Module integration:

```bash
pytest tests/integration
```

Runtime smoke:

```bash
python scripts/test_runtime.sh
```

Synthetic validation:

```bash
python scripts/run_synthetic_validation.py --tier smoke
```

Current status:

- The smoke command is implemented.
- It validates the current runtime spine and boundary expectations.
- It is still lightweight enough for default unit coverage.

Training validation:

```bash
python scripts/run_training_validation.py --family question_policy --tier smoke
```

Current minimal promotion command:

```bash
python3 scripts/promote_policy_candidate.py --family structure_policy --candidate-id <id>
```

## Current Default Coverage

The default `pytest` suite now covers:

- V30 isolation guards.
- Core chart context and evidence spine.
- BirthInput, solar/lunar/known-place true-solar boundaries, unknown-hour handling, luck/flow context, and six-pillar context.
- Ten-god energy model contracts, diagnostics, calibration tier, family coverage, band distributions, and model-signal auto-training weights.
- Strength, structure, and useful-god ranked decision boundaries, including candidate scores, scoring basis, M5 real-case score-floor calibration, follow/disputed structure candidates, ranked-basis signals, and replay weights.
- Question anchor selection.
- Question dialogue graph, structured options, selected-option persistence, `known_user_signals`, and graph-selected next question.
- Customer reading surface projection and role-gated internal Bazi context.
- Bounded LLM answer fallback/acceptance metadata without requiring a live provider.
- Runtime pointer promotion.
- Runtime repository reading persistence.
- Runtime repository trace persistence.
- Postgres repository SQL/payload boundary with fake connection.
- Redis reading and trace cache round trip.
- Auto-apply training updates active runtime pointers.
- Runtime traces report auto-applied policy versions.
- Runtime traces expose adaptive question replay diagnostics for central-brain/question-policy decisions.
- Training tests cover adaptive question replay signals and bounded question-policy candidate weights.
- Policy tests cover active-vs-candidate question-policy comparison artifacts.
- Hidden factor probes stay hypothesis-only and require dialogue feedback.
- Locale/client presentation projection covers zh/en/ko and web/mobile/admin profiles.
- 518K sample/shard/full runner contract is covered without running full corpus by default, including artifact and index persistence.
- 518K artifact search is covered with JSON fallback and fake-Postgres `v30_artifacts` indexing.
- Release gate quick/standard composition is covered without running full corpus by default.
- R6 release artifact review is covered through `ReleaseGateResult.artifact_review` and `GET /api/v30/admin/release/artifact-review`.
- R7 post-seal status review is covered through `v30.post_seal_status_review.v1`, `scripts/run_post_seal_status_review.py`, and `GET /api/v30/admin/release/status-review`.
- R8 production replay intake is covered through `v30.production_replay_intake.v1`, `scripts/run_production_replay_intake.py`, and `GET /api/v30/admin/release/production-replay-intake`.
- R9 replay store/search is covered through `v30.production_replay_store.v1`, `v30.production_replay_search.v1`, and `GET /api/v30/admin/release/production-replay-intake/search`.
- R10 release-candidate review is covered through `v30.release_candidate_review.v1`, `scripts/run_release_candidate_review.py`, and `GET /api/v30/admin/release/candidate-review`.
- R11 standard release-candidate gate review is covered through `v30.release_candidate_gate_review.v1`, `scripts/run_release_candidate_gate_review.py`, and `GET /api/v30/admin/release/candidate-gate-review`.
- R12 release-boundary finalization is covered through `v30.release_boundary_finalization.v1`, `scripts/run_release_boundary_finalization.py`, and `GET /api/v30/admin/release/boundary-finalization`.
- B1 real business Bazi reading acceptance is covered through `v30.real_business_bazi_reading_acceptance.v1`, `scripts/run_real_business_bazi_reading_acceptance.py`, and `GET /api/v30/admin/business/real-bazi-acceptance`.
- B2 business reading regression is covered through `v30.real_business_bazi_reading_regression_pack.v1`, `scripts/run_real_business_bazi_reading_regression_pack.py`, and `GET /api/v30/admin/business/reading-regression-pack`.
- B3 business answer refresh regression is covered through `v30.real_business_answer_refresh_regression.v1`, `scripts/run_real_business_answer_refresh_regression.py`, and `GET /api/v30/admin/business/answer-refresh-regression`.
- B4 boundary/blocked input regression is covered through `v30.real_business_boundary_blocked_input_regression.v1`, `scripts/run_real_business_boundary_blocked_input_regression.py`, and `GET /api/v30/admin/business/boundary-blocked-input-regression`.
- B5 business API contract freeze is covered through `v30.real_business_api_contract_freeze.v1`, `scripts/run_real_business_api_contract_freeze.py`, and `GET /api/v30/admin/business/api-contract-freeze`.
- B6 business acceptance closeout is covered through `v30.real_business_acceptance_closeout.v1`, `scripts/run_real_business_acceptance_closeout.py`, and `GET /api/v30/admin/business/acceptance-closeout`.
- S1 business acceptance steady state is covered through `v30.real_business_steady_state.v1`, `scripts/run_real_business_steady_state.py`, and `GET /api/v30/admin/business/steady-state`.
- BT1 central brain acceptance is covered through `v30.central_brain_acceptance.v1`, `scripts/run_central_brain_acceptance.py`, and `GET /api/v30/admin/brain/acceptance`.
- BT2 central brain session replay is covered through `v30.central_brain_session_replay.v1`, `scripts/run_central_brain_session_replay.py`, and `GET /api/v30/admin/brain/session-replay`.
- BT3 brain failure routing is covered through `v30.brain_failure_route.v1`, `scripts/run_central_brain_failure_routing.py`, and `GET /api/v30/admin/brain/failure-routing`.
- BT4 training system closeout is covered through `v30.training_system_closeout.v1`, `scripts/run_training_system_closeout.py`, and `GET /api/v30/admin/training/system-closeout`.
- BT5 failed-candidate quarantine is covered through `v30.training_candidate_quarantine.v1`, `scripts/run_training_candidate_quarantine.py`, and `GET /api/v30/admin/training/candidate-quarantine`.
- BT6 synthetic coverage manifest is covered through `v30.synthetic_coverage_manifest.v1`, `scripts/run_synthetic_coverage_manifest.py`, and `GET /api/v30/admin/validation/synthetic-coverage-manifest`.
- BT7 central brain synthetic tier is covered through `python3 scripts/run_synthetic_validation.py --tier central_brain` and `tests/unit/test_synthetic_validation.py::test_synthetic_central_brain_tier_passes`.
- BT8 training pipeline synthetic tier is covered through `python3 scripts/run_synthetic_validation.py --tier training_pipeline` and `tests/unit/test_synthetic_validation.py::test_synthetic_training_pipeline_tier_passes_training_contracts`.
- BT9 518K readiness matrix is covered through `v30.518k_readiness_matrix.v1`, `scripts/run_518k_readiness_matrix.py`, and `GET /api/v30/admin/validation/518k/readiness-matrix`.
- API local JSON reading and trace persistence.
- Explicit real environment test for Postgres+Redis runtime loop.

Latest validation baseline:

```text
C8 core-completion freeze baseline, 2026-06-06
python3 -m compileall -q v30
passed

F1 frozen-core calibration baseline, 2026-06-06
pytest -q tests/unit/test_frozen_core_calibration_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_frozen_core_calibration_review_endpoint_is_read_only
4 passed

python3 scripts/run_frozen_core_calibration_review.py
v30.frozen_core_calibration_review.v1: ready_for_targeted_calibration_iteration (tiers=6, signals=31)

F2 targeted calibration candidate review, 2026-06-06
pytest -q tests/unit/test_targeted_calibration_candidate_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_candidate_review_endpoint_is_read_only
4 passed

python3 scripts/run_targeted_calibration_candidate_review.py
v30.targeted_calibration_candidate_review.v1: ready_for_validation_gate_review (candidates=4)

F3 targeted calibration validation gate, 2026-06-06
pytest -q tests/unit/test_targeted_calibration_validation_gate.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_validation_gate_endpoint_is_read_only
4 passed

python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 8
v30.targeted_calibration_validation_gate.v1: ready_for_policy_pointer_review (synthetic=95/95, 518k=8)

F4 targeted calibration pointer review, 2026-06-07
pytest -q tests/unit/test_targeted_calibration_pointer_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_pointer_review_endpoint_is_read_only
4 passed

python3 scripts/run_targeted_calibration_pointer_review.py --sample-limit 8
v30.targeted_calibration_pointer_review.v1: ready_for_explicit_operator_pointer_decision (diffs=4)

F5 explicit operator pointer decision, 2026-06-07
pytest -q tests/unit/test_targeted_calibration_pointer_decision.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_pointer_decision_endpoint_is_read_only
4 passed

python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision defer
v30.targeted_calibration_pointer_decision.v1: pointer_promotion_deferred (pointer_write=false)

F6 targeted calibration closeout, 2026-06-07
pytest -q tests/unit/test_targeted_calibration_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_closeout_endpoint_is_read_only
4 passed

python3 scripts/run_targeted_calibration_closeout.py --sample-limit 8
v30.targeted_calibration_closeout.v1: targeted_calibration_closed_with_no_promotion (checks=4, pointer_write=false)

M0 mainline selection, 2026-06-07
pytest -q tests/unit/test_mainline_selection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_mainline_selection_endpoint_is_read_only
5 passed

python3 scripts/run_mainline_selection.py --sample-limit 8
v30.mainline_selection.v1: r13_external_release_dry_run_selected

R13 external release dry run, 2026-06-07
pytest -q tests/unit/test_external_release_dry_run.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_dry_run_endpoint_defers_full_pytest_by_default
6 passed

python3 scripts/run_external_release_dry_run.py --sample-limit 8
v30.external_release_dry_run.v1: external_release_dry_run_deferred_full_pytest

R14 external release full pytest decision, 2026-06-07
pytest -q tests/unit/test_external_release_full_pytest_decision.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_full_pytest_decision_endpoint_defers_by_default
6 passed

python3 scripts/run_external_release_full_pytest_decision.py --sample-limit 8
v30.external_release_full_pytest_decision.v1: external_release_full_pytest_deferred

R15 external release blocked status, 2026-06-07
pytest -q tests/unit/test_external_release_blocked_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_blocked_status_endpoint_is_read_only
5 passed

python3 scripts/run_external_release_blocked_status.py --sample-limit 8
v30.external_release_blocked_status.v1: external_release_blocked_pending_full_pytest

R16 post-release-boundary authorization, 2026-06-07
pytest -q tests/unit/test_post_release_boundary_authorization.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_post_release_boundary_authorization_endpoint_pauses_by_default
6 passed

python3 scripts/run_post_release_boundary_authorization.py --sample-limit 8
v30.post_release_boundary_authorization.v1: release_boundary_paused_pending_full_pytest_authorization

M0 mainline selection after release pause, 2026-06-07
pytest -q tests/unit/test_mainline_selection_after_release_pause.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_mainline_selection_after_release_pause_endpoint_is_read_only
5 passed

python3 scripts/run_mainline_selection_after_release_pause.py --sample-limit 8
v30.mainline_selection_after_release_pause.v1: core_monitoring_and_calibration_loop_selected

P0 core monitoring loop, 2026-06-07
pytest -q tests/unit/test_core_monitoring_loop.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_loop_endpoint_is_read_only
5 passed

python3 scripts/run_core_monitoring_loop.py --sample-limit 8
v30.core_monitoring_loop.v1: core_monitoring_loop_ready

P1 lightweight core monitoring checks, 2026-06-08
pytest -q tests/unit/test_lightweight_core_monitoring_checks.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_lightweight_core_monitoring_checks_endpoint_is_read_only
5 passed

python3 scripts/run_lightweight_core_monitoring_checks.py --sample-limit 8
v30.lightweight_core_monitoring_checks.v1: lightweight_core_monitoring_checks_passed

P2 core calibration observation summary, 2026-06-08
pytest -q tests/unit/test_core_calibration_observation_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_observation_summary_endpoint_is_read_only
4 passed

python3 scripts/run_core_calibration_observation_summary.py --sample-limit 8
v30.core_calibration_observation_summary.v1: core_calibration_observation_summary_ready

P3 core calibration drift watch, 2026-06-08
pytest -q tests/unit/test_core_calibration_drift_watch.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_drift_watch_endpoint_is_read_only
5 passed

python3 scripts/run_core_calibration_drift_watch.py --sample-limit 8
v30.core_calibration_drift_watch.v1: core_calibration_drift_watch_ready

P4 focused core calibration evidence queue, 2026-06-08
pytest -q tests/unit/test_focused_core_calibration_evidence_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_focused_core_calibration_evidence_queue_endpoint_is_read_only
5 passed

python3 scripts/run_focused_core_calibration_evidence_queue.py --sample-limit 8
v30.focused_core_calibration_evidence_queue.v1: focused_core_calibration_evidence_queue_ready

P5 core calibration queue review, 2026-06-08
pytest -q tests/unit/test_core_calibration_queue_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_queue_review_endpoint_is_read_only
5 passed

python3 scripts/run_core_calibration_queue_review.py --sample-limit 8
v30.core_calibration_queue_review.v1: core_calibration_queue_review_ready

P6 core calibration watch closeout, 2026-06-08
pytest -q tests/unit/test_core_calibration_watch_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_watch_closeout_endpoint_is_read_only
5 passed

python3 scripts/run_core_calibration_watch_closeout.py --sample-limit 8
v30.core_calibration_watch_closeout.v1: core_calibration_watch_closeout_ready

P7 core monitoring cadence baseline, 2026-06-08
pytest -q tests/unit/test_core_monitoring_cadence_baseline.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_baseline_endpoint_is_read_only
5 passed

python3 scripts/run_core_monitoring_cadence_baseline.py --sample-limit 8
v30.core_monitoring_cadence_baseline.v1: core_monitoring_cadence_baseline_ready

P8 core monitoring cadence documentation sync, 2026-06-08
pytest -q tests/unit/test_core_monitoring_cadence_documentation_sync.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_documentation_sync_endpoint_is_read_only
5 passed

python3 scripts/run_core_monitoring_cadence_documentation_sync.py --sample-limit 8
v30.core_monitoring_cadence_documentation_sync.v1: core_monitoring_cadence_documentation_sync_ready

P9 core monitoring steady state, 2026-06-09
pytest -q tests/unit/test_core_monitoring_steady_state.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_steady_state_endpoint_is_read_only
5 passed

python3 scripts/run_core_monitoring_steady_state.py --sample-limit 8
v30.core_monitoring_steady_state.v1: core_monitoring_steady_state_ready

S0 core monitoring status, 2026-06-09
pytest -q tests/unit/test_core_monitoring_s0_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_s0_status_endpoint_is_read_only
5 passed

python3 scripts/run_core_monitoring_s0_status.py --sample-limit 8
v30.core_monitoring_s0_status.v1: core_monitoring_s0_status_ready

B1 real business Bazi reading acceptance, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_real_business_bazi_acceptance_endpoint_is_read_only
4 passed

python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted

B2 business reading regression pack, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_reading_regression_pack_endpoint_is_read_only
12 passed

python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready

python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)

B3 business answer refresh regression, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_answer_refresh_regression_endpoint_is_read_only
9 passed

python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)

B4 boundary/blocked input regression, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_boundary_blocked_input_regression.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_boundary_blocked_input_regression_endpoint_is_read_only
7 passed

python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)

B5 business API contract freeze, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_api_contract_freeze.py tests/unit/test_real_business_boundary_blocked_input_regression.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_api_contract_freeze_endpoint_is_read_only
6 passed

python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen

python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)

B6 business acceptance closeout, 2026-06-09
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_acceptance_closeout.py tests/unit/test_real_business_api_contract_freeze.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_acceptance_closeout_endpoint_is_read_only
6 passed

python3 scripts/run_real_business_acceptance_closeout.py
v30.real_business_acceptance_closeout.v1: passed (4/4) b6_business_acceptance_closed

python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen

S1 business acceptance steady state, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_business_steady_state.py tests/unit/test_real_business_acceptance_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_steady_state_endpoint_is_read_only
7 passed in 1.75s

python3 scripts/run_real_business_steady_state.py
v30.real_business_steady_state.v1: passed (5/5) s1_business_acceptance_steady_state_ready

BT1 central brain acceptance, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_acceptance_endpoint_is_read_only
9 passed in 2.84s

python3 scripts/run_central_brain_acceptance.py
v30.central_brain_acceptance.v1: passed (5/5) bt1_central_brain_acceptance_ready

BT2 central brain session replay, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_session_replay_endpoint_is_read_only
12 passed in 3.37s

python3 scripts/run_central_brain_session_replay.py
v30.central_brain_session_replay.v1: passed (6/6) bt2_central_brain_session_replay_ready

BT3 brain failure routing, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_central_brain_failure_routing.py tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_failure_routing_endpoint_is_read_only
16 passed in 4.15s

python3 scripts/run_central_brain_failure_routing.py
v30.brain_failure_route.v1: passed (6/6) bt3_brain_failure_routing_ready

BT4 training system closeout, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_training_system_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_training_system_closeout_endpoint_is_read_only
5 passed in 1.35s

pytest -q tests/unit/test_training_signals.py
1 passed in 17.39s

pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
1 passed in 90.20s

python3 scripts/run_training_system_closeout.py --training-run-id bt4-closeout
v30.training_system_closeout.v1: passed (8/8) bt4_training_system_closeout_ready

BT4 did not run full pytest, synthetic all, or full 518K. The existing runtime-version auto-apply pytest was not retained as final BT4 evidence because it did not return in a useful time window during this run; full auto-apply regression remains a major-node check.

BT5 failed-candidate quarantine, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_training_candidate_quarantine.py tests/unit/test_runtime_pointer.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_training_candidate_quarantine_endpoint_is_read_only
10 passed in 1.84s

python3 scripts/run_training_candidate_quarantine.py --training-run-id bt5-quarantine
v30.training_candidate_quarantine.v1: passed (8/8) bt5_training_candidate_quarantine_ready

BT5 did not run full pytest, synthetic all, or full 518K. The script uses BT4 closeout as its prerequisite and then verifies quarantine/rollback behavior in a temporary runtime store.

BT6 synthetic coverage manifest, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
5 passed in 1.31s

python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

BT6 did not run full pytest, synthetic all, or full 518K. BT7 implements `central_brain`; BT8 implements `training_pipeline`.

BT7 central brain synthetic tier, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_central_brain_tier_passes tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
6 passed in 2.45s

python3 scripts/run_synthetic_validation.py --tier central_brain
v30.synthetic.central_brain: passed (5/5)

python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready

BT7 did not run full pytest, synthetic all, or full 518K.

BT8 training pipeline synthetic tier, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_training_pipeline_tier_passes_training_contracts tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
6 passed in 17.88s

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready

BT8 did not run full pytest, synthetic all, or full 518K.

BT9 518K readiness matrix, 2026-06-10
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_518k_validation.py::test_518k_readiness_matrix_documents_sample_shard_and_full_boundary tests/unit/test_518k_validation.py::test_518k_readiness_matrix_script tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
4 passed in 4.33s

python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260609175010408754: eligible mode=sample cases=8 shards=0
artifact record: v30.518k.artifact.v30.518k.sample.20260609175010408754 (json_fallback)

BT9 did not run full pytest, synthetic all, or full 518K.

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260606084440379258: eligible mode=sample cases=8 shards=0
artifact record: v30.518k.artifact.v30.518k.sample.20260606084440379258 (json_fallback)

pytest -q tests/test_v30_scaffold.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
38 passed

pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py tests/unit/test_question_dialogue_graph.py tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py
25 passed

python3 -m compileall -q v30
passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)

pytest -q tests/unit/test_release_candidate_review.py tests/unit/test_production_replay_store.py tests/unit/test_post_seal_status_review.py tests/unit/test_synthetic_validation.py tests/unit/test_ten_god_energy_model.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_review_endpoint_is_read_only
33 passed

pytest -q tests/unit/test_release_candidate_gate_review.py tests/unit/test_release_gate.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_gate_review_endpoint_runs_standard_gate
11 passed

pytest -q tests/unit/test_release_boundary_finalization.py tests/unit/test_release_candidate_gate_review.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_boundary_finalization_endpoint_is_read_only
12 passed
```

Next test additions:

- S1-WAIT regression only when new business evidence appears; major validation, full pytest, full 518K, and release gates remain explicit.
- Stability tests for customer reading output across domain priorities.
- Live LLM smoke gate remains explicit and must report configured/unconfigured/accepted/fallback states without mutating chart facts.

Live Postgres and Redis checks remain explicit integration work and must not enter the default suite.

Default work should keep using targeted tests and affected synthetic tiers; full pytest and full 518K remain explicit release-boundary choices.

Repository testing status:

- Default tests cover `memory`, `local_json`, and Postgres repository boundaries.
- Postgres repository tests use fake connections only.
- Real environment tests require `V30_RUN_REAL_ENV_TESTS=1`, `V30_REPOSITORY=postgres`, `V30_DATABASE_URL`, and `V30_REDIS_URL`.
- Live Docker Postgres and Redis integration test passes when explicitly enabled.

518K validation:

```bash
python scripts/run_518k_validation.py --mode sample
python scripts/run_518k_validation.py --mode shard --shard-id <id>
python scripts/run_518k_validation.py --mode full
```

Release gate:

```bash
python scripts/run_release_gate.py
```

Current implementation:

- `scripts/run_release_gate.py` exists.
- Quick mode composes runtime smoke, production API smoke, LLM live smoke, post-seal contracts, synthetic `all`, 518K sample, and artifact review.
- Standard mode also includes one selected 518K shard.
- Release gate is explicit only and remains outside default full-corpus validation.
- Latest quick gate through R10 candidate review: `eligible`, 6 checks with artifact review available.
- Latest standard gate through R11 candidate-gate review: `eligible`, 7 checks with post-seal contracts and selected 518K shard.

## Markers

V30 should use pytest markers to keep heavy tests explicit:

```text
unit
integration
runtime
synthetic
training
corpus_518k
release
slow
requires_postgres
requires_redis
requires_llm
```

Default pytest should exclude:

```text
slow
synthetic
training
corpus_518k
release
requires_postgres
requires_redis
requires_llm
```

## Fixture Strategy

V30 fixtures should be small and contract-shaped.

Use:

- Minimal chart contexts.
- Converted V20 canonical cases.
- Synthetic cases in V30 schema.
- Small policy artifacts.
- Fake Redis keyspace.
- Temporary runtime directory.
- Optional Postgres only in marked tests.

Avoid:

- Loading full runtime traces in unit tests.
- Calling V20 modules.
- Depending on nginx.
- Depending on long-running training artifacts.
- Depending on live LLM for deterministic tests.

## Training Test Strategy

Training tests must prove the loop:

```text
input cases
-> candidate
-> validation
-> policy artifact
-> runtime pointer
-> runtime behavior change
```

But default tests only need a tiny fixture for each policy family.

Heavy training should be explicit:

```text
--tier smoke
--tier sample
--tier shard
--tier full
```

## 518K Test Strategy

518K validation is a product capability, not a default test.

It should be implemented as a validation runner with these outputs:

- Run ID.
- Corpus version.
- Shard ID.
- Policy versions.
- Coverage metrics.
- Drift metrics.
- Failure clusters.
- Promotion eligibility.
- Artifact path.
- Artifact record ID and search backend metadata.

The release gate should use sample mode, not full mode.

## Acceptance for Test System

- `pytest` stays fast.
- No default test touches V20.
- Heavy validation is explicit.
- Every policy family has a smoke training validation.
- Synthetic validation can run by domain.
- Integrated feature/rule/portrait/structure validation can run without 518K full mode.
- 518K validation can run by sample/shard/full.
- Failures are machine-readable enough to drive self-training.
