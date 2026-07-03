# V30 Master Mainline Plan

Updated: 2026-06-10

## Purpose

This is the top-level control document for V30 design and development.

V30 now has several topic documents. This master plan defines the mainline so development does not over-focus on one subsystem too early.

## North Star

V30 is an independent, high-iteration Bazi intelligence runtime.

The current mainline priority is `Core Bazi Calculation First`: complete the customer-visible Bazi calculation surface before expanding question, hidden-factor, LLM, or training experiences. P7 model fusion and P8 structured interaction are now baseline runtime layers, but the active product task is to make the first screen work as a real Bazi calculation page: BirthInput, deterministic chart facts, ten-god/five-element context, luck/flow timing, structure evidence, strength/structure/useful-god candidates, practical reading, and customer presentation.

It must combine:

- Deterministic Bazi facts.
- Evidence-based reasoning.
- Knowledge/rule/portrait/structure modeling.
- Intelligent question recommendation.
- Dialogue-discovered hidden attributes and amplification factors.
- Product-facing Bazi question interaction with structured user choices.
- Role-aware LLM answers.
- Framework-level Bazi expression layer.
- Central brain orchestration that coordinates without becoming a monolith.
- Automatic self-training.
- Synthetic validation.
- 518K validation.
- Lightweight modular testing.

V30 is not:

- A V20 rename.
- A template question generator.
- A manual-review-first training system.
- A giant runtime payload rendered directly by UI.
- A system where LLM creates chart facts or unsupported conclusions.
- A customer UI that exposes internal Bazi context, structure paths, portrait projections, policy payloads, or training diagnostics by default.
- A V20 runtime migration. V20 can provide scenarios, prompts, configuration patterns, and validation references, but V30 code, contracts, flow, and runtime boundaries must remain independent. V30 UI routing is role-aware projection over one contract, not V20-style split workbench pages.

## Practical Mainline Reference

The core Bazi calculation mainline is sealed for current scope. The controlling task plan for the active support-system completion work is:

```text
docs/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md
docs/V30_MULTI_USER_TERMINAL_LOCALE_PRODUCTIZATION_MAINLINE.md
docs/V30_BAZI_LLM_CONTEXT_AND_PROMPT_MAINLINE.md
docs/V30_BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE.md
docs/V30_MAIN_MODULE_COMPLETION_REVIEW.md
docs/V30_UI_PRODUCT_DESIGN_PLAN.md
docs/V30_UNIFIED_INTERACTION_BRAIN_PLAN.md
docs/V30_PRACTICAL_BAZI_MAINLINE_PLAN.md
docs/V30_CORE_BAZI_EIGHT_MODULE_PLAN.md
docs/V30_M1_M2_BAZI_CALCULATION_FACT_LAYER_COMPLETION_PLAN.md
```

`V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md` records the completed intelligent central brain, training/auto-apply system, synthetic validation, and 518K support layer. `V30_MULTI_USER_TERMINAL_LOCALE_PRODUCTIZATION_MAINLINE.md` records the current productization steady state. `V30_BAZI_LLM_CONTEXT_AND_PROMPT_MAINLINE.md` records the BL1-BL8 Bazi LLM steady state. `V30_BAZI_INTELLIGENCE_REQUIREMENTS_COVERAGE.md` records the integrated IR1 requirements coverage gate. `V30_CORE_BAZI_EIGHT_MODULE_PLAN.md` remains the sealed record for the eight core Bazi calculation modules.
`V30_MAIN_MODULE_COMPLETION_REVIEW.md` records MCR1 and the next selected mainline after IQ5. `V30_UI_PRODUCT_DESIGN_PLAN.md` records the product UI split between Reading Shell and Admin Shell, using V20 only as a reference source; UI1-UI7 now close the first usable V30 UI surface for customer Bazi calculation plus admin LLM/training/validation observation. `V30_UNIFIED_INTERACTION_BRAIN_PLAN.md` records the active UIB mainline that merges intelligent Q&A and hidden-factor calibration into one constrained dialogue with structured inputs and pollution guards.

Validation cadence is controlled by the same plan: normal subtasks use targeted tests and the affected synthetic tier; full `pytest -q`, synthetic all, and 518K sample are reserved for major gates, module milestones, policy-affecting changes, or release/pointer promotion.

Current active chain:

```text
BirthInput
-> Deterministic Chart Facts
-> Evidence/Structure Spine
-> TenGodEnergyModel
-> Strength/Structure/UsefulGod Ranked Decisions
-> Practical Reading
-> Customer Presentation
-> Structured Interaction / Answer
-> Validation / Policy Pointer
```

Current active task:

```text
U5 Productization Closeout completed; current state U-S1 Productization Steady State
-> BT10 Unified Brain / Training / Synthetic Closeout completed; current state BT-S1 Support Systems Steady State
-> S1 Business Acceptance Steady State completed and business Bazi acceptance is waiting for new evidence
-> active productization plan is docs/V30_MULTI_USER_TERMINAL_LOCALE_PRODUCTIZATION_MAINLINE.md
-> active support-system completion plan is docs/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md
-> U1 accepted role-locale-client projection readiness: 72/72 combinations projected, 7/7 checks passed
-> guest/user remain sanitized on every terminal, including admin/lab clients
-> diagnostic actions and diagnostics are role-gated to practitioner/analyst/admin/lab
-> U2 accepted session owner boundary readiness: 7/7 checks passed; customer history requires actor+session, diagnostic roles retain role-gated owner-scope inspection
-> U3 accepted locale terminology readiness: 7/7 checks passed; zh/en/ko Bazi terms are covered, fallback count is zero, and locale projection does not change chart facts
-> U4 accepted terminal contract freeze: 8/8 checks passed; web/mobile/admin/lab required projection fields and terminal visibility/action contracts are frozen
-> U5 accepted productization closeout: 5/5 checks passed; U1-U4 evidence is accepted and U-S1 steady state is active
-> full login, payment, membership, organization permissions, and complete UI redesign remain explicit non-goals
-> BT1 accepted central brain as read-only runtime coordinator: 5/5 checks passed
-> BT2 accepted long-session brain replay: 6/6 checks passed
-> BT3 accepted brain failure routing as operator-only diagnostic queue: 6/6 checks passed
-> BT4 accepted training system closeout: 8/8 checks passed for core policy families, validation replay, artifacts, pointers, question comparison, lineage, rollback metadata, and future-family boundaries
-> BT5 accepted failed-candidate quarantine: 8/8 checks passed for source signals, failed validations, rollback target, persisted quarantine artifact, diagnostic remediation route, unchanged pointer, and last-good runtime usage
-> BT6 accepted synthetic coverage manifest: 7/7 checks passed for implemented/planned tiers, protected contracts, module scopes, major-node-only tiers, and no-truth-claim/no-chart-mutation boundaries
-> BT7 accepted central_brain synthetic tier: 5/5 cases passed for role/session/hidden-factor/expression/training-route/no-mutation contracts
-> BT8 accepted training_pipeline synthetic tier: 91/91 cases passed and required training signal families are extractable with no-chart-fact boundaries
-> BT9 accepted 518K readiness matrix: 7/7 checks passed for sample/shard/full-boundary/artifact/search/candidate-family readiness
-> BT10 accepted unified support-system closeout: 6/6 checks passed; central brain 100%, training 100%, synthetic validation 100%, 518K validation support 95%
-> support systems are now steady-state; reopen only on new evidence, explicit major validation, policy promotion, or release-boundary work
-> BL1-BL3 accepted Bazi LLM context/prompt/role foundation: task-specific context packs, role contracts for guest/user/practitioner/analyst/admin/lab, prompt contracts, budget/module/role gate, CLI, admin endpoint, and targeted tests
-> BL4 accepted customer Bazi reading LLM answer generator: runtime answer metadata carries task/role/context/prompt contracts, customer initial reading and domain follow-up are routed through Bazi prompt requests, and rule-bound fallback is preserved
-> BL5 accepted Bazi LLM output acceptance gate: schema-valid fake-provider outputs can replace rule-bound text, while missing schema fields, customer role leaks, and drift failures fallback without chart-fact mutation
-> BL6 accepted Bazi LLM training signals and synthetic tier: `bazi_llm_acceptance` passes 5/5, training signal targets expression/question strategy only, and live LLM/full synthetic/all/518K remain unnecessary
-> BL7 accepted Bazi LLM role/locale production smoke: guest/user/practitioner x zh/en/ko pass with disabled-provider fallback, customer diagnostics hidden, practitioner dense context, locale terminology boundaries, and no policy pointer writes
-> BL8 accepted Bazi LLM closeout: BL1-BL7 evidence is accepted, BL-S1 steady state is active, default validation is non-live/lightweight, and optional live provider smoke is explicit-only
-> IR1 accepted integrated Bazi intelligence requirements coverage: 6/6 checks passed across core module chain, role/locale projection, continuous Q&A, hidden-factor feedback, Bazi LLM expression, training/synthetic, and read-only boundaries
-> IR2 accepted backend API journey coverage: 6/6 checks passed across create reading, role views, answer refresh, hidden-factor feedback/state, history boundaries, and IR1 admin gate
-> IQ1 accepted intelligent question interaction audit: 8/8 checks passed for Bazi-tailored question priority, module-backed strategy, non-template evidence contracts, chained follow-up, trainability, role split, LLM context, and core-calculation boundary
-> IQ2 accepted model-signal question training readiness: 5/5 checks passed; `interaction_loop` 5/5 emits `v30.training_signal.question_model_signal_personalization`, which can tune question strategy but cannot mutate chart facts
-> IQ3 accepted model-signal question policy candidate: auto-training emits guarded `question_policy.weights.model_signal_question_policy`, F2 candidate review detects it, synthetic all override passed 100/100, and promotion path targeted tests passed
-> IQ4 accepted intelligent question chain readiness: 6/6 checks passed for two-turn chain memory, core Bazi no-mutation, multi-role projection, LLM follow-up context, trainability, and business-reading focus
-> IQ5 accepted intelligent question closeout: 6/6 checks passed; visible questions, structured options, internal calibration, LLM follow-up context, question-policy training candidates, and no-mutation boundaries are closed
-> IQ-S1 Question Intelligence Steady State is active
-> MCR1 accepted main module completion review: 5/5 checks passed; M1-M8, IQ, BT, U, and BL are steady/bounded steady, and it selected MCR2, which is now completed
-> MCR2 accepted customer surface and BaziContext reconciliation: 6/6 checks passed; customer surface and internal BaziContext accounting are steady 100%, with diagnostics role-gated and customer leak checks intact
-> IR-S1 Integrated Bazi Intelligence Steady State remains active; M3-G1 now owns source-governed M3 depth and calibration tags
-> do not reopen M1-M8 deterministic chart facts
-> do not start UI polish, dashboard expansion, release work, or auth work unless explicitly selected as a new mainline
-> C1-C8 are complete and frozen for the current core Bazi calculation scope
-> F1 frozen-core calibration baseline passed with 6 tiers and 31 training signals
-> F2 candidate review produced 4 read-only candidate tracks
-> F3 validation gate passed synthetic all 95/95 and 518K sample 8 cases with candidate overrides
-> F4 pointer review found 4 diffs ready for explicit operator decision
-> F5 recorded operator_decision=defer and pointer_write=false
-> F6 closed targeted calibration with no promotion and 4 monitoring checks
-> M0 selected R13 external-release dry run while full pytest remains explicit, not default
-> R13 recorded external-release dry run with full pytest deferred and pointer promotion disabled
-> R14 recorded full pytest defer; external release remains blocked
-> R15 recorded release blockers and keeps external release blocked pending full pytest
-> R16 paused release-boundary work without running full pytest
-> M0 after release pause selected P0 core monitoring/calibration
-> P0 established the read-only core monitoring loop with 4/4 monitoring checks
-> P1 passed 4/4 lightweight monitoring checks with no regression detected
-> P2 summarized 4 stable calibration observations with no focused module fix required
-> P3 established on-new-evidence drift watch with no drift detected and no focused module fix required
-> P4 established focused evidence queue with 0 queued evidence and module-target batching
-> P5 reviewed 0 queued modules and found no focused fix candidate
-> P6 closed the current empty watch cycle and kept future monitoring ready
-> P7 established cadence=on_new_calibration_evidence_only and routes future evidence through P4/P5
-> P8 synced cadence across required controlling docs
-> P9 entered steady state and waits for new calibration evidence
-> S0 status recorded: no default next core-monitoring task
-> B1 accepted the ready real-case BirthInput-to-customer-reading path: 12/12 business acceptance rows passed
-> B2 expanded business reading regression: 24/24 ready rows passed and M8 projects five concise domain cards
-> B3 accepted answer refresh regression: 5/5 structured answer refresh rows passed without chart-fact mutation
-> B4 accepted pending/blocked BirthInput boundary regression: 5/5 rows passed without fake chart facts
-> B5 froze B1-B4 as the minimum business reading API acceptance contract: 4/4 gates passed
-> B6 closed B-track: B1-B5 are the default business acceptance gate and further major validation requires explicit request
-> S1 entered business acceptance steady state: 5/5 checks passed, routine gate is B1-B5, and no further B-track task starts by default
-> keep first-screen core calculation result before questions
-> questions, hidden factors, LLM, training, and 518K remain auxiliary tracks
-> hidden factors only feed feedback/calibration signals, not deterministic chart facts
-> training signals tune model weights, question strategy, and expression, not deterministic chart facts
```

