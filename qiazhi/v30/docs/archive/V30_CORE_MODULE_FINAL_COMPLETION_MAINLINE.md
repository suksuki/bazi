# V30 Core Module Final Completion Mainline

Updated: 2026-06-10

## Purpose

This is the controlling plan for finishing the eight core Bazi calculation modules. It supersedes post-seal/release-hardening work as the active mainline.

Principle:

- UI stays concise.
- Core calculation modules become complete and verifiable.
- Training, synthetic validation, real-case replay, and 518K checks serve M1-M8 only.
- No new LLM, admin, release, auth, dashboard, or UI expansion work leads the mainline.
- Hidden-factor and question loops remain feedback/calibration support; they cannot become chart facts or replace the calculation surface.

## Active Mainline

Current active task:

```text
S1 Business Acceptance Steady State completed; next S1-WAIT await new business evidence or explicit major validation
```

Reason:

- M1-M8 are individually complete for the current core scope.
- C7 proved the integrated BirthInput -> facts -> M3 evidence spine -> M4/M5 -> M6 reading -> M8 projection path.
- C8 completed documentation freeze and cross-document status alignment.
- Further work must be framed as targeted calibration, release validation, or a new explicitly scoped mainline, not hidden feature expansion inside the frozen core-completion track.
- P0/P1/P2/P3/P4/P5/P6/P7/P8/P9/S0 established the lightweight post-freeze monitoring, observation, drift-watch, focused evidence-queue, queue-review, watch-closeout, cadence-baseline, documentation-sync, steady-state, and read-only status path without reopening frozen core modules.
- B1-B6 completed the business-acceptance track through ready real-case reading acceptance, expanded regression, answer refresh, blocked-boundary regression, API contract freeze, and closeout without reopening M1-M8.
- S1 entered business acceptance steady state: routine work uses the B1-B5 gate, no further B-track task starts by default, and major validation remains explicit.

## Completion Target

The eight modules are considered complete for the current V30 product scope when every module reaches a verifiable 100% current-scope seal:

| Module | Current | Target | Completion definition |
|---|---:|---:|---|
| M1 BirthInput and deterministic chart facts | 100% | 100% | C5 complete: supported solar/lunar/leap/true-solar/unknown-hour/invalid-input boundaries are deterministic, fixture-backed, no-fake-fact guarded, and consumed downstream without mutation. |
| M2 Base Bazi fact explanation layer | 100% | 100% | C5 complete: every ready chart exposes complete day-master, ten-god, hidden-stem, five-element, relation, root/vault, timing, customer-safe explanations, and M5/M6 consumption proof. |
| M3 Evidence / rule / knowledge / structure spine | 100% | 100% | C6 complete: source registry, V20 reference assets, K/R/P units, rule/counter-evidence, portrait features, dynamic graph, structure mechanisms, mainline arbitration, and M4/M5/M6 support proof form one auditable spine. |
| M4 Ten-god energy model | 100% | 100% | C2 complete: energy/stability/volatility bands expose calibration flags and ranked-decision adjustments across canonical cases without raw score leakage. |
| M5 Strength / structure / useful-god ranked decisions | 100% | 100% | C2 complete: strength, structure, and useful-god decisions consume M4 calibration flags, remain ranked/evidence-bound, and never become fixed verdicts. |
| M6 Practical reading output | 100% | 100% | C1 complete: career, wealth, relationship, health, and timing readings are calculation-backed, useful, bounded, traceable to M1-M5, and validated across M6 contract plus real-case calibration pack. |
| M7 Core validation / real-case calibration | 100% | 100% | C3 complete: canonical and metadata-safe replay cases validate M1-M6 behavior, boundaries, and module-routed calibration drift without mutating chart facts. |
| M8 User presentation / API projection | 100% | 100% | C4 complete: customer API surfaces core calculation first, hides diagnostics/raw scores/policy/training internals, preserves additive contracts, and keeps admin diagnostics role-gated. |

## Execution Order

### C1 M6 Practical Reading Output Completion

Status: completed 2026-06-06.

Target: M6 85% -> 100%.

Scope:

- Complete practical output for career, wealth, relationship, health, and timing.
- Each domain must expose calculation basis from M1/M2, M3 evidence, M4 signal bands, M5 ranked decisions, and M7 calibration references.
- Add domain-specific boundary language and blocked claims.
- Ensure output is useful without becoming deterministic life-event prediction.
- Keep LLM optional; rule-bound answer remains primary.

Validation:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py
python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
```

No full pytest by default.

Completed:

- Added M6 domain insight layer for career, wealth, relationship, health, and timing.
- Added `domain_insights` with opportunity path, pressure/risk path, and calibration path for every practical domain.
- Added `action_steps` for user-facing next actions without turning feedback into chart facts.
- Added `calibration_prompts` for domain priority, timing calibration, and expression fit.
- Added `v30.m6_practical_module_trace.v1` proving M6 consumes M1/M2 facts, M3 structure evidence, M4 model signal, and M5 ranked decisions without raw score leakage or chart-fact mutation.
- Extended real-case calibration observations with M6 insight/action/calibration/trace counts.
- Extended practical-reading training signal with M6 insight, action step, calibration prompt, and module trace coverage.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m6_practical_reading_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
3 passed
python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (30/30)
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### C2 M4 + M5 Model Signal And Ranked Decision Calibration

Status: completed 2026-06-06.

Target: M4 88% -> 100%, M5 88% -> 100%.

Scope:

- Calibrate ten-god energy/stability/volatility bands against canonical cases.
- Tighten how M4 affects strength, structure, and useful-god candidates.
- Add replay assertions for follow/disputed/regulation/special-structure/useful-god conflict cases.
- Keep raw model scores hidden.
- Keep production threshold changes gated by validation evidence.

Validation:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
python3 scripts/run_synthetic_validation.py --tier m4_ten_god_real_case_replay
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
```

Completed:

