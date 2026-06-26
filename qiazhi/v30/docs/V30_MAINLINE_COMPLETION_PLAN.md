# V30 Mainline Completion Plan

Updated: 2026-06-14

## Objective

Bring the current V30 runtime closer to practical Bazi product completeness by closing the customer reading loop: deterministic calculation, internal Bazi context, concise customer reading surface, high-value recommended questions, user feedback, and silent training validation.

The controlling integrated requirements gate is `V30_BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE.md`. The practical Bazi calculation mainline remains sealed for the current M1-M8 scope, and the BL1-BL8 LLM scope is in steady state. `V30_MAIN_MODULE_COMPLETION_REVIEW.md` now owns the post-IQ5 module-level completion review.

Current execution queue is summarized in:

```text
docs/V30_CURRENT_MAINLINE_TASKS_20260610.md
```

Active next task:

```text
CORE-CAL-WAIT Await Focused Answer Quality Evidence Or Explicit Major Validation
```

Current wait status:

```text
python3 scripts/run_core_answer_calibration_wait_status.py --artifact-dir .runtime/validation/core-answer-calibration-wait
v30.core_answer_calibration_wait_status.v1: passed (5/5) core_cal_wait_answer_quality_evidence_wait_ready
- waiting=True candidates=0 full_pytest=False auto_apply=False
- next=CORE-CAL-WAIT
```

## Current Completion

| Module | Completion | Current state |
|---|---:|---|
| Core runtime spine | 97% | R3 complete: chart context, evidence, structure, mainline, question, answer, presentation, central brain, expression, actor/session hooks, adaptive question replay diagnostics, production API smoke, live 9030 customer-loop contract, and read-history ownership contract are connected. |
| Intelligent central brain | 100% | BT10 complete: central-brain acceptance, long-session replay, failure routing, central-brain synthetic tier, and unified closeout are accepted for the current support-system scope. |
| K/R/P library | 100% current-scope / 85% depth | Runtime inventory is now 54 K/R/P units, 9 rule specs, 7 macro portrait assets, dedicated M3 Postgres persistence, domain-rule depth plus 通关/制化 path-resolution coverage. |
| Structure dynamics | 87% | Dynamic graph v2 exposes competition, suppression, conflict, path-resolution, domain path, domain-rule depth, and 通关/制化 metrics. |
| Hidden factor modeling | 95% | Event-year/repeated-state alignment, denial/conflict, runtime rehydration, expiry, time-layer summary, conservative policy weighting, latent attribute policy consumption, Admin policy observability, Admin training candidate review, training UI review panel, and workflow closeout gate are active. |
| Synthetic validation | 100% | BT10 plus CORE-CAL-S1/S2/S3/S4 complete: `central_brain`, `training_pipeline`, synthetic coverage manifest, 518K readiness evidence, `synthetic_typical_bazi_answer` tier, typical-answer training signal review, answer-calibration closeout, and steady-state queue are registered; synthetic all remains a major-node-only check. |
| Training/auto-apply | 100% | BT10 complete: training closeout, failed-candidate quarantine, training-pipeline synthetic extraction, and support-system closeout are accepted for current scope. |
| 518K validation | 95% | BT10 complete: sample/shard readiness, artifact/index/search fallback, full explicit-only boundary, and candidate-family coverage matrix are accepted for current support-system scope. |
| Customer reading surface | 100% | CORE-EVIDENCE-5/6 complete: guest/user receive core-first `v30.customer_reading_surface.v1`; answer panels now have targeted runtime/API gates for Bazi-specific text, safe LLM metadata, product context layers, stable chart facts, and non-mutating boundaries. |
| High-value question engine | 99% | IQ5 plus CORE-EVIDENCE and CORE-CAL-S1/S2/S3/S4 complete: recommended questions carry value/IG/structured options/known signals; answer quality, LLM context, runtime answer integration, typical synthetic answer calibration, interaction answer-alignment training signals, and answer-quality evidence queue are active. Remaining work is evidence-driven tuning only. |
| BaziContext internalization | 100% | MCR2 complete: `v30.internal_bazi_context.v1` is role-gated for practitioner/admin/lab, carries chart reference, structure state, mainline state, ranked decisions, practical reading context, agent question flow, and model signal without mutating deterministic facts. |
| LLM expression layer | 94% | CORE-EVIDENCE-3/4/5 and CORE-CAL-S1/S2/S3 complete: V30-native LLM path has task-specific M3/M4/M5/M6 context packs, output content-quality gates, generic-output rejection, synthetic typical-answer calibration closeout, LLM expression-boundary training signal, safe runtime answer integration, deterministic fallback, and no-mutation proof. Live provider smoke remains explicit-only. |
| Presentation/UI | 99% | UI1-UI9 plus CORE-EVIDENCE complete: `/v30/ui/` has stable product entries and the backend projection now has targeted answer-panel quality/integration gates. Remaining UI work is usability polish or future terminal expansion, not core measurement wiring. |
| Role/session/client/locale productization | 100% | U5 complete plus UI9 product layer: productization closeout passes 5/5 checks, U1-U4 evidence is accepted, current-scope multi-user/session/terminal/locale projection is in U-S1 steady state, lightweight auth/profile pages bind users to actor/session hooks, and imported V20 users can use their original stored password hashes through V30 login compatibility. Full organization permissions, payment, membership, OAuth, and production-grade identity policy remain explicit non-goals. |
| Integrated Bazi intelligence requirements | 100% | IR1 complete: `v30.bazi_intelligence_requirements_coverage.v1` passes 6/6 across M1-M8 chain, role/locale projection, continuous Q&A, hidden-factor feedback, Bazi LLM expression, training/synthetic, and read-only boundaries. IR2 complete: backend API journey passes 6/6 across create/view/answer/hidden-factor/history/admin-gate route handlers. |
| Intelligent question interaction | 99% | IQ5 and CORE-EVIDENCE complete: IQ1-IQ5 gates pass, interaction-loop synthetic passes 5/5, question priority consumes model signals, and runtime answer integration verifies question outcomes refresh Bazi-specific answer panels without chart-fact mutation. |
| Main module completion review | 100% | MCR1 complete and MCR2 complete: `v30.customer_surface_bazi_context_reconciliation.v1` passes 6/6, reconciles customer surface plus BaziContext accounting, keeps heavy validation explicit-only, and selects M3-G1 Source-Governed Depth And Calibration Tags. |
| Post-seal release hardening | 98% | R6 complete: release gate quick/standard mode requires `post_seal_contracts`, `production_api_smoke`, and `llm_live_smoke`; it exposes M1-M8 phase-seal coverage, blocks appended synthetic-all failures, keeps M5/M6/M8/R5 coverage visible, records LLM no-mutation proof, and emits admin-oriented `v30.release_artifact_review.v1`. |

## Practical Calculation Completion

