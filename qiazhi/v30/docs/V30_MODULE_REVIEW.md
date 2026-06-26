# V30 Module Review

Updated: 2026-06-10

## Purpose

This document is the migration control surface for reviewing V20 modules before V30 implementation.

V30 can learn from V20, but V30 runtime must remain independent. No module may be copied or rewritten until its role, coupling, test burden, and V30 contract are understood.

## Current System And Module Completion Review

V30 has moved past migration review into a working system-loop prototype. The current review priority is no longer "which V20 module should be copied"; it is "which V30 module needs deeper fusion, state, validation, or ownership cleanup."

| Module family | Completion | Current state | Next mainline action |
|---|---:|---|---|
| Runtime/API/UI spine | 99% | R12 plus UI1-UI9 complete: independent `/api/v30` and `/v30/ui` loop supports BirthInput, view projection, question answer refresh, actor/session hooks, read-history owner contract, lightweight product auth, V20 password-hash compatibility for imported accounts, Bazi profiles, admin diagnostics, Reading Shell, Admin Shell, deep-linked admin tabs, module review, reading/trace lookup, LLM/training/validation panels, live 9030 static/API smoke, release-gated LLM smoke telemetry, production replay metadata gate coverage, and release-boundary finalization. | Complete for current core/product shell scope; future work is browser visual regression and new product workflows. |
| BirthInput and deterministic chart facts | 100% | C5 complete for current core scope: solar, lunar, leap-month input, known-place true-solar adjustment, unknown-hour blocking, invalid timezone/date/time traces, solar-term/year-month fixtures, canonical M1/M2 real-case fact fixtures, six-pillar context, luck-cycle, flow-year/month context, no-fake-fact guardrails, and downstream consumption proof are active. | Complete for current core scope; future edge-year/cross-timezone cases are fixture expansion only. |
| Feature/rule/knowledge/structure spine | 100% | C6 complete for current core scope: source registry, V20 reference assets, K/R/P units, rule/counter-evidence, portrait features, mechanism graph, dynamic graph paths, domain-rule depth, model-signal path adjustment, mainline arbitration, and M4/M5/M6 support proof are active. | Complete for current core scope; future source depth is calibration/hardening only. |
| Ten-god energy model | 100% | C2 complete: runtime emits bounded `v30.model_signal_summary.v1` from deterministic six-pillar energy/stability/volatility with dedicated calibration tier, five-family band coverage, interface contract, calibration profile, calibration flags, ranked-decision adjustments, real-case replay, training distribution, and auto-training model-signal weights. | Complete for current core scope. |
| Strength/structure/useful-god ranked decisions | 100% | C2 complete: runtime emits bounded candidate reviews with `candidate_scores`, `scoring_basis`, model-signal summaries, M4 calibration flags and adjustment bias, follow/disputed/regulation structure candidates, M5 fixtures, score floors, replay weights, useful-god evidence calibration, auto-training policy weights, M1/M2 root/vault consumption, and no raw model-score exposure. | Complete for current core scope. |
| Practical reading output | 100% | C1 complete: career, wealth, relationship, health, and timing readings consume chart facts, structure evidence, M4 signal bands, and M5 ranked decisions with calculation basis, evidence ids, explanation units, domain insights, action steps, calibration prompts, module trace, blocked claims, and quality contracts. | Complete for current core scope. |
| Core calculation validation / real-case calibration | 100% | C3 complete: 30 canonical fixtures validate chart facts, timing context, M4 signal bands, M5 ranked candidates, M6 practical reading contracts, blocked/pending guardrails, production replay metadata tags, and `v30.real_case_calibration_drift_summary.v1` module-routed drift summaries. | Complete for current core scope; future non-synthetic replay remains metadata-only and cannot import private content into facts. |
| Customer reading and presentation | 100% | C4 complete for current core scope: guest/user receive core-first Bazi calculation, domain cards, structured options, sanitized next question, sanitized answer-panel LLM status, actor/session context, `v30.api_projection_contract.v1`, core-first projection contract, customer surface contract, full additive field preservation, forbidden-field policy, leak scan, and role-gated diagnostics. | Complete for current core scope. |
| Real business Bazi reading acceptance | 100% | B1 complete: `v30.real_business_bazi_reading_acceptance.v1` accepts 12/12 ready canonical real-case rows through M1/M2, M4, M5, M6, M8, customer leak scan, and read-only policy boundaries. | Complete; B2 now owns expanded regression. |
| Business reading regression pack | 100% | B2 complete: `v30.real_business_bazi_reading_regression_pack.v1` accepts 24/24 ready canonical rows, verifies five concise customer domain cards, five M6 practical domain contracts, base explanations, M1/M2 completion, M5 projection, privacy/no-mutation metadata, and M8 API projection 30/30. | B3 should verify answer refresh preserves the accepted reading surface. |
| Business answer refresh regression | 100% | B3 complete: `v30.real_business_answer_refresh_regression.v1` passes 5/5 structured answer refresh rows, requires B2 readiness, preserves chart context, feature evidence, core reading fingerprint, five domain cards, and customer projection leak safety. | B4 should cover pending/blocked input boundaries. |
| Boundary and blocked input regression | 100% | B4 complete: `v30.real_business_boundary_blocked_input_regression.v1` passes 5/5 pending/blocked BirthInput rows, validates no fake pillars, no M4/M5/M6 fake readiness, no fake-ready projection, explainable conversion boundaries, and metadata-only/no-mutation privacy. | B5 should freeze the B1-B4 API contract. |
| Business API contract freeze | 100% | B5 complete: `v30.real_business_api_contract_freeze.v1` passes 4/4 B1-B4 gates and freezes required business endpoints, customer surface keys, additive API policy, minimum acceptance counts, and forbidden non-mutating behaviors. | B6 should close out the business acceptance track. |
| Business acceptance closeout | 100% | B6 complete: `v30.real_business_acceptance_closeout.v1` passes 4/4 closeout checks, records B1-B5 as the default business reading gate, pauses B-track, and keeps major validation/release/pointer promotion explicit. | S1 steady state; no further B-track task by default. |
| Business acceptance steady state | 100% | S1 complete: `v30.real_business_steady_state.v1` passes 5/5 steady-state checks, keeps B1-B5 as the routine business gate, defines explicit reopen conditions, and blocks default full pytest/full 518K/release/pointer/chart-fact mutation. | Wait for new business evidence or explicit major validation request. |
| Integrated Bazi intelligence requirements | 100% | IR1 complete: `v30.bazi_intelligence_requirements_coverage.v1` passes 6/6 and verifies M1-M8, knowledge/rule/portrait/path evidence, role/locale projection, continuous Q&A, hidden-factor feedback, Bazi LLM expression, training/synthetic, and no-mutation boundaries as one backend coverage gate. IR2 complete: `/api/v30` backend journey passes 6/6 across create/view/answer/hidden-factor/history/admin-gate route handlers. | IR-S1 steady state; wait for new business or calibration evidence. |
| Intelligent central brain | 100% | BT10 complete: central-brain acceptance, session replay, failure routing, synthetic tier, and unified closeout are accepted under `v30.brain_training_synthetic_closeout.v1`. | Complete for current support-system scope; default state is BT-S1 steady state. |
| Question/dialogue graph | 98% | IQ5 complete: `interaction_state`, visible/internal next-question split, follow-up reason, selected options, `known_user_signals`, graph-selected refresh, model-signal personalized customer top question, two-turn chain readiness, dedicated `interaction_loop` validation 5/5, `v30.training_signal.question_model_signal_personalization`, guarded `model_signal_question_policy` auto-training candidate, LLM context support, role-gated diagnostics, and closeout layer separation are active. | IQ-S1 steady state; reopen only on new business evidence, role leak, interaction drift, or question-policy calibration evidence. |
| Main module completion review | 100% | MCR1 complete and MCR2 complete: `v30.main_module_completion_review.v1` passes 5/5, `v30.customer_surface_bazi_context_reconciliation.v1` passes 6/6, customer surface and BaziContext accounting are steady 100%, and full pytest/synthetic all/full 518K/live LLM/pointer promotion remain explicit-only. | M3-G1 Source-Governed Depth And Calibration Tags. |
| LLM expression | 88% | R4 complete: rule answer is composed first; bounded LLM draft can be accepted or safely fall back; live-smoke artifact records unconfigured/configured-not-executed/accepted/fallback/drift-rejected states, provider readiness, fallback reason, drift failures, and no-mutation proof. BL8 accepts BL1-BL7 evidence and enters BL-S1 steady state with live provider smoke explicit-only. | Reopen only on new LLM task/role/locale requirements, observed live-provider failures, or release-boundary live smoke. |
| Role/session/client/locale productization | 100% | U5 complete: `v30.productization_closeout.v1` passes 5/5 checks; U1-U4 evidence is accepted, multi-user/session/terminal/locale projection is in U-S1 steady state, lightweight auth/profile pages are active, and imported V20 users can authenticate with their original stored password hashes while chart-fact mutation remains blocked. | Reopen only on new product requirement, projection contract failure, or explicit full-login/UI scope. |
| Training / auto-apply system | 100% | BT10 complete: closeout, quarantine, training-pipeline synthetic tier, signal extraction, candidate boundaries, and unified closeout are accepted for current scope. | Complete for current support-system scope; default state is BT-S1 steady state. |
| Synthetic validation system | 100% | BT10 complete: `central_brain`, `training_pipeline`, synthetic coverage manifest, and 518K readiness evidence are unified by `v30.brain_training_synthetic_closeout.v1`; full synthetic/all remains a major-node-only check. | Complete for current support-system scope; reopen only on new evidence or explicit major validation. |
| 518K validation support | 95% | BT10 complete: `v30.518k_readiness_matrix.v1` remains the distribution gate, sample/shard gates are ready, full mode is explicit-only, artifacts/index/search fallback are verified, and candidate-family coverage matrix is documented. | Complete for current support-system scope; full corpus remains explicit-only. |

