# V30 Training Architecture

Updated: 2026-06-10

## Purpose

V30 is a high-iteration system. Training is not an admin side feature; it is one of the main runtime improvement loops.

The V30 training architecture must support:

- Automatic candidate generation.
- Automatic synthetic validation.
- Automatic 518K sample/shard validation.
- Automatic policy artifact creation.
- Searchable validation artifact lineage.
- Automatic runtime pointer application after validation.
- Observable rollback and lineage.

Manual review may exist for inspection and emergency override. It must not be the normal path required before every training output becomes active.

Current implementation rule:

```text
synthetic all -> training signals -> policy candidate -> synthetic all + 518K sample -> artifact -> RuntimePointer immediately
```

No review queue is part of the main path.

Current runnable entry points:

```bash
python3 scripts/run_auto_training.py --training-run-id <id>
curl -fsS -X POST http://127.0.0.1:9030/api/v30/admin/training/run \
  -H 'Content-Type: application/json' \
  -d '{"training_run_id":"<id>"}'
```

M3 background training / validation entry points:

```bash
curl -fsS -X POST http://127.0.0.1:9030/api/v30/admin/training/m3-background/run \
  -H 'Content-Type: application/json' \
  -d '{"sample_limit":8,"include_shard":false,"shard_id":7,"shard_limit":16,"include_readiness_matrix":false}'

curl -fsS 'http://127.0.0.1:9030/api/v30/admin/training/m3-background/status'
```

The Admin Training page exposes the same queue with a progress bar. Default steps are M3 snapshot write, `m3_core_spine` synthetic, `training_pipeline` synthetic, and 518K sample. 518K shard and readiness matrix are opt-in. Full 518K remains explicit-only and is not exposed as a routine background button.

Runtime isolation update, 2026-06-28:

- The V30 API process must not execute heavy training loops directly.
- Admin training entry points create a job file and start `scripts/run_admin_training_worker.py` as an isolated process.
- Job state, progress percent, worker pid, and log tail are read from `.runtime/training/...`.
- Login, profile, reading, and LLM endpoints must stay responsive while training runs.
- Legacy `/api/v30/admin/training/run` is kept as a compatibility entry, but it now queues the same isolated auto-apply worker instead of blocking the API process.

Latest M3/training evidence, 2026-06-10:

```text
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)
```

This run is evidence for M3 training-signal coverage and support-system steady state. It does not promote pointers and does not mutate chart facts.

Current first families:

```text
structure_policy
mainline_policy
question_policy
rule_policy
```

These are promoted immediately after required validation passes.

## Current Training Completion Review

| Area | Completion | Current state | Next training work |
|---|---:|---|---|
| Auto-training spine | 100% | Synthetic signals, policy candidates, validation replay, artifacts, pointer activation, rollback metadata, lineage diagnostics, failed-candidate quarantine, and BT8 training-pipeline synthetic coverage are connected for current scope. | Keep promotion contract stable and require targeted validation before any policy pointer review. |
| Policy family coverage | 86% | `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy` are active; answer/presentation/portrait families have signal coverage but less promotion depth. | Broaden only after targeted calibration evidence; do not reopen frozen M1-M8 facts through policy changes. |
| Synthetic training signals | 100% | BT10 complete: dedicated `training_pipeline` tier passes 91/91 cases, extraction covers K/R/P, per-unit tuning, M1/M2, M3, M4/M5, M6, M8, interaction, hidden-factor alignment, central-brain routes, expression, and LLM contract, and unified closeout accepts the evidence. | Training signals tune candidates, not deterministic chart facts; current default is BT-S1 steady state. |
| Integrated requirements training evidence | 100% | IR1 complete: `v30.bazi_intelligence_requirements_coverage.v1` consumes `interaction_loop` and `bazi_llm_acceptance` training signals for M3, projection, interaction, and Bazi LLM acceptance coverage. | Keep this as an integrated evidence gate; do not promote policy or tune chart facts from IR1. |
| 518K validation and artifact search | 95% | BT9 complete: `v30.518k_readiness_matrix.v1` passes 7/7 checks, sample/shard runners persist artifact/index URIs, JSON fallback or Postgres search is verified, full mode remains explicit-only, and sample `v30.518k.sample.20260609175010408754` passed 8 cases with `json_fallback`. | Use sample/shard gates for distribution drift and pointer review, not default full-corpus testing. |
| Question policy training | 92% | IQ5 complete: question graph outcomes, adaptive replay, hidden-factor events, K/R/P weights, model-signal personalization signals, and multi-turn closeout validate question strategy. Auto-training emits `model_signal_question_policy`, promotion validates it through synthetic all and 518K sample, closeout validates candidate availability, and chart-fact mutation stays blocked. | IQ-S1 steady state; train visible-next-question strategy separately from internal calibration strategy when new evidence appears. |
| LLM/expression training | 62% | Contract quality observes drift, task coverage, and fallback behavior without mutating facts. | Add configured live-smoke status and failure taxonomy as observability, not chart-fact input. |