| Practical module | Completion | Current state |
|---|---:|---|
| Explicit-pillar `ChartContext` | 100% | C5 complete for current core scope: deterministic explicit pillars, ten gods, hidden stems, elements, relation hits, root/vault facts, base fact summary, M1/M2 completion summary, and downstream M5/M6 consumption proof are active. |
| BirthInput / calendar conversion | 100% | C5 complete: supported solar, lunar, leap-month lunar, known-place true-solar, unknown-hour blocking, invalid timezone/date/time blocking, solar-term/year-month, and late-zi trace boundaries are fixture-backed and no-fake-fact guarded. |
| Luck-cycle inferred context | 100% | C5 complete for current core scope: BirthInput with gender derives current luck-cycle context from solar, lunar, or true-solar effective datetime; genderless cases remain traceable pending without fabricated direction facts. |
| Flow-year / flow-month inferred context | 100% | C5 complete for current core scope: runtime target date derives flow-year and flow-month context from deterministic calendar code and feeds six-pillar/time-layer context without mutation. |
| Ten-god energy model | 100% | C2 complete: runtime computes deterministic six-pillar ten-god energy and emits bounded `v30.model_signal_summary.v1`; dedicated calibration and real-case replay cover five families, energy/stability/volatility bands, interface contract, calibration flags, ranked-decision adjustments, training distributions, and auto-training model-signal weights without exposing raw customer scores. |
| Strength / structure / useful-god ranked decision | 100% | C2 complete: runtime emits bounded ranked decisions for strength, structure pattern, and useful-god candidates with candidate scores, scoring basis, M4 calibration flags/adjustments, model-signal evidence, follow/disputed/regulation candidates, fixtures, score floors, replay weights, useful-god evidence calibration, auto-training policy weights, M1/M2 root/vault basis, and no raw model-score leakage instead of fixed verdicts. |
| Practical reading output | 100% | C1 complete: runtime emits customer-readable career, wealth, relationship, health, and timing readings with takeaways, action prompts, priority scores, quality contracts, calculation basis, M5 decision links, M4 signal bands, evidence ids, explanation units, domain insights, action steps, calibration prompts, module trace, boundary conditions, blocked claims, and no raw model-score exposure. |
| Agent question flow | 60% | Runtime now emits chart confirmation, time confirmation, event-year discovery, domain follow-up, and final clarification stages. |
| Customer reading loop | 100% | C4 complete for current core scope: runtime projects core Bazi calculation before question loops, exposes compact domain cards and sanitized next question, refreshes the answer panel after structured option submission, preserves actor/session context, hides customer diagnostics/policy/training internals, and keeps admin diagnostics role-gated. |
| Recommended question quality | 78% | Runtime and synthetic observations now track question value, structured options, selected options, `known_user_signals`, explicit interaction state, visible/internal next-question split, expected information gain, graph-selected next question, and quality-contract coverage. |
| Bounded LLM answer MVP | 88% | R4 complete: runtime composes a rule answer first, then optional bounded LLM expression rewrite; independent smoke records unconfigured/configured-not-executed/accepted/fallback/drift-rejected states and proves no chart-fact, ranked-decision, model-signal, or interaction-state mutation. BL8 accepts BL1-BL7 evidence and enters BL-S1 steady state. |
| Role-locale-client projection | 100% | C4 complete for current core scope: guest/user/practitioner/analyst/admin/lab, zh/en/ko, web/mobile/admin/lab profiles, core-first projection contract, customer surface contract, forbidden-field policy, role visibility matrix, synthetic projection observation, and training coverage signal are active. |
| Real-case validation alignment | 100% | C3 complete: canonical real-case calibration has 30 fixtures covering solar, lunar, leap-month, true-solar, unknown-hour, unknown-gender, invalid date/time, M4 signal bands, M5 ranked candidates, M6 practical reading contracts, no-fake-fact guardrails, metadata-safe replay tags, and M7 drift summaries that route calibration issues to module targets without chart-fact mutation. |
| Real business Bazi reading acceptance | 100% | B1 complete: ready canonical real-case rows pass BirthInput-to-customer-reading business acceptance 12/12 through M1/M2, M4, M5, M6, and M8 with no customer leak and no chart-fact mutation. |
| Business reading regression pack | 100% | B2 complete: expanded ready-case regression passes 24/24 with base fact explanations, M1/M2 summary, M5 ranked projection, five M6 practical domains, five M8 customer domain cards, privacy/no-mutation metadata, and M8 projection contract 30/30. |
| Business answer refresh regression | 100% | B3 complete: structured answer refresh passes 5/5 after B2, preserves core reading fingerprints, exposes answer panel, consumes interaction state, keeps five domain cards, and proves chart facts are not mutated. |
| Boundary and blocked input regression | 100% | B4 complete: 3 pending and 2 blocked BirthInput rows pass boundary regression with no fake pillars, no premature M4/M5/M6 readiness, no fake-ready projection, explainable missing requirements, and metadata-only/no-mutation privacy. |
| Business API contract freeze | 100% | B5 complete: B1-B4 are frozen as the minimum business reading acceptance contract, required endpoints and customer surface keys are recorded, field removals are disallowed, and release/full-pytest/pointer promotion stay separate. |
| Business acceptance closeout | 100% | B6 complete: B1-B5 are recorded as the default business Bazi reading gate, B-track is paused by default, and major validation/full pytest/full 518K/release/pointer promotion require explicit request. |
| Business acceptance steady state | 100% | S1 complete: routine business Bazi reading acceptance uses the frozen B1-B5 gate, no further B-track task starts by default, and reopen requires new business evidence or explicit major validation/release-boundary request. |

Latest practical mainline validation:

```text
Main module completion review:
python3 scripts/run_main_module_completion_review.py
v30.main_module_completion_review.v1: passed (5/5) mcr1_main_module_review_ready
historical_next=MCR2 Customer Reading Surface And BaziContext Completion Reconciliation
current_status=MCR2 completed; next=M3-G1

Customer surface and BaziContext reconciliation:
python3 scripts/run_customer_surface_bazi_context_reconciliation.py
v30.customer_surface_bazi_context_reconciliation.v1: mcr2_customer_surface_bazi_context_reconciled (6/6)
next=M3-G1 full_pytest=False synthetic_all=False full_518k=False

pytest -q tests/unit/test_customer_surface_bazi_context_reconciliation.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
3 passed

Targeted validation:
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py tests/unit/test_question_dialogue_graph.py tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py
25 passed

Full validation:
pytest -q
188 passed, 1 skipped

Synthetic smoke:
python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

Synthetic all:
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

Major-node full pytest:
pytest -q
34 failed, 628 passed, 1 skipped in 5458.34s (1:30:58)

FULL-REG R1 targeted repair:
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614015436539162: eligible mode=sample cases=8 shards=0

pytest -q tests/test_v30_scaffold.py::test_smoke_runtime_and_view_contract tests/unit/test_central_brain.py::test_runtime_exposes_central_brain_trace_as_mainline_coordinator tests/unit/test_runtime_intelligence_spine.py::test_macro_dimension_signals_reach_question_and_answer_context tests/unit/test_synthetic_validation.py::test_synthetic_interaction_loop_tier_passes_customer_followup_contracts tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace tests/unit/test_session_owner_boundary_readiness.py tests/unit/test_llm_context.py tests/unit/test_bazi_llm_context_prompt_readiness.py tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/unit/test_auto_apply_training.py
40 passed

R1 note:
Runtime policy pointer isolation, baseline policy payload defaults, Redis best-effort API cache fallback, interaction-loop expectation alignment, customer leak cleanup, and auto-training smoke-mode validation are repaired. Full pytest remains major-node-only; next step is FULL-REG R2 targeted reduction of remaining failure clusters.

FULL-REG R2 targeted repair:
pytest -q tests/unit/test_intelligent_question_chain_readiness.py tests/unit/test_intelligent_question_closeout.py tests/unit/test_m6_practical_reading_closeout.py tests/unit/test_m7_real_case_calibration_closeout.py tests/unit/test_m8_projection_api_contract_closeout.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_real_business_boundary_blocked_input_regression.py tests/unit/test_real_business_api_contract_freeze.py tests/unit/test_synthetic_coverage_manifest.py
31 passed

pytest -q tests/unit/test_iq_intelligent_question_support_review.py tests/unit/test_llm_bazi_expression_support_review.py tests/unit/test_training_synthetic_support_review.py tests/unit/test_brain_training_synthetic_closeout.py
18 passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (127/127)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260614024220678512: eligible mode=sample cases=8

R2 note:
Question projection now suppresses already answered visible questions; B3 accepts fast LLM `deferred` answer panels as valid rule-bound output; B4/B5, M6/M7/M8, IQ support, LLM support, training support, and BT10 closeout recover. Synthetic manifest now documents all implemented tiers including latent and UI/product tiers.

FULL-REG R3 targeted repair:
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

R3 note:
Backend API journey accepts the fast-sync rule-bound RBD answer boundary; RBD health domain now receives bounded path claims from health-targeted dynamic paths. Product reading acceptance, distribution replay, calibration queue, diagnosis steady state, controlled release readiness, storage integration, and release-candidate targeted buckets are green. Full pytest remains deferred to the next major-node gate.

FULL-REG R4 residual bucket sweep:
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

R4 note:
Policy promotion artifacts sanitize legacy-source names before writing runtime strategy artifacts, while M3 documentation can still preserve V20 migration/reference context. Remaining lastfailed buckets for calibration status, core-chain summary, evidence queue, M6/M7, U5, and synthetic manifest are green.

Next:
FULL-REG R5 Major-Node Full Pytest Recheck. Run one full pytest recheck after R1-R4 targeted blockers are clear; if it fails, split new failures into targeted buckets instead of rerunning full pytest repeatedly.

FULL-REG R5 major-node full pytest recheck:
pytest -q
8 failed, 654 passed, 1 skipped in 4412.88s

R5 targeted repair:
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

R5 note:
Full pytest residual failures reduced to question ordering, RBD dynamic path mechanism coverage, and SYN-CAL cascade. Default question ordering now keeps user Bazi questions first unless the central brain explicitly selects context-first. RBD path engine now exposes 财官印制化, 食伤生财, and 食伤制官杀 from existing dynamic evidence and keeps conflict boundaries explicit. `lastfailed` is empty after targeted repair.

Next:
FULL-REG R6 Final Full-Pytest Confirmation Or Hold. Run one final full pytest only as a major-node confirmation; otherwise hold on current targeted evidence.

FULL-REG R6 final confirmation:
pytest -q
1 failed, 661 passed, 1 skipped in 4369.17s

R6 targeted repair:
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

R6 note:
The final full-pytest confirmation found one remaining question-policy ordering issue. Explicit hidden-factor topic boosts now override the default user-question-first boost, while central-brain context-first strategy still works. The failure was repaired with targeted tests only; no second full pytest was run.

Next:
Return to core module/product evidence review with targeted gates only. Full pytest is no longer a routine step after every fix.

CORE-EVIDENCE-1 module/product evidence rebaseline:
python3 scripts/run_main_module_completion_review.py
v30.main_module_completion_review.v1: passed (5/5) mcr1_main_module_review_ready

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted, passed=10/10

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

CORE-EVIDENCE-1 note:
After FULL-REG R1-R6, the module/product gates are green again. The next work is not broad module repair; it is CORE-EVIDENCE-2 Answer Quality Delta Review, focused on concrete Bazi answer text, Q&A output, and evidence use.

CORE-EVIDENCE-2 answer quality delta review:
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
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted, passed=10/10

python3 scripts/run_real_business_bazi_reading_acceptance.py
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted

CORE-EVIDENCE-2 note:
Added `v30.answer_quality_delta_review.v1` and `scripts/run_answer_quality_delta_review.py`. The new gate reviews career, wealth, relationship, timing, and hidden-factor-related answer anchors, requiring domain-specific Bazi language, mechanism/path/portrait/feature evidence, explicit boundary language, and traceable evidence ids. It blocks generic placeholder text and internal policy leakage. Full pytest remains major-node-only.

Next:
CORE-EVIDENCE-3 LLM Prompt Context Delta Review. Verify LLM prompt/context packs use bounded module-specific Bazi layers instead of prompt accumulation, and keep LLM as expression/synthesis over M1-M6 evidence rather than a chart-fact generator.

CORE-EVIDENCE-3 LLM prompt context delta review:
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

CORE-EVIDENCE-3 note:
`domain_followup` LLM context now includes M3 structure dynamics, M4 model signals, M5 ranked decisions, M6 practical reading, interaction state, and known user signals. Added `v30.llm_prompt_context_delta_review.v1` and `scripts/run_llm_prompt_context_delta_review.py` to prevent regression back to weak prompt packs. Full pytest and live LLM execution remain explicit-only.

Next:
CORE-EVIDENCE-4 LLM Answer Output Delta Review. Verify generated/fallback answer output actually uses concrete Bazi mechanisms, role-specific expression, and the strengthened module context without mutating verified chart facts.

CORE-EVIDENCE-4 LLM answer output delta review:
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
v30.llm_prompt_context_delta_review.v1: core_evidence_3_llm_prompt_context_ready, passed=64/64

CORE-EVIDENCE-4 note:
`validate_bazi_llm_output_payload` now rejects generic Bazi-free output even when schema, role visibility, and drift checks pass. Accepted customer/domain/practitioner outputs need concrete chart/day-master language, Bazi mechanism language, and domain/evidence-layer language. Hidden-factor dialogue output must stay constrained to feedback selection. Added `v30.llm_answer_output_delta_review.v1` and `scripts/run_llm_answer_output_delta_review.py`.

Next:
CORE-EVIDENCE-5 Runtime Answer Integration Delta Review. Verify runtime answer panels, API answer refresh, and product projection actually use the strengthened LLM acceptance/fallback path end to end.

CORE-EVIDENCE-5 runtime answer integration delta review:
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

CORE-EVIDENCE-5 note:
Added `v30.runtime_answer_integration_delta_review.v1` and `scripts/run_runtime_answer_integration_delta_review.py`. Runtime answer panels, API answer refresh, and API LLM mock enhancement now have a targeted end-to-end gate for Bazi-specific customer text, safe LLM metadata, product context layers, stable chart facts, and non-mutating answer boundaries.

Next:
CORE-EVIDENCE-6 Core Evidence Closeout And Documentation Sync. Close the CORE-EVIDENCE chain, update module completion status, and select the next core-only task.

CORE-EVIDENCE-6 closeout:
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
v30.answer_quality_delta_review.v1: core_evidence_2_answer_quality_ready, passed=40/40

python3 scripts/run_runtime_answer_integration_delta_review.py
v30.runtime_answer_integration_delta_review.v1: core_evidence_5_runtime_answer_integration_ready, passed=27/27

CORE-EVIDENCE-6 note:
Added `v30.core_evidence_closeout.v1` and `scripts/run_core_evidence_closeout.py`. CORE-EVIDENCE-2 through CORE-EVIDENCE-5 are now summarized by one closeout gate. The current answer/product evidence chain is closed without requiring full pytest, live LLM, full synthetic-all, full 518K, chart-fact mutation, or policy pointer promotion.

Next:
CORE-CAL-S1 Synthetic Typical Bazi Answer Calibration Pack. Build representative synthetic chart cases and calibrate answer text against expected Bazi mechanisms, domain coverage, timing boundaries, and hidden-attribute divergence behavior.

CORE-CAL-S1 synthetic typical Bazi answer calibration:
python3 scripts/run_synthetic_typical_bazi_answer_calibration.py
v30.synthetic_typical_bazi_answer_calibration.v1: core_cal_s1_synthetic_typical_answer_calibration_ready
passed=5/5 ready=True
next=CORE-CAL-S2 Synthetic Typical Answer Tier Registration And Training Signals

python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer
v30.synthetic.synthetic_typical_bazi_answer: passed (3/3)

pytest -q tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_answer_quality_delta_review.py tests/unit/test_core_evidence_closeout.py tests/unit/test_synthetic_coverage_manifest.py
10 passed

python3 scripts/run_core_evidence_closeout.py
v30.core_evidence_closeout.v1: core_evidence_6_closeout_ready, passed=160/160

CORE-CAL-S1 note:
Added `v30.synthetic_typical_bazi_answer_calibration.v1`, `scripts/run_synthetic_typical_bazi_answer_calibration.py`, and the `synthetic_typical_bazi_answer` synthetic tier. The gate covers career, wealth, relationship, timing, and hidden-attribute feedback answer cases. Customer answer text must include chart/day-master language, Bazi mechanisms, domain coverage, evidence-backed boundaries, and no internal policy/rule-id/English guidance leakage. M3 guidance leakage was cleaned in the answer guidance and portrait projection path.

Next:
CORE-CAL-S2 Synthetic Typical Answer Tier Registration And Training Signals. Expose the new typical-answer calibration evidence as training signal summaries for M3/M6/LLM/interaction calibration without mutating chart facts.

CORE-CAL-S2 synthetic typical answer training signal review:
python3 scripts/run_synthetic_typical_answer_training_signal_review.py
v30.synthetic_typical_answer_training_signal_review.v1: passed (6/6) core_cal_s2_training_signal_review_ready
- signals=5 queue_items=0 auto_apply=False
- next=CORE-CAL-S3

pytest -q tests/unit/test_synthetic_typical_answer_training_signal_review.py
3 passed

pytest -q tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
9 passed

python3 scripts/run_synthetic_typical_bazi_answer_calibration.py
v30.synthetic_typical_bazi_answer_calibration.v1: core_cal_s1_synthetic_typical_answer_calibration_ready
passed=5/5 ready=True

python3 scripts/run_synthetic_validation.py --tier synthetic_typical_bazi_answer
v30.synthetic.synthetic_typical_bazi_answer: passed (3/3)

CORE-CAL-S2 note:
Added `v30.synthetic_typical_answer_training_signal_review.v1` and `scripts/run_synthetic_typical_answer_training_signal_review.py`. The review emits five read-only training signals for M3 guidance sanitization, M6 domain/mechanism specificity, LLM expression boundary, interaction answer alignment, and review boundary safety. These signals are calibration evidence only: no chart-fact mutation, no auto-apply, no policy pointer promotion, no release trigger, no live LLM, no full 518K, and no routine full pytest.

Next:
CORE-CAL-S3 Synthetic Typical Answer Calibration Closeout. Record S1/S2 as the routine answer-calibration track and keep future answer-quality tuning evidence-driven.

CORE-CAL-S3 synthetic typical answer calibration closeout:
python3 scripts/run_synthetic_typical_answer_calibration_closeout.py
v30.synthetic_typical_answer_calibration_closeout.v1: passed (6/6) core_cal_s3_synthetic_typical_answer_calibration_closed
- signals=5 queue_items=0 auto_apply=False full_pytest=False
- next=CORE-CAL-S4

pytest -q tests/unit/test_synthetic_typical_answer_calibration_closeout.py
2 passed

pytest -q tests/unit/test_synthetic_typical_answer_calibration_closeout.py tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
11 passed

CORE-CAL-S3 note:
Added `v30.synthetic_typical_answer_calibration_closeout.v1` and `scripts/run_synthetic_typical_answer_calibration_closeout.py`. The closeout freezes S1 typical answer calibration, S2 training signal review, the `synthetic_typical_bazi_answer` tier, and case summary as the routine answer-calibration track. Routine cadence now targets M3 guidance, M6 answer composition, LLM prompt/context/acceptance, and interaction answer refresh changes. Full pytest, synthetic-all, full 518K, and live LLM remain explicit-only.

Next:
CORE-CAL-S4 Core Answer Calibration Steady-State Queue. Keep typical-answer calibration as a targeted routine gate and wait for fresh answer-quality evidence before changing core modules.

CORE-CAL-S4 core answer calibration steady-state queue:
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

CORE-CAL-S4 note:
Added `v30.core_answer_calibration_steady_state_queue.v1` and `scripts/run_core_answer_calibration_steady_state_queue.py`. The queue accepts answer-quality evidence from answer quality review, typical-answer synthetic tier, runtime answer integration, business answer refresh, LLM output acceptance, and user feedback. It routes review-only queue items to M3, M6, LLM, or interaction without chart-fact mutation, auto-apply, policy pointer promotion, release authorization, or default heavy gates.

Next:
CORE-CAL-WAIT Await Focused Answer Quality Evidence Or Explicit Major Validation. Serve current runtime and reopen answer calibration only from concrete evidence.

CORE-CAL-WAIT answer calibration wait status:
python3 scripts/run_core_answer_calibration_wait_status.py --artifact-dir .runtime/validation/core-answer-calibration-wait
v30.core_answer_calibration_wait_status.v1: passed (5/5) core_cal_wait_answer_quality_evidence_wait_ready
- waiting=True candidates=0 full_pytest=False auto_apply=False
- next=CORE-CAL-WAIT

pytest -q tests/unit/test_core_answer_calibration_wait_status.py
3 passed

pytest -q tests/unit/test_core_answer_calibration_wait_status.py tests/unit/test_core_answer_calibration_steady_state_queue.py tests/unit/test_synthetic_typical_answer_calibration_closeout.py tests/unit/test_synthetic_typical_answer_training_signal_review.py tests/unit/test_synthetic_typical_bazi_answer_calibration.py tests/unit/test_synthetic_coverage_manifest.py
17 passed

CORE-CAL-WAIT note:
Added `v30.core_answer_calibration_wait_status.v1` and `scripts/run_core_answer_calibration_wait_status.py`. The wait status confirms the S4 answer-calibration queue is ready and empty, accepted evidence sources and target modules are registered, and no default heavy validation, pointer promotion, auto-apply training, release, live LLM, or chart-fact mutation is allowed. No next implementation task is selected from this track without focused answer-quality evidence or explicit major validation.

Interaction loop:
python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)

Latent Bazi divergence:
python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence
v30.synthetic.latent_bazi_divergence: passed (2/2)

Real-case calibration pack:
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)

Real business Bazi reading acceptance:
python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted

Business reading regression pack:
python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready

Business answer refresh regression:
python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready

Boundary and blocked input regression:
python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready

Business API contract freeze:
python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen

Business acceptance closeout:
python3 scripts/run_real_business_acceptance_closeout.py
v30.real_business_acceptance_closeout.v1: passed (4/4) b6_business_acceptance_closed

Integrated Bazi intelligence requirements:
python3 scripts/run_bazi_intelligence_requirements_coverage.py
v30.bazi_intelligence_requirements_coverage.v1: passed (6/6) ir1_bazi_intelligence_requirements_covered

pytest -q tests/unit/test_bazi_intelligence_requirements_coverage.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed

Backend API journey acceptance:
python3 scripts/run_bazi_backend_api_journey_acceptance.py
v30.bazi_backend_api_journey_acceptance.v1: passed (6/6) ir2_bazi_backend_api_journey_accepted

pytest -q tests/unit/test_bazi_backend_api_journey_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed

Intelligent question interaction audit:
python3 scripts/run_intelligent_question_interaction_audit.py
v30.intelligent_question_interaction_audit.v1: passed (8/8) iq1_intelligent_question_interaction_ready

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)

pytest -q tests/unit/test_intelligent_question_interaction_audit.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
7 passed

518K sample:
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260524025228337725: eligible mode=sample cases=8 shards=0
artifact_record_id=v30.518k.artifact.v30.518k.sample.20260524025228337725
artifact_search_backend=json_fallback

Live smoke:
/api/v30/ui/capabilities exposed stable UI contract
structured option answer returned refreshed view and graph-selected next question
LLM runtime reported llm_bounded_answer_draft/accepted when configured
admin diagnostics exposed actor/session context and LLM runtime status

R2 production API smoke:
python3 -m compileall -q v30 scripts/run_production_api_smoke.py
passed
pytest -q tests/unit/test_release_gate.py
3 passed
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py
14 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260604011732: eligible, checks=5
production_api_smoke: passed
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260604011748344812
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r2-live-api-smoke-202606040120 --json
v30.production_api_smoke.v1: passed

R3 durable session/read-history:
python3 -m compileall -q v30 scripts/run_production_api_smoke.py
passed
pytest -q tests/unit/test_runtime_repository.py tests/test_v30_scaffold.py
17 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605051922: eligible, checks=5
production_api_smoke: passed, history_owner_scope=actor_and_session
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r3-live-history-smoke-202606050520 --json
v30.production_api_smoke.v1: passed

R4 bounded LLM live smoke:
python3 -m compileall -q v30 scripts/run_llm_live_smoke.py
passed
pytest -q tests/unit/test_llm_context.py tests/unit/test_expression_framework.py
12 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_llm_live_smoke.py --reading-id r4-llm-live-smoke-20260605 --json
v30.llm_live_smoke.20260605062559199852: passed, smoke_status=unconfigured
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605062559: eligible, checks=6
llm_live_smoke: passed, smoke_status=unconfigured

pytest -q tests/unit/test_core_chart_context.py tests/unit/test_birth_input_contract.py
7 passed

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

pytest -q tests/test_v30_scaffold.py
6 passed

pytest -q
165 passed, 1 skipped

python3 scripts/run_synthetic_validation.py --tier core_calculation
v30.synthetic.core_calculation: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (38/38)

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521195252: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service after restart:
/api/v30/health ok=true; /v30/ui/ 200; BirthInput runtime returned ready chart_build and exposed six_pillar_context, ranked_decisions, practical_reading_context, agent_question_flow, and q_v30_practical_domain_focus.
```

