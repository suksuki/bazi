# V30 Main Module Completion Review

Updated: 2026-06-13

## Purpose

This document records the current major-module completion state after IQ5/MCR2 and selects the next non-peripheral mainline task.

The rule is:

- Do not reopen M1-M8 deterministic Bazi calculation unless new failed evidence appears.
- Do not start UI polish as the mainline.
- Do not run full pytest, synthetic all, full 518K, live LLM, or pointer promotion by default.
- Use targeted validation for routine module work.

## MCR1 Result

`v30.main_module_completion_review.v1` is available through:

```text
python3 scripts/run_main_module_completion_review.py
GET /api/v30/admin/mainline/main-module-completion-review
```

Latest result:

```text
v30.main_module_completion_review.v1: passed (5/5) mcr1_main_module_review_ready
historical_next=MCR2 Customer Reading Surface And BaziContext Completion Reconciliation
current_status=SYN-CAL3 completed; UI-R1 inserted; next=UI-R1.1 Product Reading Acceptance Audit
```

## MCR2 Result

`v30.customer_surface_bazi_context_reconciliation.v1` is available through:

```text
python3 scripts/run_customer_surface_bazi_context_reconciliation.py
GET /api/v30/admin/mainline/customer-surface-bazi-context-reconciliation
```

Latest result:

```text
v30.customer_surface_bazi_context_reconciliation.v1: mcr2_customer_surface_bazi_context_reconciled (6/6)
historical_next=M3-G1
current_status=SYN-CAL3 completed; UI-R1 inserted; next=UI-R1.1 Product Reading Acceptance Audit
full_pytest=False synthetic_all=False full_518k=False
```

Current override after UI-R1.1:

```text
UI-R1.1 Product Reading Acceptance Audit: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True passed=4/9
next=UI-R1.2 Basic Assertion Projection

pytest -q tests/unit/test_ui_core_reading_product_acceptance.py
2 passed
```

Current override after UI-R1.2:

```text
UI-R1.2 Basic Assertion Projection: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True passed=5/9
failed=bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.3 Bazi Feature And Portrait Projection

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed
```

Current override after UI-R1.3:

```text
UI-R1.3 Bazi Feature And Portrait Projection: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True passed=6/9
failed=bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.4 Bazi Path Reading Projection

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed
```

Current override after UI-R1.4:

```text
UI-R1.4 Bazi Path Reading Projection: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True passed=7/9
failed=role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.8 Multi-Role Reading Surfaces

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed
```

Current override after UI-R1.8:

```text
UI-R1.8 Multi-Role Reading Surfaces: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True passed=8/9
failed=llm_context_pack_has_product_layers
next=UI-R1.7 LLM Context And Prompt Upgrade

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed
```

Current override after UI-R1.7:

```text
UI-R1.7 LLM Context And Prompt Upgrade: complete
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
product_ready=True audit_ready=True passed=9/9
next=UI-R1.10 Product-Level Synthetic Validation

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed
```

Current override after UI-R1.10:

```text
UI-R1.10 Product-Level Synthetic Validation: complete
python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_ui_core_reading_product_synthetic.py
9 passed
```

Interpretation:

- The sample's deterministic calculation is available: four pillars, day master, current luck, and flow year are present.
- UI-R1 product acceptance is now complete for the canonical sample.
- UI-R1 product output is now covered by a typical-case synthetic tier across assertions, features, portraits, paths, role differentiation, and LLM context layers.
- The next main-module task is product-level synthetic validation over typical Bazi cases, not full pytest or full 518K.

MCR2 verifies:

- guest/user receive a core-first `v30.customer_reading_surface.v1` with `v30.core_bazi_reading.v1`, domain cards, structure dynamics, time context, next question, and additive projection contract.
- guest/user diagnostics and internal policy/training/raw BaziContext payloads remain hidden.
- practitioner/admin diagnostics receive `v30.internal_bazi_context.v1`, model signal, ranked decisions, and role-gated diagnostics.
- BaziContext is consumed by runtime, question, practical reading, and LLM context contracts without becoming a chart-fact mutation path.
- default validation remains targeted; full pytest, synthetic all, full 518K, live LLM, and pointer promotion are explicit-only.

## Latest RBD-S1.4 Evidence

`v30.real_bazi_diagnosis.feature_engine.v1` and `v30.real_bazi_diagnosis.portrait_engine.v1` are available through the diagnosis package:

```text
from v30.diagnosis import extract_diagnosis_features, extract_diagnosis_portraits
```

Latest result:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
17 passed

