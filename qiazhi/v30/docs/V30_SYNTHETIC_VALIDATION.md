# V30 Synthetic Validation

Updated: 2026-06-10

## Purpose

Synthetic validation is V30's fast, focused way to test behavior and drive training without running the full 518K corpus.

It must validate:

- Core chart facts.
- Ten-god model-signal behavior.
- Feature evidence.
- Structure dynamics.
- Strength, structure, and useful-god ranked decisions.
- Mainline selection.
- Question recommendation.
- Explicit interaction state and next-question projection.
- Answer boundaries.
- Role projection.
- LLM output constraints.
- Training promotion candidates.
- Practical Bazi calculation boundaries.
- Central brain coordination boundaries.
- Training pipeline closeout boundaries.

## Active Completion Mainline

The active support-system completion plan is:

```text
docs/archive/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md
```

Synthetic validation completion now follows:

```text
BT6 Synthetic Coverage Manifest completed
BT7 Central Brain Synthetic Tier completed
BT8 Training Pipeline Synthetic Tier completed
BT9 518K Readiness Matrix completed
BT10 Unified Brain / Training / Synthetic Closeout completed
BT-S1 Support Systems Steady State
```

The existing `smoke`, `all`, `interaction_loop`, `real_case_calibration_pack`, `central_brain`, `training_pipeline`, `bazi_llm_acceptance`, M1/M2, M4, M5, M6, and M8 tiers remain active. BL6 adds the dedicated `bazi_llm_acceptance` tier with 5/5 passing cases for Bazi LLM accepted/rejected output paths. BT8 added the dedicated `training_pipeline` tier with 91/91 passing cases and training-signal extraction checks for core/support signal families. BT10 adds `v30.brain_training_synthetic_closeout.v1`, which ties central-brain synthetic evidence, training-pipeline synthetic evidence, the synthetic coverage manifest, and 518K readiness into one support-system closeout. IR1 uses `interaction_loop` 5/5 and `bazi_llm_acceptance` 5/5 as lightweight integrated requirements evidence. IQ2 uses `interaction_loop` 5/5 plus `v30.question_model_signal_training_readiness.v1` 5/5 to verify model-signal personalized questions produce trainable question-policy signals without chart-fact mutation. IQ3 verified a question-policy candidate override with synthetic all 100/100 before promotion-path targeted tests, proving `model_signal_question_policy` does not outrank required core context completion. Full synthetic/all remains a major-node-only check, not a per-subtask default.

## Core Idea

Synthetic cases should be contract-shaped, not output-snapshot-shaped.

They should check:

- Expected structures.
- Expected evidence.
- Expected question anchors.
- Expected answer boundaries.
- Forbidden drift.
- Role-specific visibility.
- Locale/client projection.

## Validation Flow

```text
ValidationCase
-> RuntimeExecution
-> ExpectedContractChecks
-> NegativeExpectationChecks
-> FailureCluster
-> TrainingSignal
```

## V30 Case Schema

The base schema is `ValidationCase` from `docs/V30_ARCHITECTURE_CONTRACT.md`.

Expanded synthetic fields:

```text
case_id
source
domain
chart_context
expected_feature_evidence
expected_structure
expected_mainline
expected_questions
expected_answer_boundaries
negative_expectations
role_expectations
locale_expectations
client_expectations
training_tags
priority
```

## Domains

Initial synthetic domains:

- Core chart facts.
- Missing time context.
- Output controls authority.
- Wealth channel.
- Resource supports self.
- Peer supports self.
- Structure clash/activation.
- Useful-god question.
- Relationship projection.
- Health boundary.
- Role visibility boundary.
- LLM drift boundary.
- Question recommendation relevance.
- Birth chart conversion boundary.
- Luck and flow activation boundary.
- Practical reading usefulness boundary.
- Ten-god energy fusion boundary.
- Ranked decision fusion boundary.
- Interaction state machine boundary.
- Interaction-loop quality boundary.
- Model-signal personalized question training boundary.
- Real-case calibration pack boundary.

## Conversion From V20

V20 synthetic assets should be converted, not imported directly.

Conversion steps:

1. Read V20 case.
2. Extract chart context.
3. Map expectations into V30 fields.
4. Remove V20 runtime field names.
5. Add negative expectations.
6. Add role/client expectations if needed.
7. Store as V30 validation case.