## Active Completion Mainline

The active support-system completion plan is now:

```text
docs/archive/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md
```

Training work must follow this order:

```text
BT1 Central Brain Acceptance Gate
BT2 Long-Session Brain Replay
BT3 Brain Failure Routing And Task Queue Contract
BT4 Training System Closeout Gate
BT5 Failed Candidate Quarantine And Rollback Readiness
BT6 Synthetic Coverage Manifest
BT7 Central Brain Synthetic Tier
BT8 Training Pipeline Synthetic Tier
BT9 518K Readiness Matrix
BT10 Unified Brain / Training / Synthetic Closeout
```

BT4 is complete as the training-system closeout baseline: `v30.training_system_closeout.v1` passes 8/8 checks and proves core policy-family training can produce signals, candidates, validation replay, artifacts, runtime pointers, question comparison, lineage, and rollback metadata without promoting future policy families by default. BT5 is also complete: `v30.training_candidate_quarantine.v1` passes 8/8 checks and proves failed candidates are quarantined with source signals, failed validations, rollback target, diagnostic remediation route, unchanged pointer, and last-good runtime usage. BT6 completed the synthetic coverage manifest, BT7 completed the `central_brain` synthetic tier with 5/5 cases, BT8 completed the `training_pipeline` synthetic tier with 91/91 cases, BT9 completed the 518K readiness matrix with 7/7 checks, and BT10 completed unified support-system closeout with 6/6 checks. IR1 later consumes the active interaction and Bazi LLM training signals as integrated requirements evidence without promoting policy. The current default state is `BT-S1 Support Systems Steady State`.

## Active Training Mainline

Historical frozen-core training stance:

```text
S0 Steady State Await New Calibration Evidence
-> C1-C8 core module completion is frozen for current M1-M8 scope
-> F1 frozen-core calibration baseline passed with 6 tiers and 31 training signals
-> F2 candidate review produced 4 read-only candidate tracks
-> F3 validation gate passed synthetic all 95/95 and 518K sample 8 cases with candidate overrides
-> F4 pointer review found 4 diffs ready for explicit operator decision
-> F5 recorded operator_decision=defer and pointer_write=false
-> F6 targeted_calibration_closed_with_no_promotion, checks=4, pointer_write=false
-> M0 selected R13 and keeps full_pytest_run_now=false
-> R13 external_release_dry_run_deferred_full_pytest, external_release_ready=false
-> R14 external_release_full_pytest_deferred, external_release_blocked=true
-> R15 external_release_blocked_pending_full_pytest, release blockers recorded
-> R16 release_boundary_paused_pending_full_pytest_authorization, full_pytest_authorized=false
-> M0 after release pause selected core_monitoring_and_calibration_loop
-> P0 core_monitoring_loop_ready, monitoring_checks=4/4
-> P1 lightweight_core_monitoring_checks_passed, checks=4/4
-> P2 core_calibration_observation_summary_ready, stable_observations=4, focused_module_fix_required=false
-> P3 core_calibration_drift_watch_ready, drift_detected=false, cadence=on_new_calibration_evidence_only
-> P4 focused_core_calibration_evidence_queue_ready, queued_evidence=0, batch_key=m1_m8_module_target
-> P5 core_calibration_queue_review_ready, reviewed_modules=0, focused_fix_candidates=0
-> P6 core_calibration_watch_closeout_ready, closeout_checks=4/4, current_cycle_closed=true
-> P7 core_monitoring_cadence_baseline_ready, cadence=on_new_calibration_evidence_only
-> P8 core_monitoring_cadence_documentation_sync_ready, required_docs_synced=10/10
-> P9 core_monitoring_steady_state_ready, steady_state_checks=4/4, waiting_for_new_evidence=true
-> S0 core_monitoring_s0_status_ready, status_checks=4/4, new_core_monitoring_task_allowed_by_default=false
-> BT1 central_brain_acceptance_ready, checks=5/5
-> BT2 central_brain_session_replay_ready, checks=6/6
-> BT3 brain_failure_routing_ready, checks=6/6
-> BT4 training_system_closeout_ready, checks=8/8, training_completion=97
-> BT5 training_candidate_quarantine_ready, checks=8/8, training_completion=99
-> training may tune model weights, question strategy, rule weights, and expression candidates
-> training may not mutate deterministic chart facts, final pillars, luck/flow facts, or base fact explanations
-> promotion still requires synthetic all plus 518K sample/shard evidence
-> external pointer promotion remains a separate explicit review track
```

