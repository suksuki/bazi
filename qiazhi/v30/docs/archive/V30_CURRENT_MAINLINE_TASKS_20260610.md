# V30 Current Mainline Task Review

Updated: 2026-06-14

## Review Conclusion

V30 is no longer in "core module build-out" mode. The eight core Bazi modules are sealed for the current product scope. The next mainline is not to reopen M1-M8 by default, and not to start peripheral UI/admin/LLM expansion as the lead task.

Current system state:

| Area | Current judgment | Mainline implication |
|---|---|---|
| M1 BirthInput / deterministic chart facts | Current-scope complete | Do not reopen unless a chart-fact regression appears. |
| M2 Base Bazi fact explanation | Current-scope complete | Keep as deterministic fact layer. |
| M3 Knowledge / rule / portrait / feature / dynamic structure | Current-scope complete, depth-growth continues | Continue source-governed calibration and training, but do not block product flow on exhaustive knowledge expansion. |
| M4 Ten-god energy model | Current-scope complete | Keep bounded model-signal usage; no raw-score customer exposure. |
| M5 Strength / structure / useful-god ranked decisions | Current-scope complete | Keep candidate-bound; no fixed verdict promotion. |
| M6 Practical reading output | Current-scope complete | Continue quality calibration through real cases and feedback. |
| M7 Real-case calibration | Current-scope complete | Expand only with meaningful boundary cases. |
| M8 User presentation / API projection | Current-scope complete | Reconcile documentation and contracts; avoid UI polish as mainline. |
| IQ Intelligent question loop | Steady, high completion | Reopen only on question drift, role leak, or poor business feedback. |
| LLM expression | Bounded steady | LLM supports Bazi expression only; live smoke explicit. |
| BT Training / synthetic / 518K | Steady support system | Run targeted gates routinely; full gates only at major nodes. |
| UI/product shell | Usable current scope | Keep concise; product workflow fixes allowed, but not the mainline unless blocking measurement. |

The previous controlling SYN-CAL3 Synthetic Archetype Training Signal Review task is complete. A product review found a higher-priority core reading output failure: V30 calculates chart facts and module outputs, but the UI/product surface still exposes generic template text instead of usable multi-role Bazi reading. The current controlling next task is:

```text
UI-R1 Core Bazi Reading Productization
```

Reason: this is not UI polish. It is a core measurement usability failure. Domain cards, basic assertions, Bazi paths, features, portraits, intelligent answers, and LLM context must be productized so the system can produce actual Bazi reading output for user/practitioner/admin roles. SYN-CAL4 remains valid but deferred until UI-R1 establishes a product reading acceptance baseline.

Current active subtask:

```text
CORE-CAL-WAIT Await Focused Answer Quality Evidence Or Explicit Major Validation
```

Reason: FULL-REG R1-R6, CORE-EVIDENCE-1/2/3/4/5/6, and CORE-CAL-S1/S2/S3/S4 are complete. Typical synthetic Bazi answer calibration is now a routine targeted validation track with a steady-state evidence queue. Do not reopen M3/M6/LLM/interaction by default; wait for focused answer-quality evidence or an explicit major validation request.

Current wait-state check:

```text
python3 scripts/run_core_answer_calibration_wait_status.py --artifact-dir .runtime/validation/core-answer-calibration-wait
v30.core_answer_calibration_wait_status.v1: passed (5/5) core_cal_wait_answer_quality_evidence_wait_ready
- waiting=True candidates=0 full_pytest=False auto_apply=False
- next=CORE-CAL-WAIT

pytest -q tests/unit/test_core_answer_calibration_wait_status.py
3 passed

pytest -q tests/unit/test_core_answer_calibration_wait_status.py tests/unit/test_core_answer_calibration_steady_state_queue.py tests/unit/test_synthetic_typical_answer_calibration_closeout.py tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
17 passed
```

WAIT result:

- Added `v30.core_answer_calibration_wait_status.v1` and `scripts/run_core_answer_calibration_wait_status.py`.
- The current answer-calibration queue is ready and empty.
- No focused answer fix candidate is queued.
- Full pytest, synthetic-all, full 518K, live LLM, policy pointer promotion, auto-apply training, release, and chart-fact mutation remain blocked by default.

FULL-REG R1 completed:

```text
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614015436539162: eligible mode=sample cases=8 shards=0

pytest -q tests/test_v30_scaffold.py::test_smoke_runtime_and_view_contract tests/unit/test_central_brain.py::test_runtime_exposes_central_brain_trace_as_mainline_coordinator tests/unit/test_runtime_intelligence_spine.py::test_macro_dimension_signals_reach_question_and_answer_context tests/unit/test_synthetic_validation.py::test_synthetic_interaction_loop_tier_passes_customer_followup_contracts tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace tests/unit/test_session_owner_boundary_readiness.py tests/unit/test_llm_context.py tests/unit/test_bazi_llm_context_prompt_readiness.py tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/unit/test_auto_apply_training.py
40 passed
```

R1 repair scope:

- Runtime smoke tests no longer consume workspace `.runtime` policy pointers unless `V30_RUNTIME_DIR` is explicitly set.
- Baseline policy artifacts now carry non-zero structure/question/rule weights, so synthetic gates do not inherit empty policy payloads.
- Customer answer and UI projection remove leaked internal rule/policy fragments while practitioner/admin retain diagnostic role text.
- Interaction-loop single-click expected next question is aligned to the current synthetic contract: career direction now advances to timing pressure while hidden-factor calibration remains internal.
- API Redis cache access is best-effort; repository remains authoritative when Redis is unavailable or blocked by sandbox/network policy.
- Auto-training unit smoke mode avoids repeated 518K/heavy promotion gates; strict mode remains the default for real pointer promotion.

Next FULL-REG step:

```text
FULL-REG R2 Remaining Full-Pytest Failure Cluster Reduction
```

Run targeted failure clusters first. Do not rerun `pytest -q` until the next major-node checkpoint.

FULL-REG R2 completed:

```text
pytest -q tests/unit/test_intelligent_question_chain_readiness.py tests/unit/test_intelligent_question_closeout.py tests/unit/test_m6_practical_reading_closeout.py tests/unit/test_m7_real_case_calibration_closeout.py tests/unit/test_m8_projection_api_contract_closeout.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_real_business_boundary_blocked_input_regression.py tests/unit/test_real_business_api_contract_freeze.py tests/unit/test_synthetic_coverage_manifest.py
31 passed

pytest -q tests/unit/test_iq_intelligent_question_support_review.py tests/unit/test_llm_bazi_expression_support_review.py tests/unit/test_training_synthetic_support_review.py tests/unit/test_brain_training_synthetic_closeout.py
18 passed

python3 scripts/run_training_synthetic_support_review.py --sample-limit 8
v30.training_synthetic_support_review.v1: passed (7/7) training_synthetic_support_ready

python3 scripts/run_brain_training_synthetic_closeout.py --sample-limit 2 --shard-limit 2
v30.brain_training_synthetic_closeout.v1: passed (6/6) bt10_support_systems_steady_state_ready

python3 -m compileall -q v30
passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614024220678512: eligible mode=sample cases=8
```

R2 repair scope:

- Customer projection now filters already answered user questions from the visible question list, while preserving invalid-input retry questions.
- IQ4/IQ5 readiness now advances multi-turn visible next questions instead of repeating the answered question.
- B3 answer-refresh regression accepts the fast LLM path `llm_status=deferred` as valid when the rule-bound answer panel is already present and non-mutating.
- B4/B5 business boundary/API freeze recover through the B3 fix.
- M6/M7/M8 closeout chain recovers through B3/B5 and M6 upstream readiness.
- Synthetic coverage manifest now documents `interaction_brain_structured_constraints`, `latent_bazi_divergence`, `synthetic_archetype_rule_claim`, `synthetic_canonical_bazi_calibration`, and `ui_core_reading_product`.
- Manifest recognizes `latent_bazi_divergence` as a special runner-backed tier with 2 cases instead of treating its `SYNTHETIC_SUITES` placeholder as empty coverage.
- IQ support, LLM support, training synthetic support, and BT10 closeout all recover after M8/IQ5/manifest blockers are removed.

FULL-REG R3 completed:

```text
pytest -q tests/unit/test_release_candidate_review.py tests/unit/test_release_candidate_gate_review.py tests/unit/test_release_boundary_finalization.py tests/unit/test_external_release_blocked_status.py tests/unit/test_external_release_full_pytest_decision.py tests/unit/test_external_release_dry_run.py tests/unit/test_post_release_boundary_authorization.py
26 passed

pytest -q tests/unit/test_controlled_release_readiness.py tests/unit/test_stage_a_release_gate_execution.py tests/unit/test_stage_a_evidence_review.py tests/unit/test_explicit_release_gate_authorization.py tests/unit/test_core_mainline_selection_after_release_hold.py tests/unit/test_mainline_selection_after_release_pause.py tests/unit/test_post_seal_status_review.py
22 passed

pytest -q tests/unit/test_runtime_repository.py tests/unit/test_storage_adapters.py tests/unit/test_518k_validation.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
28 passed

pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_real_bazi_training_calibration_queue.py tests/unit/test_real_bazi_diagnosis_steady_state.py
8 passed

pytest -q tests/unit/test_bazi_backend_api_journey_acceptance.py tests/unit/test_controlled_release_readiness.py tests/unit/test_explicit_release_gate_authorization.py
10 passed

python3 -m compileall -q v30
passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614025905559694: eligible mode=sample cases=8
```

R3 repair scope:

- Backend API journey acceptance now recognizes the fast-sync rule-bound RBD answer boundary as valid when the answer panel is already present and no chart facts mutate.
- RBD claim generation now emits bounded health path claims for dynamic paths that also target health, so the health product card has enough traceable Bazi claims instead of only a portrait and one summary.
- RBD S1.10, S1.11, training calibration queue, diagnosis steady state, REL-S1, REL-S2, controlled release readiness, storage adapter, and release-candidate targeted batches are green.
- Full pytest remains major-node-only; R3 did not rerun full pytest.

FULL-REG R4 completed:

```text
pytest -q tests/unit/test_policy_promotion.py::test_promote_structure_policy_candidate_updates_pointer tests/unit/test_policy_promotion.py::test_promoted_artifact_records_synthetic_validation tests/unit/test_policy_promotion_script.py::test_promote_policy_candidate_script
3 passed

pytest -q tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_runner_passes_targeted_gates tests/unit/test_core_chain_steady_state_summary.py::test_core_chain_summary_runner_passes_targeted_gates tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_runner_passes_targeted_gates tests/unit/test_m6_practical_reading_consumption_hardening.py::test_m6_practical_reading_consumption_runner_passes_targeted_gates
4 passed

pytest -q tests/unit/test_m7_real_case_calibration_steady_state_review.py::test_m7_real_case_calibration_runner_passes_targeted_gates tests/unit/test_productization_closeout.py::test_u5_productization_closeout_accepts_u1_u4_evidence tests/unit/test_productization_closeout.py::test_u5_productization_closeout_script_runs tests/unit/test_synthetic_coverage_manifest.py::test_synthetic_coverage_manifest_accepts_current_and_planned_tiers
4 passed

python3 -m compileall -q v30
passed

.pytest_cache/v/cache/lastfailed
{}
```

R4 repair scope:

- Policy promotion artifacts now sanitize legacy-source names in validation summaries before writing runtime policy artifacts. M3 may still document V20 as migration/reference context, but promoted runtime policy artifacts no longer carry `v20` strings.
- Await-new-calibration, core-chain summary, evidence-driven queue, M6 consumption hardening, M7 steady review, U5 productization, and synthetic manifest lastfailed nodes are green.
- Pytest `lastfailed` cache is empty after R4.

FULL-REG R5 completed:

```text
pytest -q
8 failed, 654 passed, 1 skipped in 4412.88s

Failed buckets:
- question default ordering: user-facing career entry was behind time context boundary
- RBD path engine: path count, 财官印制化 detection, conflict risk wording
- SYN-CAL1/SYN-CAL2/SYN-CAL3/SYN-CAL4: archetype mechanism coverage cascaded from RBD path engine

Targeted repairs:
pytest -q tests/unit/test_real_bazi_path_engine.py tests/unit/test_question_anchor_selector.py::test_question_recommendations_are_evidence_and_policy_driven tests/unit/test_question_anchor_selector.py::test_question_recommendations_consume_central_brain_context tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
7 passed

pytest -q tests/unit/test_synthetic_archetype_rule_claim_calibration.py::test_syn_cal1_runner_passes_current_runtime_archetypes tests/unit/test_synthetic_archetype_tier_registration.py::test_syn_cal2_runner_passes_current_registration tests/unit/test_synthetic_archetype_training_signal_review.py::test_syn_cal3_training_signal_review_ready tests/unit/test_synthetic_archetype_calibration_closeout.py::test_syn_cal4_closeout_ready
4 passed

pytest -q --lf
3 passed

pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py tests/unit/test_synthetic_archetype_tier_registration.py tests/unit/test_synthetic_archetype_training_signal_review.py tests/unit/test_synthetic_archetype_calibration_closeout.py
15 passed

python3 -m compileall -q v30
passed

python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim
v30.synthetic.synthetic_archetype_rule_claim: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614050008435538: eligible mode=sample cases=8

.pytest_cache/v/cache/lastfailed
{}
```

R5 repair scope:

- Default question ordering now keeps explicit user Bazi questions first unless central brain explicitly chooses `context_first_question_strategy`.
- RBD path engine now recognizes 财官印制化 from wealth-resource pressure paths, preserves 食伤生财 / 食伤制官杀 as distinct mechanisms, emits supplemental mechanism paths from existing dynamic evidence, and keeps conflict risk statements bounded.
- SYN-CAL1-4 recovered through the path engine fix; no chart facts, policy pointers, or real-person labels were changed.
- Full pytest was run once as a major-node recheck and then failures were repaired with targeted tests only.

FULL-REG R6 completed:

```text
pytest -q
1 failed, 661 passed, 1 skipped in 4369.17s

Failed bucket:
- question policy explicit hidden_factor boost was overridden by default user-question-first ranking

Targeted repair:
pytest -q tests/unit/test_question_anchor_selector.py
10 passed

pytest -q tests/unit/test_question_anchor_selector.py::test_question_policy_payload_can_change_recommendation_order
1 passed

python3 -m compileall -q v30
passed

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)

.pytest_cache/v/cache/lastfailed
{}
```

R6 repair scope:

- The default user-question-first boost now yields to explicit hidden-factor topic policy boosts.
- Central-brain `context_first_question_strategy` still keeps time-context questions first when intentionally selected.
- No chart facts, runtime policy pointers, or M3/RBD evidence payloads were changed in R6.
- Full pytest was run once for final confirmation; the remaining single failure was repaired with targeted tests only.

Next mainline step:

```text
CORE-MAINLINE-NEXT Module/Product Evidence Review: completed by CORE-EVIDENCE-1/2
```

This historical step is complete through CORE-EVIDENCE-1 and CORE-EVIDENCE-2. Do not rerun full pytest unless another major node requires it. Routine checks should remain targeted module gates, synthetic tiers, and 518K sample/shard as needed.

CORE-EVIDENCE-1 completed:

```text
python3 scripts/run_main_module_completion_review.py
v30.main_module_completion_review.v1: passed (5/5) mcr1_main_module_review_ready

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
passed=10/10

python3 scripts/run_real_bazi_product_reading_acceptance.py
v30.real_bazi_product_reading_acceptance.v1: passed (6/6) rbd_s110_product_reading_accepted

python3 scripts/run_productization_closeout.py
v30.productization_closeout.v1: passed (5/5) u5_productization_steady_state_ready

python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

python3 scripts/run_multi_user_terminal_locale_readiness.py
v30.multi_user_terminal_locale_readiness.v1: passed (7/7) u1_projection_readiness_ready

python3 scripts/run_bazi_llm_role_locale_production_smoke.py
v30.bazi_llm_role_locale_production_smoke.v1: passed (5/5) bl7_bazi_llm_role_locale_smoke_ready

python3 scripts/run_bazi_backend_api_journey_acceptance.py
v30.bazi_backend_api_journey_acceptance.v1: passed (6/6) ir2_bazi_backend_api_journey_accepted

pytest -q tests/unit/test_main_module_completion_review.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_ui_core_reading_product_synthetic.py tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_productization_closeout.py tests/unit/test_multi_user_terminal_locale_readiness.py tests/unit/test_bazi_llm_role_locale_production_smoke.py tests/unit/test_bazi_backend_api_journey_acceptance.py
17 passed
```

CORE-EVIDENCE-1 conclusion:

- Main module completion, RBD product reading, UI core reading product acceptance, U5 productization, role/locale projection, LLM role-locale smoke, and backend customer journey are green after FULL-REG R1-R6.
- This confirms the current module chain can support Bazi product measurement at the contract level.
- This does not claim final answer quality is complete; it confirms the product/module gates are ready for answer-quality delta review.

Next mainline step:

```text
CORE-EVIDENCE-2 Answer Quality Delta Review
```

Review the actual generated Bazi reading and intelligent Q&A output against the current M3/RBD/M5/M6 evidence. Focus on whether the answer text uses concrete Bazi mechanisms, dynamic paths, portraits, features, time layers, and role/locale context without generic filler. Use targeted product/answer gates only.

Reference:

```text
docs/V30_LATENT_BAZI_ATTRIBUTES_SYSTEM_PLAN.md
docs/V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md
```

`CORE-CAL-S0` remains the steady-state queue. Full pytest, synthetic-all, full 518K, and live LLM remain explicit major-node actions.

CORE-EVIDENCE-2 completed:

```text
python3 scripts/run_answer_quality_delta_review.py
v30.answer_quality_delta_review.v1: core_evidence_2_answer_quality_ready
answer_quality_delta_ready=True
passed=40/40
next=CORE-EVIDENCE-3 LLM Prompt Context Delta Review

pytest -q tests/unit/test_answer_quality_delta_review.py
2 passed

pytest -q tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_real_business_bazi_reading_acceptance.py tests/unit/test_answer_quality_delta_review.py
6 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
passed=10/10

python3 scripts/run_real_business_bazi_reading_acceptance.py
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted
```

CORE-EVIDENCE-2 result:

- Added `v30.answer_quality_delta_review.v1` and `scripts/run_answer_quality_delta_review.py`.
- The gate checks career, wealth, relationship, timing, and hidden-factor-related answer anchors.
- Each answer must contain domain-specific Bazi language, mechanism/path/portrait/feature evidence, boundary language, and traceable evidence ids.
- Generic/system filler such as old candidate-placeholder phrases and internal policy tokens is blocked.
- Full pytest remains major-node-only; this step used targeted answer/product gates.

Next mainline step:

```text
CORE-EVIDENCE-3 LLM Prompt Context Delta Review
```

Verify LLM context packs and prompt contracts for domain follow-up answers. The goal is stronger Bazi expression from the LLM while keeping M1/M2 chart facts, M3 evidence, M4 signals, M5 ranked decisions, M6 practical reading, role/locale, and hidden-attribute state as bounded context layers instead of one growing prompt dump.

CORE-EVIDENCE-3 completed:

```text
python3 scripts/run_llm_prompt_context_delta_review.py
v30.llm_prompt_context_delta_review.v1: core_evidence_3_llm_prompt_context_ready
llm_prompt_context_delta_ready=True
passed=64/64
next=CORE-EVIDENCE-4 LLM Answer Output Delta Review

pytest -q tests/unit/test_llm_prompt_context_delta_review.py
3 passed

pytest -q tests/unit/test_bazi_llm_context_prompt_readiness.py
6 passed

pytest -q tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/unit/test_bazi_llm_role_locale_production_smoke.py tests/unit/test_llm_prompt_context_delta_review.py
19 passed

python3 scripts/run_bazi_llm_answer_generator_readiness.py
v30.bazi_llm_answer_generator_readiness.v1: passed (5/5) bl4_bazi_llm_answer_generator_ready

python3 scripts/run_bazi_llm_output_acceptance_readiness.py
v30.bazi_llm_output_acceptance_readiness.v1: passed (5/5) bl5_bazi_llm_output_acceptance_ready

python3 scripts/run_bazi_llm_role_locale_production_smoke.py
v30.bazi_llm_role_locale_production_smoke.v1: passed (5/5) bl7_bazi_llm_role_locale_smoke_ready
```

CORE-EVIDENCE-3 result:

- `domain_followup` LLM context now includes M3 structure dynamics, M4 model signals, M5 ranked decisions, M6 practical reading, interaction state, and known user signals.
- Added `v30.llm_prompt_context_delta_review.v1` and `scripts/run_llm_prompt_context_delta_review.py`.
- The new gate verifies task-specific prompt packs, domain follow-up coverage for career/wealth/relationship/timing, read-only fact boundaries, no raw runtime payload, verifier/fallback presence, and bounded prompt budgets.
- Live LLM execution remains explicit-only; this step validates prompt/context shape and adjacent LLM output contracts.

Next mainline step:

```text
CORE-EVIDENCE-4 LLM Answer Output Delta Review
```

Review LLM answer output acceptance and fallback text quality against the strengthened context packs. The focus is whether output actually uses concrete Bazi mechanisms and role-specific expression while preserving verified chart facts.

CORE-EVIDENCE-4 completed:

```text
python3 scripts/run_llm_answer_output_delta_review.py
v30.llm_answer_output_delta_review.v1: core_evidence_4_llm_answer_output_ready
llm_answer_output_delta_ready=True
passed=29/29
next=CORE-EVIDENCE-5 Runtime Answer Integration Delta Review

pytest -q tests/unit/test_llm_answer_output_delta_review.py
3 passed

pytest -q tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_llm_answer_output_delta_review.py
16 passed

python3 scripts/run_bazi_llm_answer_generator_readiness.py
v30.bazi_llm_answer_generator_readiness.v1: passed (5/5) bl4_bazi_llm_answer_generator_ready

python3 scripts/run_bazi_llm_output_acceptance_readiness.py
v30.bazi_llm_output_acceptance_readiness.v1: passed (5/5) bl5_bazi_llm_output_acceptance_ready

python3 scripts/run_llm_prompt_context_delta_review.py
v30.llm_prompt_context_delta_review.v1: core_evidence_3_llm_prompt_context_ready
passed=64/64
```

CORE-EVIDENCE-4 result:

- `validate_bazi_llm_output_payload` now includes content-quality checks, not just schema/role/drift checks.
- Customer/domain/practitioner LLM outputs must contain chart/day-master language, Bazi mechanism language, and domain or evidence-layer language.
- Domain follow-up output must include selected-domain language.
- Hidden-factor dialogue output must be constrained feedback language, not an open-ended hidden-factor lecture.
- Generic placeholder output is rejected even if schema, role, and drift checks pass.
- Added `v30.llm_answer_output_delta_review.v1` and `scripts/run_llm_answer_output_delta_review.py`.

Next mainline step:

```text
CORE-EVIDENCE-5 Runtime Answer Integration Delta Review
```

Verify the runtime answer panel, API answer refresh, and product projection use this strengthened LLM acceptance/fallback path end to end without exposing internal diagnostics or weakening Bazi-specific answer text.

CORE-EVIDENCE-5 completed:

```text
python3 scripts/run_runtime_answer_integration_delta_review.py
v30.runtime_answer_integration_delta_review.v1: core_evidence_5_runtime_answer_integration_ready
runtime_answer_integration_ready=True
passed=27/27
next=CORE-EVIDENCE-6 Core Evidence Closeout And Documentation Sync

pytest -q tests/unit/test_runtime_answer_integration_delta_review.py
2 passed

pytest -q tests/unit/test_runtime_answer_integration_delta_review.py tests/unit/test_bazi_backend_api_journey_acceptance.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/unit/test_llm_answer_output_delta_review.py
17 passed

python3 scripts/run_bazi_backend_api_journey_acceptance.py
v30.bazi_backend_api_journey_acceptance.v1: passed (6/6) ir2_bazi_backend_api_journey_accepted

python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready
```

CORE-EVIDENCE-5 result:

- Added `v30.runtime_answer_integration_delta_review.v1` and `scripts/run_runtime_answer_integration_delta_review.py`.
- The gate validates runtime answer panels after question outcome, API answer refresh, and API LLM enhancement with a mock provider.
- Customer answer panels must keep Bazi-specific text, safe LLM metadata, product context layers, and stable chart facts.
- API LLM enhancement can accept a high-quality Bazi output without live provider execution and without exposing internal prompt/context ids to customers.
- Full pytest and live LLM remain explicit-only.

Next mainline step:

```text
CORE-EVIDENCE-6 Core Evidence Closeout And Documentation Sync
```

Close the CORE-EVIDENCE chain, update module completion status, and define the next non-peripheral core task only after the current evidence chain is recorded.

CORE-EVIDENCE-6 completed:

```text
python3 scripts/run_core_evidence_closeout.py
v30.core_evidence_closeout.v1: core_evidence_6_closeout_ready
core_evidence_closeout_ready=True
passed=160/160
next=CORE-CAL-S1 Synthetic Typical Bazi Answer Calibration Pack

pytest -q tests/unit/test_core_evidence_closeout.py
2 passed

pytest -q tests/unit/test_core_evidence_closeout.py tests/unit/test_answer_quality_delta_review.py tests/unit/test_llm_prompt_context_delta_review.py tests/unit/test_llm_answer_output_delta_review.py tests/unit/test_runtime_answer_integration_delta_review.py
12 passed

python3 scripts/run_answer_quality_delta_review.py
v30.answer_quality_delta_review.v1: core_evidence_2_answer_quality_ready
passed=40/40

python3 scripts/run_runtime_answer_integration_delta_review.py
v30.runtime_answer_integration_delta_review.v1: core_evidence_5_runtime_answer_integration_ready
passed=27/27
```

CORE-EVIDENCE-6 result:

- Added `v30.core_evidence_closeout.v1` and `scripts/run_core_evidence_closeout.py`.
- CORE-EVIDENCE-2 through CORE-EVIDENCE-5 are now summarized by one closeout gate.
- The closeout confirms no full pytest, live LLM execution, chart-fact mutation, or policy pointer promotion is required for the evidence chain.
- The next task is deliberately core calibration: synthetic typical Bazi answer patterns.

Next mainline step:

```text
CORE-CAL-S1 Synthetic Typical Bazi Answer Calibration Pack
```

Build a synthetic representative chart pack for answer calibration. It should cover typical strong/weak, 官印相生, 财官印制化, 食伤生财, 食伤制官杀, 比劫争财, relationship/health/timing stress, and hidden-attribute divergence cases, then validate actual answer text against expected mechanism coverage and boundaries.

CORE-CAL-S1 completed:

```text
python3 scripts/run_synthetic_typical_bazi_answer_calibration.py
v30.synthetic_typical_bazi_answer_calibration.v1: core_cal_s1_synthetic_typical_answer_calibration_ready
passed=5/5 ready=True
next=CORE-CAL-S2 Synthetic Typical Answer Tier Registration And Training Signals

python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer
v30.synthetic.synthetic_typical_bazi_answer: passed (3/3)

pytest -q tests/unit/test_synthetic_typical_bazi_answer_calibration.py
3 passed

pytest -q tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_answer_quality_delta_review.py tests/unit/test_core_evidence_closeout.py tests/unit/test_synthetic_coverage_manifest.py
10 passed

python3 scripts/run_core_evidence_closeout.py
v30.core_evidence_closeout.v1: core_evidence_6_closeout_ready
passed=160/160
```

CORE-CAL-S1 result:

- Added `v30.synthetic_typical_bazi_answer_calibration.v1` and `scripts/run_synthetic_typical_bazi_answer_calibration.py`.
- Registered `synthetic_typical_bazi_answer` in the synthetic validation manifest and suite registry.
- The gate validates representative customer answers for career, wealth, relationship, timing, and hidden-attribute feedback cases.
- Answer text must include Bazi chart/day-master language, domain mechanisms, evidence-backed boundaries, and no internal policy/rule-id/English guidance leakage.
- M3 guidance text was cleaned so runtime answer/portrait projections no longer leak implementation phrases such as English policy guidance or rule ids.
- Full pytest, live LLM, policy pointer promotion, and full 518K remain explicit-only.

Next mainline step:

```text
CORE-CAL-S2 Synthetic Typical Answer Tier Registration And Training Signals
```

Expose the new typical-answer synthetic tier through training signal summaries, calibration artifacts, and documentation so answer quality can be iterated by M3/M6/LLM/interaction calibration instead of ad hoc wording changes.

CORE-CAL-S2 completed:

```text
python3 scripts/run_synthetic_typical_answer_training_signal_review.py
v30.synthetic_typical_answer_training_signal_review.v1: passed (6/6) core_cal_s2_training_signal_review_ready
- signals=5 queue_items=0 auto_apply=False
- next=CORE-CAL-S3

pytest -q tests/unit/test_synthetic_typical_answer_training_signal_review.py
3 passed

pytest -q tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
9 passed
```

CORE-CAL-S2 result:

- Added `v30.synthetic_typical_answer_training_signal_review.v1` and `scripts/run_synthetic_typical_answer_training_signal_review.py`.
- Derived five review-only training signals from S1 answer calibration and the `synthetic_typical_bazi_answer` tier:
  `synthetic_typical_answer_m3_guidance_sanitization`,
  `synthetic_typical_answer_m6_domain_mechanism_specificity`,
  `synthetic_typical_answer_llm_expression_boundary`,
  `synthetic_typical_answer_interaction_answer_alignment`,
  and `synthetic_typical_answer_review_boundary_safety`.
- Signals route only to M3, M6, LLM, and interaction calibration. They cannot mutate chart facts, auto-apply training, promote policy pointers, trigger release, or require live LLM/full 518K/full pytest.

Next mainline step:

```text
CORE-CAL-S3 Synthetic Typical Answer Calibration Closeout
```

Record S1/S2 as the routine typical-answer calibration track, define cadence, and keep future answer-quality tuning evidence-driven rather than wording patches.

CORE-CAL-S3 completed:

```text
python3 scripts/run_synthetic_typical_answer_calibration_closeout.py
v30.synthetic_typical_answer_calibration_closeout.v1: passed (6/6) core_cal_s3_synthetic_typical_answer_calibration_closed
- signals=5 queue_items=0 auto_apply=False full_pytest=False
- next=CORE-CAL-S4

pytest -q tests/unit/test_synthetic_typical_answer_calibration_closeout.py
2 passed

pytest -q tests/unit/test_synthetic_typical_answer_calibration_closeout.py tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
11 passed
```

CORE-CAL-S3 result:

- Added `v30.synthetic_typical_answer_calibration_closeout.v1` and `scripts/run_synthetic_typical_answer_calibration_closeout.py`.
- Frozen evidence now records S1 typical-answer calibration, S2 training signal review, the `synthetic_typical_bazi_answer` tier, and case summary.
- Routine cadence is defined for M3 guidance, M6 answer composition, LLM prompt/context/acceptance, and interaction answer refresh changes.
- Heavy gates remain explicit-only: full pytest, synthetic-all, full 518K, and live LLM smoke.

Next mainline step:

```text
CORE-CAL-S4 Core Answer Calibration Steady-State Queue
```

Keep the typical-answer tier as a routine targeted gate, expose any future answer-quality gaps as review-only queue items, and avoid changing M3/M6/LLM/interaction logic without fresh evidence.

CORE-CAL-S4 completed:

```text
python3 scripts/run_core_answer_calibration_steady_state_queue.py --artifact-dir .runtime/validation/core-answer-calibration-s4
v30.core_answer_calibration_steady_state_queue.v1: passed (8/8) core_cal_s4_answer_calibration_steady_state_queue_ready
- waiting=True candidates=0 full_pytest=False auto_apply=False
- next=CORE-CAL-WAIT

pytest -q tests/unit/test_core_answer_calibration_steady_state_queue.py
3 passed

pytest -q tests/unit/test_core_answer_calibration_steady_state_queue.py tests/unit/test_synthetic_typical_answer_calibration_closeout.py tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
14 passed

python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer
v30.synthetic.synthetic_typical_bazi_answer: passed (3/3)
```

CORE-CAL-S4 result:

- Added `v30.core_answer_calibration_steady_state_queue.v1` and `scripts/run_core_answer_calibration_steady_state_queue.py`.
- The queue accepts answer-quality evidence from `answer_quality_delta_review`, `synthetic_typical_bazi_answer`, `runtime_answer_integration`, `business_answer_refresh`, `llm_output_acceptance`, and `user_feedback_answer_quality`.
- Queue targets are limited to M3, M6, LLM, and interaction.
- Queue items are review-only; no chart-fact mutation, no auto-apply training, no policy pointer promotion, no release trigger, and no default full pytest/synthetic-all/full 518K/live LLM.

Next mainline step:

```text
CORE-CAL-WAIT Await Focused Answer Quality Evidence Or Explicit Major Validation
```

Serve the current system, collect concrete answer-quality evidence, and run the S1-S4 targeted chain only when answer logic changes or a major node is explicitly requested.

Latest CORE-CAL-WAIT status:

```text
python3 scripts/run_core_answer_calibration_wait_status.py --artifact-dir .runtime/validation/core-answer-calibration-wait
v30.core_answer_calibration_wait_status.v1: passed (5/5) core_cal_wait_answer_quality_evidence_wait_ready
- waiting=True candidates=0 full_pytest=False auto_apply=False
- next=CORE-CAL-WAIT
```

No next implementation task is selected from this track until focused answer-quality evidence appears or a major validation/release check is explicitly requested.

UIB-2 evidence:

```text
pytest -q tests/unit/test_interaction_constraints.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
9 passed

pytest -q tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context
2 passed
```

## Latest Evidence

LLM-PERF1 fast answer path:

```text
pytest -q tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py
12 passed

python3 scripts/run_bazi_llm_answer_generator_readiness.py
v30.bazi_llm_answer_generator_readiness.v1: passed (5/5) bl4_bazi_llm_answer_generator_ready

python3 scripts/run_bazi_llm_output_acceptance_readiness.py
v30.bazi_llm_output_acceptance_readiness.v1: passed (5/5) bl5_bazi_llm_output_acceptance_ready

python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id perf-review-fast-001
v30.production_api_smoke.v1: passed

local segmented probe:
create=0.437s view=0.062s answer=0.341s
llm_status=deferred
llm_reason=sync_mode_fast_llm_deferred
llm_executed=false
```

Completed:

- Added `V30_LLM_SYNC_MODE=fast` as the default production answer path.
- Answer API returns rule/RBD answer without waiting for remote Ollama/Gemma.
- Explicit synchronous LLM remains available through `V30_LLM_SYNC_MODE=blocking`.
- Real env LLM budget reduced to `V30_LLM_HTTP_TIMEOUT_SEC=6` and `V30_LLM_MAX_TOKENS=220`.
- Ollama provider timeout no longer forces a minimum 30s wait.
- Plan recorded in `docs/V30_LLM_INTERACTION_PERFORMANCE_PLAN.md`.

LLM-PERF2.5 optional answer enhancement endpoint:

```text
python3 -m compileall -q v30/api/app.py v30/llm/client.py
passed

pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading tests/test_v30_scaffold.py::test_admin_bazi_llm_answer_generator_readiness_endpoint_is_read_only
3 passed

node --check frontend/app.js
passed

pytest -q tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py
12 passed

local segmented probe:
answer=0.371s
answer_llm_status=deferred
enhance=9.923s
enhancement_status=accepted
llm_executed=true
```

Completed:

- Added `POST /api/v30/readings/{reading_id}/questions/{question_id}/answer/llm`.
- Main answer API stays fast; optional LLM endpoint can enhance answer after the user already sees RBD output.
- Frontend now calls optional LLM enhancement in the background when `answer_panel.llm_metadata.status=deferred`.
- Capabilities contract exposes `enhance_answer_with_llm` and `llm_answer_enhancement_mode`.

Core Bazi Reading Claim Quality And Synthetic Archetype Calibration:

```text
python3 -m compileall -q v30/runtime.py v30/presentation/client_model.py v30/validation/ui_core_reading_product_acceptance.py v30/validation/synthetic_archetype_rule_claim_calibration.py
passed

pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py
11 passed

python3 scripts/run_real_bazi_product_reading_acceptance.py
v30.real_bazi_product_reading_acceptance.v1: passed (6/6) rbd_s110_product_reading_accepted

python3 scripts/run_synthetic_archetype_rule_claim_calibration.py
v30.synthetic_archetype_rule_claim_calibration.v1: syn_cal1_archetype_rule_claim_calibration_ready
- cases: 4/4
- failed_case_ids: none
- queue_items: 0

python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim
v30.synthetic.synthetic_archetype_rule_claim: passed (4/4)
```

RBD-S1.11-CQ distribution replay claim-quality hardening:

```text
python3 -m compileall -q v30/validation/real_bazi_distribution_replay.py
passed

pytest -q tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_real_bazi_product_reading_acceptance.py
4 passed

python3 scripts/run_real_bazi_distribution_replay.py
v30.real_bazi_distribution_replay.v1: passed (6/6) rbd_s111_distribution_replay_ready
- real_case=8/8 sample_518k=8/8

pytest -q tests/unit/test_real_bazi_training_calibration_queue.py tests/unit/test_real_bazi_diagnosis_steady_state.py
4 passed

python3 scripts/run_real_bazi_diagnosis_steady_state.py
v30.real_bazi_diagnosis_steady_state.v1: passed (6/6) rbd_s113_steady_state_ready
- signals=5 queue_items=2 next=RBD-S1-WAIT
```

Completed:

- Added `v30.core_bazi_claim_quality.v1` to RBD-backed practical domain readings.
- Customer projection now exposes claim-quality flags without raw trace.
- UI-R1 acceptance and SYN-CAL1 archetype review now validate that domain cards use traceable Bazi claims and do not fall back to generic candidate-language.
- Customer structure dynamic paths now expose concrete `diagnosis_statement` text derived from ten-god path chains.
- RBD-S1.11 distribution replay now requires all five product domains to pass `core_claim_quality` over real-case calibration rows and generated 518K sample rows.
- RBD-S1.12 now emits `v30.training_signal.rbd_core_claim_quality` as a read-only training signal.
- Full pytest, synthetic-all, live LLM, and full 518K remain major-node explicit actions.

UI-R1.10 product-level synthetic validation:

```text
python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_ui_core_reading_product_synthetic.py
9 passed
```

UI-R1.11 customer answer surface cleanup:

```text
pytest -q tests/unit/test_answer_composer.py tests/unit/test_presentation_projection.py::test_customer_answer_panel_filters_internal_diagnostic_text tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions tests/unit/test_bazi_llm_output_acceptance_readiness.py::test_bazi_llm_rejects_customer_answer_internal_chinese_sections tests/unit/test_bazi_llm_output_acceptance_readiness.py::test_bazi_llm_rejects_customer_role_diagnostic_leak tests/unit/test_ui_core_reading_product_acceptance.py::test_ui_r1_acceptance_records_current_product_blockers
7 passed
```

Completed:

- Customer-facing answer text removes internal sections such as `基础判断`, `路径复核`, `特征画像`, evidence counts, and LLM status labels.
- Practitioner/admin answer projection keeps diagnostic lines in structured `role_adaptation` fields rather than mixing them into the reading text.
- Runtime answer selection now prefers the first `user_question` recommendation; hidden-attribute calibration probes can rank highly for the brain but do not become the default product answer panel.
- UI-R1 product acceptance remains ready after the hidden-attribute question priority change.

SYN-CAL4 synthetic archetype calibration closeout:

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

CORE-CAL-S0 core calibration steady-state queue:

```text
python3 -m compileall -q v30/validation/core_calibration_steady_state_queue.py scripts/run_core_calibration_steady_state_queue.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_core_calibration_steady_state_queue.py
3 passed

pytest -q tests/unit/test_core_calibration_steady_state_queue.py tests/unit/test_synthetic_archetype_calibration_closeout.py tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_ready tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_blocks_candidates_or_queue_gap tests/unit/test_await_new_calibration_evidence_status.py::test_await_new_calibration_evidence_status_blocks_missing_sources_or_heavy_gate tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_ready tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_reports_focused_candidates tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_blocks_core_or_queue_gap tests/unit/test_evidence_driven_calibration_queue.py::test_evidence_driven_calibration_queue_blocks_heavy_default_gate
12 passed
```

Note: `scripts/run_core_calibration_steady_state_queue.py` is available, but it calls the older E/W sample chain and is treated as targeted-but-heavier. It is not required for every small subtask.

Recent M3 / training / 518K run:

```text
M3 snapshot:
v30.m3.snapshot.20260610052254738537
krp=54 rules=9 portrait_assets=7 synthetic=8/8
db: postgres searchable=True rows={'knowledge_units': 54, 'rule_specs': 9, 'portrait_assets': 7, 'validation_snapshots': 1}

M3 synthetic:
v30.synthetic.m3_core_spine: passed (8/8)

Training synthetic:
v30.synthetic.training_pipeline: passed (91/91)

518K sample:
v30.518k.sample.20260610061011596029: eligible mode=sample cases=8 shards=0

518K shard:
v30.518k.shard.20260610061046503507: eligible mode=shard cases=16 shards=7

518K readiness:
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready

M3-G3 training candidate review:
v30.m3_training_candidate_review.v1: passed (7/7) m3_g3_training_candidate_review_ready candidates=8

M3-G4 source extraction backlog:
v30.m3_source_extraction_backlog.v1: passed (6/6) m3_g4_source_extraction_backlog_ready rows=6

M3-G5 backlog review surface:
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=6 backend=json_fallback_generated_backlog
filtered useful_god: passed rows=3

M3-G6 source backlog closeout:
v30.m3_source_backlog_closeout.v1: passed (5/5) m3_g6_source_backlog_closeout_ready candidates=8 backlog_rows=6

M5-H1 evidence consumption hardening:
v30.m5_evidence_consumption_hardening.v1: passed (7/7) m5_evidence_consumption_hardening_ready domains=3 scores=17
m5_ranked_decision_contract: passed (30/30)
strength_structure_useful_god: passed (1/1)

M5-H2 calibration replay review:
v30.m5_calibration_replay_review.v1: passed (6/6) m5_calibration_replay_review_ready cases=51 complete=51 close_candidates=51
m5_ranked_decision_contract: passed (30/30)
strength_structure_useful_god: passed (1/1)
real_case_calibration_pack: passed (30/30)

M5-H3 calibration replay closeout:
v30.m5_calibration_replay_closeout.v1: passed (6/6) m5_calibration_replay_closed cases=51 complete=51 close_candidates=51 next=M6 Practical Reading Consumption Hardening
m5_ranked_decision_contract: passed (30/30)
real_case_calibration_pack: passed (30/30)

M6-H1 practical reading consumption hardening:
v30.m6_practical_reading_consumption_hardening.v1: passed (8/8) m6_practical_reading_consumption_hardening_ready domains=125 next=M6 Practical Reading Closeout
m6_practical_reading_contract: passed (30/30)
real_case_calibration_pack: passed (30/30)

M6-H2 practical reading closeout:
v30.m6_practical_reading_closeout.v1: passed (7/7) m6_practical_reading_closed domains=125 next=M7 Real-Case Calibration Steady-State Review
m6_practical_reading_contract: passed (30/30)
real_case_calibration_pack: passed (30/30)

M7-S1 real-case calibration steady-state review:
v30.m7_real_case_calibration_steady_state_review.v1: passed (7/7) m7_real_case_calibration_steady_state_ready fixtures=30 next=M7 Real-Case Calibration Closeout
real_case_calibration_pack: passed (30/30)

M7-S2 real-case calibration closeout:
v30.m7_real_case_calibration_closeout.v1: passed (6/6) m7_real_case_calibration_closed fixtures=30 next=M8 Projection/API Contract Closeout
real_case_calibration_pack: passed (30/30)

M8-S1 projection/API contract closeout:
v30.m8_projection_api_contract_closeout.v1: passed (6/6) m8_projection_api_contract_closed contracts=25 next=IQ Intelligent Question Support Review
m8_api_projection_contract: passed (30/30)

IQ-S1 intelligent question support review:
v30.iq_intelligent_question_support_review.v1: passed (6/6) iq_intelligent_question_support_ready interaction=5 next=LLM Bazi Expression Support Review
interaction_loop: passed (5/5)

LLM-S1 Bazi expression support review:
v30.llm_bazi_expression_support_review.v1: passed (6/6) llm_bazi_expression_support_ready acceptance=5 next=Training/Synthetic Support Review
bazi_llm_acceptance: passed (5/5)

BT-S1 training/synthetic support review:
v30.training_synthetic_support_review.v1: passed (7/7) training_synthetic_support_ready training=91 signals=33 sample518k=8 next=Core Chain Steady-State Summary
training_pipeline: passed (91/91)
518K sample: v30.518k.sample.20260611225420867821 eligible cases=8 json_fallback

S-S1 core chain steady-state summary:
v30.core_chain_steady_state_summary.v1: passed (5/5) core_chain_steady_state_ready modules=13 next=Evidence-Driven Calibration Queue
pytest -q tests/unit/test_core_chain_steady_state_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

E-S1 evidence-driven calibration queue:
v30.evidence_driven_calibration_queue.v1: passed (4/4) evidence_driven_calibration_queue_ready candidates=0 next=Await New Calibration Evidence
pytest -q tests/unit/test_evidence_driven_calibration_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

W-S1 await new calibration evidence status:
v30.await_new_calibration_evidence_status.v1: passed (4/4) await_new_calibration_evidence_ready waiting=True next=Await Evidence Or Explicit Major Validation
pytest -q tests/unit/test_await_new_calibration_evidence_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

RBD audit:
FeatureEvidence=33 KRP=72 dynamic_paths=12 wealth_paths=7 career_paths=12 relationship_paths=10 health_paths=12 useful_god_paths=12
Finding: internal evidence exists, but customer-facing domain summaries remain generic and do not yet produce concrete traceable Bazi diagnosis claims.
```

Recent UI/product fixes:

- BirthInput and Bazi profile forms now use dropdowns for year/month/day/hour/minute.
- Chart UI now renders pillars as upper heavenly stem / lower earthly branch.
- Four pillars, flow-year, luck-cycle, and time-layer pillars show ten-god annotations.
- Customer reading UI is aligned to the latest concise Bazi-product design: user pages now hide trace/policy/boundary/system wording, use natural terms such as 命盘/命局判断/继续追问/补充线索, and keep diagnostics visible only for practitioner/admin roles.
- Admin UI copy now focuses on database, Redis, LLM, training, validation, and measurement operations while avoiding product-facing engineering terms on customer surfaces.
- These are presentation changes only; they do not mutate chart facts.

UI core reading review 2026-06-13:

```text
Sample BirthInput: 1990-02-04 23:30 Beijing female
Four pillars: 庚午 / 戊寅 / 庚子 / 戊子
Current luck: 甲戌 2020-2029
Flow year 2026: 丙午
Day master: 庚金
```

Finding:

- Deterministic calculation works.
- Domain cards remain generic.
- Basic assertions are not productized.
- M3/RBD Bazi features and portraits are underused.
- Bazi paths are visible as abstract chains but not expressed as practical reading.
- Intelligent Q&A can answer the wrong domain: a wealth question produced career-heavy text.
- LLM is acting mostly as a loose expression rewrite, not a strong task-specific Bazi synthesis layer.

New mainline plan:

```text
docs/V30_UI_CORE_READING_PRODUCTIZATION_PLAN.md
```

UI-R1.1 product acceptance audit:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=4/9
failed=basic_assertions_present, bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.2 Basic Assertion Projection

pytest -q tests/unit/test_ui_core_reading_product_acceptance.py
2 passed
```

Interpretation:

- M1/M2 calculation for the sample is ready: four pillars, day master, current luck, and flow year are available.
- The next blocker is not more UI layout work. It is productizing module-backed Bazi reading content in this order: basic assertions, M3 features/portraits, path rows, role-specific answer text, then LLM product context-pack alignment.

UI-R1.2 basic assertion projection:

```text
python3 -m compileall -q v30/presentation/client_model.py v30/validation/ui_core_reading_product_acceptance.py scripts/run_ui_core_reading_product_acceptance.py
passed

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=5/9
failed=bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.3 Bazi Feature And Portrait Projection
```

Added:

- `reading_surface.basic_assertions`
- `core_bazi_reading.basic_assertions`
- assertion kinds: day master, strength, structure, useful-god direction, luck/flow, risk boundary
- source module labels and evidence labels for each assertion

UI-R1.3 Bazi feature and portrait projection:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=6/9
failed=bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.4 Bazi Path Reading Projection
```

Added:

- `reading_surface.bazi_features`
- `reading_surface.bazi_portraits`
- customer-safe rows without raw ids
- practitioner/admin evidence-linked rows
- product statement cleanup for raw source notation

UI-R1.4 Bazi path reading projection:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=7/9
failed=role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.8 Multi-Role Reading Surfaces
```

Added:

- `reading_surface.bazi_paths`
- `domain_cards[].path_summary`
- `domain_cards[].path_assertions`
- practical path rows for 官印相生、财官印制化、食伤生财 and other dynamic paths
- customer-safe path rows plus practitioner diagnostic path fields

UI-R1.8 multi-role reading surfaces:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=8/9
failed=llm_context_pack_has_product_layers
next=UI-R1.7 LLM Context And Prompt Upgrade
```

Added:

- diagnostic role answer projection
- `reading_surface.role_contract`
- practitioner answer sections for basic judgment, paths, features/portraits, boundary, and evidence count
- user/practitioner answer text differentiation without chart fact mutation

UI-R1.7 LLM context and prompt upgrade:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
product_ready=True audit_ready=True
passed=9/9
next=UI-R1.10 Product-Level Synthetic Validation
```

Added:

- `llm_metadata.context_pack_summary`
- product context layers in compact LLM prompt surface
- safe customer metadata projection for context layer summary
- live provider smoke remains explicit-only

MCR2 reconciliation:

```text
python3 scripts/run_customer_surface_bazi_context_reconciliation.py
v30.customer_surface_bazi_context_reconciliation.v1: mcr2_customer_surface_bazi_context_reconciled (6/6)
historical_next=M3-G1
current_status=SYN-CAL3 completed; UI-R1 inserted; next=UI-R1.1 Product Reading Acceptance Audit
full_pytest=False synthetic_all=False full_518k=False

pytest -q tests/unit/test_customer_surface_bazi_context_reconciliation.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
3 passed
```

RBD-S1.4 feature/portrait extraction:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
17 passed

runtime sample:
features=33 portraits=65
feature domains={'hidden_factor': 1, 'overview': 8, 'structure': 17, 'timing': 3, 'useful_god': 4}
portrait domains={'career': 10, 'health': 5, 'hidden_factor': 1, 'overview': 7, 'relationship': 11, 'structure': 13, 'timing': 2, 'useful_god': 8, 'wealth': 8}
```

## Active Mainline Queue

### MCR2 Customer Reading Surface And BaziContext Completion Reconciliation

Status: Complete

Result:

- `Customer reading surface accounting`: 100%, steady.
- `BaziContext internalization accounting`: 100%, steady.
- Admin route: `/api/v30/admin/mainline/customer-surface-bazi-context-reconciliation`.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

### M3-G1 Source-Governed Depth And Calibration Tags

Priority: P0

Status: Complete 2026-06-10

Goal:

- Keep M3 growing in a controlled way after current-scope seal.
- Add real-case calibration tags mapped to K/R/P units, rule states, dynamic paths, portrait density, and domain rule depth.
- Use M3 training and 518K observations to identify coverage gaps, not to create fixed Bazi verdicts.

Scope:

- `m3.real_case_calibration_tags`
- `m3.domain_rule_depth_expansion`
- `m3.training_synthetic_distribution`
- `m3.source_extraction_queue`
- `m3.518k_distribution_summary`
- No chart-fact mutation.
- No pointer promotion.

Expected outputs:

- M3 calibration tag schema/artifact.
- Updated M3 snapshot evidence with source/rule/portrait/path tag coverage.
- Targeted synthetic/training/518K sample evidence.

Default validation:

```text
python3 scripts/run_m3_core_spine_snapshot.py --sample-limit 8
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
python3 scripts/run_synthetic_validation.py --tier training_pipeline
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Optional long validation:

```text
python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

Full 518K remains explicit-only:

```text
python3 scripts/run_518k_validation.py --mode full --confirm-full
```

Completed:

- Added `v30.m3_source_governed_calibration.v1`.
- M3 snapshots now include `source_governed_calibration` with five tag groups:
  - `real_case_calibration_tags`
  - `domain_rule_depth_expansion`
  - `training_synthetic_distribution`
  - `source_extraction_queue`
  - `distribution_518k_summary`
- Added `scripts/run_m3_source_governed_calibration.py`.
- Kept G1 observational only: no chart-fact mutation, no pointer promotion, no fixed Bazi verdict, no default full 518K.

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_source_governed_calibration.py scripts/run_m3_core_spine_snapshot.py
passed

pytest -q tests/unit/test_m3_core_spine_snapshot.py
4 passed

python3 scripts/run_m3_source_governed_calibration.py --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=False