## Core Calculation Module Priority

The current product priority is core Bazi calculation support. These module families are the first-class calculation modules; question, hidden-factor, LLM, training, and corpus tracks remain supporting systems.

| Priority | Core module family | Completion | Current state | Mainline action |
|---:|---|---:|---|---|
| 1 | BirthInput and deterministic chart facts | 100% | C5 complete: BirthInput can build solar, lunar, leap-month, known-place true-solar, unknown-hour blocked, invalid-timezone blocked, solar-term/year-month boundary, canonical real-case facts, luck-cycle, flow-year/month, six-pillar contexts, deterministic base summaries, and M5/M6 consumption proof. | Complete for current core scope. |
| 2 | Bazi base fact explanation layer | 100% | C5 complete: four pillars, visible/hidden ten gods, hidden stem summaries, five-element distribution, relation families, vault branches, root/vault facts, fact integrity, base explanations, `v30.m1_m2_completion_summary.v1`, and category/downstream coverage are active in `core_bazi_reading`. | Complete for current core scope. |
| 3 | Feature/rule/knowledge/structure spine | 100% | C6 complete: source-backed K/R/P, V20 references, rule/counter-evidence, portrait features, mechanism paths, dynamic graph paths, model-signal path adjustment, mainline arbitration, `v30.m3_completion_summary.v1`, and M4/M5/M6 support proof are active. | Complete for current core scope. |
| 4 | Ten-god energy model | 100% | C2 complete: `v30.model_signal_summary.v1` influences structure paths, ranked decisions, answer context, training extraction, auto-training candidates, diagnostics, dedicated five-family calibration, real-case replay, calibration flags, and ranked-decision adjustments. | Complete for current core scope. |
| 5 | Strength/structure/useful-god ranked decisions | 100% | C2 complete: strength, structure pattern, and useful-god are ranked candidates with candidate scores, scoring basis, evidence, boundaries, M4 calibration flags/adjustments, follow/disputed/regulation candidates, fixtures, score floors, replay weights, useful-god evidence calibration, M1/M2 root/vault basis, and no raw model-score leakage. | Complete for current core scope. |
| 6 | Practical reading output | 100% | C1 complete: career, wealth, relationship, health, and timing readings expose calculation basis, M5 decision links, M4 signal bands, evidence ids, explanation units, domain insights, action steps, calibration prompts, module trace, blocked claims, and quality contracts. | Complete for current core scope. |
| 7 | Core calculation validation / real-case calibration | 100% | C3 complete: 30 canonical fixtures validate chart facts, timing context, M4 signal bands, M5 ranked candidates, M6 practical reading contracts, blocked/pending guardrails, production replay metadata tags, and module-routed M7 drift summaries. | Complete for current core scope. |
| 8 | User presentation / API projection | 100% | C4 complete: additive projection contract, customer leak scan, core-first reading surface, customer surface contract, full additive field preservation, sanitized question/answer projection, customer forbidden-field policy, role visibility matrix, and role-gated diagnostics are active. | Complete for current core scope. |