C8 freeze baseline:

```text
Core module state: M1-M8 100% current-scope complete
Synthetic all: v30.synthetic.all passed (95/95)
518K sample: v30.518k.sample.20260606084440379258, cases=8, json_fallback
Targeted core pytest: 38 passed
Frozen-core calibration review: ready_for_targeted_calibration_iteration, tiers=6, signals=31
Targeted calibration candidate review: ready_for_validation_gate_review, candidates=4
Targeted calibration validation gate: ready_for_policy_pointer_review, synthetic=95/95, 518k=8
Targeted calibration pointer review: ready_for_explicit_operator_pointer_decision, diffs=4
Targeted calibration pointer decision: pointer_promotion_deferred, pointer_write=false
```

Implemented in the current P7/P8/P9.1 slice:

- Runtime emits `v30.model_signal_summary.v1`.
- Ranked decisions carry bounded `model_signal_summary` sections.
- Synthetic observation includes `model_signal_summary`.
- Training extraction emits `v30.training_signal.ten_god_energy_fusion`, `v30.training_signal.ranked_decision_fusion`, and `v30.training_signal.m5_weight_replay`.
- `v30.training_signal.ten_god_energy_fusion` includes M4 real-case replay count, interface-ready count, and replay family coverage.
- Training extraction emits `v30.training_signal.m1_m2_base_fact_contract` from deterministic base fact observations, including root/vault fact readiness and canonical category coverage.
- Structure dynamic training payload includes model-signal readiness, energy-band count, and path adjustment metrics.
- Dedicated `ten_god_energy_calibration` synthetic tier covers five ten-god families and energy/stability/volatility bands.
- Dedicated `m4_ten_god_real_case_replay` synthetic tier covers real-case model-signal interface readiness without promoting threshold changes.
- Auto-training structure candidates can emit `dynamic_graph.model_signal_fusion` plus bounded model-signal family, energy-band, stability-review, and volatility-review weights.
- Runtime emits `v30.interaction_state.v1`.
- Training extraction emits `v30.training_signal.interaction_state_machine`.
- Training extraction emits `v30.training_signal.interaction_loop_quality`.
- Training extraction emits `v30.training_signal.question_model_signal_personalization` from interaction-loop model-signal focus observations.
- IQ2 readiness passes `v30.question_model_signal_training_readiness.v1` with interaction-loop coverage, actionable focus pairs/topics, and no chart-fact tuning.
- Auto-training question candidates emit `model_signal_question_policy` from `v30.training_signal.question_model_signal_personalization`.
- Runtime consumes `model_signal_question_policy` only in the user-question layer; required core context completion still wins.
- Auto-training question candidates can emit `interaction_followup_policy`.
- Dedicated `interaction_loop` synthetic tier passes direct-click, structured-domain, hidden-calibration, visible/internal split, and answer API state cases.
- Dedicated `central_brain` synthetic tier passes guest/user/practitioner/admin/missing-time cases for role/session/hidden-factor/expression/training-route/no-mutation contracts.
- Dedicated `real_case_calibration_pack` synthetic tier passes 30 canonical fixtures across solar, lunar, leap-month lunar, true-solar, unknown-hour, unknown-gender, invalid date/time, M5 ranked score-floor, follow-structure, disputed-structure, ranked-basis-signal, and M6 practical-reading contract calibration.
- Dedicated `m5_ranked_decision_contract` tier validates that ranked decisions consume M1/M2 root/vault facts and M4 model-signal interface/calibration profiles while staying candidate-bound and raw-score-free.
- Dedicated `m6_practical_reading_contract` tier validates that practical readings expose calculation basis, M5 decision links, M4 signal bands, evidence ids, explanation units, blocked claims, and quality contracts without raw model-score leakage.
- M7/R5 training extraction records M6 contract readiness, practical domain contract count, practical raw-score leak count, production replay metadata coverage, privacy guard pass count, ready/pending/blocked counts, calendar/true-solar/unknown boundary counts, and projection leak-scan count in `v30.training_signal.real_case_calibration_pack`.
- Dedicated `m8_api_projection_contract` tier validates additive API projection, customer leak scan, core-first surface order, and role-gated diagnostics.
- Training extraction emits `v30.training_signal.api_projection_contract`.
- Dedicated `m1_m2_bazi_calculation` synthetic tier passes solar, lunar, leap-month lunar, true-solar, unknown-hour, invalid-timezone, solar-term/year-month boundary, unknown-gender natal facts, root/vault facts, base fact summary, base fact explanations, and fact-integrity cases.
- Training extraction emits `v30.training_signal.real_case_calibration_pack`.
- Raw scores remain out of the bounded summary; detailed ten-god model remains diagnostic, while calibration family/band distributions train policy candidates only.