Additional targeted validation:

```text
pytest -q tests/unit/test_luck_flow_context.py tests/unit/test_practical_reading_context.py tests/unit/test_birth_input_contract.py tests/unit/test_training_signals.py tests/unit/test_release_gate.py
12 passed

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_training_signals.py tests/unit/test_expression_framework.py tests/unit/test_portrait_projection.py tests/test_v30_scaffold.py
18 passed

pytest -q
166 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521200713: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

pytest -q tests/unit/test_birth_calendar_boundaries.py tests/unit/test_training_signals.py tests/unit/test_release_gate.py
8 passed

python3 scripts/run_synthetic_validation.py --tier real_case_validation
v30.synthetic.real_case_validation: passed (4/4)

pytest -q
170 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521202109: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service after restart:
/api/v30/health ok=true; /v30/ui/ 200; solar female real-case BirthInput returned ready chart_build and admin view exposed client_profile, six_pillar_context, ranked_decisions, practical_reading_context, agent_question_flow, and q_v30_practical_domain_focus.

Latest calendar completion validation:
pytest -q
171 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521203307: eligible

Live lunar and true-solar checks returned ready chart_build with deterministic pillars.

Latest customer reading loop validation:
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_training_signals.py
7 passed

Guest/user views now expose `reading_surface` and high-value question fields while hiding internal structure confidence, path scores, and full Bazi context. Practitioner/admin/lab diagnostics expose `bazi_context` for inspection without changing chart facts.

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (38/38)

pytest -q
173 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521210509: eligible

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service check on http://127.0.0.1:8030:
/api/v30/health ok=true; /v30/ui/ 200; user reading view returned `v30.customer_reading_surface.v1`, `expected_information_gain`, `v30.high_value_question.v1`, `internal_context_visible=false`, no internal-context token leaks, and no diagnostics for the user role.

Latest P6 LLM and interaction validation:
pytest -q tests/unit/test_llm_context.py tests/unit/test_answer_composer.py tests/unit/test_expression_framework.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py
23 passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (38/38)

pytest -q
175 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521212134: eligible

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live P6 service check on http://127.0.0.1:8030:
/api/v30/health ok=true; /v30/ui/ 200; BirthInput created ready runtime; user view returned `v30.customer_reading_surface.v1`; answer submission returned refreshed view and next question. Local environment has no LLM execution config, so answer used `rule_bound_fallback` with `llm_fallback_keeps_rule_answer_and_does_not_mutate_chart_facts`.
```