## Synthetic Suite Tiers

### Smoke

Small and fast.

Target:

- 10 core cases.
- 10 structure cases.
- 10 question cases.
- 10 answer boundary cases.

### Domain

Focused suite for one module family.

Examples:

- `core_calculation`
- `luck_flow`
- `structure_strength`
- `practical_reading`
- `structure`
- `question`
- `answer`
- `role_projection`
- `llm`
- `ten_god_energy_fusion`
- `ten_god_energy_calibration`
- `ranked_decision_fusion`
- `m5_weight_replay`
- `interaction_loop`
- `real_case_calibration_pack`

### Regression

Protects known bugs and previous failure clusters.

### Promotion

Required for policy candidate auto-apply.

### Release

Composed suite used by release gate.

Post-seal release gate now adds `post_seal_contracts` before synthetic all, so release eligibility requires core reading projection, M5/M6/M8 contract presence, user leak-scan pass, and admin diagnostic visibility before 518K sample runs. R6 also emits `v30.release_artifact_review.v1`, which groups synthetic suite summary, 518K artifact ids, policy lineage, and projection contract summaries for admin review without promoting policy.

## Synthetic Case Types

V30 synthetic validation should use five case types:

| Type | Purpose |
|---|---|
| Positive prototype | Confirm obvious target structures fire correctly. |
| Negative counter | Prevent overbroad rules and portraits. |
| Metamorphic pair | Change one condition and require an explainable output shift. |
| Boundary gradient | Tune thresholds across weak/neutral/strong transitions. |
| Composite conflict | Validate conflict resolution in realistic mixed charts. |

These case types are required for feature, rule, portrait, structure, question, and answer validation.

## Parameter Tuning

Synthetic validation should tune parameter families:

- Feature thresholds.
- Rule activation weights.
- Structure graph weights.
- Portrait mapping weights.
- Question ranking weights.
- Answer boundary policies.

Synthetic validation must not tune or generate deterministic chart facts:

- Birth information facts.
- Four-pillar facts.
- Luck-cycle facts.
- Flow-year or flow-month facts.

For practical calculation work, synthetic validation checks deterministic conversion behavior and emits quality signals only after runtime code has produced facts.

The output of tuning is a policy candidate, not direct runtime mutation.

```text
SyntheticBaziCase[]
-> current runtime replay
-> failure clusters
-> candidate parameter set
-> synthetic validation
-> 518K sample validation
-> policy artifact
-> runtime pointer
```

## Failure Clustering

Failures should be machine-readable:

```text
failure_id
case_id
domain
contract_field
expected
actual
severity
cluster_key
training_signal
```

This lets synthetic validation feed training instead of only producing test logs.

## Role in Training

Synthetic validation has two training roles:

1. Reject bad candidates.
2. Generate targeted training signals.

Example:

```text
question_policy candidate improves relevance on wealth cases
but fails missing_time boundary
-> reject candidate
-> emit failure cluster: question_missing_time_overreach
```

## Practical Calculation Signals

P0 introduces:

```text
v30.training_signal.birth_chart_conversion_boundary
```

Purpose:

- Track solar-term boundary coverage.
- Track late-night/子时 boundary coverage.
- Track unknown-hour handling.
- Track timezone and true-solar-time assumption coverage.
- Gate policy promotion on practical calculation coverage without creating chart facts.

Planned follow-on signals:

- Canonical real-case feedback from live user sessions beyond the current fixed fixture set.

Implemented practical mainline signals:

- `v30.training_signal.luck_cycle_alignment`
- `v30.training_signal.flow_timing_activation`
- `v30.training_signal.six_pillar_context_coverage`
- `v30.training_signal.strength_structure_decision`
- `v30.training_signal.practical_reading_quality`
- `v30.training_signal.agent_question_flow_quality`
- `v30.training_signal.high_value_question_quality`
- `v30.training_signal.real_case_feedback_alignment`
- `v30.training_signal.ten_god_energy_fusion`
- `v30.training_signal.ranked_decision_fusion`
- `v30.training_signal.m5_weight_replay`
- `v30.training_signal.interaction_state_machine`
- `v30.training_signal.interaction_loop_quality`
- `v30.training_signal.real_case_calibration_pack`
- `v30.training_signal.latent_bazi_attribute_alignment`