## Current Completion Snapshot

| Track | Completion | Review |
|---|---:|---|
| Runtime product spine | 97% | API/UI/readings/view/answer/projection/actor-session hooks, read-history ownership contract, additive API projection contract, customer leak scan, release-gated API smoke, and live 9030 smoke are connected. |
| Bazi reasoning spine | 100% | C7 complete for the current core scope: evidence, rules, K/R/P, structure graph, model-signal path adjustment, mainline arbitration, and M4/M5/M6 support proof are integrated. |
| Practical calculation | 100% | C7 complete for the current core-calculation scope: deterministic chart facts, base fact explanation, M3 evidence spine, M4 model signals, M5 ranked decisions, M6 practical output, M7 calibration, and M8 projection pass the integrated core gate. |
| Interaction and LLM | 98% | Structured options, question graph, interaction state, answer refresh, model-signal personalized question priority, IQ1-IQ5 accepted, IQ-S1 steady state active, bounded LLM fallback/acceptance, release-gated LLM live smoke, failure telemetry, no-mutation proof, BL1-BL8 closeout exist. |
| Training and validation | 99% | C7 integrated gate passed compileall, synthetic all 95/95, 518K sample 8 cases, and targeted core pytest 38/38; B1-B6 and S1 passed; BL8 closeout passed; IR1 integrated requirements coverage passed 6/6; IR2 backend API journey passed 6/6; IQ3 emits and promotes trainable question personalization policy candidates; external full pytest and release promotion remain separate. |
| Role/session/client/locale productization | 100% | U5 complete: U1-U4 evidence is accepted, current-scope multi-user/session/terminal/locale productization is in U-S1 steady state, and full login/UI redesign remain explicit non-goals. |