Training can tune:

- Ten-god energy/stability/volatility thresholds.
- Ranked decision candidate weights.
- Question strategy and visible next-question ordering.
- Follow-up policy and selected-domain routing.
- Expression density and boundary language.

Training must not tune or generate:

- Birth facts.
- Pillars.
- Luck-cycle facts.
- Flow-year or flow-month facts.
- Hidden-factor facts.
- Fixed useful-god verdicts.

Current implementation status:

- Auto-training runs synthetic `all` as a training-signal source before candidate creation.
- `SyntheticTrainingSignal` extracts K/R/P unit coverage, macro dimension coverage, portrait projection coverage, question graph edge coverage, question dialogue outcomes, hidden-factor event alignment, and failure clusters.
- `v30.training_signal.hidden_factor_event_alignment` now reports state coverage, average strength, average alignment score, average time-layer alignment score, candidate/conflict/denial/expired counts, event-year coverage, repeated-state coverage, time-layer coverage, and repeated-state domains.
- Auto-training now converts `v30.training_signal.hidden_factor_event_alignment` into conservative `hidden_factor_event_policy` weights for question and rule policies.
- Hidden-factor event weights only apply after persisted feedback state exists; aligned candidates receive a small boost, expired states receive refresh pressure, and conflicting/denied states are downweighted.
- `v30.training_signal.latent_bazi_attribute_alignment` now reports same-Bazi latent divergence, base chart/model stability, active latent attributes, active ten-god modifiers, and active domain biases.
- Candidate payloads can convert that signal into `v30.latent_bazi_attribute_policy.v1` for question/rule policies.
- Runtime question recommendation consumes `latent_bazi_attribute_policy` as a bounded hidden-attribute question-need adjustment; it cannot tune chart facts, calendar conversion, luck cycle, or flow timing.
- `v30.training_signal.portrait_projection_view_coverage` tracks role/client portrait view coverage, visibility coverage, average view count, and guest/admin hidden-factor contrast.
- `v30.training_signal.role_locale_client_projection_coverage` tracks supported roles, locales, clients, sampled projection combinations, diagnostic roles, compact clients, and presentation-policy boundaries.
- `v30.training_signal.real_case_feedback_alignment` tracks canonical real-case fixture coverage, ready/blocked counts, no-fake-fact coverage, six-pillar readiness, practical reading usability, agent flow, and projection readiness.
- `question_policy` candidates consume K/R/P signals into `krp_unit_weights`, question outcome signals into conservative topic/intent weights, and hidden-factor event signals into feedback-conditioned event policy weights.
- `v30.training_signal.question_model_signal_personalization` tracks model-signal focused question counts, focus reasons, focus pairs/topics, top-question coverage, and the boundary `question_model_signal_personalization_trains_question_strategy_not_chart_facts`.
- `question_policy.weights.model_signal_question_policy` tracks focus topics/pairs and is guarded by `model_signal_question_policy_trains_question_strategy_not_chart_facts`.
- `v30.training_signal.per_unit_parameter_tuning` now maps synthetic K/R/P coverage and failure clusters into bounded rule, domain, and mechanism weight maps.
- `rule_policy` candidates consume per-unit maps into `rule_weights`, `domain_weights`, and `per_unit_parameter_policy`; `structure_policy` candidates consume mechanism maps into `mechanism.*` weights.
- `per-unit-tuning-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active rule/structure policies carry `per_unit_parameter_policy.unit_count=46`, `mechanism.useful_god_candidate_gate=1.035`, and `domain_weights.structure_dynamic=1.015`.
- `v30.training_signal.llm_output_contract_quality` tracks four-task contract coverage for answer drafts, question explanations, synthetic case drafts, and failure cluster summaries, plus drift failures and failed synthetic cases.
- `v30.training_signal.bazi_llm_output_acceptance_quality` tracks Bazi LLM accepted/rejected schema, role-leak, and drift paths. It can tune expression and question strategy only; it cannot tune chart facts, calendar conversion, luck-cycle, or flow timing.
- `SyntheticTrainingSignal` now also extracts structure dynamic competition/suppression/conflict-family/path-resolution/domain-path and domain-rule-depth metrics.
- `structure_policy` candidates consume those metrics into `dynamic_graph.v2`, `dynamic_graph.competition_suppression`, `dynamic_graph.conflict_family`, `dynamic_graph.path_resolution`, `dynamic_graph.domain_path`, `dynamic_graph.domain_rule_depth`, and `dynamic_graph.useful_god_candidate_path` weights.
- `structure_policy` candidates now also consume 通关/制化 path metrics into `dynamic_graph.tongguan_zhihua`.
- `question_policy.krp_unit_weights` now includes wealth, career, relationship, and health domain weights from K/R/P coverage.
- Candidate promotion still replays synthetic `all` and 518K sample before pointer activation.
- 518K validation now records deterministic artifact record IDs and can upsert run summaries into `v30_artifacts` for artifact search.
- Release gate summaries expose 518K `artifact_record_id`, `artifact_search_backend`, and `artifact_searchable` so promotion diagnostics can find the exact distribution replay artifact.
- Runtime now emits `v30.adaptive_question_diagnostics.v1`, giving training a traceable source for adaptive question-policy candidates.
- `v30.training_signal.adaptive_question_replay` converts replay diagnostics into decision coverage, alignment coverage, topic/stage/intent coverage, strategy coverage, and reason-category counts.
- `question_policy` candidates now include `adaptive_question_policy` with bounded topic, stage, and intent weight deltas.
- `question_policy` promotion now persists active-vs-candidate comparison artifacts and stores the comparison summary in the policy artifact validation summary.
- Validation artifact discovery now searches 518K and question-policy comparison artifacts through the shared `v30_artifacts` surface with JSON fallback.
- Promotion lineage diagnostics now link runtime pointers, policy artifacts, validation artifacts, rollback pointers, and active runtime trace consumption.
- No review queue is required between validated candidate and active runtime pointer.
- `structure-signal-001` has been applied through the normal auto-training path with 4/4 families promoted.
- The active structure policy now carries `dynamic_graph.v2=1.04` and `dynamic_graph.competition_suppression=1.03`.
- Real API runtime verification confirmed those weights are loaded from active pointers and visible in runtime trace.
- `macro-signal-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed `macro_dimension_coverage` is present in active policy payload training signals.
- Portrait projection coverage is now available as `v30.training_signal.portrait_projection_coverage`.
- `krp-conflict-family-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active `structure_policy.krp-conflict-family-001.structure_policy` carries `dynamic_graph.conflict_family=1.015`.
- `strength-path-resolution-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active `structure_policy.strength-path-resolution-001.structure_policy` carries `dynamic_graph.path_resolution=1.036`.
- `domain-rule-depth-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active `structure_policy.domain-rule-depth-001.structure_policy` carries `dynamic_graph.domain_path=1.06` and `dynamic_graph.useful_god_candidate_path=1.06`.
- `hidden-factor-policy-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active `question_policy.hidden-factor-policy-001.question_policy` carries `hidden_factor_event_policy.candidate_alignment_multiplier=1.029`, `conflict_multiplier=0.885`, and `denial_multiplier=0.825`.
- 通关/制化 training extraction now records average tongguan and zhihua path counts in `v30.training_signal.structure_dynamic_competition`.
- `tongguan-zhihua-001` has been applied through the normal auto-training path with 4/4 families promoted.
- Runtime verification confirmed active `structure_policy.tongguan-zhihua-001.structure_policy` carries `dynamic_graph.tongguan_zhihua=1.06`.