runtime sample:
feature_count=33
portrait_count=65
feature domains={'hidden_factor': 1, 'overview': 8, 'structure': 17, 'timing': 3, 'useful_god': 4}
portrait domains={'career': 10, 'health': 5, 'hidden_factor': 1, 'overview': 7, 'relationship': 11, 'structure': 13, 'timing': 2, 'useful_god': 8, 'wealth': 8}
```

S1.4 verifies:

- Feature extraction projects `FeatureEvidence` into readable Bazi-specific diagnosis features.
- Portrait extraction combines KRP portrait dimensions, matched rules, and dynamic paths.
- Every feature has evidence ids; every portrait has evidence ids or path ids.
- Health, hidden-factor, chart-fact, useful-god, and domain-outcome boundaries remain explicit.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest RBD-S1.5 Evidence

`v30.real_bazi_diagnosis.claim_generator.v1` is available through the diagnosis package:

```text
from v30.diagnosis import generate_diagnosis_claims, summarize_diagnosis_claims
```

Latest result:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
21 passed

runtime sample:
claim_count=71
domains={'career': 7, 'health': 3, 'hidden_factor': 4, 'overview': 1, 'relationship': 7, 'structure': 28, 'timing': 3, 'useful_god': 10, 'wealth': 8}
levels={'domain': 7, 'fact': 1, 'feature': 20, 'path': 4, 'portrait': 37, 'question': 1, 'timing': 1}
```

S1.5 verifies:

- Claims are generated from matched rules, diagnosis features, diagnosis paths, and portraits.
- Wealth, career, relationship, health, timing, structure, useful-god, and hidden-factor claims are concrete but bounded.
- Every claim is traceable through evidence ids, rule ids, path ids, or portrait ids.
- Claims are not LLM-generated, cannot mutate chart facts, and cannot become fixed event predictions.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest RBD-S1.6 Evidence

`v30.real_bazi_diagnosis.graph.v1` and `v30.real_bazi_diagnosis.router.v1` are available through the diagnosis and brain packages:

```text
from v30.diagnosis import build_diagnosis_graph, summarize_diagnosis_graph
from v30.brain import route_real_bazi_diagnosis, summarize_diagnosis_route
```

Latest result:

```text
python3 -m compileall -q v30/diagnosis v30/brain
passed

pytest -q tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py tests/unit/test_central_brain.py
29 passed

runtime sample:
node_count=261
edge_count=1426
node_counts={'chart_fact': 1, 'claim': 71, 'feature': 65, 'matched_rule': 49, 'path': 10, 'portrait': 65}
edge_counts={'activates': 5, 'asks_followup': 23, 'blocks': 90, 'explains': 690, 'supports': 618}
wealth route selected_claim_count=5 selected_path_count=6 selected_portrait_count=6 followup_required=True
```

S1.6 verifies:

- Diagnosis graph connects evidence, features, matched rules, paths, portraits, and claims.
- Graph edges validate references and include support, explanation, activation, blocking, and follow-up edges.
- Diagnosis router selects claims by mode/domain/role without generating facts.
- Hidden-factor calibration routes to question strategy and training signals.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest RBD-S1.7 Evidence

Runtime and presentation now consume RBD:

```text
question_plan.policy_effect.real_bazi_diagnosis
practical_reading_context.domain_readings[].diagnosis_summary
reading_surface.diagnosis_overview
reading_surface.domain_cards[].diagnosis_summary
reading_surface.structure_dynamics.top_paths[].diagnosis_statement
```

Latest result:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_presentation_projection.py tests/unit/test_practical_reading_context.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py
19 passed

runtime sample:
claims=71 graph_nodes=261 graph_edges=1426
career=事业主线落在官印相生；此局更重视压力如何转成资质、规则、平台或可交付能力，不能只按职位升降下断。
wealth=财运主线不是单点求财，而是沿财官印制化展开；财星需要被输出、官杀责任或印星资源承接，适合看资源转化、方案输出、平台授权和分配结构。
```

S1.7 verifies:

- Runtime emits RBD payload and public projection.
- Practical reading consumes RBD claims additively without breaking M6 contracts.
- Customer presentation shows concrete Bazi diagnosis summaries while hiding raw traces.
- Admin diagnostics can inspect full RBD summaries.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest RBD-S1.8 Evidence

`v30.real_bazi_diagnosis.storage.v1` is available through:

```text
from v30.storage.diagnosis import write_real_bazi_diagnosis_to_postgres
```

Latest result:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_storage_adapters.py
14 passed

runtime sample:
claim_count=71
path_count=10
portrait_count=65
rule_match_count=49
backend=json_fallback
searchable=False
```

S1.8 verifies:

- RBD diagnosis runs, rule matches, paths, portraits, claims, and feedback have V30-only Postgres tables.
- Runtime RBD payload includes full matched rules and features for replay/storage.
- No-DB environments use JSON fallback.
- Storage records are replay/training/calibration support, not authoritative chart facts.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest RBD-S1.9 Evidence

`v30.synthetic.real_bazi_diagnosis` is available through:

```text
python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
```

Latest result:

```text
python3 -m compileall -q v30/validation
passed

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_synthetic_validation.py::test_synthetic_real_bazi_diagnosis_tier_passes
10 passed
```

S1.9 verifies:

- RBD has a dedicated synthetic tier and coverage-manifest contract.
- Synthetic cases cover ready luck/flow diagnosis, unknown-time boundary, hidden-factor feedback routing, and customer projection.
- RBD quality observation checks rule matches, paths, portraits, claims, graph counts, domain coverage, storage replay record, customer leak safety, and admin diagnostics.
- Claims remain traceable and are not LLM-generated, chart-fact-mutating, or fixed event predictions.
- Lightweight 518K sample readiness is recorded; full 518K remains explicit-only.

## Latest RBD-S1.10 Evidence

`v30.real_bazi_product_reading_acceptance.v1` is available through:

```text
python3 scripts/run_real_bazi_product_reading_acceptance.py
```

Latest result:

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

## Latest RBD-S1.11 Evidence

`v30.real_bazi_distribution_replay.v1` is available through:

```text
python3 scripts/run_real_bazi_distribution_replay.py
```

Latest result:

```text
python3 -m compileall -q v30/validation/real_bazi_distribution_replay.py scripts/run_real_bazi_distribution_replay.py
passed

pytest -q tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_real_bazi_product_reading_acceptance.py
4 passed

python3 scripts/run_real_bazi_distribution_replay.py
v30.real_bazi_distribution_replay.v1: passed (5/5) rbd_s111_distribution_replay_ready
real_case=8/8 sample_518k=8/8

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)
```

S1.11 verifies:

- RBD acceptance metrics replay over ready real-case calibration rows.
- Generated 518K sample-style replay reaches 8/8 without generic-language hits or customer internal leaks.
- Minimum sample admin payload counts remain above claim/path/portrait thresholds.
- Full pytest, synthetic all, and full 518K remain explicit-only.

## Latest RBD-S1.12 Evidence

`v30.real_bazi_training_calibration_queue.v1` is available through:

```text
python3 scripts/run_real_bazi_training_calibration_queue.py
```

Latest result:

```text
python3 -m compileall -q v30/validation/real_bazi_training_calibration_queue.py scripts/run_real_bazi_training_calibration_queue.py
passed

pytest -q tests/unit/test_real_bazi_training_calibration_queue.py tests/unit/test_real_bazi_distribution_replay.py
4 passed

python3 scripts/run_real_bazi_training_calibration_queue.py
v30.real_bazi_training_calibration_queue.v1: passed (5/5) rbd_s112_training_calibration_queue_ready
signals=4 queue_items=2 auto_apply=False
```

S1.12 verifies:

- Accepted S1.11 replay metrics become four read-only RBD training signal candidates.
- Evidence-backed calibration queue items are grouped by source/domain.
- Queue and signals cannot mutate chart facts, auto-apply training, or promote policy pointers.
- Full pytest, synthetic all, and full 518K remain explicit-only.

## Latest RBD-S1.13 Evidence

`v30.real_bazi_diagnosis_steady_state.v1` is available through:

```text
python3 scripts/run_real_bazi_diagnosis_steady_state.py
```

Latest result:

```text
python3 -m compileall -q v30/validation/real_bazi_diagnosis_steady_state.py scripts/run_real_bazi_diagnosis_steady_state.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_real_bazi_diagnosis_steady_state.py tests/unit/test_real_bazi_training_calibration_queue.py
4 passed

python3 scripts/run_real_bazi_diagnosis_steady_state.py
v30.real_bazi_diagnosis_steady_state.v1: passed (6/6) rbd_s113_steady_state_ready
signals=4 queue_items=2 next=RBD-S1-WAIT
```

S1.13 verifies:

- RBD current-scope spine is usable for customer reading, practitioner review, and admin diagnostics.
- Routine cadence is targeted: RBD steady-state script and `real_bazi_diagnosis` synthetic tier.
- Calibration queue items remain read-only until explicit evidence review.
- Full pytest, synthetic all, full 518K, live LLM, chart-fact mutation, auto-apply training, and pointer promotion remain explicit/non-default.

## Major Module Matrix

| Module | Completion | State | Evidence |
|---|---:|---|---|
| M1/M2 BirthInput and deterministic chart facts | 100% | steady | C5/C7 sealed. |
| M3 Knowledge, rule, portrait, feature, and structure spine | 100% | steady | C6/C7 sealed. |
| M4 Ten-god energy model and model-signal summary | 100% | steady | C2/C7 sealed. |
| M5 Strength, structure, and useful-god ranked decisions | 100% | steady | C2/C7 sealed. |
| M6 Practical Bazi reading output | 100% | steady | C1/C7 sealed. |
| M7 Real-case calibration pack and drift routing | 100% | steady | C3/C7 sealed. |
| M8 Customer reading projection and API contract | 100% | steady | C4/C7/B2 sealed. |
| IQ Intelligent question interaction | 98% | steady | IQ5 closed; IQ-S1 active. |
| LLM Bazi expression layer | 88% | bounded steady | BL8 closed; live provider smoke explicit-only. |
| BT Central brain, training, synthetic, and 518K support | 100% | steady | BT10 closed; 518K support 95%. |
| U Multi-user, terminal, session, and locale projection | 100% | steady | U5 closed. |
| Customer reading surface accounting | 100% | steady | MCR2 reconciled against runtime projection and customer leak contract. |
| BaziContext internalization accounting | 100% | steady | MCR2 reconciled against role-gated `v30.internal_bazi_context.v1` diagnostics. |