## Core Bazi Calculation Priority

The modules that directly support Bazi calculation now take precedence over interaction and diagnostics:

| Core calculation module | Completion | Current judgment |
|---|---:|---|
| BirthInput and deterministic chart facts | 100% | C5/C7 complete: solar/lunar/leap-month/true-solar/unknown-hour/invalid-input boundaries, solar-term/year-month fixture coverage, canonical real-case fact fixtures, luck/flow/six-pillar context, base fact summary, no-fake-fact guardrails, and downstream no-mutation proof are active. |
| Bazi base fact explanation layer | 100% | C5/C7 complete: four pillars, ten gods, hidden stems, five elements, relation families, root/vault facts, fact integrity, customer-safe base explanations, M5/M6 consumption proof, and canonical category coverage are first-class in `core_bazi_reading`. |
| Feature/rule/knowledge/structure spine | 100% | C6/C7 complete: source registry, V20 reference assets, K/R/P units, rule/counter-evidence gates, portrait features, mechanism graph, dynamic graph, mainline arbitration, and M4/M5/M6 support proof form one auditable spine. |
| Ten-god energy model | 100% | C2/C7 complete: model signal is active across structure, ranked decisions, answer context, training, diagnostics, dedicated calibration tier, five-family band coverage, interface contract, calibration profile, real-case replay, and auto-training model-signal weights. |
| Strength/structure/useful-god ranked decisions | 100% | C2/C7 complete: unified candidate scoring basis, follow/disputed/regulation candidates, real-case fixtures, score floors, M5 replay weights, useful-god evidence calibration, auto-training policy weights, M1/M2 root/vault consumption, M4 interface/calibration consumption, and no-raw-score contract are active. |
| Practical reading output | 100% | C1/C7 complete: career, wealth, relationship, health, and timing readings expose calculation basis, M5 decision links, M4 signal bands, evidence ids, explanation units, domain insights, action steps, calibration prompts, blocked claims, and quality contracts without raw model-score exposure. |
| Customer reading and presentation | 100% | C4/C7/B2 complete: customer surface is core-calculation-first, five concise business domain cards are projected while three focus domains drive priority, next-question and answer-panel projection are sanitized, diagnostics are role-gated, and `v30.api_projection_contract.v1` preserves additive API fields. |

Question recommendation, hidden-factor discovery, LLM expression, training, synthetic validation, and 518K validation support this chain. They must not become the first-screen product surface or mutate chart facts.

## Mainline Execution Plan

### P7 Model Fusion

Deliverables:

- [x] `model_signal_summary` contract for ten-god energy, stability, volatility, confidence, and boundaries.
- [x] Strength, structure, and useful-god ranked decisions consume model signals through one scoring boundary.
- [x] Answer context, synthetic observation, training extraction, and admin diagnostics reuse the same summary.
- [x] Customer surface receives explanation only, not raw model scores.
- [x] Structure path scoring consumes model-signal bands as bounded path-score diagnostics.
- [x] Auto-training can generate `structure_policy.weights.dynamic_graph.model_signal_fusion`.
- [x] First tuning stays under `structure_policy`; `model_signal_policy` remains a future split decision.

Validation:

- Ten-god fusion unit tests.
- Ranked decision fusion tests.
- Synthetic signal extraction for `v30.training_signal.ten_god_energy_fusion`.
- Synthetic signal extraction for `v30.training_signal.ranked_decision_fusion`.

### P8 Structured Interaction Hardening

Deliverables:

- [x] `interaction_stage`, `selected_domain`, `answered_question_ids`, `selected_option_ids`, `visible_next_question_id`, `internal_next_question_id`, and `followup_reason`.
- [x] `QuestionDialogueGraph` owns internal strategy; presentation owns customer-visible projection.
- [x] Existing API fields remain additive and backward compatible.
- [x] Synthetic/training extraction emits interaction state and loop quality signals.
- [x] Question-policy auto-training candidates include `interaction_followup_policy`.
- [x] Add a dedicated synthetic `interaction_loop` tier with direct-click/domain-choice/hidden-calibration cases.

Validation:

- Interaction state machine unit tests.
- Synthetic `interaction_loop` tier.
- Role projection tests proving guest/user never see internal calibration as the default next action.

### P9 Real-case Calibration

Deliverables:

- Canonical fixture pack for solar, lunar, leap-month lunar, true-solar, unknown-hour, and unknown-gender cases.
- Calibration checks for luck-cycle, flow-year/month, six-pillar, ten-god energy, ranked decisions, and question order.
- No fixture hard-codes final fortune verdicts or chart conclusions beyond deterministic facts.