- Added M4 `calibration_flags` to `v30.model_signal_calibration_profile.v1`.
- Added `v30.model_signal_ranked_decision_adjustments.v1` under the bounded model-signal profile.
- Added M5 scoring-basis fields for calibration flags, ranked adjustment version, ranked adjustment flags, and score-bias maps.
- M5 now consumes M4 calibration bias conservatively for strength review, dynamic/disputed structure review, and non-unique useful-god review.
- Extended M4/M5 synthetic observations and training signals with calibration flag and ranked-adjustment coverage.
- Kept raw model scores hidden and kept all ranked decisions candidate-bound.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_practical_reading_context.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
9 passed
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
v30.synthetic.ten_god_energy_calibration: passed (5/5)
python3 scripts/run_synthetic_validation.py --tier m4_ten_god_real_case_replay
v30.synthetic.m4_ten_god_real_case_replay: passed (5/5)
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
v30.synthetic.strength_structure_useful_god: passed (1/1)
python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract
v30.synthetic.m5_ranked_decision_contract: passed (30/30)
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

### C3 M7 Real-Case Calibration Completion

Status: completed 2026-06-06.

Target: M7 90% -> 100%.

Scope:

- Expand canonical case pack only where it covers a real calculation boundary.
- Keep private production content out of deterministic facts.
- Validate solar, lunar, leap-month, true-solar, unknown-hour, unknown-gender, invalid input, M4 bands, M5 decisions, and M6 practical outputs.
- Add calibration-drift summaries that tell which module needs adjustment.

Validation:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
python3 scripts/run_production_replay_intake.py --persist --selection-status calibration_ready --module-ready m4
```

Completed:

- Added `v30.real_case_calibration_drift_summary.v1` to every canonical real-case fixture observation.
- The drift summary compares expected chart, six-pillar, and practical-reading states with observed runtime output.
- Drift flags route failures to M1, M2, M4, M5, or M6 module adjustment targets instead of changing deterministic chart facts.
- Stable cases expose `calibration_status=stable`; review cases would expose `needs_module_review` with explicit module targets.
- Extended `v30.training_signal.real_case_calibration_pack` with M7 drift-summary counts, stable/review counts, drift-flag counts, module-adjustment counts, and module-readiness counts.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
2 passed
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract
v30.synthetic.m6_practical_reading_contract: passed (30/30)
```

### C4 M8 Core-First API Projection Completion

Status: completed 2026-06-06.

Target: M8 90% -> 100%.

Scope:

- Ensure customer API always shows core calculation before questions or feedback probes.
- Keep `reading_surface`, `core_bazi_reading`, `domain_cards`, `questions`, `answer_panel`, `next_question_id`, `internal_next_question_id`, `actor_context`, and `llm_runtime_status` additive.
- Hide diagnostics, raw model scores, internal traces, policy payloads, and training internals from guest/user.
- Keep UI simple; do not expand visual surfaces unless needed to show calculation clearly.

Validation:

```text
python3 -m compileall -q v30
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py
python3 scripts/run_synthetic_validation.py --tier api_projection_contract
```

Completed:

- Added `v30.core_first_projection.v1` to `v30.api_projection_contract.v1`.
- Added `v30.customer_surface_contract.v1` to prove the customer surface contains core Bazi reading, domain cards, time context, and next question in the right order.
- Expanded additive API policy to preserve `reading_surface`, `core_bazi_reading`, `domain_cards`, `questions`, `answer_panel`, `next_question_id`, `visible_next_question_id`, `internal_next_question_id`, `actor_context`, `llm_runtime_status`, `diagnostics`, and `projection_contract`.
- Added `v30.role_visibility_matrix.v1` and `v30.customer_forbidden_projection_fields.v1`.
- Sanitized guest/user question rows and answer-panel LLM metadata so policy/training/internal call details do not leak while useful customer state remains available.
- Extended M8 synthetic validation and `v30.training_signal.api_projection_contract` with core-first policy, customer surface contract, full additive policy, and forbidden-field policy coverage.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py::test_synthetic_m8_api_projection_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
8 passed
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
pytest -q tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
1 passed
```

### C5 M1 + M2 Deterministic Fact Completion

Status: completed 2026-06-06.

Target: M1 95% -> 100%, M2 92% -> 100%.

Scope:

- Harden edge-year, solar-term, lunar/leap-month, true-solar, unknown-hour, timezone, invalid-date, and invalid-time boundaries.
- Ensure M2 explanations are complete for every ready M1 chart.
- Ensure M5/M6 consume M1/M2 facts rather than recalculating or mutating them.
- Preserve no-fake-facts guardrails.

Validation:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
pytest -q tests/unit/test_synthetic_validation.py tests/unit/test_practical_reading_context.py
```

Completed:

- Added `v30.m1_m2_completion_summary.v1` under `core_bazi_reading`.
- The summary validates required base fact keys, explanation-section coverage, deterministic fact integrity, M5 root/vault scoring-basis consumption, M6 module-trace consumption, and chart-fact no-mutation.
- Extended `m1_m2_base_fact_contract` synthetic observation with completion summary, downstream consumption readiness, M5 root-fact count, M6 M1/M2 consumption count, and no-mutation flag.
- Extended `v30.training_signal.m1_m2_base_fact_contract` with completion-ready and downstream-consumption counts.
- Preserved existing no-fake-fact guardrails for unknown-hour, invalid timezone/date/time, and blocked BirthInput cases.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context tests/unit/test_synthetic_validation.py::test_synthetic_m1_m2_bazi_calculation_tier_seals_base_fact_contract tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
3 passed
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
v30.synthetic.m1_m2_bazi_calculation: passed (12/12)
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
v30.synthetic.core_bazi_calculation: passed (4/4)
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py
24 passed
```

### C6 M3 Evidence / Knowledge / Rule / Structure Completion

Status: completed 2026-06-06.

Target: M3 96% -> 100%.

Scope:

- Complete the source-backed knowledge/rule/portrait spine for current product scope.
- Ensure rule evidence, counter-evidence, dynamic graph paths, mechanism scores, and mainline arbitration are auditable.
- Reuse V20 knowledge only as reference/source material; V30 schemas remain authoritative.
- Add validation that M3 supports M4/M5/M6 instead of becoming a separate conclusion engine.

Validation:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier knowledge_rule_portrait
python3 scripts/run_synthetic_validation.py --tier structure_dynamics
pytest -q tests/unit/test_training_signals.py tests/unit/test_synthetic_validation.py
```