python3 scripts/run_m3_core_spine_snapshot.py --no-db --sample-limit 8
v30.m3.snapshot.20260610073045434170: krp=54 rules=9 portrait_assets=7 synthetic=8/8

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260610073103365458: eligible mode=sample cases=8 shards=0

python3 scripts/run_m3_source_governed_calibration.py --include-518k-sample --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=True
```

### M3-G2 Domain Rule Depth Expansion Batch

Priority: P0

Status: Complete 2026-06-10

Goal:

- Use M3-G1 tags to deepen wealth, career, relationship, health, structure dynamic, structure pattern, and useful-god rule coverage.
- Add source-governed K/R/P or rule units only where G1 tags identify growth candidates.
- Keep all domain claims bounded as rule/evidence paths, not fixed life-outcome verdicts.

Scope:

- Add domain subfamily tags and K/R/P units for weak domains.
- Add counter-evidence paths for domain outcome claims.
- Add synthetic assertions that new domain-depth evidence is consumed by M4/M5/M6 but does not mutate M1/M2 facts.

Default validation:

```text
python3 scripts/run_m3_source_governed_calibration.py --include-518k-sample --sample-limit 8
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
python3 scripts/run_synthetic_validation.py --tier training_pipeline
pytest -q tests/unit/test_knowledge_library.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py
```

Completed:

- Expanded M3 K/R/P from 54 to 72 units.
- Expanded M3 rule specs from 9 to 20.
- G2 added source-governed depth for:
  - chart fact boundary and calculation basis
  - element balance / seasonal counterforce
  - foundation M1/M2/M3 chain and training read-only boundary
  - romance/private-fact boundary
  - domain-rule subfamily and outcome-language gates
  - rule-counterevidence trace and silent-policy-override blocks
  - structure pattern success/failure/rescue review
  - explicit time-layer requirement
- G1 domain-depth growth candidates are now closed for the current G2 scope: `growth_count=0`.
- No chart-fact mutation, no pointer promotion, no fixed Bazi verdicts.

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_source_governed_calibration.py
passed

pytest -q tests/unit/test_knowledge_library.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
10 passed

python3 scripts/run_m3_source_governed_calibration.py --include-518k-sample --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=True

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_m3_core_spine_snapshot.py --no-db --sample-limit 8
v30.m3.snapshot.20260610095515875803: krp=72 rules=20 portrait_assets=7 synthetic=8/8
```

### M3-G3 Training / Synthetic Distribution Candidate Review

Priority: P0

Status: Complete

Goal:

- Use G1/G2 M3 calibration tags, synthetic observations, and 518K sample distribution to produce bounded training candidate review evidence.
- Identify which M3 weights or coverage paths can be tuned later.
- Keep this as review evidence only; do not promote pointers.

Scope:

- M3 training candidate rows from G1/G2 tags.
- Candidate domains: source coverage, rule path priority, domain-rule depth, counter-evidence trace, dynamic path priority, question strategy.
- Explicit forbidden domains: chart facts, luck-cycle facts, flow-year/month facts, fixed structure verdicts, fixed useful-god verdicts.

Default validation:

```text
python3 scripts/run_m3_training_candidate_review.py --sample-limit 8
python3 scripts/run_synthetic_validation.py --tier training_pipeline
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
pytest -q tests/unit/test_m3_training_candidate_review.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
```

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m3_training_candidate_review.py
passed

pytest -q tests/unit/test_m3_training_candidate_review.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
8 passed

python3 scripts/run_m3_training_candidate_review.py --sample-limit 8
v30.m3_training_candidate_review.v1: passed (7/7) m3_g3_training_candidate_review_ready candidates=8

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

### M3-G4 Source Extraction Queue Operationalization

Priority: P0

Status: Complete

Goal:

- Convert G1 source extraction queue tags into operational backlog artifacts that can be stored, filtered, and reviewed.
- Keep source extraction source-governed and review-only; do not import V20 runtime code or promote policy pointers.
- Connect backlog rows to M3 K/R/P, rule specs, portrait density, and future calibration tags.

Scope:

- Source-family backlog rows.
- Target domains and queue state.
- Review status, evidence links, and no-runtime-import boundary.
- Targeted tests and CLI output; no full 518K by default.

Implementation:

- `v30.m3_source_extraction_backlog.v1`
- CLI: `python3 scripts/run_m3_source_extraction_backlog.py`
- Dedicated optional Postgres table: `v30_m3_source_backlog`

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m3_source_extraction_backlog.py
passed

pytest -q tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_storage_adapters.py
12 passed

python3 scripts/run_m3_source_extraction_backlog.py
v30.m3_source_extraction_backlog.v1: passed (6/6) m3_g4_source_extraction_backlog_ready rows=6

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

### M3-G5 Backlog Persistence And Admin Review Surface

Priority: P0

Status: Complete

Goal:

- Expose the G4 source backlog as queryable M3 support data for admin/training review.
- Keep storage/query surfaces read-only for runtime decisions.
- Add filters for source family, priority, queue state, target domain, and review status.

Scope:

- Admin/API query endpoint or validation retrieval helper.
- JSON fallback plus Postgres-backed path.
- Tests for filtering, no V20 table access, and no pointer/chart-fact mutation.

Implementation:

- `v30.m3_source_backlog_review_surface.v1`
- CLI: `python3 scripts/run_m3_source_backlog_review_surface.py`
- Admin endpoint: `GET /api/v30/admin/m3/source-backlog`
- Filters: `source_family_id`, `priority`, `queue_state`, `review_status`, `target_domain`, `limit`
- Query path: Postgres `v30_m3_source_backlog`; fallback path generates current G4 backlog JSON artifact.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m3_source_backlog_review_surface.py
passed

pytest -q tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_storage_adapters.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
13 passed

python3 scripts/run_m3_source_backlog_review_surface.py
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=6 backend=json_fallback_generated_backlog

python3 scripts/run_m3_source_backlog_review_surface.py --target-domain useful_god --limit 3
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=3 backend=json_fallback_generated_backlog

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

### M3-G6 Source Backlog Closeout And M3 Seal Review

Priority: P0

Status: Complete

Goal:

- Review G1-G5 M3 artifacts as one flow and decide whether M3 can return to steady-state calibration.
- Confirm source backlog, candidate review, storage/query surface, and synthetic validation are connected.
- Keep M3 seal decision explicit and evidence-bound; do not promote policy pointers.

Scope:

- Closeout validation module and CLI.
- M3 seal evidence summary.
- Next-module recommendation after M3 closeout.

Implementation:

- `v30.m3_source_backlog_closeout.v1`
- CLI: `python3 scripts/run_m3_source_backlog_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m3/source-backlog-closeout`
- Closeout links G3 training candidate review, G5 backlog review surface, and `m3_core_spine` synthetic validation.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m3_source_backlog_closeout.py
passed

pytest -q tests/unit/test_m3_source_backlog_closeout.py tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_training_candidate_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
12 passed

python3 scripts/run_m3_source_backlog_closeout.py --sample-limit 8
v30.m3_source_backlog_closeout.v1: passed (5/5) m3_g6_source_backlog_closeout_ready candidates=8 backlog_rows=6

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

### M5 Evidence Consumption Hardening

Priority: P0

Status: Complete

Goal:

- Consume the sealed M3 source-governed evidence spine in M5 ranked decisions.
- Verify strength, structure-pattern, and useful-god ranked candidates reference M3 K/R/P, rule, counter-evidence, dynamic path, and source backlog signals coherently.
- Keep M5 candidate-bound; do not create fixed verdicts or mutate chart facts.

Scope:

- M5 evidence consumption diagnostics.
- Candidate scoring basis coverage from M3.
- Targeted tests and synthetic replay; no full pytest or full 518K by default.

Implementation:

- `v30.m5_evidence_consumption_hardening.v1`
- CLI: `python3 scripts/run_m5_evidence_consumption_hardening.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/evidence-consumption-hardening`
- Review links M3-G6 closeout, runtime ranked decisions, M3 completion summary, M5 contract synthetic, and strength/structure/useful-god synthetic.

Latest validation:

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

### M5 Calibration Replay Review

Priority: P0

Status: Complete

Goal:

- Review M5 calibration replay before any threshold, score floor, or policy-weight changes.
- Compare ranked candidate stability across M5 synthetic contract, strength/structure/useful-god tier, and real-case calibration pack.
- Keep replay review candidate-only; do not promote pointers or fixed verdicts.

Scope:

- Calibration replay review artifact.
- M5 score distribution and close-candidate monitoring.
- Targeted tests and synthetic replay; full pytest/full 518K only at a later major gate.

Implementation:

- `v30.m5_calibration_replay_review.v1`
- CLI: `python3 scripts/run_m5_calibration_replay_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/calibration-replay-review`
- Review links M5-H1, M5 contract synthetic, strength/structure/useful-god synthetic, real-case calibration pack, and `v30.training_signal.m5_weight_replay`.

Latest validation:

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

### M5 Calibration Replay Closeout

Priority: P0

Status: Complete

Goal:

- Close M5 calibration replay as a stable support module for M6 reading and IQ question strategy.
- Confirm H1/H2 evidence, replay summaries, training signal boundary, and no-threshold-change policy are synchronized.
- Decide whether M5 returns to steady-state monitoring or needs a later explicit threshold-review task.

Scope:

- Closeout artifact and admin route.
- Documentation synchronization for M5 status and next downstream module selection.
- Targeted tests only; no full pytest/full 518K by default.

Implementation:

- `v30.m5_calibration_replay_closeout.v1`
- CLI: `python3 scripts/run_m5_calibration_replay_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m5/calibration-replay-closeout`
- Closeout links M5-H2 replay review, H1/H2 lineage, close-candidate monitoring, `v30.training_signal.m5_weight_replay`, and no-write boundaries.

Latest validation:

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

### M6 Practical Reading Consumption Hardening

Priority: P0

Status: Complete

Goal:

- Verify customer-facing practical readings consume M1/M2 facts, M3 evidence, M4 model signals, and M5 ranked decisions coherently.
- Keep M6 as expression and reading composition, not a chart-fact generator and not a fixed verdict engine.
- Confirm role/locale projection remains clean while practitioner/admin diagnostics can inspect evidence lineage.

Scope:

- Practical reading evidence-consumption artifact and admin route.
- M6 contract, answer refresh, real-case reading acceptance, and fallback/LLM boundary checks.
- Targeted tests only; full pytest/full 518K remain major-gate-only.

Implementation:

- `v30.m6_practical_reading_consumption_hardening.v1`
- CLI: `python3 scripts/run_m6_practical_reading_consumption_hardening.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m6/practical-reading-consumption-hardening`
- Hardening links M5-H3 closeout, M6 synthetic contract, real-case calibration pack, B1 business acceptance, B3 answer refresh, and `v30.training_signal.practical_reading_quality`.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m6_practical_reading_consumption_hardening.py
passed

pytest -q tests/unit/test_m6_practical_reading_consumption_hardening.py tests/unit/test_practical_reading_context.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
8 passed

python3 scripts/run_m6_practical_reading_consumption_hardening.py --sample-limit 8
v30.m6_practical_reading_consumption_hardening.v1: passed (8/8) m6_practical_reading_consumption_hardening_ready domains=125 next=M6 Practical Reading Closeout

python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (30/30)

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### M6 Practical Reading Closeout

Priority: P0

Status: Complete

Goal:

- Close M6 as stable customer-facing practical reading support for the product flow.
- Confirm M6-H1 evidence, training signal boundary, answer refresh stability, and customer projection safety are synchronized.
- Decide whether the next core mainline returns to IQ question loop, M7 real-case calibration, or release readiness.

Scope:

- Closeout artifact and admin route.
- Documentation synchronization for M6 status and next downstream module selection.
- Targeted tests only; no full pytest/full 518K by default.

Implementation:

- `v30.m6_practical_reading_closeout.v1`
- CLI: `python3 scripts/run_m6_practical_reading_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m6/practical-reading-closeout`
- Closeout links M6-H1 hardening, domain coverage, B1/B3 business surface stability, practical-reading training signal, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m6_practical_reading_closeout.py
passed

pytest -q tests/unit/test_m6_practical_reading_closeout.py tests/unit/test_m6_practical_reading_consumption_hardening.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
13 passed

python3 scripts/run_m6_practical_reading_closeout.py --sample-limit 8
v30.m6_practical_reading_closeout.v1: passed (7/7) m6_practical_reading_closed domains=125 next=M7 Real-Case Calibration Steady-State Review

python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (30/30)

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### M7 Real-Case Calibration Steady-State Review

Priority: P0

Status: Complete

Goal:

- Review real-case calibration as the current backbone for M1-M6/M8 validation.
- Confirm canonical solar/lunar/unknown-hour/unknown-gender and M5/M6 replay cases remain sufficient for ongoing calibration.
- Decide whether M7 stays in steady-state monitoring or needs a focused real-case expansion pack.

Scope:

- Real-case calibration review artifact and admin route.
- M7 coverage, training signal, production replay metadata, M5/M6 readiness, and no-chart-fact-mutation checks.
- Targeted tests only; no full pytest/full 518K by default.

Implementation:

- `v30.m7_real_case_calibration_steady_state_review.v1`
- CLI: `python3 scripts/run_m7_real_case_calibration_steady_state_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m7/real-case-calibration-steady-state-review`
- Review links M6-H2 closeout, real-case calibration pack, production replay metadata, drift summaries, and `v30.training_signal.real_case_calibration_pack`.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m7_real_case_calibration_steady_state_review.py
passed