Validation:

- `real_case_calibration_pack` synthetic tier.
- Release-gate summary fields for calibration coverage.

Current status:

- Dedicated `real_case_calibration_pack` tier is phase sealed with 30 fixtures covering solar, lunar, leap-month lunar, true-solar, unknown-hour, unknown-gender, invalid date/time, M4 signal bands, M5 ranked candidates, and M6 practical reading contracts.
- Training extraction emits `v30.training_signal.real_case_calibration_pack`.

### P10 Minimal User/Session Foundation

Deliverables:

- Minimal read-history API around current `actor_id/session_id`.
- Durable session-state ownership rules.
- Unified presentation projection remains the only role surface.

Validation:

- Storage/repository contract tests are active for memory, local JSON, and Postgres adapters.
- API projection tests verify user history hides diagnostics while admin history keeps actor/internal next-question diagnostics.

## Parallel Execution Plan

The next slice should advance framework, modules, training, and synthetic validation together instead of waiting for one track to finish first.

| Workstream | Owner module | Deliverable | Validation |
|---|---|---|---|
| Framework contract | `v30/contracts.py`, runtime result, presentation diagnostics | Additive contracts for `model_signal_summary`, interaction state, real-case calibration metadata, and session/history hooks. | Contract/unit tests plus no UI-facing field removals. |
| Model fusion | ten-god energy, structure, ranked decisions | Ten-god energy/stability/volatility influence strength, structure, and useful-god candidates through one bounded scoring boundary, with dedicated M4 calibration and M5 replay signals active. | `ten_god_energy_calibration`, `ten_god_energy_fusion`, `m5_weight_replay`, and ranked-decision synthetic checks. |
| Interaction state | question graph, answer endpoint, presentation | Persist stage/domain/answered ids and separate visible next question from internal strategy. | `interaction_loop` synthetic tier and role projection tests. |
| Training | synthetic extraction, policy candidate generation | Emit model-fusion, ranked-decision, M5 replay, interaction-loop, and real-case calibration training signals. | Domain tiers for subtask gates; synthetic all + 518K sample before major pointer activation. |
| Synthetic validation | validation suites | Add fixed P7/P8/P9 cases first; generator remains a later task. | smoke/all plus domain tiers. |
| 518K validation | corpus runner and artifacts | Coverage fields for model-signal, interaction-state, visible/internal split, and calibration-probe leak checks. | sample and selected shard gates. |
| Session foundation | repository/API/presentation | Minimal read-history contract using actor/session hooks, no full login. | repository and projection contract tests are active. |

Execution order inside the slice:

```text
1. Define additive contracts
2. Add fixed synthetic cases for the intended behavior
3. Implement module/runtime behavior
4. Extract training signals
5. Run synthetic smoke/all and targeted unit gates
6. Run 518K sample for policy-affecting changes
7. Update completion docs and promotion notes
```

Non-P0 work must state why it directly serves the practical Bazi calculation mainline.

## Mainline Definition

The V30 mainline is:

```text
User or validation input
-> Actor/Session Context
-> V30 ChartContext
-> TenGodEnergyModel
-> Evidence and structure runtime
-> Strength/structure/useful-god ranked candidates
-> Mainline and question intelligence
-> Expression and central brain orchestration
-> Role-aware answer/presentation
-> Trace and feedback
-> Training and validation
-> Runtime pointer auto-apply
```

This mainline is the development order. Subsystems can be designed in parallel, but implementation should keep this order.

## Five System Tracks

### Track A: Runtime Product Track

Purpose: keep V30 independently usable.

Scope:

- API `/api/v30`.
- UI `/v30/ui`.
- Reading creation.
- Actor/session as the identity hook.
- View model.
- Role presentation.
- Runtime health.
- Deployment/nginx/systemd.

Primary docs:

- `V30_SCAFFOLD.md`
- `V30_ROADMAP.md`
- `V30_TEST_ARCHITECTURE.md`

First milestone:

```text
create reading -> view reading -> answer bound question -> record trace
```

### Track B: Bazi Reasoning Track

Purpose: build the actual Bazi intelligence core.

Scope:

- Chart context.
- Original chart.
- Luck cycle.
- Annual flow.
- Ten-god energy and stability model.
- Ten-god energy fusion into strength, structure, and useful-god candidate ranking.
- Feature evidence.
- Knowledge packs.
- Rule evidence.
- Portrait model.
- Structure dynamics.
- Mainline arbitration.

Primary docs:

- `V30_MODULE_REVIEW.md`
- `V30_ALGORITHM_AND_MODELING_REVIEW.md`
- `V30_INTEGRATED_BAZI_MODEL_PIPELINE.md`

First milestone:

```text
ChartContext -> FeatureEvidence -> StructureState -> MainlineState
```

### Track C: Training and Validation Track

Purpose: make V30 self-improving without heavy default tests.

Scope:

- Synthetic Bazi cases.
- Training runs.
- Validation runs.
- Policy candidates.
- Policy artifacts.
- Runtime pointers.
- 518K sample/shard/full validation.
- DB-backed 518K artifact search with JSON fallback.
- Auto-apply after validation.