Completed:

- Added runtime `v30.m3_completion_summary.v1`.
- The summary validates source registry coverage, V20 reference usage, K/R/P domain coverage, knowledge/rule/portrait signal coverage, rule counter-evidence, mechanism paths, dynamic graph paths, mainline arbitration, M4 model-signal support, M5 ranked-decision support, and M6 practical-reading support.
- Proved M3 does not act as a final conclusion engine and cannot mutate chart facts.
- Extended synthetic M3 checks so M3 cases require a ready completion summary.
- Extended `v30.training_signal.m3_core_spine_coverage` with completion-ready counts, M4/M5/M6 support counts, conclusion-engine count, and chart-fact-mutation count.
- Sanitized customer answer-panel projection so internal synthetic/evidence ids do not leak `dynamic_graph` style diagnostic tokens.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_krp_case_requires_bound_signals tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
2 passed
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
python3 scripts/run_synthetic_validation.py --tier knowledge_rule_portrait
v30.synthetic.knowledge_rule_portrait: passed (2/2)
python3 scripts/run_synthetic_validation.py --tier structure_dynamic_v2
v30.synthetic.structure_dynamic_v2: passed (1/1)
pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_v20_reference_registry.py tests/unit/test_knowledge_library.py tests/unit/test_evidence_compiler.py tests/unit/test_structure_mainline_spine.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_structure_mechanism_graph.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
37 passed
```

### C7 Integrated Core Calculation Gate

Status: completed 2026-06-06.

Target: M1-M8 integrated 100% current-scope seal.

Scope:

- Run all core module tiers together.
- Verify M1-M8 data flow from BirthInput to practical reading and API projection.
- Confirm no chart fact mutation from training, feedback, hidden factors, LLM, or policy pointers.
- Confirm customer-facing output is calculation-first and concise.

Validation:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q tests/test_v30_scaffold.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
```

Completed:

- Proved the core integrated gate across compile, all synthetic tiers, 518K sample, and targeted core pytest.
- Confirmed M1-M8 data flow remains intact from deterministic BirthInput/chart facts through M3 evidence spine, M4/M5 decisions, M6 practical reading, M7 validation, and M8 projection.
- Confirmed training, feedback, hidden factors, LLM, and policy pointers remain calibration/support layers and do not mutate chart facts.
- Updated the release-candidate scaffold expectation to the current 12 completed post-seal tasks; this was a test baseline alignment, not a runtime boundary change.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260606084440379258: eligible mode=sample cases=8 shards=0
artifact record: v30.518k.artifact.v30.518k.sample.20260606084440379258 (json_fallback)
pytest -q tests/test_v30_scaffold.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
38 passed
```

Full pytest was not run for this step; C7 used the documented integrated core gate set to avoid repeated full-suite cost.

### C8 Core Completion Documentation And Freeze

Status: completed 2026-06-06.

Target: docs and status aligned to core-complete state.

Scope:

- Update this document first.
- Sync `docs/V30_CORE_BAZI_EIGHT_MODULE_PLAN.md`.
- Sync `docs/V30_MODULE_REVIEW.md`.
- Sync `docs/V30_MAINLINE_COMPLETION_PLAN.md`.
- Sync `docs/V30_MASTER_MAINLINE_PLAN.md`.
- Sync synthetic/training validation docs affected by changed gates.
- Mark external release/full pytest/pointer-promotion as separate from core module completion.

Completed:

- Froze M1-M8 as 100% complete for the current core Bazi calculation scope.
- Synchronized core-complete status across the core module plan, eight-module plan, module review, mainline completion plan, master mainline plan, test architecture, synthetic validation, training architecture, and 518K validation plan.
- Carried forward C7 validation evidence as the current integrated core gate baseline.
- Reconfirmed the operating rule that training, synthetic validation, real-case replay, 518K sample/shard checks, hidden factors, LLM, and question loops are support/calibration tracks only.
- Kept external release, full pytest, policy pointer promotion, auth, dashboard, and UI expansion outside the core-completion track.

C8 freeze baseline:

```text
Core module state: M1-M8 100% current-scope complete
Latest integrated synthetic gate: v30.synthetic.all passed (95/95)
Latest integrated 518K sample: v30.518k.sample.20260606084440379258, cases=8, json_fallback
Latest targeted core pytest: 38 passed
Full pytest: not run for C8; reserved for explicit release/full-freeze decision
```

## Stop Rules

- Do not reopen the frozen M1-M8 core scope unless a concrete targeted validation failure points to it.
- Do not start new UI, LLM, auth, admin, release, or observability work under the core-completion label.
- Do not convert user feedback, hidden factors, training signals, or LLM output into chart facts.
- Do not run full pytest after every subtask; run targeted tests and module synthetic tiers.
- Full pytest is reserved for explicit external release work or an explicitly requested full-freeze decision.

## Immediate Next Step

No further C-task remains in this core-completion track:

```text
M1-M8 core module completion is frozen for the current scope.
```

The next mainline must be chosen explicitly as either targeted calibration, external release validation, policy pointer promotion review, or a newly scoped product/module track.

## Frozen-Core Follow-Up Track

### F1 Frozen Core Calibration Baseline

Status: completed 2026-06-06.

Target: establish the first post-freeze calibration baseline without reopening M1-M8.

Scope:

- Add a read-only frozen-core calibration review.
- Run targeted calibration tiers that cover M1/M2, M3, M4, M5/M6/M7 through real-case calibration, and interaction-loop calibration.
- Extract training signals from the combined calibration result.
- Confirm the next step is targeted calibration candidate review, not core-module reopening, UI work, or release/pointer promotion.

Implementation:

- Added `v30.frozen_core_calibration_review.v1`.
- Added `scripts/run_frozen_core_calibration_review.py`.
- Added `GET /api/v30/admin/calibration/frozen-core-review`.
- Added unit and scaffold coverage for the review builder and read-only endpoint.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_frozen_core_calibration_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_frozen_core_calibration_review_endpoint_is_read_only
4 passed
python3 scripts/run_frozen_core_calibration_review.py --tier ten_god_energy_calibration
calibration_baseline_blocked, tiers=1, signals=27, blocker=required_training_signals_missing
python3 scripts/run_frozen_core_calibration_review.py
ready_for_targeted_calibration_iteration, tiers=6, signals=31
```