## Training Loop

```text
RuntimeTrace
-> FeedbackEvent
-> SyntheticCaseResult
-> SyntheticTrainingSignal
-> Corpus518KResult
-> ArtifactSearchRecord
-> TrainingRun
-> PolicyCandidate
-> QuestionPolicyComparisonArtifact
-> ValidationRun
-> PolicyArtifact
-> RuntimePointerUpdate
-> PromotionLineageGraph
-> RuntimeBehavior
```

## Policy Families

Initial V30 policy families:

| Family | Purpose |
|---|---|
| `feature_policy` | Feature thresholds, visibility weights, strength boundaries. |
| `structure_policy` | Graph weights, mechanism scoring, structure selection. |
| `mainline_policy` | Mainline candidate ranking and arbitration. |
| `question_policy` | Question intent ranking and next-question recommendation. |
| `answer_policy` | Answer planning, evidence density, boundary behavior. |
| `presentation_policy` | Role/client visibility and language density. |
| `knowledge_policy` | Knowledge pack retrieval and weighting. |
| `rule_policy` | Rule activation, conflict handling, defeasible resolution. |
| `portrait_policy` | Portrait tag selection and projection density. |
| `hidden_factor_policy` | Boundary questions, special-year/repeated-state alignment, hidden factor confidence updates. |