## Current Mainline Tasks

### P7 Ten-god Energy Fusion

- [x] Emit unified `v30.model_signal_summary.v1` from ten-god energy, stability, and volatility.
- [x] Attach bounded model-signal inputs to strength, structure, and useful-god ranked decisions.
- [x] Reuse `model_signal_summary` in answer context, admin diagnostics, synthetic observation, and training extraction.
- [x] Keep raw model scores hidden from customer-facing summaries.
- [x] Feed model-signal bands into structure path scores and adjusted top-path diagnostics.
- [x] Keep first model-signal tuning under `structure_policy.weights.dynamic_graph.model_signal_fusion`.
- [ ] Decide later whether `model_signal_policy` is needed after P7/P8 validation evidence accumulates.

### P8 Interaction State Machine

- [x] Add explicit `v30.interaction_state.v1` with `interaction_stage`, `selected_domain`, `answered_question_ids`, `selected_option_ids`, `visible_next_question_id`, `internal_next_question_id`, and `followup_reason`.
- [x] Let `QuestionDialogueGraph` keep internal strategy while presentation projects role-visible next question.
- [x] Keep `next_question_id` backward compatible and add `internal_next_question_id`/`followup_reason`.
- [x] Emit `v30.training_signal.interaction_state_machine` and `v30.training_signal.interaction_loop_quality`.
- [x] Generate `question_policy.weights.interaction_followup_policy` candidates from interaction signals.
- [x] Add dedicated synthetic `interaction_loop` tier beyond current all-suite observations.
- [x] Add `real_case_calibration_pack` tier covering solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender fixtures.

### P9 Real-case Calibration

- Build canonical real-case fixtures for solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender boundaries.
- Validate luck-cycle, flow-year, six-pillar, ten-god energy, and recommended question ordering without hard-coding fixed conclusions.

### P10 Role/session Foundation

- Preserve current `actor_id` and `session_id` hooks.
- Add the minimal read-history interface needed for repeated readings without implementing a full login system.
- Keep guest/user/practitioner/admin projection on the same presentation contract.

Current P10.1 status:

- Repository history filtering is active for memory, local JSON, and Postgres adapters.
- `GET /api/v30/readings/history` returns `v30.reading_history_projection.v1` by `actor_id` and/or `session_id`.
- User history projection hides actor/internal diagnostics; admin/practitioner-style roles retain actor context and internal next-question diagnostics.
- The interface projects existing reading payloads and does not mutate chart facts or add authentication scope.

## Execution Completed In Practical Measurement Baseline Slice

1. Add BirthInput-derived `LuckCycleContext`, `FlowContext`, and `SixPillarContext`.
2. Derive current luck pillar, flow-year pillar, and flow-month pillar for supported solar BirthInput.
3. Add `RankedDecision` and `PracticalReadingContext` contracts.
4. Add `TenGodEnergyModel` as a deterministic model-signal layer between ChartContext and FeatureEvidence.
5. Emit strength, structure-pattern, and useful-god ranked decisions.
5. Emit career, wealth, relationship, health, and timing practical reading domains.
6. Emit agent question flow and practical-domain follow-up anchor.
7. Expose the new context through runtime policy effects, answer role contract, client diagnostics, and synthetic observations.
8. Add practical mainline synthetic suites and training signals.
9. Preserve deterministic chart-fact boundaries: training, feedback, LLM, and synthetic drafts cannot create pillars, luck-cycle facts, or flow facts.

## Execution Completed In Customer Reading Loop Slice

1. Add `reading_surface` to `ClientPresentationModel` as the customer-facing product surface.
2. Keep `mainline_card`, `structure_card`, and `chart_summary` backward compatible while hiding internal context for guest/user roles.
3. Expose internal `v30.internal_bazi_context.v1` only through diagnostics for practitioner/admin/lab roles.
4. Add `question_value`, `expected_information_gain`, and `v30.high_value_question.v1` to recommended questions.
5. Add synthetic observation and `v30.training_signal.high_value_question_quality` so question quality can tune policy candidates without mutating chart facts.

## Execution Completed In P6 LLM And Recommended Interaction Slice

1. Add V30-native LLM provider/readiness configuration with `V30_LLM_*` first and `V20_LLM_*` compatibility fallback.
2. Add V30-native LLM answer draft client for OpenAI-compatible and Ollama-style endpoints.
3. Compose rule-bound answer first, then optional bounded LLM draft; unavailable, disabled, failed, or drifted LLM output falls back to rule answer.
4. Expose `llm_provider_readiness` and `llm_answer_draft_call` in diagnostics and answer metadata.
5. Make the answer endpoint return the refreshed customer view after user feedback.
6. Replace the UI debug screen with a customer loop: BirthInput, concise reading, recommended questions, answer submission, refreshed answer.
7. Preserve V30/V20 boundary: V20 configuration shape may be read for migration compatibility; V30 code does not import V20 runtime.

## Execution Completed In Structured Interaction Contract Slice

1. Freeze the UI-facing API shape through `v30.ui_api_contract.v1` in `/api/v30/ui/capabilities`.
2. Add structured options to recommended questions and project the active question options into `reading_surface.options`.
3. Persist `selected_option`, confidence, tags, and compact `known_user_signals` as dialogue context, not chart facts.
4. Make `QuestionDialogueGraph.next_question_id` drive the customer surface next question after answer submission.
5. Expose admin `v30.llm_runtime_status.v1` so operators can see fallback/accepted/executed/readiness without exposing secrets.
6. Add `v30.actor_context.v1` as the minimal multi-user/session hook on reading creation without introducing a heavy auth system.
7. Update `/v30/ui/` to submit structured option clicks while keeping the direct "查看回答" path.

## Execution Completed In P5 Reading Quality Upgrade Slice

1. Add customer-readable domain summaries for career, wealth, relationship, health, and timing.
2. Add `customer_takeaway`, `action_prompt`, `priority_score`, and `v30.practical_reading_quality.v1` to domain readings.
3. Project prioritized `domain_cards` into the customer reading surface without exposing internal diagnostics.
4. Feed practical reading gaps into recommended-question scoring, expected information gain, and quality-contract focus metadata.
5. Expand `v30.training_signal.practical_reading_quality` with summary, takeaway, action prompt, quality contract, state, and priority-score coverage.
6. Preserve the boundary that reading quality trains expression, ranking, and question strategy, not chart facts.

## Execution Completed In Role-Locale-Client Projection Slice

1. Add `ClientKey` for `web`, `mobile`, `admin`, and `lab`.
2. Add `ClientProfile` contract with density, question count, diagnostics visibility, actions, and boundary.
3. Normalize presentation output through contract-shaped client profiles.
4. Add `v30.role_locale_client_projection_matrix.v1` for supported roles, locales, clients, sampled combinations, and projection boundaries.
5. Observe the projection matrix in synthetic replay.
6. Extract `v30.training_signal.role_locale_client_projection_coverage`.
7. Keep projection training silent, backend-driven, candidate-first, and validation-gated; it may tune visibility, density, labels, and question strategy, but not chart facts.

## Execution Completed In Real-Case Boundary Slice