Next:

```text
F2 Targeted Calibration Candidate Review
```

F2 may review candidate weights for model signal, rule weights, question strategy, and expression only. It must still keep deterministic chart facts, final pillars, luck/flow facts, and frozen M1-M8 completion sealed.

### F2 Targeted Calibration Candidate Review

Status: completed 2026-06-06.

Target: convert F1 training evidence into reviewable calibration candidates without applying them.

Scope:

- Generate review-only candidates for model-signal weights, rule weights, question strategy, and expression policy.
- Confirm no candidate payload contains deterministic chart facts, final pillars, luck/flow facts, or base fact explanations.
- Keep policy pointer promotion and auto-apply disabled.
- Select the next task as validation gate review, not pointer promotion.

Implementation:

- Added `v30.targeted_calibration_candidate_review.v1`.
- Added `scripts/run_targeted_calibration_candidate_review.py`.
- Added `GET /api/v30/admin/calibration/targeted-candidate-review`.
- Added unit and scaffold coverage for candidate-review readiness and read-only endpoint behavior.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_targeted_calibration_candidate_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_candidate_review_endpoint_is_read_only
4 passed
python3 scripts/run_targeted_calibration_candidate_review.py --family structure_policy
targeted_calibration_review_blocked, candidates=1, blockers=targeted_candidate_count_low,targeted_candidate_track_missing
python3 scripts/run_targeted_calibration_candidate_review.py
ready_for_validation_gate_review, candidates=4
```

Next:

```text
F3 Targeted Calibration Validation Gate
```

F3 must validate reviewed candidates with synthetic all and 518K sample before any later pointer-review discussion. F3 still must not promote policy pointers.

### F3 Targeted Calibration Validation Gate

Status: completed 2026-06-06.

Target: validate F2 candidates with synthetic all and 518K sample evidence without promoting pointers.

Scope:

- Rebuild F2 candidates and apply them as runtime policy overrides only for validation.
- Run synthetic all with candidate overrides.
- Run 518K sample with candidate overrides.
- Keep deterministic chart facts, frozen M1-M8 completion, auto-apply, and policy pointer promotion sealed.

Implementation:

- Added `v30.targeted_calibration_validation_gate.v1`.
- Added `scripts/run_targeted_calibration_validation_gate.py`.
- Added `GET /api/v30/admin/calibration/targeted-validation-gate`.
- Added unit and scaffold coverage for validation-gate readiness and read-only endpoint behavior.

Validation 2026-06-06:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_targeted_calibration_validation_gate.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_validation_gate_endpoint_is_read_only
4 passed
python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 1
targeted_validation_gate_blocked, synthetic=95/95, 518k=1, blocker=518k_sample_case_count_low
python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 8
ready_for_policy_pointer_review, synthetic=95/95, 518k=8
```

Next:

```text
F4 Targeted Calibration Pointer Review
```

F4 may inspect F2/F3 evidence before any pointer decision. It still must keep automatic promotion disabled unless explicitly requested.

### F4 Targeted Calibration Pointer Review

Status: completed 2026-06-07.

Target: inspect F2/F3 evidence and pointer diffs without writing active pointers.

Scope:

- Re-run the F3 validation gate as evidence input.
- Compare candidate families against currently active runtime pointers.
- Confirm whether an explicit operator pointer decision is ready.
- Keep pointer promotion, auto-apply, chart-fact mutation, and M1-M8 reopening disabled.

Implementation:

- Added `v30.targeted_calibration_pointer_review.v1`.
- Added `scripts/run_targeted_calibration_pointer_review.py`.
- Added `GET /api/v30/admin/calibration/targeted-pointer-review`.
- Added unit and scaffold coverage for pointer-review readiness and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_targeted_calibration_pointer_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_pointer_review_endpoint_is_read_only
4 passed
python3 scripts/run_targeted_calibration_pointer_review.py --sample-limit 1
pointer_review_blocked, diffs=4, blockers=f3_validation_gate_not_ready,518k_sample_evidence_low
python3 scripts/run_targeted_calibration_pointer_review.py --sample-limit 8
ready_for_explicit_operator_pointer_decision, diffs=4
```

Next:

```text
F5 Explicit Operator Pointer Decision
```

F5 is the first step that may decide whether to promote targeted-calibration pointers. It must remain explicit and operator-controlled; no background or automatic pointer write is allowed.

### F5 Explicit Operator Pointer Decision

Status: completed 2026-06-07.

Target: record the explicit operator decision for F4-ready pointer diffs.

Scope:

- Run F4 pointer review as evidence input.
- Record the operator decision.
- Because no explicit promotion approval was requested, record `operator_decision=defer`.
- Prove active pointers are unchanged.
- Keep pointer promotion, auto-apply, chart-fact mutation, and M1-M8 reopening disabled.

Implementation:

- Added `v30.targeted_calibration_pointer_decision.v1`.
- Added `scripts/run_targeted_calibration_pointer_decision.py`.
- Added `GET /api/v30/admin/calibration/targeted-pointer-decision`.
- Added unit and scaffold coverage for defer decision, blocked promotion request, unchanged pointers, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_targeted_calibration_pointer_decision.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_pointer_decision_endpoint_is_read_only
4 passed
python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision request_promotion
promotion_request_blocked_pending_explicit_write_command, pointer_write=False, blocker=promotion_requires_separate_explicit_pointer_write_command
python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision defer
pointer_promotion_deferred, pointer_write=False
```

Completed follow-up:

```text
F6 Targeted Calibration Closeout And Monitoring Baseline
```

F6 recorded the no-promotion outcome, kept F2/F3/F4/F5 evidence available, and defined the lightweight monitoring checks for future targeted-calibration regressions.

### F6 Targeted Calibration Closeout And Monitoring Baseline

Status: completed 2026-06-07.

Target: close the targeted-calibration F track with no pointer promotion and define the lightweight monitoring baseline for future targeted-calibration regressions.

Scope:

- Run the F5 explicit operator pointer decision as evidence input.
- Record that the operator decision remains `defer`.
- Prove no active pointer was written or changed.
- Preserve F1-F5 evidence lineage for later explicit review.
- Define monitoring checks that can be run without mutating policy pointers or deterministic chart facts.

Implementation:

- Added `v30.targeted_calibration_closeout.v1`.
- Added `scripts/run_targeted_calibration_closeout.py`.
- Added `GET /api/v30/admin/calibration/targeted-closeout`.
- Added unit and scaffold coverage for closeout readiness, pointer-write blocking, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_targeted_calibration_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_targeted_calibration_closeout_endpoint_is_read_only
4 passed
python3 scripts/run_targeted_calibration_closeout.py --sample-limit 1
targeted_calibration_closeout_blocked, checks=4, pointer_write=False, blockers=f5_pointer_decision_not_recorded,pointer_promotion_not_deferred
python3 scripts/run_targeted_calibration_closeout.py --sample-limit 8
targeted_calibration_closed_with_no_promotion, checks=4, pointer_write=False
```

Completed follow-up:

```text
M0 Mainline Selection After Targeted Calibration Closeout
```

F1-F6 are closed for the current targeted-calibration cycle. M0 chose the next mainline explicitly; deterministic chart facts, active policy pointers, and frozen M1-M8 completion remain sealed.

### M0 Mainline Selection After Targeted Calibration Closeout

Status: completed 2026-06-07.

Target: choose the next evidence-backed mainline after F6 without reopening core modules or mixing release, pointer promotion, full pytest, and UI expansion into routine core work.

Scope:

- Read F6 closeout evidence.
- Confirm R12 internal release-candidate finalization remains the release-boundary input.
- Select the next mainline explicitly.
- Keep M1-M8 frozen, policy pointers unchanged, and full pytest/full 518K out of default iteration.

Implementation:

- Added `v30.mainline_selection.v1`.
- Added `scripts/run_mainline_selection.py`.
- Added `GET /api/v30/admin/mainline/selection`.
- Added unit and scaffold coverage for R13 selection, blocked M0 behavior, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_mainline_selection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_mainline_selection_endpoint_is_read_only
5 passed
python3 scripts/run_mainline_selection.py --sample-limit 8
v30.mainline_selection.v1: r13_external_release_dry_run_selected
next: R13 External Release Dry Run And Full Pytest Decision
full_pytest_run_now: False
pointer_promotion_allowed: False
```

Next:

```text
R13 External Release Dry Run And Full Pytest Decision
```

R13 is a release-boundary decision. It may run or explicitly defer full pytest, and it must not promote policy pointers or reopen M1-M8 without an explicit operator decision and concrete validation evidence.

### R13 External Release Dry Run And Full Pytest Decision

Status: completed 2026-06-07.

Target: record the external-release dry run boundary without running full pytest by default and without promoting policy pointers.

Implementation:

- Added `v30.external_release_dry_run.v1`.
- Added `scripts/run_external_release_dry_run.py`.
- Added `GET /api/v30/admin/release/external-dry-run`.
- Added unit and scaffold coverage for default full-pytest defer, passed/failed full-pytest records, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_dry_run.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_dry_run_endpoint_defers_full_pytest_by_default
6 passed
python3 scripts/run_external_release_dry_run.py --sample-limit 8
v30.external_release_dry_run.v1: external_release_dry_run_deferred_full_pytest
external_release_ready: False
full_pytest_deferred: True
pointer_promotion_allowed: False
```

Next:

```text
R14 External Release Full Pytest Execution Decision
```

R14 must either explicitly run and record full pytest or keep external release blocked with a recorded defer decision. Pointer promotion remains a separate manual operator gate.

### R14 External Release Full Pytest Execution Decision

Status: completed 2026-06-07.

Target: record the full pytest execution decision explicitly without running full pytest by default.

Implementation:

- Added `v30.external_release_full_pytest_decision.v1`.
- Added `scripts/run_external_release_full_pytest_decision.py`.
- Added `GET /api/v30/admin/release/full-pytest-decision`.
- Added unit and scaffold coverage for defer/pass/fail decision records and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_full_pytest_decision.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_full_pytest_decision_endpoint_defers_by_default
6 passed
python3 scripts/run_external_release_full_pytest_decision.py --sample-limit 8
v30.external_release_full_pytest_decision.v1: external_release_full_pytest_deferred
external_release_ready: False
full_pytest_deferred: True
pointer_promotion_allowed: False
```

Next:

```text
R15 External Release Blocked Pending Full Pytest
```

R15 must keep the external-release boundary blocked while full pytest remains deferred. No pointer promotion, chart-fact mutation, or M1-M8 reopening is allowed.

### R15 External Release Blocked Pending Full Pytest

Status: completed 2026-06-07.

Target: record the blocked external-release status while full pytest remains deferred.

Implementation:

- Added `v30.external_release_blocked_status.v1`.
- Added `scripts/run_external_release_blocked_status.py`.
- Added `GET /api/v30/admin/release/blocked-status`.
- Added unit and scaffold coverage for release blockers, invalid ready-state blocking, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_blocked_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_blocked_status_endpoint_is_read_only
5 passed
python3 scripts/run_external_release_blocked_status.py --sample-limit 8
v30.external_release_blocked_status.v1: external_release_blocked_pending_full_pytest
external_release_ready: False
external_release_blocked: True
pointer_promotion_allowed: False
```

Next:

```text
R16 Post-Release-Boundary Pause Or Full Pytest Authorization
```

R16 should either pause release-boundary work and return to targeted module/calibration work, or explicitly authorize full pytest. It still must not approve external release or promote policy pointers.

### R16 Post-Release-Boundary Pause Or Full Pytest Authorization

Status: completed 2026-06-07.

Target: pause release-boundary work by default and make full pytest authorization explicit.

Implementation:

- Added `v30.post_release_boundary_authorization.v1`.
- Added `scripts/run_post_release_boundary_authorization.py`.
- Added `GET /api/v30/admin/release/post-boundary-authorization`.
- Added unit and scaffold coverage for pause, full-pytest authorization without execution, invalid release-ready blocking, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_post_release_boundary_authorization.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_post_release_boundary_authorization_endpoint_pauses_by_default
6 passed
python3 scripts/run_post_release_boundary_authorization.py --sample-limit 8
v30.post_release_boundary_authorization.v1: release_boundary_paused_pending_full_pytest_authorization
release_boundary_paused: True
full_pytest_authorized: False
full_pytest_run_triggered: False
pointer_promotion_allowed: False
```