Each family uses the same promotion skeleton:

```text
candidate -> validation -> artifact -> pointer
```

## Core Contracts

### TrainingRun

Required fields:

```text
training_run_id
family
source
input_artifacts
input_cases
base_policy_version
candidate_ids
started_at
finished_at
status
metrics
failure_reasons
```

### PolicyCandidate

Required fields:

```text
candidate_id
family
training_run_id
base_policy_version
change_summary
artifact_payload
expected_improvements
risk_flags
created_at
```

### ValidationRun

Required fields:

```text
validation_run_id
candidate_id
family
tiers
synthetic_results
corpus_518k_results
regression_results
promotion_decision
failure_clusters
created_at
```

### PolicyArtifact

Required fields:

```text
artifact_id
family
candidate_id
version
payload_uri
checksum
metrics
created_at
```

### RuntimePointer

Required fields:

```text
family
active_artifact_id
previous_artifact_id
version
updated_by
validation_run_id
updated_at
rollback_uri
```

## Promotion Rule

V30 promotion should be automatic:

```text
if validation passes required gates:
    publish policy artifact
    update runtime pointer
    record lineage
else:
    reject candidate with failure clusters
```

No default human approval step is required.

Human involvement is allowed for:

- Inspecting failures.
- Triggering rollback.
- Changing promotion thresholds.
- Pausing a policy family.
- Reviewing high-impact model drift.