pytest -q tests/unit/test_m7_real_case_calibration_steady_state_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
8 passed

python3 scripts/run_m7_real_case_calibration_steady_state_review.py --sample-limit 8
v30.m7_real_case_calibration_steady_state_review.v1: passed (7/7) m7_real_case_calibration_steady_state_ready fixtures=30 next=M7 Real-Case Calibration Closeout

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### M7 Real-Case Calibration Closeout

Priority: P0

Status: Complete

Goal:

- Close M7 as the steady calibration backbone for M1-M6/M8.
- Preserve focused expansion as a future optional task, not a blocker for current core flow.
- Select whether the next core mainline should move to M8 projection/API closeout or IQ/LLM support review.

Scope:

- Closeout artifact and admin route.
- M7 steady-state monitoring baseline and documentation sync.
- Targeted tests only; no full pytest/full 518K by default.

Implementation:

- `v30.m7_real_case_calibration_closeout.v1`
- CLI: `python3 scripts/run_m7_real_case_calibration_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m7/real-case-calibration-closeout`
- Closeout links M7-S1 review, real-case calibration pack, production replay metadata, drift summaries, downstream M1-M6/M8 readiness, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m7_real_case_calibration_closeout.py
passed

pytest -q tests/unit/test_m7_real_case_calibration_closeout.py tests/unit/test_m7_real_case_calibration_steady_state_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
14 passed

python3 scripts/run_m7_real_case_calibration_closeout.py --sample-limit 8
v30.m7_real_case_calibration_closeout.v1: passed (6/6) m7_real_case_calibration_closed fixtures=30 next=M8 Projection/API Contract Closeout

python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### M8 Projection/API Contract Closeout

Priority: P0

Status: Complete

Goal:

- Close M8 as the stable customer/user/practitioner/admin projection and API contract layer for M1-M7.
- Confirm role, locale, client, answer, history, and admin projection contracts remain additive and leak-free.
- Keep this focused on backend projection/API contracts, not visual UI redesign.

Scope:

- M8 projection/API closeout artifact and admin route.
- Customer/internal split, role/client/locale projection matrix, API route contract, history projection, and training signal boundary.
- Targeted tests and synthetic projection replay only; no full pytest/full 518K by default.

Implementation:

- `v30.m8_projection_api_contract_closeout.v1`
- CLI: `python3 scripts/run_m8_projection_api_contract_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m8/projection-api-contract-closeout`
- Closeout links M7-S2 closeout, `m8_api_projection_contract`, real business API freeze, projection training signal boundary, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_m8_projection_api_contract_closeout.py
passed

pytest -q tests/unit/test_m8_projection_api_contract_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
7 passed

python3 scripts/run_m8_projection_api_contract_closeout.py --sample-limit 8
v30.m8_projection_api_contract_closeout.v1: passed (6/6) m8_projection_api_contract_closed contracts=25 next=IQ Intelligent Question Support Review

python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
```

### IQ-S1 Question Loop Business Feedback Watch

Priority: P0

Status: Complete

Goal:

- Keep intelligent Q&A personalized around the actual chart.
- Watch whether questions remain too template-like, lose continuity, leak diagnostics, or fail to collect useful hidden-factor clues.
- Only tune question strategy; never mutate deterministic chart facts.
- Verify IQ consumes M1-M8 through projection-safe context and supports customer/practitioner/admin roles.

Implementation:

- `v30.iq_intelligent_question_support_review.v1`
- CLI: `python3 scripts/run_iq_intelligent_question_support_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/iq/intelligent-question-support-review`
- Review links M8-S1 closeout, IQ5 closeout, `interaction_loop`, multi-role projection, LLM question context, hidden-factor clue boundary, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_iq_intelligent_question_support_review.py
passed

pytest -q tests/unit/test_iq_intelligent_question_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

python3 scripts/run_iq_intelligent_question_support_review.py --sample-limit 8
v30.iq_intelligent_question_support_review.v1: passed (6/6) iq_intelligent_question_support_ready interaction=5 next=LLM Bazi Expression Support Review

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)
```

### BL-S1 Bazi LLM Expression Watch

Priority: P0

Status: Complete

Goal:

- Keep LLM as Bazi expression/rewrite support.
- Verify each LLM task uses a bounded context pack rather than dumping all module state into one prompt.
- Keep no-fact-mutation proof.
- Verify role-specific prompt/context behavior after M1-M8 and IQ-S1 are stable.

Implementation:

- `v30.llm_bazi_expression_support_review.v1`
- CLI: `python3 scripts/run_llm_bazi_expression_support_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/llm/bazi-expression-support-review`
- Review links IQ-S1 support, BL8 closeout, `bazi_llm_acceptance`, role-specific prompt/context contracts, fallback/live-smoke boundaries, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_llm_bazi_expression_support_review.py
passed

pytest -q tests/unit/test_llm_bazi_expression_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

python3 scripts/run_llm_bazi_expression_support_review.py --sample-limit 8
v30.llm_bazi_expression_support_review.v1: passed (6/6) llm_bazi_expression_support_ready acceptance=5 next=Training/Synthetic Support Review

python3 scripts/run_synthetic_validation.py --tier bazi_llm_acceptance
v30.synthetic.bazi_llm_acceptance: passed (5/5)
```

Live provider smoke stays explicit, especially for release gates:

```text
python3 scripts/run_llm_live_smoke.py --json
```

### BT-S1 Training/Synthetic Support Review

Priority: P0

Status: Complete

Goal:

- Review training, synthetic validation, and 518K support around the stable M1-M8/IQ/LLM chain.
- Confirm training signals tune policies, expression, projection, question strategy, and calibration only; they cannot mutate deterministic chart facts.
- Keep full pytest, synthetic all, and full 518K explicit for major gates.

Implementation:

- `v30.training_synthetic_support_review.v1`
- CLI: `python3 scripts/run_training_synthetic_support_review.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/training/synthetic-support-review`
- Review links LLM-S1, `training_pipeline`, synthetic coverage manifest, 518K sample, extracted training signals, and no-write guardrails.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_training_synthetic_support_review.py
passed

pytest -q tests/unit/test_training_synthetic_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

python3 scripts/run_training_synthetic_support_review.py --sample-limit 8
v30.training_synthetic_support_review.v1: passed (7/7) training_synthetic_support_ready training=91 signals=33 sample518k=8 next=Core Chain Steady-State Summary

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260611225420867821: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260611225420867821
```

### S-S1 Core Chain Steady-State Summary

Priority: P0

Status: Complete 2026-06-12

Goal:

- Summarize current module completion after M5-H1/H2/H3, M6-H1/H2, M7-S1/S2, M8-S1, IQ-S1, LLM-S1, and BT-S1.
- Confirm default validation cadence and major-node gates.
- Keep the next work selection grounded in evidence, not broad reopening of completed modules.

Default validation:

```text
python3 -m compileall -q v30 scripts/run_core_chain_steady_state_summary.py
pytest -q tests/unit/test_core_chain_steady_state_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
python3 scripts/run_core_chain_steady_state_summary.py --sample-limit 8
```

Implementation:

- Added `v30.core_chain_steady_state_summary.v1`.
- CLI: `python3 scripts/run_core_chain_steady_state_summary.py --sample-limit 8`.
- Admin endpoint: `GET /api/v30/admin/mainline/core-chain-steady-state-summary`.
- Summary consumes BT-S1 and MCR2 evidence, records 13 module rows, separates routine targeted validation from major-node heavy gates, and keeps the task read-only.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_core_chain_steady_state_summary.py
passed

pytest -q tests/unit/test_core_chain_steady_state_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

python3 scripts/run_core_chain_steady_state_summary.py --sample-limit 8
v30.core_chain_steady_state_summary.v1: passed (5/5) core_chain_steady_state_ready modules=13 next=Evidence-Driven Calibration Queue
```

### E-S1 Evidence-Driven Calibration Queue

Priority: P0

Status: Complete 2026-06-12

Goal:

- Review only concrete evidence that appears after the core chain entered steady state.
- Accept evidence from real-case calibration, business acceptance, 518K sample/shard drift, training signal distribution, LLM expression failures, question-chain failures, or user-facing measurement regressions.
- Do not reopen M1-M8, IQ, LLM, BT, or U broadly without a failed targeted gate or specific evidence row.

Default validation:

```text
python3 -m compileall -q v30 scripts/run_evidence_driven_calibration_queue.py
pytest -q tests/unit/test_evidence_driven_calibration_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
python3 scripts/run_evidence_driven_calibration_queue.py --sample-limit 8
```

Implementation:

- Added `v30.evidence_driven_calibration_queue.v1`.
- CLI: `python3 scripts/run_evidence_driven_calibration_queue.py --sample-limit 8`.
- Admin endpoint: `GET /api/v30/admin/mainline/evidence-driven-calibration-queue`.
- E-S1 consumes S-S1 core-chain steady state and focused calibration queue review, records accepted evidence intake sources, and decides whether to wait, open a focused fix plan, or remediate blocked queue checks.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_evidence_driven_calibration_queue.py
passed

pytest -q tests/unit/test_evidence_driven_calibration_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed

python3 scripts/run_evidence_driven_calibration_queue.py --sample-limit 8
v30.evidence_driven_calibration_queue.v1: passed (4/4) evidence_driven_calibration_queue_ready candidates=0 next=Await New Calibration Evidence
```

### W-S1 Await New Calibration Evidence

Priority: P0

Status: Recorded 2026-06-12

Goal:

- Keep the completed core chain closed unless concrete evidence appears.
- Accept future evidence from real-case calibration, business acceptance, 518K distribution drift, training signal distribution, LLM expression acceptance, question-chain acceptance, or user-facing measurement regression.
- When evidence appears, open a focused calibration fix plan only for the affected module targets.

Default validation:

```text
python3 -m compileall -q v30 scripts/run_await_new_calibration_evidence_status.py
pytest -q tests/unit/test_await_new_calibration_evidence_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit 8
```

Implementation:

- Added `v30.await_new_calibration_evidence_status.v1`.
- CLI: `python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit 8`.
- Admin endpoint: `GET /api/v30/admin/mainline/await-new-calibration-evidence`.
- W-S1 consumes E-S1, confirms there are no current focused candidates, records the wait policy, and keeps evidence intake open without runtime mutation.

Latest validation:

```text
python3 -m compileall -q v30 scripts/run_await_new_calibration_evidence_status.py
passed

pytest -q tests/unit/test_await_new_calibration_evidence_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit 8
v30.await_new_calibration_evidence_status.v1: passed (4/4) await_new_calibration_evidence_ready waiting=True next=Await Evidence Or Explicit Major Validation
```

### RBD-S1 Real Bazi Diagnosis Engine

Priority: P0

Status: Active

Plan:

- See `docs/V30_REAL_BAZI_DIAGNOSIS_ENGINE_PLAN.md`.

Goal:

- Build a real diagnosis orchestration layer, not a UI wording patch.
- Let the central brain route diagnosis mode and evidence depth.
- Match M3 knowledge/rules/portrait/features, M4 model signals, M5 ranked decisions, and structure paths into concrete diagnosis claims.
- Persist diagnosis runs, matched rules, paths, portraits, and claims for training and replay.
- Keep LLM as expression only; diagnosis is generated by RBD module evidence.

Immediate implementation:

```text
Await Synthetic Canonical Trigger
```

Default validation:

```text
python3 scripts/run_synthetic_canonical_await_trigger.py
python3 scripts/run_synthetic_canonical_steady_state.py
python3 scripts/run_synthetic_canonical_pack_decision.py
python3 scripts/run_synthetic_validation.py --tier synthetic_canonical_bazi_calibration
pytest -q tests/unit/test_synthetic_canonical_await_trigger.py
```

Completed RBD-S1.1:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_diagnosis_contracts.py
5 passed
```

Completed RBD-S1.2:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
9 passed

v30.real_bazi_diagnosis.rule_matcher.v1: matches=49 claim_ready=45 calibration=5 domains={'career': 5, 'health': 6, 'hidden_factor': 1, 'overview': 7, 'relationship': 9, 'structure': 13, 'timing': 2, 'useful_god': 6, 'wealth': 6}
```

Completed RBD-S1.3:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
13 passed

v30.real_bazi_diagnosis.path_engine.v1: paths=10 high=7 domains={'career': 8, 'health': 4, 'relationship': 10, 'structure': 10, 'useful_god': 8, 'wealth': 5} mechanisms={'官印相生': 3, '财官印制化': 3, '食伤制官杀': 2, '食伤生财': 2}
top_statement=官杀 → 印星形成官印相生路径，压力、规则或职责需要通过印星转成资质、凭证、学习或平台承接。
```

Completed RBD-S1.4:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
17 passed

v30.real_bazi_diagnosis.feature_engine.v1: feature_count=33 domains={'hidden_factor': 1, 'overview': 8, 'structure': 17, 'timing': 3, 'useful_god': 4}
v30.real_bazi_diagnosis.portrait_engine.v1: portrait_count=65 domains={'career': 10, 'health': 5, 'hidden_factor': 1, 'overview': 7, 'relationship': 11, 'structure': 13, 'timing': 2, 'useful_god': 8, 'wealth': 8}
```

Completed RBD-S1.5:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
21 passed