Current backend coverage: IR1 verifies that the original Bazi intelligence requirements are covered by the current backend module chain, and IR2 verifies the same chain through `/api/v30` backend route handlers. Remaining risk is product experience, release discipline, or new calibration evidence, not missing core module support. Hidden factors must remain feedback clues, not chart facts or primary calculation content.

## Migration Categories

| Category | Meaning |
|---|---|
| Direct reuse candidate | Small, deterministic, typed, and free of V20 runtime coupling after namespace cleanup. |
| Reimplement from idea | V20 concept is valuable but implementation is too coupled or patch-shaped. |
| Convert data | Data, cases, catalogs, rules, or artifacts are useful but must be converted into V30 schemas. |
| Reference only | Useful for behavior comparison, not a V30 implementation source. |
| Retire | Pattern should not continue in V30. |

## Review Questions

Every module family must answer:

- What V30 contract does this support?
- What chart context does it bind to?
- What evidence does it produce or consume?
- What role can see the output?
- What tests prove it does not drift?
- Does it depend on V20 runtime files, DB, Redis, or pointer state?
- Is it light enough for default tests?
- Does it belong in runtime, training, validation, or offline conversion?

## Module Family Inventory

### Core Chart Facts

V20 paths:

```text
core/chart.py
core/schemas.py
core/ten_gods.py
core/relations.py
core/time_context.py
core/strength.py
core/useful_god.py
core/context_frame.py
```