## Validation Gates

Every promotion must define its required gates.

Minimum gates:

- Contract validation.
- Synthetic smoke validation.
- Regression validation for existing fixtures.
- Drift boundary validation.

For production-capable policy families:

- 518K sample validation.
- Selected shard validation.
- Role/presentation stability validation where relevant.

## Integrated Model Training

Knowledge, rules, features, portraits, and structure dynamics are trained as related but separate policy families.

V30 may generate these candidates in parallel:

```text
feature_policy candidate
rule_policy candidate
structure_policy candidate
portrait_policy candidate
```

But promotion must validate their combined runtime effect.

Required integrated checks:

- Feature changes do not over-trigger rules.
- Rule changes do not create unsupported portraits.
- Structure changes do not shift mainline without evidence.
- Portrait changes do not become a second truth source.
- Question changes remain bound to evidence after upstream policy changes.
- Hidden factor policy changes do not convert hypotheses into facts.
- Expression changes do not leak engineering tokens or drop Bazi boundary language.
- Central brain route changes keep feedback flowing to question, expression, hidden-factor, and context-binding domains.

Synthetic validation is the first integrated gate. 518K sample/shard validation is the distribution gate.

## Current Training Signals

Current synthetic extraction emits and the active mainline is adding:

- `v30.training_signal.krp_unit_coverage`
- `v30.training_signal.per_unit_parameter_tuning`
- `v30.training_signal.macro_dimension_coverage`
- `v30.training_signal.portrait_projection_coverage`
- `v30.training_signal.portrait_projection_view_coverage`
- `v30.training_signal.role_locale_client_projection_coverage`
- `v30.training_signal.real_case_feedback_alignment`
- `v30.training_signal.m1_m2_base_fact_contract`
- `v30.training_signal.ten_god_energy_fusion`
- `v30.training_signal.ranked_decision_fusion`
- `v30.training_signal.m5_weight_replay`
- `v30.training_signal.interaction_state_machine`
- `v30.training_signal.interaction_loop_quality`
- `v30.training_signal.question_model_signal_personalization`
- `v30.training_signal.real_case_calibration_pack`
- `v30.training_signal.question_graph_edge_coverage`
- `v30.training_signal.question_dialogue_outcome`
- `v30.training_signal.central_brain_route_coverage`
- `v30.training_signal.adaptive_question_replay`
- `v30.training_signal.expression_quality`
- `v30.training_signal.llm_output_contract_quality`
- `v30.training_signal.structure_dynamic_competition`
- `v30.training_signal.synthetic_failure_cluster`

Expression quality observes:

- Bazi term count.
- User-visible engineering-token leakage.
- Boundary language presence.
- Role voice.
- Role density.

This keeps expression improvement inside the same train-validate-apply loop. It does not introduce a manual review gate.

## Auto-Apply Safety

Auto-apply does not mean blind apply.

V30 safety comes from:

- Small policy families.
- Versioned artifacts.
- Required validation gates.
- Runtime pointer lineage.
- Fast rollback.
- Failure clustering.
- Canary mode where needed.

## Runtime Consumption

Runtime code reads only V30 pointers:

```text
v30:{env}:policy:{family}
```

Runtime code must not:

- Read V20 pointers.
- Read training scratch files.
- Import training modules in hot paths.
- Mutate policy artifacts during a reading.

## Test Strategy

Training tests are tiered:

- Smoke: one small fixture per family.
- Sample: representative synthetic suite.
- Shard: selected 518K shard.
- Full: large validation run.

Default tests must not run training jobs.

## Open Design Questions

- Which ten-god fusion metrics are mandatory before model-signal policy auto-apply?
- Should `model_signal_summary` tuning live under `structure_policy`, `mainline_policy`, or a dedicated `model_signal_policy`?
- How should visible next-question strategy and internal calibration strategy be compared in artifacts?
- Which real-case calibration failures block release versus only create training candidates?
- Which families need canary mode before full pointer update?