1. Add canonical `real_case_validation` synthetic cases for common ready and blocked user scenarios.
2. Validate ready solar male/female BirthInput through chart build, six-pillar context, practical reading, and agent question flow.
3. Validate unknown-gender BirthInput as usable natal/practical context without forcing luck-cycle direction.
4. Validate invalid timezone as blocked with no fabricated pillars.
5. Add calendar boundary unit tests for invalid timezone, invalid date, invalid time, and late 子 hour recording.
6. Extract `v30.training_signal.real_case_feedback_alignment`.
7. Keep real-case training silent and validation-gated; it tunes quality and policy candidates, not deterministic chart facts.

## Execution Completed In This Slice

1. Expand K/R/P from 27+ to 35+ matched runtime units.
2. Add fine-grained domain-rule supports for wealth, career, relationship, health, and useful-god candidate review.
3. Expose domain-rule depth path scores in `StructureState`.
4. Feed domain-rule depth into synthetic training payload and `structure_policy.weights.dynamic_graph.domain_rule_depth`.
5. Add hidden-factor `expires_at`, `stale_after_days`, and `time_layer_alignment_score`.
6. Rehydrate expired hidden-factor candidates as refresh-needed state instead of active amplifier candidates.
7. Update synthetic expectations, unit tests, and documentation.
8. Run full validation gates and live service checks.

## Execution Completed In 518K Index Slice

1. Add persistent 518K validation run index at `.runtime/validation/518k/index.json`.
2. Add per-run index entries under `.runtime/validation/518k/index/{run_id}.index.json`.
3. Add `index_uri` and `index_entry_uri` to `Corpus518KValidationResult`.
4. Include artifact and index URIs in release gate 518K check summaries.
5. Print artifact and index paths from `scripts/run_518k_validation.py`.
6. Keep the index as a JSON artifact layer, without a database schema change.

## Execution Completed In 518K Artifact Search Slice

1. Promote 518K validation runs into `v30_artifacts` records when `V30_DATABASE_URL` is available.
2. Keep `.runtime/validation/518k/index.json` and per-run index entries as the canonical local fallback.
3. Add deterministic `artifact_record_id`, `artifact_search_backend`, and `artifact_searchable` fields to `Corpus518KValidationResult`.
4. Add `GET /api/v30/admin/validation/518k/artifacts` for searchable validation artifact diagnostics.
5. Add 518K artifact search metadata to release gate sample/shard summaries.
6. Preserve the no-schema-change boundary by reusing the existing `v30_artifacts` table.

## Execution Completed In Central Brain Adaptive Question Diagnostics Slice

1. Add `v30.adaptive_question_diagnostics.v1` as a replayable diagnostic contract.
2. Record per-question decision rows with rank, score, topic, stage, policy weight, policy version, and reason categories.
3. Summarize active question policy weights, hidden-factor event policy presence, and weighted decision coverage.
4. Attach replay inputs including active policy versions, mainline/structure IDs, time status, hidden-factor status, question outcomes, brain unknown context, and feedback slots.
5. Expose diagnostics in runtime trace, admin presentation diagnostics, and `GET /api/v30/admin/runs/{reading_id}/question-replay`.
6. Preserve boundaries: adaptive diagnostics replay trace state only and do not mutate chart facts or policy pointers.

## Execution Completed In Adaptive Question Policy Candidate Slice

1. Add `v30.training_signal.adaptive_question_replay` from synthetic runtime replay diagnostics.
2. Include decision count, weighted-decision coverage, alignment coverage, topics, stages, intents, strategies, and reason-category counts in the signal payload.
3. Convert replay signals into `question_policy.weights.adaptive_question_policy`.
4. Apply bounded topic/stage/intent boosts while preserving existing question-policy, hidden-factor, and K/R/P weighting boundaries.
5. Auto-apply adaptive question candidates through the existing synthetic + 518K sample promotion path.
6. Keep the boundary `adaptive_question_policy_weights_replay_diagnostics_not_chart_facts`.

## Execution Completed In Question Policy Comparison Diagnostics Slice

1. Add `v30.question_policy_comparison.v1` for active-vs-candidate question-policy comparison.
2. Recompute candidate recommendations against the same runtime trace without mutating runtime state.
3. Record rank delta, score delta, policy-weight delta, added reasons, and removed reasons per question.
4. Persist comparison artifacts under `.runtime/validation/question_policy_comparisons/` with an index.
5. Attach question-policy comparison summaries to promoted policy artifacts.
6. Expose `GET /api/v30/admin/policies/question/comparison` for latest or candidate-specific comparison lookup.
7. Preserve boundaries: comparison diagnostics are candidate artifacts, not chart facts or pointer mutations.

## Execution Completed In Unified Validation Artifact Discovery Slice

1. Extend the existing `v30_artifacts` search surface beyond 518K artifacts.
2. Index question-policy comparison artifacts as `family=question_policy_comparison` when Postgres is configured.
3. Keep JSON fallback under `.runtime/validation/question_policy_comparisons/`.
4. Add unified `GET /api/v30/admin/validation/artifacts` with `family`, `candidate_id`, `run_id`, and `limit` filters.
5. Preserve the existing 518K-specific endpoint for compatibility.
6. Keep boundaries: artifact discovery is validation lineage, not chart fact generation.

## Execution Completed In Promotion Lineage Graph Diagnostics Slice

1. Add `v30.promotion_lineage.v1` to connect runtime pointer, policy artifact, validation evidence, and active runtime trace consumption.
2. Build lineage from existing `RuntimePointerStore`, policy artifact validation summary, unified validation artifact discovery, and a smoke runtime trace.
3. Expose `GET /api/v30/admin/policies/lineage?family=question_policy`.
4. Support core runtime policy families: `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy`.
5. Include rollback pointer, previous artifact, validation run id, validation artifacts, and runtime active-policy consumption summary.
6. Preserve boundaries: lineage is diagnostic only and does not mutate pointers, retrain, or create chart facts.

## Execution Completed In Question Outcome Slice

1. Upgrade question answer feedback from acknowledgement-only to `QuestionIntentPlan.session_state.question_outcomes`.
2. Recompute recommendations and `QuestionDialogueGraph` after question outcome feedback.
3. Add `question_dialogue_outcome_consumed` and `question_outcome_topic:*` graph notes.
4. Extract `v30.training_signal.question_dialogue_outcome` from synthetic outcomes.
5. Feed outcome signal into conservative `question_policy` topic/intent weights.
6. Keep question outcomes as feedback state, not chart facts.

## Execution Completed In LLM Output Contract Slice

1. Add `v30.llm.output_contracts` with `AnswerDraft` and `QuestionExplanation` task contracts.
2. Validate contracts through deterministic drift checks before exposing them in runtime policy effects.
3. Expose `llm_output_contracts` and `llm_output_contract_summary` in runtime/admin diagnostics.
4. Add synthetic validation for LLM contract status.
5. Extract `v30.training_signal.llm_output_contract_quality`.
6. Keep output contracts as expression/LLM safety boundaries, not chart reasoning inputs.

## Execution Completed In Role-Aware Portrait View Slice

1. Add `MacroPortraitProjectionView` with role/client visibility, density, summaries, display tags, and projection boundaries.
2. Emit default user/web `macro_portrait_projection_views` and `macro_portrait_view_summary` from runtime policy effects.
3. Expose matched portrait views in `role_answer_contract.macro_portrait_projection_views`.
4. Rebuild role/client-specific portrait views in presentation diagnostics, including admin diagnostic views and mobile compact views.
5. Add synthetic role contrast validation: guest hides hidden-factor views while admin keeps diagnostic hidden-factor views.
6. Extract `v30.training_signal.portrait_projection_view_coverage` from synthetic replay.
7. Keep portrait views as role-filtered projection surfaces, not chart facts.

## Execution Completed In Remaining LLM Contract Slice

1. Extend LLM task contracts to include `SyntheticCaseDraft` and `FailureClusterSummary`.
2. Add deterministic builders for synthetic case draft and failure cluster summary contracts.
3. Expose four runtime output contracts: `AnswerDraft`, `QuestionExplanation`, `SyntheticCaseDraft`, and `FailureClusterSummary`.
4. Update synthetic/training quality extraction so `v30.training_signal.llm_output_contract_quality` measures four-task coverage.
5. Preserve boundaries: synthetic case drafts cannot mutate chart facts; failure cluster summaries are training triage, not runtime facts.

## Execution Completed In Hidden-Factor Policy Weight Slice