Next:

```text
M0 Mainline Selection After Release Boundary Pause
```

Release-boundary work is paused. The next mainline should be selected explicitly, and external release remains blocked until full pytest is separately authorized and passed.

### M0 Mainline Selection After Release Boundary Pause

Status: completed 2026-06-07.

Target: select a non-release next mainline after R16 paused release-boundary work.

Implementation:

- Added `v30.mainline_selection_after_release_pause.v1`.
- Added `scripts/run_mainline_selection_after_release_pause.py`.
- Added `GET /api/v30/admin/mainline/selection-after-release-pause`.
- Selected `P0 Core Module Monitoring And Calibration Loop`.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_mainline_selection_after_release_pause.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_mainline_selection_after_release_pause_endpoint_is_read_only
5 passed
python3 scripts/run_mainline_selection_after_release_pause.py --sample-limit 8
v30.mainline_selection_after_release_pause.v1: core_monitoring_and_calibration_loop_selected
next: P0 Core Module Monitoring And Calibration Loop
```

Next:

```text
P0 Core Module Monitoring And Calibration Loop
```

P0 should run lightweight monitoring against frozen M1-M8 and route only concrete regressions to focused module fixes. External release, full pytest, full 518K, and pointer promotion remain out of default iteration.

### P0 Core Module Monitoring And Calibration Loop

Status: completed 2026-06-07.

Target: establish the read-only lightweight monitoring loop for frozen M1-M8.

Implementation:

- Added `v30.core_monitoring_loop.v1`.
- Added `scripts/run_core_monitoring_loop.py`.
- Added `GET /api/v30/admin/core/monitoring-loop`.
- Added unit and scaffold coverage for ready state, missing-monitoring-check blocker, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_loop.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_loop_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_loop.py --sample-limit 8
v30.core_monitoring_loop.v1: core_monitoring_loop_ready
monitoring_checks: 4/4
regression_detected: False
core_module_reopen_recommended: False
```

Next:

```text
P1 Execute Lightweight Core Monitoring Checks
```

P1 should execute the four F6 monitoring checks and record pass/blocker status. It still must not run full pytest or promote pointers by default.

### P1 Execute Lightweight Core Monitoring Checks

Status: completed 2026-06-08.

Target: execute the four F6 lightweight monitoring checks and record pass/blocker status.

Implementation:

- Added `v30.lightweight_core_monitoring_checks.v1`.
- Added `scripts/run_lightweight_core_monitoring_checks.py`.
- Added `GET /api/v30/admin/core/lightweight-monitoring-checks`.
- Added unit and scaffold coverage for pass state, failed-check blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_lightweight_core_monitoring_checks.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_lightweight_core_monitoring_checks_endpoint_is_read_only
5 passed
python3 scripts/run_lightweight_core_monitoring_checks.py --sample-limit 8
v30.lightweight_core_monitoring_checks.v1: lightweight_core_monitoring_checks_passed
checks: 4/4
regression_detected: False
```

Next:

```text
No default next core-monitoring task
```

S0 means no further core-monitoring task should run by default. Future calibration evidence enters P4/P5; release/full-freeze requests remain explicit.

### S0 Steady State Await New Calibration Evidence

Status: active state recorded 2026-06-09.

Target: record the read-only steady-state status after P9 and prevent default continuation into new core-monitoring tasks.

Implementation:

- Added `v30.core_monitoring_s0_status.v1`.
- Added `scripts/run_core_monitoring_s0_status.py`.
- Added `GET /api/v30/admin/core/monitoring-s0-status`.
- Added unit and scaffold coverage for ready S0 status, not-waiting blocker, pointer-pressure blocker, and read-only endpoint behavior.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_s0_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_s0_status_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_s0_status.py --sample-limit 8
v30.core_monitoring_s0_status.v1: core_monitoring_s0_status_ready
status_checks: 4/4
waiting_for_new_evidence: True
new_core_monitoring_task_allowed_by_default: False
```

Next:

```text
B1 Real Business Bazi Reading Acceptance
```

S0 remains the monitoring state; routine work should not continue into another monitoring task unless new calibration evidence appears.

### B1 Real Business Bazi Reading Acceptance

Status: completed 2026-06-09.

Target: prove the actual business reading path can produce a customer-visible Bazi calculation before question/UI expansion.

Implementation:

- Added `v30.real_business_bazi_reading_acceptance.v1`.
- Added `scripts/run_real_business_bazi_reading_acceptance.py`.
- Added `GET /api/v30/admin/business/real-bazi-acceptance`.
- B1 aggregates ready rows from `real_case_calibration_pack` and checks M1/M2, M4, M5, M6, M8, customer leak scans, and non-mutating boundaries.
- B1 keeps pending/blocked chart cases in the source synthetic pack, but the business acceptance sample prioritizes ready charts because the target is “can complete a real Bazi reading.”

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_real_business_bazi_acceptance_endpoint_is_read_only
4 passed
python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted
```

Full pytest / full 518K: not run for B1; reserved for explicit release/full-freeze decisions.

Next:

```text
B2 Business Reading Case Expansion And Regression Pack
```

### B2 Business Reading Case Expansion And Regression Pack

Status: completed 2026-06-09.

Target: expand B1 from basic acceptance into a reusable business reading regression pack.

Implementation:

- Added `v30.real_business_bazi_reading_regression_pack.v1`.
- Added `scripts/run_real_business_bazi_reading_regression_pack.py`.
- Added `GET /api/v30/admin/business/reading-regression-pack`.
- Added unit and scaffold coverage for ready regression, incomplete domain-card/practical-contract blockers, and read-only endpoint behavior.
- Updated M8 projection so `focus_domains` remains a concise three-domain priority list while `domain_cards` and `core_bazi_reading.practical_domains` expose five concise business domains.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_reading_regression_pack_endpoint_is_read_only
12 passed
python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready
python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
```