Primary docs:

- `V30_TRAINING_ARCHITECTURE.md`
- `V30_SYNTHETIC_VALIDATION.md`
- `V30_518K_VALIDATION_PLAN.md`

First milestone:

```text
SyntheticBaziCase -> validation result -> policy candidate -> runtime pointer
```

### Track D: Interaction and LLM Track

Purpose: turn Bazi reasoning into useful dialogue and answers.

Scope:

- Seed questions.
- Question intents.
- Question recommendations.
- Question anchors.
- User-facing question layer.
- Structured interaction options.
- Explicit interaction state machine.
- Hidden factor hypotheses.
- Boundary and special-year discovery questions.
- Role-aware rendering.
- Expression orchestration.
- Central brain coordination.
- Answer context.
- LLM role contracts.
- Drift checks.

Primary docs:

- `V30_QUESTION_INTELLIGENCE.md`
- `V30_LLM_CONTEXT_AND_ROLES.md`
- `V30_HIDDEN_FACTORS_AND_DIALOGUE_DISCOVERY.md`

First milestone:

```text
MainlineState -> user question anchor -> AnswerContext -> Expression -> CentralBrainTrace -> role-aware answer -> next question
```

Current status:

- `v30.expression` produces expression plans and rendered narratives.
- `v30.brain` produces central brain trace, runtime planner decision, question dialogue strategy, expression orchestration, and training signal routes.
- `v30.brain` now also produces session memory, role state, and feedback strategy.
- Admin/analyst/lab presentation diagnostics consume central brain coordination output.
- Question recommendations now consume central brain unknown context, feedback slots, and question strategy.
- Guest/user presentation now shows user-facing Bazi questions by default, while hidden factor/useful-god/structure calibration probes stay diagnostic or optional.
- Answered user questions are suppressed so the visible next question changes.
- Expression plans can consume central brain role state for role density and voice.
- Adaptive question diagnostics now replay central-brain/question-policy decisions from runtime traces.
- `/api/v30/admin/runs/{reading_id}/question-replay` exposes question decision drilldown without mutating runtime state.
- Adaptive question replay diagnostics now feed bounded `question_policy` candidate weights through auto-training.
- Question-policy promotion now writes active-vs-candidate comparison artifacts for rank, score, policy-weight, and reason deltas.
- Unified validation artifact discovery now covers 518K artifacts and question-policy comparison artifacts.
- Promotion lineage diagnostics now connect policy artifacts, validation artifacts, runtime pointers, rollback metadata, and active runtime trace consumption.
- The central brain coordinates only; it does not mutate chart facts, structure scoring, storage, Redis, or policy pointers.

Training/validation status:

- 518K sample and shard gates persist JSON artifacts and indexes.
- 518K runs now also upsert searchable `v30_artifacts` records when Postgres is configured.
- `/api/v30/admin/validation/518k/artifacts` exposes validation artifact search with JSON fallback.
- Release gate summaries include artifact record IDs and search backend metadata.

### Track E: Engineering Quality Track

Purpose: keep V30 maintainable under high iteration.

Scope:

- Test tiers.
- Runtime isolation guards.
- Storage isolation.
- Redis isolation.
- Doc updates.
- Release gate.
- Observability.
- Artifact lineage.

Primary docs:

- `V30_TEST_ARCHITECTURE.md`
- `V30_ROADMAP.md`
- `V30_TRAINING_ARCHITECTURE.md`

First milestone:

```text
fast default tests + runtime smoke + synthetic smoke
```

## Development Order

V30 should not implement every track fully before moving on. It should build thin vertical slices.

### Slice 1: Independent Thin Runtime

Goal: V30 is independently reachable and has a small contract loop.

Status: mostly complete.

Includes:

- API.
- UI.
- Health.
- Smoke runtime.
- Storage naming guards.
- No V20 runtime imports.

Exit criteria:

- `/api/v30/health` works.
- `/v30/ui/` works through domain.
- Default tests pass quickly.

### Slice 2: Real Core Context

Goal: replace smoke facts with deterministic Bazi core facts.

Current active mapping: `P8.2 + P9.1 Mainline Validation And Calibration` in `V30_PRACTICAL_BAZI_MAINLINE_PLAN.md`.

Includes:

- Chart context schema.
- Pillar model.
- Ten gods.
- Elements.
- Time layers.
- Missing time handling.
- Core fixture tests.

Exit criteria:

- Converted V20 core cases pass.
- No downstream module mutates chart facts.

### Slice 3: Evidence and Structure Spine

Goal: create the first real reasoning spine.

Includes:

- Feature evidence compiler.
- Rule evidence skeleton.
- Structure graph skeleton.
- Structure state.
- Mainline state.

Exit criteria:

- At least 10 synthetic structure cases pass.
- Structure output is evidence-bound.
- Mainline explains selection.

### Slice 4: Synthetic Validation and Runtime Pointer Base