## Latest M3-G3 Evidence

`v30.m3_training_candidate_review.v1` is available through:

```text
python3 scripts/run_m3_training_candidate_review.py --sample-limit 8
```

Latest result:

```text
v30.m3_training_candidate_review.v1: passed (7/7) m3_g3_training_candidate_review_ready candidates=8
python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
pytest -q tests/unit/test_m3_training_candidate_review.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
8 passed
```

G3 verifies:

- Source coverage, rule priority, domain depth, counter-evidence trace, dynamic-path, question-strategy, training distribution, and 518K distribution candidates are generated as review evidence.
- Candidates require operator review and disallow auto-apply, pointer promotion, chart-fact mutation, and fixed Bazi verdicts.
- Full pytest, synthetic all, full 518K, live LLM, and pointer promotion remain explicit-only.

## Latest M3-G4 Evidence

`v30.m3_source_extraction_backlog.v1` is available through:

```text
python3 scripts/run_m3_source_extraction_backlog.py
```

Latest result:

```text
v30.m3_source_extraction_backlog.v1: passed (6/6) m3_g4_source_extraction_backlog_ready rows=6
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
pytest -q tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_storage_adapters.py
12 passed
```

G4 verifies:

- Every registered M3 source family has one review-ready backlog row.
- Rows include source family, target domains, queue state, priority, extraction targets, validation requirements, linked K/R/P units, linked rule specs, linked portrait assets, and review status.
- `v30_m3_source_backlog` is part of the V30 Postgres schema and optional write path.
- Backlog rows disallow V20 runtime import, chart-fact mutation, pointer promotion, and fixed Bazi verdicts.

## Latest M3-G5 Evidence

`v30.m3_source_backlog_review_surface.v1` is available through:

```text
python3 scripts/run_m3_source_backlog_review_surface.py
GET /api/v30/admin/m3/source-backlog
```

Latest result:

```text
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=6 backend=json_fallback_generated_backlog
python3 scripts/run_m3_source_backlog_review_surface.py --target-domain useful_god --limit 3
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=3 backend=json_fallback_generated_backlog
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
pytest -q tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_storage_adapters.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
13 passed
```

G5 verifies:

- Admin/training review can query source backlog rows by source family, priority, queue state, review status, target domain, and limit.
- Postgres-backed query uses `v30_m3_source_backlog`; JSON fallback generates current G4 backlog rows when DB rows are absent.
- The API route is available at `/api/v30/admin/m3/source-backlog`.
- Query surfaces remain read-only and disallow V20 runtime import, chart-fact mutation, pointer promotion, and fixed Bazi verdicts.

## Latest M3-G6 Evidence

`v30.m3_source_backlog_closeout.v1` is available through:

```text
python3 scripts/run_m3_source_backlog_closeout.py --sample-limit 8
GET /api/v30/admin/m3/source-backlog-closeout
```

Latest result:

```text
v30.m3_source_backlog_closeout.v1: passed (5/5) m3_g6_source_backlog_closeout_ready candidates=8 backlog_rows=6
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
pytest -q tests/unit/test_m3_source_backlog_closeout.py tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_training_candidate_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
12 passed
```

G6 verifies:

- G3 training candidate review is ready with training-pipeline and 518K sample evidence.
- G5 backlog review surface is ready with all source families visible.
- M3 core synthetic tier passes.
- G3/G5/G6 remain read-only: no V20 runtime import, no chart-fact mutation, no pointer promotion, no fixed Bazi verdict.
- M3 source backlog flow is closed and M3 can return to steady-state calibration.

## Latest M5-H1/H2/H3 Evidence

`v30.m5_evidence_consumption_hardening.v1` is available through:

```text
python3 scripts/run_m5_evidence_consumption_hardening.py --sample-limit 8
GET /api/v30/admin/m5/evidence-consumption-hardening
```

`v30.m5_calibration_replay_review.v1` is available through:

```text
python3 scripts/run_m5_calibration_replay_review.py --sample-limit 8
GET /api/v30/admin/m5/calibration-replay-review
```

`v30.m5_calibration_replay_closeout.v1` is available through:

```text
python3 scripts/run_m5_calibration_replay_closeout.py --sample-limit 8
GET /api/v30/admin/m5/calibration-replay-closeout
```

Latest result:

```text
v30.m5_evidence_consumption_hardening.v1: passed (7/7) m5_evidence_consumption_hardening_ready domains=3 scores=17
v30.m5_calibration_replay_review.v1: passed (6/6) m5_calibration_replay_review_ready cases=51 complete=51 close_candidates=51
v30.m5_calibration_replay_closeout.v1: passed (6/6) m5_calibration_replay_closed cases=51 complete=51 close_candidates=51 next=M6 Practical Reading Consumption Hardening
v30.synthetic.m5_ranked_decision_contract: passed (30/30)
v30.synthetic.strength_structure_useful_god: passed (1/1)
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_m5_calibration_replay_closeout.py tests/unit/test_m5_calibration_replay_review.py tests/unit/test_m5_evidence_consumption_hardening.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
15 passed
```