Initial decision: direct reuse candidate / light reimplementation.

V30 target:

```text
v30/core/chart_context.py
v30/core/time_context.py
v30/core/ten_gods.py
v30/core/relations.py
v30/core/strength.py
v30/core/useful_god.py
```

Review focus:

- Determinism.
- Missing time context.
- Original chart, luck cycle, annual flow binding.
- Typed `ChartContext`.
- Fast pure unit tests.

Risks:

- Hidden dependence on V20 schema names.
- Useful-god logic mixing fact extraction and interpretation.
- Time context becoming implicit.

### Feature Evidence

V20 paths:

```text
features/compiler.py
features/schema.py
features/state_model.py
features/confidence.py
features/calibration.py
features/discovery_engine.py
```

Initial decision: reimplement from idea.

V30 target:

```text
v30/evidence/schema.py
v30/evidence/features.py
v30/evidence/compiler.py
```

Review focus:

- `FeatureEvidence` as foundational runtime data.
- Evidence supports or weakens claims.
- Confidence semantics.
- Calibration as training-time policy, not hard-coded runtime patch.

Risks:

- Feature layer leaking into questions, answer, or learning.
- Confidence scores without validation lineage.

### Rules and Defeasible Reasoning

V20 paths:

```text
rules/engine.py
rules/catalog.py
decision/defeasible_model.py
decision/fusion.py
decision/knowledge_bridge.py
decision/engine.py
```

Initial decision: mixed.

V30 target:

```text
v30/rules/catalog.py
v30/rules/evaluator.py
v30/evidence/rule_evidence.py
```

Review focus:

- One V30 evidence/rule path.
- Defeasible reasoning as explicit conflict handling.
- Rule evidence output, not direct public verdicts.
- Rule catalog versioning.

Risks:

- Carrying forward legacy seed decisions.
- Compatibility bridge becoming a second runtime truth source.

### Knowledge System

V20 paths:

```text
knowledge/loader.py
knowledge/schema.py
knowledge/retrieval.py
knowledge/rule_library.py
knowledge/structure_mechanisms.py
docs/bazi_knowledge/
```

Initial decision: convert data / reimplement loader.

V30 target:

```text
v30/knowledge/schema.py
v30/knowledge/loaders/
v30/knowledge/packs/
```

Review focus:

- Knowledge packs are versioned.
- Knowledge facts do not mutate chart facts.
- Rule library and knowledge library have clear boundaries.
- Retrieval returns evidence-backed units.

Risks:

- Giant hard-coded loader.
- Approval/review workflow replacing automatic training application.
- Knowledge text becoming untestable prompt filler.

### Structure Dynamics

V20 paths:

```text
dynamics/graph_engine.py
dynamics/engine.py
dynamics/schema.py
graph/chart_graph.py
graph/rule_graph.py
graph/scoring.py
knowledge/structure_mechanisms.py
validation/structure_dynamics_synthetic.py
```

Initial decision: reimplement from idea, convert cases.

V30 target:

```text
v30/structure/graph.py
v30/structure/mechanisms.py
v30/structure/policy.py
v30/structure/state.py
```

Review focus:

- Weighted dynamic graph.
- Mechanism-backed semantic labels.
- Separate graph extraction, scoring, policy, and presentation.
- Synthetic structure validation.

Risks:

- Graph output tied to V20 report shape.
- Runtime reading V20 pointer files.
- Generic fallback labels appearing in user views.

### Integrated Bazi Model Pipeline

V20 paths:

```text
knowledge/
rules/
features/
dynamics/
interaction/portrait_*.py
learning/*_runtime_pointer.py
validation/
corpus/
```

Initial decision: reimplement as a unified V30 pipeline.

V30 target:

```text
v30/evidence/
v30/rules/
v30/knowledge/
v30/structure/
v30/portrait/
v30/learning/
v30/validation/
```

Review focus:

- Knowledge, rules, features, portraits, and structure dynamics share one artifact lifecycle.
- Parallel generation is allowed only after `ChartContext`; runtime truth remains sequential and evidence-bound.
- Synthetic Bazi cases validate every generated family.
- Parameter tuning is family-scoped and pointer-applied.
- 518K validation checks distribution stability, not single-chart truth.

Risks:

- Subsystems generating independently and applying independently.
- Synthetic validation staying too shallow.
- 518K statistics becoming a false truth source.
- Parameter tuning changing runtime behavior without shared promotion gates.

### Mainline and Orchestration

V20 paths:

```text
orchestrator/evidence.py
orchestrator/mainline.py
orchestrator/brain_state.py
orchestrator/question_focus.py
orchestrator/runtime_policy.py
```

Initial decision: reimplement from idea.

V30 target:

```text
v30/mainline/candidates.py
v30/mainline/arbitration.py
v30/mainline/state.py
v30/policy/runtime_pointer.py
```

Review focus:

- Evidence-weighted arbitration.
- Mainline selection explains why selected.
- Selected question may bias tie-breaks, not override evidence.
- Runtime policy is explicit and versioned.

Risks:

- Brain state becoming a giant mixed payload.
- Runtime policy mixing with presentation or training.

### Question System

V20 paths:

```text
interaction/question_atoms.py
interaction/question_dag.py
interaction/question_anchor.py
interaction/question_ranker.py
interaction/question_intent.py
interaction/question_agent.py
decision/questions.py
decision/question_titles.py
role_view/narrative_prompt_framework.py
```

Initial decision: reimplement from idea, convert seeds/data, retire template-title path.

V30 target:

```text
v30/questions/intents.py
v30/questions/seeds.py
v30/questions/graph.py
v30/questions/anchor.py
v30/questions/recommender.py
v30/questions/policy.py
```

Review focus:

- Intelligent recommendation from current chart context.
- Seed questions evolve through training.
- Anchors are the only display question source.
- Role projection changes visibility/expression, not facts.

Risks:

- Template-generated questions returning.
- Raw title fields becoming internal and external source at once.
- Follow-up compatibility layers hiding unsupported recommendations.

### Hidden Factors and Dialogue Discovery

V20 paths:

```text
interaction/feedback.py
interaction/feedback_analysis.py
interaction/latent_event_calibration.py
interaction/practitioner_calibration.py
interaction/session_model.py
learning/latent_factor_calibration.py
learning/practitioner_calibration_training.py
```

Initial decision: reimplement from idea.

V30 target:

```text
v30/dialogue/hidden_factors.py
v30/dialogue/discovery_questions.py
v30/questions/hidden_factor_policy.py
v30/learning/hidden_factor_training.py
```

Review focus:

- Hidden attributes are dialogue-discovered hypotheses, not chart facts.
- Amplification factors can shift confidence, timing, or emphasis.
- Special-year questions are confirmation questions, not deterministic predictions.
- User denial/conflict/staleness must reduce confidence.
- LLM may render hidden factor questions but cannot confirm them.

Risks:

- Treating hidden factors as calculated facts.
- Turning special-year checks into fixed event predictions.
- Letting hidden factors override structure evidence.
- Storing user state as if it were chart truth.

### Answer and LLM

V20 paths:

```text
answer/plan.py
answer/composer.py
answer/domain_reading.py
llm/context.py
llm/contracts.py
llm/prompts.py
llm/enforcement.py
llm/practitioner.py
validation/answer_safety_evaluator.py
```

Initial decision: reimplement from idea, convert safety cases.

V30 target:

```text
v30/answer/context.py
v30/answer/planner.py
v30/answer/composer.py
v30/llm/roles.py
v30/llm/context.py
v30/llm/contracts.py
v30/llm/policies.py
```

Review focus:

- LLM receives compact `AnswerContext`.
- LLM supports different roles and user states.
- LLM has more generative space inside explicit boundaries.
- Answer safety and drift tests are separate tiers.

Risks:

- Prompt context becoming too large.
- LLM reading raw trace for ordinary user answers.
- Role style rewriting facts.

### Role, Locale, and Client Projection

V20 paths:

```text
access/projection.py
access/roles.py
role_view/projection.py
role_view/policy.py
i18n/ui_labels.py
frontend/app.js
```

Initial decision: reimplement.

V30 target:

```text
v30/presentation/roles.py
v30/presentation/locales.py
v30/presentation/client_model.py
```

Review focus:

- UI consumes `ClientPresentationModel`.
- Role controls visibility and language density.
- Locale rendering does not create new claims.
- Admin/lab diagnostics are explicit sections.

Risks:

- UI reading internal runtime fields.
- Role projection rewriting selected structure or mainline.

### Training and Runtime Pointers

V20 paths:

```text
learning/*_runtime_pointer.py
learning/*_training.py
learning/*_policy_*.py
learning_orchestrator/
validation/
corpus/
```

Initial decision: reimplement architecture, convert validation data and selected artifacts.

V30 target:

```text
v30/learning/runs.py
v30/learning/candidates.py
v30/learning/promotion.py
v30/policy/runtime_pointer.py
v30/validation/
```

Review focus:

- Automatic validation and application.
- Runtime pointer as active policy source.
- Training artifacts are versioned.
- Synthetic and 518K validation are built in.

Risks:

- Manual review-first application path.
- Many policy families without a shared contract.
- Heavy validation accidentally entering default tests.

### Corpus and 518K Validation

V20 paths:

```text
corpus/artifacts.py
corpus/canonical_case.py
corpus/coverage.py
corpus/enumerator.py
corpus/full_precompute.py
corpus/storage.py
validation/synthetic_replay.py
```

Initial decision: reimplement runners, convert summaries/cases.

V30 target:

```text
v30/corpus/
v30/validation/corpus_518k.py
v30/validation/coverage.py
```

Review focus:

- Shard-level validation.
- Sample mode for fast iteration.
- Coverage and drift metrics.
- Artifact lineage.

Risks:

- Full corpus jobs blocking local development.
- Validation results not tied to policy promotion.

### Testing System

V20 paths:

```text
testing/
tests/
scripts/test_*.sh
scripts/release_smoke.py
```

Initial decision: reimplement.

V30 target:

```text
tests/unit/
tests/integration/
tests/runtime/
tests/synthetic/
tests/release/
scripts/test_fast.sh
scripts/run_validation.py
scripts/run_release_gate.py
```

Review focus:

- Fast default test path.
- Explicit heavy validation tiers.
- Independent module tests.
- Stable smoke tests.

Risks:

- Every pytest run taking too long.
- Tests depending on service state or V20 runtime.
- Training jobs hiding inside ordinary tests.

## Review Backlog

### Completed Baseline Review

- Core chart facts.
- Feature evidence.
- Test architecture.
- Runtime pointer architecture.
- Synthetic validation contract.
- Integrated Bazi model pipeline.
- Structure dynamics.
- Knowledge and rule packs.
- Mainline arbitration.
- Question intelligence.
- Answer context and LLM roles.
- 518K validation.
- Corpus storage.
- UI/presentation model.
- Release gate.
- Observability and dashboards.

### Active Mainline Review

The active core-completion review is frozen for the current M1-M8 scope. P7/P8 hooks remain baseline support layers. C1 completed M6 practical reading output, C2 completed M4/M5 model-signal/ranked-decision calibration, C3 completed M7 real-case calibration drift routing, C4 completed M8 core-first API projection, C5 completed M1/M2 deterministic fact and base explanation completion, C6 completed M3 evidence/rule/knowledge/structure spine completion, C7 completed the integrated core calculation gate, C8 completed core-completion documentation freeze, F1 completed the frozen-core calibration baseline, F2 completed targeted calibration candidate review, F3 completed targeted calibration validation gate, F4 completed targeted calibration pointer review, F5 completed explicit operator pointer decision with promotion deferred, F6 completed targeted calibration closeout with no promotion, M0 completed mainline selection, R13 completed external-release dry run with full pytest deferred, R14 completed the full-pytest execution decision with full pytest deferred, R15 completed blocked-release status recording, R16 paused the release-boundary track without running full pytest, M0 after release pause selected P0 core monitoring/calibration, P0 established the read-only core monitoring loop, P1 passed all lightweight monitoring checks, P2 summarized four stable calibration observations with no regression, P3 established the on-new-evidence drift-watch route matrix with no drift detected, P4 established the focused module-target evidence queue, P5 reviewed the empty queue with no focused fix candidate, P6 closed the current empty watch cycle, P7 established the ongoing cadence baseline, P8 synchronized the cadence across controlling docs, P9 entered steady state, S0 status is recorded, B1 accepted the ready real-business Bazi reading path 12/12, B2 accepted expanded business reading regression 24/24, B3 accepted answer refresh regression 5/5, B4 accepted boundary/blocked input regression 5/5, B5 froze the B1-B4 API acceptance contract 4/4, B6 closed business acceptance 4/4, and S1 entered business acceptance steady state 5/5. Current state is S1-WAIT Await New Business Evidence Or Explicit Major Validation. External release dry run, full pytest decision, and policy pointer promotion are separate tracks and must not be mixed back into business acceptance.

1. `S1-WAIT Await New Business Evidence Or Explicit Major Validation`: no further B-track task by default; explicit request required for major validation.
2. `Post-seal release hardening`: keep gates targeted, run full gates only at release/pointer boundaries, and fix only real validation failures.
## Retire List

These patterns should not enter V30:

- Runtime import from `v20.*`.
- Raw question title as display source.
- Template-only question generation.
- V20 all-in-one runtime payload for ordinary UI.
- Role projection that rewrites facts.
- Training output requiring manual review before every runtime application.
- Knowledge loader as a giant hard-coded Python function.
- Runtime code reading V20 pointer files.
- Heavy corpus validation in default tests.