1. Convert `v30.training_signal.hidden_factor_event_alignment` into a conservative `hidden_factor_event_policy`.
2. Attach that policy under `question_policy.weights.hidden_factor_event_policy` and `rule_policy.weights.hidden_factor_event_policy`.
3. Apply hidden-factor policy weights only when a persisted hidden-factor state is present.
4. Boost aligned amplifier candidates slightly, refresh expired states slightly, and downweight conflicting or denied states.
5. Preserve the boundary `hidden_factor_policy_weights_feedback_conditioned_not_chart_fact`.

## Execution Completed In Tongguan/Zhihua Path Slice

1. Add domain-rule supports for 通关 resource mediation, output-to-wealth bridge, output-controls-authority 制化, and wealth-authority-resource 制化 chains.
2. Add four K/R/P units for bounded 通关/制化 candidate review.
3. Tag dynamic graph paths with `tongguan_*` and `zhihua_*` resolution families.
4. Expose `dynamic_tongguan_*` and `dynamic_zhihua_*` path scores in `StructureState`.
5. Feed those metrics into `v30.training_signal.structure_dynamic_competition`.
6. Add `structure_policy.weights.dynamic_graph.tongguan_zhihua` to auto-training.
7. Keep all 通关/制化 outputs as path-resolution candidates, not final structure/useful-god verdicts.

## Execution Completed In Expression Question Label Slice

1. Add deterministic expression-rendered question labels for role/client presentation.
2. Make `ClientPresentationModel.questions[].label` consume rendered labels instead of raw anchor text.
3. Add label metadata: source, boundary, and rendered-label summary.
4. Expose rendered question label diagnostics for admin/lab style clients.
5. Add synthetic observation for rendered labels and forbidden engineering-token leakage.
6. Keep question labels as presentation text, not chart facts or recommendation inputs.

## Execution Completed In Per-Unit Parameter Tuning Slice

1. Add `v30.training_signal.per_unit_parameter_tuning` from synthetic K/R/P unit coverage and failure clusters.
2. Emit bounded `rule_weights`, `domain_weights`, and `mechanism_weights` maps.
3. Feed per-unit maps into `rule_policy.weights.per_unit_parameter_policy`.
4. Merge per-unit mechanism weights into `structure_policy.weights.mechanism.*`.
5. Preserve the boundary `per_unit_weights_tune_runtime_candidates_not_chart_facts`.

## Next Mainline Gaps

Priority order:

1. U-S1 Productization Steady State.

Next recommended slice:

```text
U-S1 Productization Steady State
-> U5 accepted U1-U4 evidence through v30.productization_closeout.v1
-> keep current-scope multi-user/session/terminal/locale productization stable
-> reopen only on new product requirement, projection contract failure, full login scope approval, or explicit UI redesign scope
-> keep deterministic chart facts and frozen M1-M8 completion sealed
-> do not run full pytest, synthetic all, or full 518K unless explicitly requested for release/full-freeze or a major module gate
```

Reason:

- C3 completed M7 real-case calibration drift routing across the 30-case canonical pack.
- C4 completed M8 core-first API projection: customer projection now has core-first contract, customer surface contract, full additive preservation, forbidden-field policy, sanitized question/answer projection, and role-gated diagnostics.
- C7 completed the integrated core gate: `compileall` passed, synthetic all passed 95/95, 518K sample `v30.518k.sample.20260606084440379258` passed with 8 cases using `json_fallback`, and targeted core pytest passed 38/38.
- C5 completed M1/M2 deterministic facts and base explanations: `v30.m1_m2_completion_summary.v1` validates required fact keys, explanation coverage, deterministic integrity, M5/M6 downstream consumption, and no chart-fact mutation.
- C6 completed M3 evidence/rule/knowledge/structure spine: `v30.m3_completion_summary.v1` validates source/KRP/rule/structure coverage, M4/M5/M6 support, no conclusion-engine behavior, and no chart-fact mutation.
- C8 completed core-completion documentation freeze: M1-M8 are 100% current-scope complete, C7 validation evidence is carried forward, and external release/full pytest/pointer-promotion are separated from the core-completion track.
- F1 completed the frozen-core calibration baseline: `v30.frozen_core_calibration_review.v1` is available through CLI and admin API, the complete F1 review passed with 6 tiers and 31 training signals, and the next task is F2.
- F2 completed targeted calibration candidate review: `v30.targeted_calibration_candidate_review.v1` is available through CLI and admin API, four candidate tracks are ready, and the next task is F3 validation gate.
- F3 completed targeted calibration validation gate: `v30.targeted_calibration_validation_gate.v1` is available through CLI and admin API, candidate overrides passed synthetic all 95/95 and 518K sample 8 cases, and the next task is F4 pointer review.
- F4 completed targeted calibration pointer review: `v30.targeted_calibration_pointer_review.v1` is available through CLI and admin API, four pointer diffs are ready for an explicit operator decision, and no pointer was written.
- F5 completed explicit operator pointer decision: `v30.targeted_calibration_pointer_decision.v1` is available through CLI and admin API, promotion request remains blocked without a separate explicit write command, the recorded operator decision is `defer`, and no active pointer was written.
- F6 completed targeted calibration closeout: `v30.targeted_calibration_closeout.v1` is available through CLI and admin API, the closeout status is `targeted_calibration_closed_with_no_promotion`, four monitoring checks are recorded, `pointer_write=false`, and no active pointer was changed.
- M0 completed mainline selection: `v30.mainline_selection.v1` is available through CLI and admin API, selected `R13 External Release Dry Run And Full Pytest Decision`, keeps `full_pytest_run_now=false`, and keeps pointer promotion disabled.
- R13 completed external release dry run: `v30.external_release_dry_run.v1` is available through CLI and admin API, `full_pytest_decision=defer` is recorded, `external_release_ready=false`, and pointer promotion remains disabled.
- R14 completed external release full pytest decision: `v30.external_release_full_pytest_decision.v1` is available through CLI and admin API, `full_pytest_decision=defer` is recorded, `external_release_ready=false`, `external_release_blocked=true`, and pointer promotion remains disabled.
- R15 completed external release blocked status: `v30.external_release_blocked_status.v1` is available through CLI and admin API, release blockers are recorded, `external_release_ready=false`, `external_release_blocked=true`, and pointer promotion remains disabled.
- R16 completed post-release-boundary authorization: `v30.post_release_boundary_authorization.v1` is available through CLI and admin API, `authorization_decision=pause` is recorded, `full_pytest_authorized=false`, `full_pytest_run_triggered=false`, and pointer promotion remains disabled.
- M0 after release pause completed mainline selection: `v30.mainline_selection_after_release_pause.v1` is available through CLI and admin API, selected `P0 Core Module Monitoring And Calibration Loop`, keeps external release blocked, and keeps full pytest/pointer promotion disabled.
- P0 completed core monitoring loop setup: `v30.core_monitoring_loop.v1` is available through CLI and admin API, confirms 4/4 monitoring checks, no regression detected, and no module reopen recommended.
- P1 completed lightweight core monitoring execution: `v30.lightweight_core_monitoring_checks.v1` is available through CLI and admin API, passed 4/4 checks, no regression detected, and no pointer promotion occurred.
- P2 completed core calibration observation summary: `v30.core_calibration_observation_summary.v1` is available through CLI and admin API, summarized 4 stable observations, found no regression, required no focused module fix, and did not run full pytest.
- P3 completed core calibration drift watch: `v30.core_calibration_drift_watch.v1` is available through CLI and admin API, established on-new-evidence cadence, found no drift, exposed the check-to-module route matrix, and did not run full pytest.
- P4 completed focused core calibration evidence queue: `v30.focused_core_calibration_evidence_queue.v1` is available through CLI and admin API, keeps future evidence batched by module target, starts with an empty queue, and does not run full pytest.
- P5 completed core calibration queue review: `v30.core_calibration_queue_review.v1` is available through CLI and admin API, reviewed an empty queue, found no focused fix candidate, and did not run full pytest.
- P6 completed core calibration watch closeout: `v30.core_calibration_watch_closeout.v1` is available through CLI and admin API, passed 4/4 closeout checks, closed the current empty watch cycle, and did not run full pytest.
- P7 completed core monitoring cadence baseline: `v30.core_monitoring_cadence_baseline.v1` is available through CLI and admin API, sets default cadence to `on_new_calibration_evidence_only`, routes future evidence through P4/P5, and keeps heavy validation explicit.
- P8 completed core monitoring cadence documentation sync: `v30.core_monitoring_cadence_documentation_sync.v1` is available through CLI and admin API, synchronizes the required cadence docs, and keeps future evidence routed through P4/P5.
- P9 completed core monitoring steady state: `v30.core_monitoring_steady_state.v1` is available through CLI and admin API, passed 4/4 steady-state checks, and waits for new calibration evidence.
- S0 status is recorded: `v30.core_monitoring_s0_status.v1` is available through CLI and admin API, passed 4/4 status checks, and explicitly disallows starting another core-monitoring task by default.
- B1 completed real business Bazi reading acceptance: `v30.real_business_bazi_reading_acceptance.v1` is available through CLI and admin API, accepted 12/12 ready canonical rows, and did not run full pytest or full 518K.
- B2 completed business reading regression: `v30.real_business_bazi_reading_regression_pack.v1` is available through CLI and admin API, accepted 24/24 ready canonical rows, expanded M8 projection to five concise business domain cards, and did not run full pytest or full 518K.
- B3 completed business answer refresh regression: `v30.real_business_answer_refresh_regression.v1` is available through CLI and admin API, passed 5/5 answer refresh rows, preserved core reading fingerprints and chart facts, and did not run full pytest or full 518K.
- B4 completed boundary and blocked input regression: `v30.real_business_boundary_blocked_input_regression.v1` is available through CLI and admin API, passed 5/5 pending/blocked rows, prevented fake chart facts and fake-ready runtime outputs, and did not run full pytest or full 518K.
- B5 completed business API contract freeze: `v30.real_business_api_contract_freeze.v1` is available through CLI and admin API, froze B1-B4 as 4/4 required gates, and did not run full pytest or full 518K.
- B6 completed business acceptance closeout: `v30.real_business_acceptance_closeout.v1` is available through CLI and admin API, passed 4/4 closeout checks, paused B-track by default, and did not run full pytest or full 518K.
- S1 completed business acceptance steady state: `v30.real_business_steady_state.v1` is available through CLI and admin API, passed 5/5 steady-state checks, uses B1-B5 as the routine business gate, and did not run full pytest or full 518K.
- BT support-system completion mainline is complete for current scope: `docs/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md` records BT1-BT10 and the BT-S1 steady-state rule for central brain, training, synthetic validation, and 518K readiness.
- BT1 completed central brain acceptance: `v30.central_brain_acceptance.v1` is available through CLI and admin API, passed 5/5 acceptance checks, raises central brain completion to 90%, and did not run full pytest or full 518K.
- BT2 completed long-session brain replay: `v30.central_brain_session_replay.v1` is available through CLI and admin API, passed 6/6 replay checks, raises central brain completion to 94%, and did not run full pytest, synthetic all, or full 518K.
- BT3 completed brain failure routing: `v30.brain_failure_route.v1` is available through CLI and admin API, passed 6/6 routing checks, raises central brain completion to 97%, and did not run full pytest, synthetic all, or full 518K.
- BT4 completed training system closeout: `v30.training_system_closeout.v1` is available through CLI and admin API, passed 8/8 closeout checks, raises training / auto-apply completion to 97%, and did not run full pytest, synthetic all, or full 518K.
- BT5 completed failed-candidate quarantine: `v30.training_candidate_quarantine.v1` is available through CLI and admin API, passed 8/8 quarantine checks, raises training / auto-apply completion to 99%, and did not run full pytest, synthetic all, or full 518K.
- BT6 completed synthetic coverage manifest: `v30.synthetic_coverage_manifest.v1` is available through CLI and admin API, passed 7/7 manifest checks, raises synthetic validation completion to 96%, and did not run full pytest, synthetic all, or full 518K.
- BT7 completed central brain synthetic tier: `v30.synthetic.central_brain` passed 5/5 cases, validates role/session/hidden-factor/expression/training-route/no-mutation contracts, raises intelligent central brain completion to 100% and synthetic validation completion to 98%, and did not run full pytest, synthetic all, or full 518K.
- BT8 completed training pipeline synthetic tier: `v30.synthetic.training_pipeline` passed 91/91 cases, training signal extraction covers core/support signal families and no-chart-fact boundaries, raises training / auto-apply completion to 100% and synthetic validation completion to 99%, and did not run full pytest, synthetic all, or full 518K.
- BT9 completed 518K readiness matrix: `v30.518k_readiness_matrix.v1` passed 7/7 checks, sample 8 passed with JSON fallback artifact record `v30.518k.artifact.v30.518k.sample.20260609175010408754`, raises 518K validation support completion to 95%, and did not run full pytest, synthetic all, or full 518K.
- BT10 completed unified support-system closeout: `v30.brain_training_synthetic_closeout.v1` is available through CLI and admin API, passed 6/6 closeout checks, records central brain 100%, training 100%, synthetic validation 100%, 518K validation support 95%, enters `BT-S1 Support Systems Steady State`, and did not run full pytest, synthetic all, or full 518K.
- U1 completed multi-user / terminal / locale projection readiness: `v30.multi_user_terminal_locale_readiness.v1` is available through CLI and admin API, passed 7/7 checks across 72 role/locale/client combinations, keeps guest/user sanitized on every terminal, gates diagnostics/actions by role, and did not run full pytest, synthetic all, or full 518K.
- U2 completed session ownership and role boundary hardening: `v30.session_owner_boundary_readiness.v1` is available through CLI and admin API, passed 7/7 checks, requires actor+session for customer history, keeps customer owner IDs and diagnostics hidden, allows diagnostic actor-only owner inspection, blocks same-session cross-actor leakage, and did not run full pytest, synthetic all, or full 518K.
- U3 completed locale terminology and fallback contract: `v30.locale_terminology_readiness.v1` is available through CLI and admin API, passed 7/7 checks, adds `v30.locale_terminology_contract.v1`, covers zh/en/ko Bazi terms with zero required fallback, localizes domain/base-fact labels, proves locale projection does not change chart facts, and did not run full pytest, synthetic all, or full 518K.
- U4 completed terminal contract freeze: `v30.terminal_contract_freeze.v1` is available through CLI and admin API, passed 8/8 checks, freezes web/mobile/admin/lab required fields, validates customer/practitioner/admin/lab terminal visibility and action contracts, proves terminal projection does not change chart facts, and did not run full pytest, synthetic all, or full 518K.
- U5 completed productization closeout: `v30.productization_closeout.v1` is available through CLI and admin API, passed 5/5 checks, accepts U1-U4 evidence, enters `U-S1 Productization Steady State`, records full login/payment/membership/organization permissions/complete UI redesign as explicit non-goals, and did not run full pytest, synthetic all, or full 518K.
- R8 completed the metadata-only intake contract and canonical intake selection: 30 rows, 25 calibration-ready, 3 pending, 2 blocked.
- R9 completed metadata-safe replay storage/search: 30 persisted intake rows, 25 calibration-ready rows searchable by readiness/module readiness.
- R10 completed the evidence-backed review: quick gate and replay store readiness recommended R11 standard release-candidate gate.
- R11 completed the standard release-candidate gate: seven checks passed with sample and selected shard evidence, and policy pointer promotion remains disallowed.
- R12 completed the release-boundary finalization: the internal release candidate is finalized, while external release still requires explicit full pytest and manual pointer-promotion decisions.
- Active core module completion under `docs/V30_CORE_MODULE_FINAL_COMPLETION_MAINLINE.md` is frozen for the current M1-M8 scope; S0 is recorded. No further core-monitoring task runs by default without new evidence or an explicit release/full-freeze request.
- C1 completed M6 practical reading output: all practical domains now expose calculation basis, domain insights, action steps, calibration prompts, M1-M5 module trace, blocked claims, and quality contracts.
- C2 completed M4/M5 calibration: M4 model-signal profiles expose calibration flags and ranked-decision adjustments; M5 scoring consumes them while keeping ranked decisions candidate-bound and raw scores hidden.
- C3 completed M7 real-case calibration: canonical fixtures now emit `v30.real_case_calibration_drift_summary.v1`, and training signals summarize stable/review counts, drift flags, module adjustment targets, and module readiness without mutating chart facts.
- Current runtime supports explicit pillars, solar/lunar/known-place true-solar BirthInput conversion, luck/flow context, six-pillar context, ranked decisions, practical reading context, agent question flow, projection contracts, canonical real-case validation, and release artifact review.
- Training and synthetic validation should continue silently in the background and tune candidate behavior after replay metadata coverage exists.