Full pytest / full 518K: not run for B2; reserved for explicit release/full-freeze decisions.

Next:

```text
B3 Business Reading Answer Refresh Regression
```

### B3 Business Reading Answer Refresh Regression

Status: completed 2026-06-09.

Target: verify structured answer submission refreshes the answer panel and question strategy without mutating the accepted Bazi reading surface.

Implementation:

- Added `v30.real_business_answer_refresh_regression.v1`.
- Added `scripts/run_real_business_answer_refresh_regression.py`.
- Added `GET /api/v30/admin/business/answer-refresh-regression`.
- Added cases for direct career, structured practical-domain choice, wealth, relationship, and hidden-factor-to-career feedback.
- B3 requires B2 readiness, then validates answer panel, interaction state, visible next question, chart/fact stability, five domain cards, projection leak scan, and answer boundary.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_answer_refresh_regression_endpoint_is_read_only
9 passed
python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready
python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready
python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)
```

Full pytest / full 518K: not run for B3; reserved for explicit release/full-freeze decisions.

Next:

```text
B4 Business Reading Boundary And Blocked Input Regression
```

### B4 Business Reading Boundary And Blocked Input Regression

Status: completed 2026-06-09.

Target: verify pending and blocked BirthInput states explain missing chart facts without fabricating a reading.

Implementation:

- Added `v30.real_business_boundary_blocked_input_regression.v1`.
- Added `scripts/run_real_business_boundary_blocked_input_regression.py`.
- Added `GET /api/v30/admin/business/boundary-blocked-input-regression`.
- Added unit and scaffold coverage for ready boundary regression, fake-pillar blocker, premature runtime-readiness blocker, and read-only endpoint behavior.
- B4 uses the 3 pending plus 2 blocked rows in `real_case_calibration_pack`.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_boundary_blocked_input_regression.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_boundary_blocked_input_regression_endpoint_is_read_only
7 passed
python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready
python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

Full pytest / full 518K: not run for B4; reserved for explicit release/full-freeze decisions.

Next:

```text
B5 Business Reading API Contract Freeze
```

### B5 Business Reading API Contract Freeze

Status: completed 2026-06-09.

Target: freeze B1-B4 as the minimum business reading acceptance contract.

Implementation:

- Added `v30.real_business_api_contract_freeze.v1`.
- Added `scripts/run_real_business_api_contract_freeze.py`.
- Added `GET /api/v30/admin/business/api-contract-freeze`.
- Added unit and scaffold coverage for all-gates-ready contract freeze, failed-gate blocker, and read-only endpoint behavior.
- Frozen contract records required endpoints, customer surface keys, minimum case counts, additive API policy, and forbidden behaviors.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_api_contract_freeze.py tests/unit/test_real_business_boundary_blocked_input_regression.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_api_contract_freeze_endpoint_is_read_only
6 passed
python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen
python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
```

Full pytest / full 518K: not run for B5; reserved for explicit release/full-freeze decisions.

Next:

```text
B6 Business Reading Acceptance Closeout
```

### B6 Business Reading Acceptance Closeout

Status: completed 2026-06-09.

Target: record B1-B5 as the default business Bazi reading acceptance gate and pause B-track by default.

Implementation:

- Added `v30.real_business_acceptance_closeout.v1`.
- Added `scripts/run_real_business_acceptance_closeout.py`.
- Added `GET /api/v30/admin/business/acceptance-closeout`.
- Added unit and scaffold coverage for ready closeout, additive-contract/heavy-validation blockers, and read-only endpoint behavior.
- B6 records S1 Business Acceptance Steady State as the next state.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_acceptance_closeout.py tests/unit/test_real_business_api_contract_freeze.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_acceptance_closeout_endpoint_is_read_only
6 passed
python3 scripts/run_real_business_acceptance_closeout.py
v30.real_business_acceptance_closeout.v1: passed (4/4) b6_business_acceptance_closed
python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen
```

Full pytest / full 518K: not run for B6; reserved for explicit release/full-freeze decisions.

Next:

```text
S1-WAIT Await New Business Evidence Or Explicit Major Validation
```

### S1 Business Acceptance Steady State

Status: completed 2026-06-10.

Target: make B6 closeout operational as a read-only steady state: use B1-B5 as the routine business Bazi reading gate and do not start another B-track task by default.

Implementation:

- Added `v30.real_business_steady_state.v1`.
- Added `scripts/run_real_business_steady_state.py`.
- Added `GET /api/v30/admin/business/steady-state`.
- Added unit and scaffold coverage for ready steady state, heavy-validation/B-track reopen blockers, release/pointer/chart-fact mutation blockers, and read-only endpoint behavior.
- S1 records explicit reopen conditions for new real-business failure, API contract change request, boundary/blocked input failure, or explicit major validation/release-boundary request.

Validation 2026-06-10:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_steady_state.py tests/unit/test_real_business_acceptance_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_steady_state_endpoint_is_read_only
7 passed in 1.75s
python3 scripts/run_real_business_steady_state.py
v30.real_business_steady_state.v1: passed (5/5) s1_business_acceptance_steady_state_ready
```

Full pytest / full 518K: not run for S1; reserved for explicit release/full-freeze decisions.

Next:

```text
S1-WAIT Await New Business Evidence Or Explicit Major Validation
```

### P9 Core Monitoring Steady State

Status: completed 2026-06-09.

Target: enter steady state after P8 documentation sync and wait for new calibration evidence.

Implementation:

- Added `v30.core_monitoring_steady_state.v1`.
- Added `scripts/run_core_monitoring_steady_state.py`.
- Added `GET /api/v30/admin/core/monitoring-steady-state`.
- Added unit and scaffold coverage for ready steady state, missing-doc blocker, pointer-pressure blocker, and read-only endpoint behavior.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_steady_state.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_steady_state_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_steady_state.py --sample-limit 8
v30.core_monitoring_steady_state.v1: core_monitoring_steady_state_ready
steady_state_checks: 4/4
waiting_for_new_evidence: True
future_monitoring_ready: True
```

Next:

```text
S0 Steady State Await New Calibration Evidence
```

### P8 Core Monitoring Cadence Documentation Sync

Status: completed 2026-06-08.

Target: sync the P7 cadence baseline across controlling docs and keep future evidence routed through P4/P5.

Implementation:

- Added `v30.core_monitoring_cadence_documentation_sync.v1`.
- Added `scripts/run_core_monitoring_cadence_documentation_sync.py`.
- Added `GET /api/v30/admin/core/monitoring-cadence-documentation-sync`.
- Added unit and scaffold coverage for ready sync, missing-doc blocker, heavy-validation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_cadence_documentation_sync.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_documentation_sync_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_cadence_documentation_sync.py --sample-limit 8
v30.core_monitoring_cadence_documentation_sync.v1: core_monitoring_cadence_documentation_sync_ready
docs: 10/10
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P9 Core Monitoring Steady State
```

P9 should keep the cadence in steady state and route only future evidence through P4/P5.

### P7 Core Monitoring Cadence Baseline

Status: completed 2026-06-08.

Target: document the ongoing lightweight monitoring cadence after P6 closeout.

Implementation:

- Added `v30.core_monitoring_cadence_baseline.v1`.
- Added `scripts/run_core_monitoring_cadence_baseline.py`.
- Added `GET /api/v30/admin/core/monitoring-cadence-baseline`.
- Added unit and scaffold coverage for ready cadence, unclosed-cycle blocker, heavy-validation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_cadence_baseline.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_baseline_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_cadence_baseline.py --sample-limit 8
v30.core_monitoring_cadence_baseline.v1: core_monitoring_cadence_baseline_ready
default_cadence: on_new_calibration_evidence_only
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P8 Core Monitoring Cadence Documentation Sync
```

P8 should sync the P7 cadence baseline across the controlling docs.

### P6 Core Calibration Watch Closeout

Status: completed 2026-06-08.

Target: close the current empty core calibration watch cycle and keep future monitoring ready.

Implementation:

- Added `v30.core_calibration_watch_closeout.v1`.
- Added `scripts/run_core_calibration_watch_closeout.py`.
- Added `GET /api/v30/admin/core/calibration-watch-closeout`.
- Added unit and scaffold coverage for ready closeout, focused-candidate blocker, upstream queue blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_watch_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_watch_closeout_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_watch_closeout.py --sample-limit 8
v30.core_calibration_watch_closeout.v1: core_calibration_watch_closeout_ready
closeout_checks: 4/4
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P7 Core Monitoring Cadence Baseline
```

P7 should document the ongoing lightweight cadence after closeout without reopening all frozen core modules.

### P5 Core Calibration Queue Review

Status: completed 2026-06-08.

Target: review queued calibration evidence by module target and decide whether focused module fixes are needed.

Implementation:

- Added `v30.core_calibration_queue_review.v1`.
- Added `scripts/run_core_calibration_queue_review.py`.
- Added `GET /api/v30/admin/core/calibration-queue-review`.
- Added unit and scaffold coverage for empty queue readiness, focused candidates, upstream queue blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_queue_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_queue_review_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_queue_review.py --sample-limit 8
v30.core_calibration_queue_review.v1: core_calibration_queue_review_ready
reviewed_modules: 0
focused_fix_candidates: 0
focused_module_fix_required: False
```

Next:

```text
P6 Core Calibration Watch Closeout
```

P6 should close the current empty queue review cycle and keep future monitoring ready without reopening all frozen core modules.

### P4 Focused Core Calibration Evidence Queue

Status: completed 2026-06-08.

Target: batch future calibration evidence by M1-M8 module target without changing core facts or policy pointers.

Implementation:

- Added `v30.focused_core_calibration_evidence_queue.v1`.
- Added `scripts/run_focused_core_calibration_evidence_queue.py`.
- Added `GET /api/v30/admin/core/focused-calibration-evidence-queue`.
- Added unit and scaffold coverage for empty queue readiness, module batching, mutation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_focused_core_calibration_evidence_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_focused_core_calibration_evidence_queue_endpoint_is_read_only
5 passed
python3 scripts/run_focused_core_calibration_evidence_queue.py --sample-limit 8
v30.focused_core_calibration_evidence_queue.v1: focused_core_calibration_evidence_queue_ready
queued_evidence: 0
queue_items: 0
focused_module_fix_required: False
```

Next:

```text
P5 Core Calibration Queue Review
```

P5 should review queued evidence by module target and decide whether focused fixes are needed without reopening all frozen core modules.

### P3 Core Calibration Drift Watch

Status: completed 2026-06-08.

Target: establish the lightweight drift-watch cadence and route future calibration drift to focused module fixes.

Implementation:

- Added `v30.core_calibration_drift_watch.v1`.
- Added `scripts/run_core_calibration_drift_watch.py`.
- Added `GET /api/v30/admin/core/calibration-drift-watch`.
- Added unit and scaffold coverage for ready state, drift routing, pointer-write pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_drift_watch.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_drift_watch_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_drift_watch.py --sample-limit 8
v30.core_calibration_drift_watch.v1: core_calibration_drift_watch_ready
drift_detected: False
drift_routes: 0
focused_module_fix_required: False
```

Next:

```text
P4 Focused Core Calibration Evidence Queue
```

P4 should batch future calibration evidence by M1-M8 module target without reopening all frozen core modules.

### P2 Core Calibration Observation Summary

Status: completed 2026-06-08.

Target: summarize P1 monitoring evidence and choose whether to continue observation or open a focused module fix.

Implementation:

- Added `v30.core_calibration_observation_summary.v1`.
- Added `scripts/run_core_calibration_observation_summary.py`.
- Added `GET /api/v30/admin/core/calibration-observation-summary`.
- Added unit and scaffold coverage for ready state, failed-check blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_observation_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_observation_summary_endpoint_is_read_only
4 passed
python3 scripts/run_core_calibration_observation_summary.py --sample-limit 8
v30.core_calibration_observation_summary.v1: core_calibration_observation_summary_ready
observations: 4 stable, 0 needs_review
regression_detected: False
focused_module_fix_required: False
```

Next:

```text
P3 Core Calibration Drift Watch
```

P3 should define a lightweight cadence for future calibration drift evidence and route concrete drift to focused module fixes without reopening all M1-M8.