H1 verifies:

- M3-G6 closeout is ready before M5 hardening.
- M5 ranked domains are complete: strength, structure-pattern, useful-god.
- Scoring basis consumes M1/M2 root/vault facts, M4 model-signal interface, and M3 source/rule/dynamic-path support.
- Decisions have supporting evidence and fixed-verdict counter-evidence guards.
- M5 remains candidate-bound, raw-score-free, and read-only.

H2 verifies:

- M5-H1 is ready before calibration replay review.
- M5 contract, strength/structure/useful-god, and real-case calibration tiers pass.
- Ranked observations cover strength, structure-pattern, and useful-god with reviewable score distribution.
- Close-candidate cases are visible for later calibration but do not trigger threshold writes.
- `v30.training_signal.m5_weight_replay` is present and is limited to candidate-weight training, not chart facts.
- M5 remains read-only: no pointer promotion, no fixed verdict, no chart-fact mutation.

H3 verifies:

- M5-H2 replay review is ready and H1/H2 lineage is complete.
- M5 is closed as steady ranked-candidate support for M6, IQ, and training.
- Close-candidate monitoring is retained, but threshold and score-floor changes are deferred.
- No pointer, threshold, fixed-verdict, or chart-fact write occurred.

## Latest M6-H1 Evidence

`v30.m6_practical_reading_consumption_hardening.v1` is available through:

```text
python3 scripts/run_m6_practical_reading_consumption_hardening.py --sample-limit 8
GET /api/v30/admin/m6/practical-reading-consumption-hardening
```

Latest result:

```text
v30.m6_practical_reading_consumption_hardening.v1: passed (8/8) m6_practical_reading_consumption_hardening_ready domains=125 next=M6 Practical Reading Closeout
v30.synthetic.m6_practical_reading_contract: passed (30/30)
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_m6_practical_reading_consumption_hardening.py tests/unit/test_practical_reading_context.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
8 passed
```

H1 verifies:

- M5-H3 closeout is ready for M6 consumption.
- M6 contract and real-case calibration synthetic tiers pass.
- Every practical domain reading traces consumption of M1/M2, M3, M4, and M5.
- M6 domain readings expose quality contracts, evidence links, explanations, action steps, and calibration prompts.
- M6 hides raw scores, blocks fixed claims, and cannot mutate chart facts.
- Business reading acceptance and answer refresh preserve the M6 customer surface.
- `v30.training_signal.practical_reading_quality` remains runtime-context training, not chart-fact training.
- M6 hardening remains read-only across M5, business acceptance, and answer refresh.

## Latest M6-H2 Evidence

`v30.m6_practical_reading_closeout.v1` is available through:

```text
python3 scripts/run_m6_practical_reading_closeout.py --sample-limit 8
GET /api/v30/admin/m6/practical-reading-closeout
```

Latest result:

```text
v30.m6_practical_reading_closeout.v1: passed (7/7) m6_practical_reading_closed domains=125 next=M7 Real-Case Calibration Steady-State Review
v30.synthetic.m6_practical_reading_contract: passed (30/30)
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_m6_practical_reading_closeout.py tests/unit/test_m6_practical_reading_consumption_hardening.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
13 passed
```

H2 verifies:

- M6-H1 consumption hardening is ready for closeout.
- Career, wealth, relationship, health, and timing domains have steady coverage.
- Business reading and answer refresh preserve the M6 customer surface.
- M6 contract, real-case pack, and practical-reading training signal lineage are complete.
- Blocked claims are present and raw score/chart mutation leaks are absent.
- M6 can support IQ, LLM context, training, and release acceptance paths.
- No pointer, fixed-verdict, or chart-fact write occurred.

## Latest M7-S1 Evidence

`v30.m7_real_case_calibration_steady_state_review.v1` is available through:

```text
python3 scripts/run_m7_real_case_calibration_steady_state_review.py --sample-limit 8
GET /api/v30/admin/m7/real-case-calibration-steady-state-review
```

Latest result:

```text
v30.m7_real_case_calibration_steady_state_review.v1: passed (7/7) m7_real_case_calibration_steady_state_ready fixtures=30 next=M7 Real-Case Calibration Closeout
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_m7_real_case_calibration_steady_state_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
8 passed
```

S1 verifies:

- M6-H2 closeout is ready before M7 steady-state review.
- Real-case pack covers solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender paths.
- M4/M5/M6 and six-pillar readiness remain sufficient across ready fixtures, while pending/blocked fixtures do not fabricate facts.
- M7 drift summaries are stable and do not request module adjustments.
- Production replay metadata is metadata-only, privacy-safe, and projection-leak free.
- `v30.training_signal.real_case_calibration_pack` trains validation policy, not chart facts.
- M7 review is read-only and inherits no-write boundaries from upstream closeout.