Goal: introduce self-training infrastructure early.

Includes:

- `SyntheticBaziCase` schema.
- Synthetic validation runner.
- Policy candidate schema.
- Runtime pointer schema.
- First policy family: `structure_policy`.

Exit criteria:

- Synthetic validation can reject and accept candidates.
- Passing candidate can auto-apply through V30 pointer.
- Default pytest remains fast.

### Slice 5: Knowledge, Rules, Portraits Integration

Goal: integrate the domain modeling system after the validation loop exists.

Includes:

- Knowledge pack schema.
- Rule catalog schema.
- Portrait dimensions.
- Integrated validation checks.
- Parameter family tuning.

Exit criteria:

- Knowledge/rule/portrait changes cannot promote without synthetic validation.
- 518K sample validation can run outside default tests.

### Slice 6: Intelligent Question Recommendation

Goal: replace template question behavior with context-bound recommendation.

Includes:

- Seed question schema.
- Question intent.
- Recommendation scoring.
- Anchors.
- Role visibility.
- Question policy.

Exit criteria:

- User-visible questions are bound anchors only.
- Recommendation explains evidence and information gain.
- Synthetic question cases pass.

### Slice 7: LLM Role System

Goal: let LLM do more, through contracts.

Includes:

- Answer context.
- Role context.
- Prompt policy.
- Output contracts.
- Drift checks.
- Optional live LLM smoke tier.

Exit criteria:

- LLM answers use structured context.
- Role output is testable.
- LLM cannot change facts, structure, mainline, or pointers.

### Slice 8: 518K Validation and Release Gate

Goal: support broad distribution validation and release confidence.

Includes:

- 518K sample mode.
- Shard mode.
- Full mode.
- Coverage metrics.
- Drift metrics.
- Release gate runner.

Exit criteria:

- 518K sample can gate policy promotion.
- Full validation is explicit only.
- Release gate composes fast and heavy tiers intentionally.

## Task Ledger

### P0: Already Done

- [x] V30 scaffold.
- [x] API prefix `/api/v30`.
- [x] UI prefix `/v30/ui`.
- [x] Runtime directory `.runtime`.
- [x] Storage naming guards.
- [x] No `v20.*` import test.
- [x] Domain nginx route to V30.
- [x] Initial topic docs.

### P1: Master Planning

- [x] Create master mainline plan.
- [x] Create runtime pointer design doc.
- [x] Create knowledge/rule/portrait plan doc.
- [x] Create structure dynamics design doc.
- [x] Create system service/deployment doc.

### P2: V20 Deep Review

- [x] Review V20 core chart modules.
- [ ] Review V20 feature compiler and calibration modules.
- [x] Review V20 rules and defeasible reasoning modules.
- [x] Review V20 knowledge loader and rule library modules.
- [x] Review V20 structure dynamics graph modules.
- [ ] Review V20 portrait ontology/projection modules.
- [ ] Review V20 question DAG/ranker/anchor modules.
- [ ] Review V20 dialogue, feedback, and calibration modules for hidden factor discovery.
- [ ] Review V20 learning runtime pointer modules.
- [ ] Review V20 synthetic and 518K corpus modules.
- [ ] Review V20 LLM prompt/context/enforcement modules.

### P3: First Implementation Slice

- [x] Implement V30 core chart context.
- [x] Add V30 core fixtures.
- [x] Convert first V20 core cases into V30 test fixtures.
- [x] Add unit tests for ten gods, elements, relationships, and time layers.
- [x] Keep default tests under a fast target.

### P4: First Validation Slice

- [x] Define `SyntheticBaziCase`.
- [ ] Define synthetic case generator constraints.
- [x] Add positive prototype cases.
- [x] Add negative counter cases.
- [x] Add metamorphic pair cases.
- [x] Add boundary gradient cases.
- [x] Add composite conflict cases.
- [x] Add synthetic validation smoke runner.
- [x] Add synthetic validation gradient runner.
- [x] Add candidate policy payload injection for synthetic promotion gates.
- [x] Add role-aware portrait projection view validation and training signal extraction.
- [x] Add four-task LLM output contract validation for answer, question explanation, synthetic case draft, and failure summary tasks.
- [x] Convert hidden-factor event-year alignment training signals into conservative feedback-conditioned policy weights.
- [x] Add bounded 通关/制化 path-resolution supports, K/R/P units, structure metrics, and training weights.
- [x] Feed expression-rendered question labels into presentation models.
- [x] Expand per-unit parameter tuning beyond question policy into rule and structure policy weights.

### P5: First Training Slice

- [x] Define policy candidate schema.
- [x] Define policy artifact schema.
- [x] Define runtime pointer schema.
- [x] Implement baseline `structure_policy` pointer.
- [x] Implement local auto-apply after synthetic smoke validation.
- [x] Implement rollback metadata.
- [x] Add manual promotion script for `structure_policy`.

### P6: First Reasoning Slice