v30.real_bazi_diagnosis.claim_generator.v1: claim_count=71 domains={'career': 7, 'health': 3, 'hidden_factor': 4, 'overview': 1, 'relationship': 7, 'structure': 28, 'timing': 3, 'useful_god': 10, 'wealth': 8}
levels={'domain': 7, 'fact': 1, 'feature': 20, 'path': 4, 'portrait': 37, 'question': 1, 'timing': 1}
```

Completed RBD-S1.6:

```text
python3 -m compileall -q v30/diagnosis v30/brain
passed

pytest -q tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py tests/unit/test_central_brain.py
29 passed

v30.real_bazi_diagnosis.graph.v1: node_count=261 edge_count=1426 node_counts={'chart_fact': 1, 'claim': 71, 'feature': 65, 'matched_rule': 49, 'path': 10, 'portrait': 65}
v30.real_bazi_diagnosis.router.v1: mode=wealth selected_domain=wealth selected_claim_count=5 selected_path_count=6 selected_portrait_count=6 followup_required=True
```

Completed RBD-S1.7:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_presentation_projection.py tests/unit/test_practical_reading_context.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py
19 passed

v30.real_bazi_diagnosis.runtime_integration.v1: claims=71 graph_nodes=261 graph_edges=1426
customer surface now projects:
career=事业主线落在官印相生；此局更重视压力如何转成资质、规则、平台或可交付能力，不能只按职位升降下断。
wealth=财运主线不是单点求财，而是沿财官印制化展开；财星需要被输出、官杀责任或印星资源承接，适合看资源转化、方案输出、平台授权和分配结构。
```

Completed RBD-S1.8:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_storage_adapters.py
14 passed

v30.real_bazi_diagnosis.storage.v1: claim_count=71 path_count=10 portrait_count=65 rule_match_count=49 backend=json_fallback searchable=False
```

Completed RBD-S1.9:

```text
python3 -m compileall -q v30/validation
passed

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_synthetic_validation.py::test_synthetic_real_bazi_diagnosis_tier_passes
10 passed
```

S1.9 verifies:

- `real_bazi_diagnosis` synthetic tier is implemented and documented in the synthetic coverage manifest.
- RBD rule matches, paths, portraits, claims, graph counts, domain coverage, storage record, customer projection, and admin diagnostics are observed.
- Claims remain traceable and are not LLM-generated, chart-fact-mutating, or fixed event predictions.
- Lightweight 518K sample readiness is recorded; full 518K stays explicit-only.

Completed RBD-S1.10:

```text
python3 -m compileall -q v30/expression v30/validation/real_bazi_product_reading_acceptance.py scripts/run_real_bazi_product_reading_acceptance.py
passed

pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_expression_framework.py tests/unit/test_real_bazi_runtime_integration.py
9 passed

python3 scripts/run_real_bazi_product_reading_acceptance.py
v30.real_bazi_product_reading_acceptance.v1: passed (6/6) rbd_s110_product_reading_accepted

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)
```

S1.10 verifies:

- Product answer text consumes RBD public projection instead of returning generic candidate language.
- Customer surface has RBD-backed career, wealth, relationship, health, and timing summaries.
- Structure paths, claims, and portraits are visible in customer-safe projection.
- Admin diagnostics keep the full RBD payload inspectable.
- Full pytest, synthetic all, live LLM, and full 518K remain explicit-only.

Completed RBD-S1.11:

```text
python3 -m compileall -q v30/validation/real_bazi_distribution_replay.py scripts/run_real_bazi_distribution_replay.py
passed

pytest -q tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_real_bazi_product_reading_acceptance.py
4 passed

python3 scripts/run_real_bazi_distribution_replay.py
v30.real_bazi_distribution_replay.v1: passed (6/6) rbd_s111_distribution_replay_ready
real_case=8/8 sample_518k=8/8

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)
```

S1.11 verifies:

- RBD acceptance metrics replay over ready real-case calibration rows.
- Generated 518K sample-style replay reaches 8/8 without generic-language hits or customer internal leaks.
- Every replayed case has five domains passing `v30.core_bazi_claim_quality.v1`.
- Minimum sample admin payload counts remain above claim/path/portrait thresholds.
- Full pytest, synthetic all, and full 518K remain explicit-only.

Completed RBD-S1.12:

```text
python3 -m compileall -q v30/validation/real_bazi_training_calibration_queue.py scripts/run_real_bazi_training_calibration_queue.py
passed

pytest -q tests/unit/test_real_bazi_training_calibration_queue.py tests/unit/test_real_bazi_distribution_replay.py
4 passed

python3 scripts/run_real_bazi_training_calibration_queue.py
v30.real_bazi_training_calibration_queue.v1: passed (5/5) rbd_s112_training_calibration_queue_ready
signals=5 queue_items=2 auto_apply=False
```

S1.12 verifies:

- Accepted S1.11 replay metrics become five read-only RBD training signal candidates.
- `v30.training_signal.rbd_core_claim_quality` records five-domain claim-quality replay coverage.
- Evidence-backed calibration queue items are grouped by source/domain.
- Queue and signals cannot mutate chart facts, auto-apply training, or promote policy pointers.
- Full pytest, synthetic all, and full 518K remain explicit-only.

Completed RBD-S1.13:

```text
python3 -m compileall -q v30/validation/real_bazi_diagnosis_steady_state.py scripts/run_real_bazi_diagnosis_steady_state.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_real_bazi_diagnosis_steady_state.py tests/unit/test_real_bazi_training_calibration_queue.py
4 passed

python3 scripts/run_real_bazi_diagnosis_steady_state.py
v30.real_bazi_diagnosis_steady_state.v1: passed (6/6) rbd_s113_steady_state_ready
signals=5 queue_items=2 next=RBD-S1-WAIT
```

S1.13 verifies:

- RBD current-scope spine is usable for customer reading, practitioner review, and admin diagnostics.
- Routine cadence is targeted: RBD steady-state script and `real_bazi_diagnosis` synthetic tier.
- Calibration queue items remain read-only until explicit evidence review.
- Full pytest, synthetic all, full 518K, live LLM, chart-fact mutation, auto-apply training, and pointer promotion remain explicit/non-default.

Completed SCAL-S1:

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

SCAL-S1 verifies:

- Synthetic canonical Bazi cases validate typical structures without using unverifiable real-person truth labels.
- The tier checks RBD rule/path/portrait/claim density, traceability, generic-language rate, customer leak safety, and fixed-event boundaries.
- Failed expectations would enter read-only calibration queue items.
- No chart-fact mutation, no auto-apply training, no pointer promotion, no full pytest/full 518K by default.

Completed SCAL-S2:

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

SCAL-S2 verifies:

- Canonical pack now covers 16 synthetic cases and 10 expanded structural families.
- Expansion covers 财多身弱、食伤生财、官杀混杂、印比过重、财官印相生、寒热燥湿、刑冲合害、从格候选、大运触发、流年触发.
- The expanded pack remains structural: no real-person truth labels and no fixed destiny verdicts.
- Failures remain read-only calibration candidates; no chart-fact mutation, auto-apply training, pointer promotion, full pytest, or full 518K by default.

Completed SCAL-S3:

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

SCAL-S3 verifies:

- The expanded 16-case canonical pack is frozen as routine targeted gate.
- Trigger events are explicit: RBD, M3, M5, IQ changes, and before release-boundary validation.
- Failures route to read-only calibration review.
- No real-person truth labels, no chart-fact mutation, no auto-apply training, no pointer promotion, no full pytest/full 518K by default.

Completed SCAL-S3-WAIT:

```text
python3 -m compileall -q v30/validation/synthetic_canonical_await_trigger.py scripts/run_synthetic_canonical_await_trigger.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_canonical_await_trigger.py tests/unit/test_synthetic_canonical_steady_state.py
6 passed

python3 scripts/run_synthetic_canonical_await_trigger.py
v30.synthetic_canonical_await_trigger.v1: passed (4/4) scal_s3_await_trigger_ready waiting=True run_required=False next=Await Synthetic Canonical Trigger
```

SCAL-S3-WAIT verifies:

- The frozen 16-case canonical gate is ready and currently has no active trigger.
- Known triggers are RBD, M3, M5, IQ changes, and release-boundary validation.
- Unknown triggers block the wait status rather than silently running or mutating anything.
- No chart-fact mutation, auto-apply training, pointer promotion, full pytest, synthetic all, or full 518K by default.

Completed REL-S1:

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

- The synthetic canonical gate is frozen and waiting without an active trigger.
- RBD steady state and backend API customer journey are ready for controlled trial use.
- Runtime config remains V30 scoped.
- Controlled trial readiness is allowed, but external release remains disabled.
- Full pytest, synthetic all, full 518K, live LLM, real-env smoke, and pointer promotion remain explicit-only.

Completed REL-S2:

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

REL-S2 verifies:

- Stage-A gate execution is authorized but not triggered.
- Authorized gates are controlled readiness, synthetic all, 518K sample, and 518K shard.
- Full pytest, live LLM smoke, real-env smoke, and full 518K stay deferred.
- External release, chart-fact mutation, auto-apply training, and pointer promotion remain disabled.

Completed REL-S3:

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

REL-S3 verifies:

- Only Stage-A authorized gates were executed.
- Controlled readiness, synthetic all, 518K sample, and 518K shard passed.
- Full pytest, live LLM smoke, real-env smoke, and full 518K were not run.
- External release, chart-fact mutation, auto-apply training, and pointer promotion remain disabled.

Completed REL-S4:

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

REL-S4 verifies:

- Stage-A evidence is complete and reviewed.
- Controlled trial readiness is confirmed.
- External release remains held.
- Full pytest, live LLM smoke, real-env smoke, full 518K, pointer promotion, auto-apply training, and chart-fact mutation remain disabled.
- The next mainline returns to core-module targeted work.

Completed MCR3:

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

MCR3 verifies:

- REL-S4 release hold is accepted as the current baseline.
- The next task is selected by direct Bazi measurement impact, not UI or release expansion.
- `SYN-CAL1` is selected over more release work because it validates rules, portraits, dynamic paths, ranked decisions, and claims through synthetic archetypes.
- Real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release remain disabled.

Completed SYN-CAL1:

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

SYN-CAL1 verifies:

- Four synthetic archetypes validate M3 claim domains and dynamic mechanisms.
- M5 strength and useful-god ranked candidates match expected archetype states.
- M6 practical domain claims and Bazi-specific summaries are present.
- RBD graph links claims, bounded overclaim blocks exist, and calibration routes remain review-only.
- Real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release remain disabled.

Completed SYN-CAL2:

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

SYN-CAL2 verifies:

- `synthetic_archetype_rule_claim` is a registered targeted synthetic tier.
- The tier passes 4/4 current archetype cases.
- Future failed archetype rows can be represented as read-only queue items.
- The tier is not a default full/release gate.
- Real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release remain disabled.

Completed SYN-CAL3:

```text
python3 -m compileall -q v30/validation/synthetic_archetype_training_signal_review.py scripts/run_synthetic_archetype_training_signal_review.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_synthetic_archetype_training_signal_review.py tests/unit/test_synthetic_archetype_tier_registration.py
6 passed

python3 scripts/run_synthetic_archetype_training_signal_review.py
v30.synthetic_archetype_training_signal_review.v1: syn_cal3_training_signal_review_ready
passed=6/6
signals=4
queue_items=0
auto_apply=False
next=SYN-CAL4
```

SYN-CAL3 verifies:

- Synthetic archetype outcomes now produce review-only training signals for M3, M5, and M6.
- Signals cover M3 rule/claim coverage, M5 ranked candidate alignment, M6 practical claim specificity, and boundary safety.
- Signals and queues cannot mutate chart facts, auto-apply training, promote pointers, or authorize external release.
- Full pytest, synthetic all, full 518K, and live LLM remain explicit-only.

Major-node validation remains explicit-only:

```text
python3 scripts/run_synthetic_validation.py --tier all
pytest -q
python3 scripts/run_llm_live_smoke.py --json
python3 scripts/run_518k_validation.py --mode full --confirm-full
```

### Product-Shell Usability Fixes

Priority: P3

Goal:

- Fix UI issues that directly block Bazi measurement or user flow.
- Examples: unusable BirthInput, missing chart display, broken profile selection, broken Admin DB/LLM/training panels.
- Do not start broad visual redesign as the mainline.

Default validation:

```text
node --check frontend/app.js
curl -fsS http://127.0.0.1:9030/api/v30/health
```

Browser visual regression should be added at a major UI checkpoint, not after every small fix.

## Validation Cadence

Routine task validation:

- Compile changed backend modules.
- Run targeted unit tests.
- Run the relevant synthetic tier.
- Run 518K sample only when the task affects training/calibration/distribution.

Major node validation:

```text
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

Release-boundary validation:

```text
python3 scripts/run_release_gate.py --mode standard --sample-limit 8 --shard-id 7 --shard-limit 16
python3 scripts/run_llm_live_smoke.py --json
python3 scripts/run_518k_validation.py --mode full --confirm-full
```

Release-boundary validation is explicit-only.

## What Not To Do Next

- Do not reopen M1-M8 just because they can always be deeper.
- Do not treat M3 content expansion as a blocker for using the system.
- Do not run full pytest or full 518K after every subtask.
- Do not make LLM a chart-fact generator.
- Do not let hidden-factor feedback modify pillars, luck cycles, flow-year/month, or deterministic facts.
- Do not promote pointers unless a task explicitly enters promotion/release scope.

## HF-R1 Latent Bazi Profile Refactor

Review conclusion:

- Hidden-factor interaction was partially integrated, not fully isolated.
- It could persist state and condition question strategy, central brain focus, admin diagnostics, and training signals.
- It was still too shallow for core Bazi measurement because the state was not modeled as chart-bound latent attributes.
- The missing layer was an explicit profile that links user calibration to `reading_id`, `context_id`, natal pillars, day master, ten-god families, dynamic paths, RBD claims, and evidence ids.

HF-R1.1 completed:

- Added `v30.latent_bazi_profile.v1`.
- Added `v30/hidden_factor/latent_profile.py`.
- `attach_hidden_factor_state()` now writes `policy_effect.latent_bazi_profile` and `policy_effect.latent_bazi_profile_summary`.
- Admin diagnostics expose the profile and summary.
- Customer-facing wording now uses “校准线索/背景校准线索” instead of the internal “隐藏因子” term.
- Added `tests/unit/test_latent_bazi_profile.py`.

Validation:

```text
pytest -q tests/unit/test_latent_bazi_profile.py tests/unit/test_hidden_factor_state.py tests/unit/test_interaction_constraints.py
python3 -m compileall -q v30/hidden_factor v30/runtime.py v30/presentation/client_model.py
```

Result:

```text
17 passed
```

Reference:

```text
docs/V30_LATENT_BAZI_PROFILE_REFACTOR_PLAN.md
```

## HF-R2 Latent Bazi Attribute System

Concept:

- Hidden factors are now defined as latent personal Bazi attributes.
- They explain why people with the same Bazi diverge under the same luck/flow time field.
- They start from neutral defaults and are reverse-inferred from structured interaction feedback.
- They must be chart-bound and calculation-ready, but cannot mutate deterministic chart facts.

HF-R2.1 completed:

- Added `v30.latent_bazi_attributes.v1`.
- Added `v30/hidden_factor/attributes.py`.
- Added default global attributes:
  - `luck_index`
  - `stability_index`
  - `execution_index`
  - `resource_index`
  - `risk_index`
  - `recovery_index`
  - `choice_quality_index`
- Added ten-god modifiers:
  - `day_master`
  - `wealth`
  - `authority`
  - `resource`
  - `output`
  - `peer`
- Added domain biases and stability thresholds.
- Added reverse-inference mapping from profile dimensions to latent attribute deltas.
- Added calculation modifiers:
  - `family_energy_multipliers`
  - `domain_path_multipliers`
  - `global_energy_context`
  - `stability_thresholds`
- Runtime initializes neutral defaults for every reading.
- Runtime rebuilds inferred attributes after structured feedback.
- Admin diagnostics expose `latent_bazi_attributes` and `latent_bazi_attributes_summary`.
- Added `tests/unit/test_latent_bazi_attributes.py`.

HF-R2.2 completed:

- Added `v30.latent_bazi_individualized_model_projection.v1`.
- Runtime now consumes `latent_bazi_attributes.calculation_modifiers` into diagnostic-only projections.
- Runtime exposes:
  - `policy_effect.latent_bazi_individualized_projection`
  - `policy_effect.latent_bazi_individualized_projection_summary`
- Projection includes:
  - family energy base/multiplier/adjusted score
  - domain path base/multiplier/adjusted score
  - ranked decision diagnostic projection
  - global latent context
  - stability thresholds
- Projection explicitly blocks:
  - chart fact mutation
  - base ten-god energy mutation
  - ranked decision mutation
- Added `tests/unit/test_latent_bazi_individualized_projection.py`.

HF-R2.3a/HF-R2.3b/HF-R2.3c completed:

- Added complete hidden attribute concept and question design documentation.
- Added `v30.latent_question_need_strategy.v1`.
- Runtime emits `policy_effect.latent_question_strategy`.
- Recommender consumes latent strategy so hidden-attribute questions are asked only when useful to the current Bazi reading.
- Structured uncertain/default/skip answers are valid and do not update hidden-factor state or latent attributes.
- Recent skip/default answers apply cooldown to future latent questions.
- Chart/six-pillar UI now displays all hidden attribute raw values in a temporary `DEBUG · 临时` section.
- Each valid structured latent interaction must refresh the related hidden attribute values in the returned view.
- Added `v30.synthetic.latent_bazi_divergence` to validate same-Bazi divergent latent attributes without chart-fact, M4, or M5 mutation.
- Targeted validation passed: `python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence` -> `passed (2/2)`.
- Added `v30.training_signal.latent_bazi_attribute_alignment` from the divergence tier.
- The signal trains latent inference, question strategy, and individualized projection only; chart facts, calendar conversion, luck cycle, and flow timing remain blocked.
- Added `v30.latent_bazi_attribute_policy.v1` candidate consumption under question/rule policy payloads.
- Runtime question recommendation consumes `latent_bazi_attribute_policy` as a small hidden-attribute question-need signal without overriding deterministic context priority.
- Pointer promotion remains explicit major-gate work; HF-R2.4 only completes candidate generation and runtime consumption.

HF-R2.5 completed:

- Added Admin-only `v30.latent_policy_observability.v1`.
- Admin diagnostics now show:
  - active question/rule policy versions
  - latent attribute status and active attribute summaries
  - latent question strategy status
  - question-policy and rule-policy latent policy projection
  - influenced question rows and policy reasons
  - training boundary and blocked chart-fact routes
- Customer/user projection hides `latent_policy_observability` and `latent_bazi_attribute_policy`.
- Added readiness artifact `v30.latent_policy_observability_readiness.v1`.
- Added CLI `python3 scripts/run_latent_policy_observability.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-policy-observability`.
- HF-R2.5 does not promote pointers and does not mutate chart facts.

Validation:

```text
python3 -m compileall -q v30/presentation/client_model.py v30/validation/latent_policy_observability.py v30/validation/__init__.py v30/api/app.py scripts/run_latent_policy_observability.py
passed

pytest -q tests/unit/test_latent_policy_observability.py tests/unit/test_presentation_projection.py::test_admin_projection_exposes_diagnostics_and_training_actions tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed

python3 scripts/run_latent_policy_observability.py
v30.latent_policy_observability_readiness.v1: hf_r25_latent_policy_observability_ready
- passed: 6/6
- failed: none
- next: HF-R2.6
```

HF-R2.6 completed:

- Added `v30.latent_attribute_admin_training_review.v1`.
- Review connects HF-R2.5 observability, `latent_bazi_divergence` synthetic evidence, and `v30.training_signal.latent_bazi_attribute_alignment`.
- Generates three review-only candidates:
  - `latent_reverse_inference_review`
  - `latent_question_strategy_review`
  - `latent_individualized_projection_review`
- Candidate scope is limited to:
  - `latent_attribute_inference`
  - `question_strategy`
  - `individualized_projection`
- Candidate scope explicitly forbids chart facts, calendar conversion, luck cycle, flow timing, four pillars, fixed structure verdict, and fixed useful-god verdict.
- Auto-apply, pointer promotion, and chart-fact mutation stay disabled.
- Added CLI `python3 scripts/run_latent_attribute_admin_training_review.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-attribute-review`.

Validation:

```text
python3 -m compileall -q v30/validation/latent_attribute_admin_training_review.py v30/validation/__init__.py v30/api/app.py scripts/run_latent_attribute_admin_training_review.py
passed

pytest -q tests/unit/test_latent_attribute_admin_training_review.py tests/unit/test_latent_policy_observability.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

python3 scripts/run_latent_attribute_admin_training_review.py --review-id hf-r26-check
v30.latent_attribute_admin_training_review.v1: hf_r26_latent_attribute_admin_training_review_ready
- candidates: 3
- passed: 5/5
- failed: none
- next: HF-R2.7
```

HF-R2.7 completed:

- Admin training page now loads `GET /api/v30/admin/training/latent-attribute-review` together with training status.
- Added a read-only "隐藏属性训练候选审核" panel.
- Panel shows:
  - decision status
  - candidate count
  - check pass count
  - next task
  - auto-apply / pointer-promotion / chart-fact mutation boundaries
  - allowed training scopes
  - forbidden training scopes
  - review-only candidate rows
- Added endpoint test for the Admin training review route.
- UI remains operator review only; it does not add apply/promote buttons.

Validation:

```text
node --check frontend/app.js
passed

pytest -q tests/unit/test_latent_attribute_admin_training_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_latent_attribute_training_review_endpoint_is_read_only
4 passed

python3 scripts/run_latent_attribute_admin_training_review.py --review-id hf-r27-ui-source-check
v30.latent_attribute_admin_training_review.v1: hf_r26_latent_attribute_admin_training_review_ready
- candidates: 3
- passed: 5/5
- failed: none
- next: HF-R2.7
```

Reference:

```text
docs/V30_LATENT_BAZI_ATTRIBUTES_SYSTEM_PLAN.md
docs/V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md
```

### HF-R2.8 Latent Attribute Workflow Closeout

Status: completed.

Implemented:

- Added `v30.latent_attribute_workflow_closeout.v1`.
- Added CLI `python3 scripts/run_latent_attribute_workflow_closeout.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-attribute-closeout`.
- Closeout now verifies the full hidden-attribute workflow across:
  - HF-R2.5 Admin policy observability
  - `latent_bazi_divergence` runtime/synthetic validation
  - `v30.training_signal.latent_bazi_attribute_alignment`
  - HF-R2.6 review-only Admin training candidates
  - customer projection hiding latent policy internals
  - Admin training UI read-only review panel
- Boundary remains unchanged: hidden attributes can train latent inference, question strategy, and individualized projection only; chart facts, calendar conversion, luck cycle, and flow timing remain blocked.
- No auto-apply, pointer promotion, full pytest, synthetic-all, full 518K, or live LLM is required for this closeout.

Validation:

```text
python3 -m compileall -q v30/validation/latent_attribute_workflow_closeout.py v30/validation/__init__.py v30/api/app.py scripts/run_latent_attribute_workflow_closeout.py
passed

pytest -q tests/unit/test_latent_attribute_workflow_closeout.py tests/unit/test_latent_attribute_admin_training_review.py tests/unit/test_latent_policy_observability.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_latent_attribute_workflow_closeout_endpoint_is_read_only
8 passed

python3 scripts/run_latent_attribute_workflow_closeout.py --closeout-id hf-r28-closeout-check
v30.latent_attribute_workflow_closeout.v1: hf_r28_latent_attribute_workflow_closeout_ready
- passed: 7/7
- failed: none
- next: HF-S1
```

### Major Node Validation 2026-06-14

Status: full regression triage required.

What passed:

```text
python3 -m compileall -q v30
passed

python3 scripts/run_latent_attribute_workflow_closeout.py --closeout-id major-node-hf-r28
v30.latent_attribute_workflow_closeout.v1: hf_r28_latent_attribute_workflow_closeout_ready
- passed: 7/7
- failed: none
- next: HF-S1

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260613230038346246: eligible mode=sample cases=8 shards=0
- artifact record: v30.518k.artifact.v30.518k.sample.20260613230038346246 (json_fallback)

python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)
```

Repair made during this node:

- Practitioner/admin answer projection now emits role-specific answer text while keeping diagnostic lines in `role_adaptation`.
- Customer answer text remains concise and stripped of diagnostic/system lines.
- This repaired the `ui_core_reading_product` synthetic tier, which initially failed on `ui_role_answer_not_differentiated`.

Full pytest result:

```text
pytest -q
34 failed, 628 passed, 1 skipped in 5458.34s (1:30:58)
```

Failure classes:

- Redis/network sandbox failures: local Redis socket access is blocked under the default sandbox in API/session-owner tests.
- Question ordering and central-brain expectation drift: smoke/runtime and interaction-loop tests still expect older top-question IDs.
- Policy pointer/test isolation failures: auto-apply and policy-promotion tests see baseline pointers or blocked synthetic gates instead of isolated promoted pointers.
- Cascading support/release closeout failures: support review, release readiness, M6/M7/M8/productization closeouts are blocked by lower-level targeted gate failures.
- Runtime macro-signal gap: macro dimension signals are missing from the answer contract in `test_runtime_intelligence_spine`.

## Next Action

Continue:

```text
CORE-CAL-WAIT Await Focused Answer Quality Evidence Or Explicit Major Validation
```

M5-H1 through M5-H3, M6-H1/H2, M7-S1/S2, M8-S1, IQ-S1, LLM-S1, BT-S1, S-S1, E-S1, W-S1, RBD-S1.1 through RBD-S1.13, RBD-S1.10-CQ, SCAL-S1/S2/S3/S3-WAIT, REL-S1 through REL-S4, MCR3, SYN-CAL1/SYN-CAL2/SYN-CAL3/SYN-CAL4, UI-R1.1, UI-R1.2, UI-R1.3, UI-R1.4, UI-R1.8, UI-R1.7, UI-R1.10, UI-R1.11, CORE-CAL-S0, HF-R1.1, HF-R2.1, HF-R2.2, HF-R2.3a, HF-R2.3b, HF-R2.3c, HF-R2.3d, HF-R2.3e, HF-R2.4, HF-R2.5, HF-R2.6, HF-R2.7, HF-R2.8, FULL-REG R1, FULL-REG R2, FULL-REG R3, FULL-REG R4, FULL-REG R5, FULL-REG R6, CORE-EVIDENCE-1, CORE-EVIDENCE-2, CORE-EVIDENCE-3, CORE-EVIDENCE-4, CORE-EVIDENCE-5, CORE-EVIDENCE-6, and CORE-CAL-S1 through CORE-CAL-S4 are complete or recorded. The next step is wait mode unless focused answer-quality evidence or an explicit major validation request appears.