## Latest M7-S2 Evidence

`v30.m7_real_case_calibration_closeout.v1` is available through:

```text
python3 scripts/run_m7_real_case_calibration_closeout.py --sample-limit 8
GET /api/v30/admin/m7/real-case-calibration-closeout
```

Latest result:

```text
v30.m7_real_case_calibration_closeout.v1: passed (6/6) m7_real_case_calibration_closed fixtures=30 next=M8 Projection/API Contract Closeout
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_m7_real_case_calibration_closeout.py tests/unit/test_m7_real_case_calibration_steady_state_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
14 passed
```

S2 verifies:

- M7-S1 steady-state review is ready before closeout.
- The canonical real-case backbone remains ready across solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender fixtures.
- Production replay metadata stays metadata-only, privacy-safe, and projection-leak free.
- Drift and focused expansion are tracked without blocking the current core flow.
- `v30.training_signal.real_case_calibration_pack` remains validation-policy training, not chart-fact training.
- M7 supports downstream M1-M6/M8 calibration and release acceptance without pointer, fixed-verdict, or chart-fact writes.

## Latest M8-S1 Evidence

`v30.m8_projection_api_contract_closeout.v1` is available through:

```text
python3 scripts/run_m8_projection_api_contract_closeout.py --sample-limit 8
GET /api/v30/admin/m8/projection-api-contract-closeout
```

Latest result:

```text
v30.m8_projection_api_contract_closeout.v1: passed (6/6) m8_projection_api_contract_closed contracts=25 next=IQ Intelligent Question Support Review
v30.synthetic.m8_api_projection_contract: passed (30/30)
pytest -q tests/unit/test_m8_projection_api_contract_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
7 passed
```

S1 verifies:

- M7-S2 closeout is ready before M8 projection/API closeout.
- `m8_api_projection_contract` passes across 30 real-case calibration rows.
- Ready-row projection contracts are core-first, additive, customer-safe, and admin-diagnostic capable.
- Real business API freeze is ready and keeps the customer reading API additive.
- `v30.training_signal.api_projection_contract` trains visibility/presentation policy only, not chart facts.
- M8 closeout does not require full pytest/full 518K and performs no pointer, fixed-verdict, or chart-fact writes.

## Latest IQ-S1 Evidence

`v30.iq_intelligent_question_support_review.v1` is available through:

```text
python3 scripts/run_iq_intelligent_question_support_review.py --sample-limit 8
GET /api/v30/admin/iq/intelligent-question-support-review
```

Latest result:

```text
v30.iq_intelligent_question_support_review.v1: passed (6/6) iq_intelligent_question_support_ready interaction=5 next=LLM Bazi Expression Support Review
v30.synthetic.interaction_loop: passed (5/5)
pytest -q tests/unit/test_iq_intelligent_question_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed
```

S1 verifies:

- M8-S1 projection/API contract is closed before IQ review.
- IQ5 closeout remains ready on the current M1-M8 surfaces.
- `interaction_loop` passes and emits question strategy training signals.
- Visible/internal question split, customer/admin role projection, and diagnostic boundaries remain stable.
- Question training and LLM question context support follow-up/expression only, not chart fact generation.
- Core Bazi chain remains authoritative; hidden-factor feedback stays a clue path and no pointer/chart-fact write occurs.

## Latest LLM-S1 Evidence

`v30.llm_bazi_expression_support_review.v1` is available through:

```text
python3 scripts/run_llm_bazi_expression_support_review.py --sample-limit 8
GET /api/v30/admin/llm/bazi-expression-support-review
```

Latest result:

```text
v30.llm_bazi_expression_support_review.v1: passed (6/6) llm_bazi_expression_support_ready acceptance=5 next=Training/Synthetic Support Review
v30.synthetic.bazi_llm_acceptance: passed (5/5)
pytest -q tests/unit/test_llm_bazi_expression_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed
```

S1 verifies:

- IQ-S1 is ready before LLM expression support review.
- BL8 closeout remains ready across context, answer, output acceptance, training synthetic, and role/locale evidence.
- Task-specific bounded context packs, role prompt contracts, fallback answer path, and role/locale coverage remain ready.
- `bazi_llm_acceptance` accepts valid expression outputs and rejects schema, role, and drift failures.
- LLM training can tune expression and question strategy only; it cannot tune chart facts.
- Live provider smoke remains explicit-only and no heavy gate, pointer write, or chart-fact mutation occurs.

## Latest BT-S1 Evidence

`v30.training_synthetic_support_review.v1` is available through:

```text
python3 scripts/run_training_synthetic_support_review.py --sample-limit 8
GET /api/v30/admin/training/synthetic-support-review
```

Latest result:

```text
v30.training_synthetic_support_review.v1: passed (7/7) training_synthetic_support_ready training=91 signals=33 sample518k=8 next=Core Chain Steady-State Summary
v30.synthetic.training_pipeline: passed (91/91)
v30.518k.sample.20260611225420867821: eligible mode=sample cases=8 shards=0
pytest -q tests/unit/test_training_synthetic_support_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed
```

S1 verifies:

- LLM-S1 is ready before training/synthetic support review.
- `training_pipeline` passes with 91/91 cases.
- Extracted training signals cover core modules, projection, question strategy, expression, real-case calibration, and LLM support.
- No extracted training signal can tune deterministic chart facts.
- Synthetic manifest is ready; `all` remains a major-node-only tier.
- 518K sample passes 8 cases with no visible calibration leaks and no failure clusters.
- No pointer promotion, synthetic all, full pytest, or full 518K is run by default.

## Latest S-S1 Evidence

`v30.core_chain_steady_state_summary.v1` is available through:

```text
python3 scripts/run_core_chain_steady_state_summary.py --sample-limit 8
GET /api/v30/admin/mainline/core-chain-steady-state-summary
```

Latest result:

```text
v30.core_chain_steady_state_summary.v1: passed (5/5) core_chain_steady_state_ready modules=13 next=Evidence-Driven Calibration Queue
pytest -q tests/unit/test_core_chain_steady_state_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed
```

S1 verifies:

- BT-S1 training/synthetic/518K support is ready before the core chain steady-state summary.
- MCR2 customer surface and BaziContext reconciliation remains ready.
- M1-M8, customer surface, BaziContext, BT, and U are 100%; IQ and LLM are bounded steady.
- Routine validation stays targeted; synthetic all, full pytest, full 518K, and live LLM are major-node explicit gates only.
- The summary is read-only: no policy pointer promotion, no pointer write, no chart-fact mutation, and no fixed Bazi verdict.

## Latest E-S1 Evidence

`v30.evidence_driven_calibration_queue.v1` is available through:

```text
python3 scripts/run_evidence_driven_calibration_queue.py --sample-limit 8
GET /api/v30/admin/mainline/evidence-driven-calibration-queue
```

Latest result:

```text
v30.evidence_driven_calibration_queue.v1: passed (4/4) evidence_driven_calibration_queue_ready candidates=0 next=Await New Calibration Evidence
pytest -q tests/unit/test_evidence_driven_calibration_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
6 passed
```

E-S1 verifies:

- S-S1 core chain steady state is ready before accepting post-steady-state calibration work.
- Focused calibration queue review is ready and has no current focused fix candidates.
- Accepted evidence sources are real-case calibration, business acceptance, 518K distribution, training signal distribution, LLM expression acceptance, and question-chain acceptance.
- Heavy gates and live LLM remain explicit-only.
- No pointer promotion, pointer write, auto-apply training, chart-fact mutation, or fixed Bazi verdict is allowed.

## Latest W-S1 Evidence

`v30.await_new_calibration_evidence_status.v1` is available through:

```text
python3 scripts/run_await_new_calibration_evidence_status.py --sample-limit 8
GET /api/v30/admin/mainline/await-new-calibration-evidence
```

Latest result:

```text
v30.await_new_calibration_evidence_status.v1: passed (4/4) await_new_calibration_evidence_ready waiting=True next=Await Evidence Or Explicit Major Validation
pytest -q tests/unit/test_await_new_calibration_evidence_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed
```

W-S1 verifies:

- E-S1 evidence-driven queue is ready.
- No current focused calibration candidates are queued.
- All accepted evidence sources are registered.
- The system waits without heavy gates, pointer promotion, chart-fact mutation, auto-apply training, or fixed Bazi verdict.

## Latest SCAL-S1 Evidence

`v30.synthetic_canonical_bazi_calibration_review.v1` is available through:

```text
python3 scripts/run_synthetic_canonical_bazi_calibration_review.py
```

Latest result:

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

## Latest SCAL-S2 Evidence

`v30.synthetic_canonical_pack_decision.v1` is available through:

```text
python3 scripts/run_synthetic_canonical_pack_decision.py
```

Latest result:

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

## Latest SCAL-S3 Evidence

`v30.synthetic_canonical_steady_state.v1` is available through:

```text
python3 scripts/run_synthetic_canonical_steady_state.py
```

Latest result:

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

## Latest SCAL-S3-WAIT Evidence

`v30.synthetic_canonical_await_trigger.v1` is available through:

```text
python3 scripts/run_synthetic_canonical_await_trigger.py
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

SCAL-S3-WAIT verifies:

- The frozen 16-case canonical gate is ready and currently has no active trigger.
- Known triggers are RBD, M3, M5, IQ changes, and release-boundary validation.
- Unknown triggers block the wait status rather than silently running or mutating anything.
- No chart-fact mutation, auto-apply training, pointer promotion, full pytest, synthetic all, or full 518K by default.

## Latest REL-S1 Evidence

`v30.controlled_release_readiness.v1` is available through:

```text
python3 scripts/run_controlled_release_readiness.py
```

Latest result:

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

- The frozen synthetic canonical gate is waiting without an active trigger.
- RBD steady state and backend API customer journey are ready for controlled trial use.
- Runtime configuration remains V30 scoped.
- Controlled trial readiness is true, but external release remains false.
- Full pytest, synthetic all, full 518K, live LLM, real-env smoke, and pointer promotion remain explicit-only.

## Latest REL-S2 Evidence

`v30.explicit_release_gate_authorization.v1` is available through:

```text
python3 scripts/run_explicit_release_gate_authorization.py
```

Latest result:

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
- Full pytest, live LLM smoke, real-env smoke, and full 518K remain deferred.
- External release, chart-fact mutation, auto-apply training, and pointer promotion remain disabled.

## Latest REL-S3 Evidence

`v30.stage_a_release_gate_execution.v1` is available through:

```text
python3 scripts/run_stage_a_release_gate_execution.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

Latest result:

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

- Only REL-S2-authorized Stage-A gates were executed.
- Controlled readiness, synthetic all, 518K sample, and 518K shard passed.
- Full pytest, live LLM smoke, real-env smoke, and full 518K were not run.
- External release, chart-fact mutation, auto-apply training, and pointer promotion remain disabled.

## Latest REL-S4 Evidence

`v30.stage_a_evidence_review.v1` is available through:

```text
python3 scripts/run_stage_a_evidence_review.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

Latest result:

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
- Full pytest, live LLM smoke, real-env smoke, full 518K, chart-fact mutation, auto-apply training, and pointer promotion remain disabled.
- The next mainline returns to core-module targeted work.

## Latest MCR3 Evidence

`v30.core_mainline_selection_after_release_hold.v1` is available through:

```text
python3 scripts/run_core_mainline_selection_after_release_hold.py
```

Latest result:

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
- The next task is selected by direct Bazi measurement impact.
- Synthetic archetype calibration is selected over UI or release expansion.
- Real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release remain disabled.

## Latest SYN-CAL1 Evidence

`v30.synthetic_archetype_rule_claim_calibration.v1` is available through:

```text
python3 scripts/run_synthetic_archetype_rule_claim_calibration.py
```

Latest result:

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

## Latest SYN-CAL2 Evidence

`v30.synthetic_archetype_tier_registration.v1` is available through:

```text
python3 scripts/run_synthetic_archetype_tier_registration.py
```

Latest result:

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

- `synthetic_archetype_rule_claim` is registered as a targeted synthetic tier.
- The tier passes 4/4 current archetype cases.
- SYN-CAL1 artifact is aligned with tier case count.
- Future archetype failures route to read-only calibration queues.
- The tier is not a default full/release gate.
- Real-person truth labels, chart-fact mutation, auto-apply training, pointer promotion, and external release remain disabled.

## Latest SYN-CAL3 Evidence

`v30.synthetic_archetype_training_signal_review.v1` is available through:

```text
python3 scripts/run_synthetic_archetype_training_signal_review.py
```

Latest result:

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

- Synthetic archetype outcomes produce four review-only M3/M5/M6 training signals.
- Signal targets are limited to M3 rule/claim coverage, M5 candidate alignment, M6 practical claim specificity, and boundary safety.
- Signals and queues cannot mutate chart facts, auto-apply training, promote pointers, or authorize external release.
- Full pytest, synthetic all, full 518K, and live LLM remain explicit-only.

## Latest SYN-CAL4 Evidence

`v30.synthetic_archetype_calibration_closeout.v1` is available through:

```text
python3 scripts/run_synthetic_archetype_calibration_closeout.py
```

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

SYN-CAL4 verifies:

- SYN-CAL1/SYN-CAL2/SYN-CAL3 evidence is frozen into a closeout artifact.
- Routine targeted cadence is defined for archetype tier, training-signal review, and closeout.
- Heavy gates remain explicit-only.
- No chart-fact mutation, auto-training, pointer promotion, live provider call, or external release is authorized.

## Next Task

`CORE-CAL-WAIT Await Focused Calibration Evidence Or Explicit Major Validation`

Scope:

- Serve the current Bazi system.
- Keep `synthetic_archetype_rule_claim`, SYN-CAL3, SYN-CAL4, and CORE-CAL-S0 as targeted routine gates.
- Accept new work only from focused evidence sources: real-case calibration, business acceptance, 518K distribution, training signal distribution, LLM expression acceptance, or question-chain acceptance.
- Do not reopen all core modules from vague expansion pressure.
- Keep chart-fact mutation, auto-apply training, pointer promotion, full pytest, synthetic-all, full 518K, and live LLM explicit-only.

Default validation:

```text
python3 -m compileall -q v30/validation/core_calibration_steady_state_queue.py scripts/run_core_calibration_steady_state_queue.py v30/validation/__init__.py
pytest -q tests/unit/test_core_calibration_steady_state_queue.py
```

Reference:

```text
scripts/run_core_calibration_steady_state_queue.py
```