- [x] Implement feature evidence compiler.
- [x] Implement rule evidence skeleton.
- [x] Implement structure state skeleton.
- [x] Implement mainline state skeleton.
- [x] Validate with 10 synthetic cases across smoke and gradient tiers.

### P7: Question and LLM Slice

- [ ] Define question seed schema.
- [ ] Define question intent schema.
- [ ] Define hidden attribute schema.
- [ ] Define amplification factor schema.
- [x] Implement question anchor binding.
- [ ] Implement first recommendation scorer.
- [ ] Define answer context schema.
- [ ] Define LLM task contracts.
- [ ] Add drift checker skeleton.

### P8: 518K and Release Slice

- [ ] Locate canonical 518K source.
- [x] Define V30 corpus case summary.
- [x] Implement sample validation runner.
- [x] Implement shard validation runner.
- [x] Add candidate policy payload injection for 518K replay.
- [x] Add 518K sample gate to policy promotion.
- [x] Verify selected shard replay outside default tests.
- [x] Define release gate runner.
- [x] Connect release gate to selected tiers.

### P9: Storage Adapter Slice

- [x] Define V30 Postgres SQL/table boundary.
- [x] Define V30 database URL isolation guard.
- [x] Define V30 Redis keyspace/cache boundary.
- [x] Add storage adapter tests without live DB/Redis.
- [x] Add runtime repository factory.
- [x] Add memory runtime repository.
- [x] Add local JSON runtime repository.
- [x] Add Postgres runtime repository boundary.
- [ ] Add live Postgres integration test behind marker.
- [ ] Add live Redis integration test behind marker.
- [x] Persist readings through repository in API.
- [x] Persist runtime traces through repository in API.
- [x] Wire API to Redis runtime cache when `V30_REDIS_URL` is configured.
- [x] Add real environment Postgres/Redis smoke script.
- [x] Run live Redis smoke against host service.
- [x] Add Docker Postgres bootstrap script for independent `qiazhi_v30` database/user.
- [x] Run real Docker Postgres/Redis smoke against host services.
- [x] Start V30 API with `repository=postgres` and `redis_cache=true`.
- [x] Add auto-apply training loop for core runtime policy families.
- [x] Add API endpoint for validation-driven immediate training application.
- [x] Verify runtime traces show newly active trained policy versions.
- [x] Add evidence-driven scored question recommendation plan.
- [x] Expose question recommendation score/stage/topic/reasons in runtime view.
- [x] Add hidden factor dialogue discovery probe.
- [x] Add hidden factor recommendation question without deterministic hidden-factor claim.
- [x] Add hidden factor dialogue discovery to synthetic smoke validation.
- [x] Add locale projection for `zh`, `en`, and `ko`.
- [x] Add client profiles for `web`, `mobile`, and `admin`.
- [x] Expose admin diagnostics and training actions in presentation projection.
- [x] Add V30-owned knowledge/rule/portrait seed registry.
- [x] Emit bound knowledge/rule/portrait signals into runtime trace.
- [x] Add knowledge/rule/portrait signal case to synthetic smoke validation.
- [x] Consume knowledge/rule/portrait signals in structure path scores and graph nodes.
- [x] Consume knowledge/rule/portrait signals in mainline support and question recommendation reasons.
- [x] Add structure mechanism path graph v1.
- [x] Consume mechanism paths in mainline and question recommendation.
- [x] Add mechanism path checks to synthetic smoke validation.
- [x] Load active structure_policy artifact payload at runtime.
- [x] Apply structure_policy weights to mechanism path scores.
- [x] Generate structure_policy weights through auto-training.
- [x] Load active question_policy artifact payload at runtime.
- [x] Apply question_policy weights to recommendation scores/order.
- [x] Generate question_policy weights through auto-training.

## Design Rules for Every Task

Every task must answer before implementation:

- Which V30 contract does it support?
- Which track does it belong to?
- Which slice does it unblock?
- Which V20 assets were reviewed?
- Which tests are default?
- Which validations are explicit?
- Which runtime pointer, if any, can it affect?
- What Markdown document must be updated?

## Current Priority

The next concrete work should be:

1. Keep live Postgres and Redis integration tests behind explicit markers.
2. Return to larger algorithm/modeling work only after the minimal runtime chain can be persisted and pointer-driven.

This prevents V30 from starting with an isolated subsystem instead of the whole system mainline.

## Near-Term Alignment Rule

The repository implementation step completed:

```text
Runtime trace repository persistence
```

Rationale:

- Runtime trace persistence completes the current P9 repository slice without starting a new subsystem.
- Runtime pointers define how validated policies will apply without manual review.
- Postgres and Redis should persist a meaningful reading/trace/pointer model, not an incomplete smoke payload.

Do not start these larger branches before the three steps above:

- Real structure graph algorithm.
- Knowledge/rule/portrait integration.
- Synthetic validation runner.
- 518K validation.
- Full question intelligence.
- LLM role expansion.

Those branches remain designed, but they should build on the completed chain:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> BaziQuestionAnchor
-> RuntimePointer
-> Storage/Cache
```