## Active Parallel Validation Plan

The next synthetic work runs alongside module implementation and training extraction.

### P7 Model Fusion Cases

Add fixed synthetic cases before broad generation:

- Ten-god energy dominant but low-stability candidate weakens direct conclusion.
- High-volatility ten-god changes question priority without changing chart facts.
- Strength candidate receives support from energy/stability summary.
- Useful-god candidate exposes unresolved requirements instead of a fixed verdict.
- Customer projection hides raw scores while admin diagnostics retain model summary.

Expected signal:

```text
v30.training_signal.ten_god_energy_fusion
v30.training_signal.ranked_decision_fusion
```

Current P7 implementation status:

- `model_signal_summary` is observed in synthetic runtime payloads.
- `ranked_decisions.*.model_signal_summary` is observed for strength, structure pattern, and useful-god.
- Dedicated `ten_god_energy_calibration` tier is active and passes 5/5.
- Dedicated `m4_ten_god_real_case_replay` tier is active and passes 5/5.
- `model_signal_summary` exposes `v30.model_signal_interface_contract.v1` and `v30.model_signal_calibration_profile.v1`.
- Calibration covers self, resource, output, wealth, authority, high-volatility, low-stability, and mixed-family signal patterns.
- Training extraction emits both P7 signals.
- Raw numeric scores stay outside `model_signal_summary`.

### P8 Interaction Loop Cases

Add fixed cases:

- Direct question click records answered id and changes visible next question.
- Structured domain choice records `selected_domain` and `known_user_signals`.
- Hidden calibration remains diagnostics-only for guest/user.
- `visible_next_question_id` changes while `internal_next_question_id` remains diagnosable.
- `followup_reason` explains the next question without exposing internal policy payloads.

Expected signal:

```text
v30.training_signal.interaction_state_machine
v30.training_signal.interaction_loop_quality
```

Current P8 implementation status:

- Synthetic observation includes `interaction_state`.
- Runtime emits visible/internal next-question split.
- Customer reading surface exposes visible next question only.
- Training extraction emits both P8 signals.
- Auto-training question candidates can emit `interaction_followup_policy`.
- Dedicated `interaction_loop` tier is active and passes 5/5.
- The tier covers direct user-question click, structured domain choice, hidden calibration hidden from user, initial visible/internal split, and answer API interaction-state return.

### P9 Real-case Calibration Cases

Add calibration-only fixtures:

- Solar ready chart.
- Lunar ready chart.
- Leap-month lunar chart.
- Known-place true-solar chart.
- Unknown-hour blocked hour pillar.
- Unknown-gender usable natal/practical context.

Checks:

- Calendar/luck/flow/six-pillar facts are deterministic.
- Ten-god energy and ranked decisions are present and bounded.
- Recommended question order is stable enough for calibration.
- No final life verdict is hard-coded into the fixture.

Expected signal:

```text
v30.training_signal.real_case_calibration_pack
```

Current P9.1 implementation status:

- Dedicated `real_case_calibration_pack` tier is phase sealed and passes 30/30.
- The pack covers solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender fixtures.
- Fixtures validate chart facts, six-pillar readiness, model-signal readiness, ranked decision presence, ranked primary candidates, ranked score keys, ranked minimum score floors, practical reading status, question flow, and no-fake-fact boundaries without hard-coding final conclusions.
- R5 adds `v30.production_replay_metadata.v1` to real-case observations and `v30.production_replay_metadata_summary.v1` to training/release coverage. The metadata is privacy guarded and records replay tags only; it does not import private content or mutate chart facts.

## Acceptance

- V20 cases are converted into V30 schema.
- Synthetic smoke is fast enough to run frequently.
- Synthetic failures produce training signals.
- Promotion cannot skip required synthetic gates.
- Synthetic validation never imports V20 runtime.

## Current Implementation Status

- `SyntheticBaziCase` schema exists.
- `SyntheticValidationResult` schema exists.
- `SyntheticValidationSuiteResult` schema exists.
- Smoke runner validates current V30 runtime spine.
- Smoke suite contains the first fixed cases for core spine, useful-god boundary, missing-time boundary, hidden-factor dialogue discovery, and knowledge/rule/portrait seed signals.
- Gradient suite contains the first fixed cases for question-policy weighting, question dialogue graph extraction, rule-policy weighting, hidden-factor recommendation promotion, hidden-factor state transitions, structure mechanism thresholds, K/R/P composite consumption, K/R/P library expansion, and mainline stability.
- Script entry exists: `python scripts/run_synthetic_validation.py --tier smoke`.
- Script entry exists: `python scripts/run_synthetic_validation.py --tier gradient`.
- Script entry exists: `python scripts/run_synthetic_validation.py --tier all`.
- Synthetic `all` is used as the promotion gate for policy candidates.
- Promotion validation injects the candidate policy payload into runtime replay before pointer activation.
- Current runner checks expected evidence domains, expected anchors, useful-god boundary, missing-time boundary, hidden-factor recommendation topic, hidden-factor probe boundary, K/R/P signal consumption by structure/mainline/question recommender, and required mechanism paths.
- Current runner also validates question dialogue graph edge coverage, question outcome feedback consumption, LLM output contract status, K/R/P unit count, required unit IDs, K/R/P pack IDs, required portrait tags, required macro domains, required macro signal domains, required macro portrait domains, hidden-factor persistent state status including year-only, state-only, year+state amplifier, multi-year+state amplifier, denial, and conflict-after-candidate paths, rule-policy weighted rule evidence, explicit-time counter-evidence, hidden-factor feedback counter-evidence, useful-god feedback counter-evidence, branch-relation feedback counter-evidence, and dynamic graph v2 extraction/competition/suppression/conflict-family/path-resolution/strength-pattern/domain-path coverage through the normal runtime chain.
- Current smoke result is 5/5 passing.
- Current gradient result is 19/19 passing.
- Current all-tier result is 49/49 passing.
- Latest promotion run `structure-signal-001` used synthetic `all` + 518K sample validation before pointer activation.
- Latest promotion run `macro-signal-001` used synthetic `all` + 518K sample validation before pointer activation and included `macro_dimension_coverage`.
- Synthetic validation now guards macro signal question consumption and missing-time priority together.
- Synthetic validation now checks expanded K/R/P coverage at 35+ matched units, including ten-god family, branch conflict/alignment family, seasonal strength, 格局 candidate, useful-god family candidate, path-resolution, domain-rule depth, and wealth/career/relationship/health domain units.
- Synthetic validation now checks `dynamic_conflict_family_count`, `dynamic_path_resolution_family_count`, `dynamic_branch_conflict_edge_count`, `dynamic_branch_alignment_edge_count`, `strength_pattern_review_count`, wealth/career/relationship/health/useful-god domain path counts, and fine-grained domain-rule depth counts.
- Latest standard release gate is eligible with runtime smoke, synthetic `all`, 518K sample, and selected 518K shard checks passing.
- Synthetic replay now validates role-aware portrait projection views: guest views must not expose hidden-factor portrait projections, admin views must retain diagnostic hidden-factor projections, and runtime must emit a default user portrait view summary.
- Training extraction now emits `v30.training_signal.portrait_projection_view_coverage` from synthetic role contrast observations.
- Synthetic replay now observes `v30.role_locale_client_projection_matrix.v1`, covering guest/user/practitioner/analyst/admin/lab roles, zh/en/ko locales, and web/mobile/admin/lab client profiles.
- Training extraction now emits `v30.training_signal.role_locale_client_projection_coverage` so silent presentation-policy training can tune visibility, density, labels, and question strategy without mutating chart facts.
- Synthetic replay now also checks four LLM output contract tasks: `AnswerDraft`, `QuestionExplanation`, `SyntheticCaseDraft`, and `FailureClusterSummary`.
- `v30.training_signal.llm_output_contract_quality` now records four-task coverage in addition to drift failures and failed synthetic cases.
- LLM answer draft observations now include provider readiness, execution/fallback status, fallback reason, and drift check metadata. These train expression policy only and cannot mutate chart facts.
- Hidden-factor event alignment signals now feed a validation-gated policy weight artifact. Synthetic conflict and denial cases verify that negative feedback remains stronger than positive alignment.
- Synthetic structure validation now observes bounded 通关/制化 path metrics through `dynamic_tongguan_*` and `dynamic_zhihua_*` path scores and feeds them into structure dynamic training signals.
- Synthetic replay now observes expression-rendered question labels and fails on missing labels or engineering-token leakage in presentation text.
- Synthetic replay now observes the customer reading surface and high-value question contract. Guest/user projections must expose concise reading and next-question interaction while keeping internal Bazi context in diagnostics.
- Training extraction now emits `v30.training_signal.high_value_question_quality` from expected information gain, question-value coverage, and quality-contract coverage.
- Synthetic training extraction now emits `v30.training_signal.per_unit_parameter_tuning`, keeping unit-derived weights bounded and candidate-only.
- Generator remains pending; fixed metamorphic, gradient, and composite cases now exist.
- Practical calculation mainline is now tracked in `V30_PRACTICAL_BAZI_MAINLINE_PLAN.md`.
- `core_calculation` synthetic coverage is active for P0 BirthInput to deterministic four pillars.
- `m1_m2_bazi_calculation` synthetic coverage is active for solar, lunar, leap-month lunar, true-solar, unknown-hour, invalid-timezone, solar-term/year-month boundary, unknown-gender natal facts, root/vault facts, base fact summary, base fact explanations, and deterministic fact integrity.
- Current `core_calculation` result is 4/4 passing.
- Current `m1_m2_bazi_calculation` result is 12/12 passing.
- Practical mainline synthetic coverage is active for luck-cycle, flow timing, six-pillar context, ranked strength/structure/useful-god decisions, practical reading, and agent question flow.
- Canonical real-case synthetic coverage is active for ready solar male/female inputs, unknown-gender partial context, and invalid-timezone blocked input.
- Synthetic training extraction now emits `v30.training_signal.real_case_feedback_alignment`, keeping real-case feedback as quality/policy signal rather than chart-fact source.
- Synthetic `all` included 95 cases at the M7 major gate; the current real-case calibration pack has expanded to 30 cases.
- Latest verification for the P7/P8 baseline and next validation slice:

```text
C8 core-completion freeze baseline, 2026-06-06
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)

F1 frozen-core calibration baseline, 2026-06-06
python3 scripts/run_frozen_core_calibration_review.py
v30.frozen_core_calibration_review.v1: ready_for_targeted_calibration_iteration (tiers=6, signals=31)

F2 targeted calibration candidate review, 2026-06-06
python3 scripts/run_targeted_calibration_candidate_review.py
v30.targeted_calibration_candidate_review.v1: ready_for_validation_gate_review (candidates=4)

F3 targeted calibration validation gate, 2026-06-06
python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 8
v30.targeted_calibration_validation_gate.v1: ready_for_policy_pointer_review (synthetic=95/95, 518k=8)

F4 targeted calibration pointer review, 2026-06-07
python3 scripts/run_targeted_calibration_pointer_review.py --sample-limit 8
v30.targeted_calibration_pointer_review.v1: ready_for_explicit_operator_pointer_decision (diffs=4)

F5 explicit operator pointer decision, 2026-06-07
python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision defer
v30.targeted_calibration_pointer_decision.v1: pointer_promotion_deferred (pointer_write=false)

F6 targeted calibration closeout, 2026-06-07
python3 scripts/run_targeted_calibration_closeout.py --sample-limit 8
v30.targeted_calibration_closeout.v1: targeted_calibration_closed_with_no_promotion (checks=4, pointer_write=false)

M0 mainline selection, 2026-06-07
python3 scripts/run_mainline_selection.py --sample-limit 8
v30.mainline_selection.v1: r13_external_release_dry_run_selected

R13 external release dry run, 2026-06-07
python3 scripts/run_external_release_dry_run.py --sample-limit 8
v30.external_release_dry_run.v1: external_release_dry_run_deferred_full_pytest

R14 external release full pytest decision, 2026-06-07
python3 scripts/run_external_release_full_pytest_decision.py --sample-limit 8
v30.external_release_full_pytest_decision.v1: external_release_full_pytest_deferred

R15 external release blocked status, 2026-06-07
python3 scripts/run_external_release_blocked_status.py --sample-limit 8
v30.external_release_blocked_status.v1: external_release_blocked_pending_full_pytest

R16 post-release-boundary authorization, 2026-06-07
python3 scripts/run_post_release_boundary_authorization.py --sample-limit 8
v30.post_release_boundary_authorization.v1: release_boundary_paused_pending_full_pytest_authorization

M0 mainline selection after release pause, 2026-06-07
python3 scripts/run_mainline_selection_after_release_pause.py --sample-limit 8
v30.mainline_selection_after_release_pause.v1: core_monitoring_and_calibration_loop_selected

P0 core monitoring loop, 2026-06-07
python3 scripts/run_core_monitoring_loop.py --sample-limit 8
v30.core_monitoring_loop.v1: core_monitoring_loop_ready

P1 lightweight core monitoring checks, 2026-06-08
python3 scripts/run_lightweight_core_monitoring_checks.py --sample-limit 8
v30.lightweight_core_monitoring_checks.v1: lightweight_core_monitoring_checks_passed

P2 core calibration observation summary, 2026-06-08
python3 scripts/run_core_calibration_observation_summary.py --sample-limit 8
v30.core_calibration_observation_summary.v1: core_calibration_observation_summary_ready
observations: 4 stable, 0 needs_review

P3 core calibration drift watch, 2026-06-08
python3 scripts/run_core_calibration_drift_watch.py --sample-limit 8
v30.core_calibration_drift_watch.v1: core_calibration_drift_watch_ready
drift_detected: False

P4 focused core calibration evidence queue, 2026-06-08
python3 scripts/run_focused_core_calibration_evidence_queue.py --sample-limit 8
v30.focused_core_calibration_evidence_queue.v1: focused_core_calibration_evidence_queue_ready
queued_evidence: 0

P5 core calibration queue review, 2026-06-08
python3 scripts/run_core_calibration_queue_review.py --sample-limit 8
v30.core_calibration_queue_review.v1: core_calibration_queue_review_ready
focused_fix_candidates: 0

P6 core calibration watch closeout, 2026-06-08
python3 scripts/run_core_calibration_watch_closeout.py --sample-limit 8
v30.core_calibration_watch_closeout.v1: core_calibration_watch_closeout_ready
closeout_checks: 4/4

P7 core monitoring cadence baseline, 2026-06-08
python3 scripts/run_core_monitoring_cadence_baseline.py --sample-limit 8
v30.core_monitoring_cadence_baseline.v1: core_monitoring_cadence_baseline_ready
default_cadence: on_new_calibration_evidence_only

P8 core monitoring cadence documentation sync, 2026-06-08
python3 scripts/run_core_monitoring_cadence_documentation_sync.py --sample-limit 8
v30.core_monitoring_cadence_documentation_sync.v1: core_monitoring_cadence_documentation_sync_ready
docs: 10/10

P9 core monitoring steady state, 2026-06-09
python3 scripts/run_core_monitoring_steady_state.py --sample-limit 8
v30.core_monitoring_steady_state.v1: core_monitoring_steady_state_ready
waiting_for_new_evidence: True

S0 core monitoring status, 2026-06-09
python3 scripts/run_core_monitoring_s0_status.py --sample-limit 8
v30.core_monitoring_s0_status.v1: core_monitoring_s0_status_ready
status_checks: 4/4

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (55/55 at previous major gate; not rerun for the current M5 batch)
v30.synthetic.m5_ranked_decision_contract: passed (14/14)
v30.synthetic.real_case_calibration_pack: passed (30/30)
v30.synthetic.m5_ranked_decision_contract: passed (30/30)
v30.synthetic.m6_practical_reading_contract: passed (30/30)
v30.synthetic.m8_api_projection_contract: passed (30/30)
v30.synthetic.all: passed (95/95)
v30.synthetic.practical_reading: passed (1/1)
v30.synthetic.m6_practical_reading_contract: passed (14/14)

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)

python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence
v30.synthetic.latent_bazi_divergence: passed (2/2)

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)

pytest -q tests/unit/test_production_replay_metadata.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
4 passed

pytest -q tests/unit/test_release_gate.py
3 passed

pytest -q tests/unit/test_release_gate.py tests/unit/test_518k_validation.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_artifact_review_endpoint_is_observability_only
14 passed

python3 scripts/run_release_gate.py --sample-limit 2
v30.release_gate.quick.20260605103342: eligible mode=quick checks=6

pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py tests/unit/test_question_dialogue_graph.py tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py
25 passed

pytest -q
188 passed, 1 skipped
```
