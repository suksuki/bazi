# V30 Practical Bazi Mainline Plan

Updated: 2026-05-24

## North Star

V30 current mainline prioritizes `Core Bazi Calculation First`: deterministic calculation, customer-visible chart facts, evidence-bound structure judgment, ranked strength/structure/useful-god candidates, practical reading output, and then high-value questions, bounded LLM expression, and silent training validation.

The active product path is:

```text
BirthInput
-> Calendar Conversion Trace
-> Deterministic Chart Facts
-> Base Bazi Fact Explanation
-> Evidence / Structure Spine
-> TenGodEnergyModel
-> Strength / Structure / Useful-god Ranked Decisions
-> Practical Reading Context
-> Customer Reading Surface
-> User-Facing Recommended Questions
-> Direct Answer / Structured Option Feedback
-> QuestionDialogueGraph-selected Next Question
-> Refreshed Answer Context
-> Bounded LLM / Rule Fallback Answer
-> Synthetic / 518K / Real Case Validation
-> Policy Candidate
-> Runtime Pointer
```

The runtime may train policy weights, thresholds, candidate ordering, question strategy, and expression strategy. It must not train, generate, or mutate deterministic chart facts.

The strict module-by-module execution plan is:

```text
docs/V30_CORE_BAZI_EIGHT_MODULE_PLAN.md
```

After every completed task, update that plan first, then sync this document and the module review if completion, validation, or next-task status changed.

Validation cadence follows that plan. Do not run full `pytest -q`, synthetic all, or 518K sample for every small subtask; use targeted unit tests plus the directly affected synthetic tier, and reserve full gates for major module milestones or policy/release boundaries.

## Current Mainline Priority

| Priority | Task | Status | Completion |
|---|---|---|---:|
| P0 | BirthInput to deterministic chart facts | phase sealed; solar-term/year-month fixture, canonical M1/M2 real-case facts, synthetic, and base-fact training gates active | 95% |
| P1 | Four pillars, ten gods, five elements, hidden stems, relations, root/vault facts, luck/flow, and six-pillar base presentation | phase sealed with `core_bazi_reading`, `fact_integrity`, base explanations, and category coverage | 92% |
| P2 | Strength, structure pattern, and useful-god ranked decision | phase sealed with candidate scoring layer, follow/disputed/regulation candidates, real-case fixtures, replay weights, useful-god evidence calibration, auto-training policy weights, M1/M2 root/vault basis, M4 interface/calibration basis, and no raw model-score leakage | 88% |
| P3 | Practical career, wealth, relationship, health, and timing reading output | phase sealed with calculation basis, M5 decision links, M4 signal bands, evidence ids, explanation units, blocked claims, quality contracts, and no raw model-score exposure | 85% |
| P4 | Core calculation validation, silent training protection, role-locale-client projection, real-case validation, and 518K calculation coverage | active | 95% |
| P5 | Customer Bazi calculation surface and high-value question engine | active | 74% |
| P6 | Interaction, hidden-factor feedback clues, and bounded LLM expression | active; auxiliary to core calculation | 62% |

## Active Task: M1/M2 Bazi Calculation And Base Fact Layer Seal

Goal:

Make the usable customer product loop start with reliable deterministic chart facts and complete base Bazi explanations before M5 judgment or question recommendation. The first screen must show deterministic chart facts, base Bazi explanations, timing context, ranked strength/structure/useful-god candidates, and practical reading summaries before hidden-factor feedback, answer refresh, or LLM expression.

Implementation direction:

- Finish M1/M2 through `docs/archive/V30_M1_M2_BAZI_CALCULATION_FACT_LAYER_COMPLETION_PLAN.md`.
- Keep M1 responsible for BirthInput conversion, chart facts, boundary traces, luck/flow, and six-pillar context.
- Keep M2 responsible for day master, visible/hidden ten gods, hidden stems, five elements, relation families, fact integrity, and base explanations.
- Keep the customer-safe `core_bazi_reading` projection under `reading_surface` concise; internal evidence diagnostics stay behind admin/training projections.
- Include chart build status, four pillars, day master, visible/hidden ten gods, five-element distribution, relation hits, luck/flow/month, six-pillar context, strength/structure/useful-god candidates, and practical domain summaries.
- Keep hidden factors as feedback clues only; they cannot become chart facts or first-screen calculation content.
- Keep API changes additive. Do not remove `reading_surface`, `questions[]`, `answer_panel`, `next_question_id`, `internal_next_question_id`, `actor_context`, or `llm_runtime_status`.
- Continue synthetic, training, real-case, and 518K validation as protection around the core calculation chain.

Required input contract:

- `calendar_type`: `solar` or `lunar`.
- `birth_date`.
- `birth_time`.
- `timezone`.
- Optional `birth_place`.
- Optional `gender`.
- `use_true_solar_time`.
- `unknown_hour`.
- `calendar_assumption`.
- `source`.

Required runtime output:

- `ChartBuildSource`.
- `CalendarConversionTrace`.
- `FourPillarResult`.
- Updated `ChartContext.input_pillars`.
- `LuckCycleContext`.
- `FlowContext`.
- `SixPillarContext`.
- `RankedDecision`.
- `PracticalReadingContext`.
- Customer reading surface.
- High-value question contract.
- Bounded LLM answer draft metadata.
- Agent question flow.
- Interaction state.
- Role-locale-client projection matrix.
- Deterministic chart-fact guardrails.

Required behavior:

- Keep the explicit-pillars entrypoint available for advanced users, tests, fixtures, and migration.
- BirthInput must produce a conversion trace even when the first implementation is partial.
- Unknown birth hour must not create a fake hour pillar.
- Solar-term boundary, late-night/子时 boundary, timezone, and true-solar-time assumptions must be explicitly represented.
- LLM output, user feedback, synthetic case drafts, and training signals cannot create or mutate four-pillar facts.
- Guest/user views must not expose raw structure paths, feature evidence, portrait internals, policy payloads, or training diagnostics.
- Practitioner/admin/lab views may inspect Bazi context through diagnostics.
- Recommended questions must carry purpose, expected information gain, and quality boundary metadata.
- Guest/user recommended questions must be product-facing Bazi questions by default; hidden-factor, useful-god, and structure calibration probes stay diagnostic or optional.
- User choices should be structured where possible; free text is supplemental and cannot mutate chart facts.
- API changes remain additive. Do not remove `reading_surface`, `questions[]`, `answer_panel`, `next_question_id`, `internal_next_question_id`, `actor_context`, or `llm_runtime_status`.
- LLM provider/client must be V30-native. It may read the existing V20-style environment variable shape for migration compatibility, but must not import V20 code or adopt V20 runtime flow.
- LLM can only rewrite expression from `AnswerContext`, customer surface, selected question, and rule answer. It cannot create pillars, luck-cycle facts, flow facts, event years, hidden-factor facts, or fixed verdicts.

Exit criteria:

- Runtime/API can build a `ChartContext` from BirthInput.
- Existing explicit-pillars runtime path remains compatible.
- Unit tests cover solar-term boundary, late-night/子时 boundary, unknown hour, and timezone assumptions.
- Synthetic validation includes `core_calculation`, `luck_cycle`, `flow_timing`, `six_pillar_context`, `strength_structure_useful_god`, `practical_reading`, `agent_question_flow`, and `real_case_validation` case families.
- Customer reading surface is visible for guest/user and internal Bazi context is role-gated.
- High-value question quality is observed by synthetic validation and emitted as a training signal.
- Answer submission returns a refreshed customer view with the next question and answer panel.
- The next visible user question changes after an answered question.
- LLM unavailable, disabled, or drifted output falls back to the deterministic rule answer.
- This document is updated with completed work, validation results, next task, and current completion.

## Training And Validation Alignment

Training and synthetic validation serve the practical calculation mainline, but they stay below the deterministic fact boundary.

Training may tune:

- Policy weights.
- Evidence thresholds.
- Candidate ranking.
- Question strategy.
- Expression strategy.

Training must not tune or generate:

- Birth information facts.
- Four-pillar facts.
- Luck-cycle facts.
- Flow-year or flow-month facts.
- Any deterministic chart foundation fact.

Implemented practical validation signals:

```text
v30.training_signal.birth_chart_conversion_boundary
v30.training_signal.luck_cycle_alignment
v30.training_signal.flow_timing_activation
v30.training_signal.six_pillar_context_coverage
v30.training_signal.strength_structure_decision
v30.training_signal.practical_reading_quality
v30.training_signal.agent_question_flow_quality
v30.training_signal.high_value_question_quality
v30.training_signal.role_locale_client_projection_coverage
v30.training_signal.real_case_feedback_alignment
```

Signal purpose:

- Record coverage of calendar-conversion, luck-cycle, flow timing, six-pillar, ranked-decision, reading-quality, agent-question-flow, and high-value-question boundaries.
- Record coverage of role, locale, and client projection boundaries.
- Feed promotion-gate quality checks.
- Remain validation signals, not chart-fact sources.

## Progress Update Rule

Every completed task must update this document before final handoff.

Required update fields:

- Current active task status.
- Completion percentage.
- Completed work.
- Validation commands and results.
- Next highest-priority task.
- Whether the work stayed aligned to the practical Bazi mainline.

Any task outside P0-P4 must state why it directly serves the current practical calculation mainline.

## Completed In P0.1 Contract Foundation

Completed:

- Added `BirthInput`.
- Added `ChartBuildSource`.
- Added `CalendarConversionTrace`.
- Added `FourPillarResult`.
- Added `BirthChartBuildResult`.
- Preserved explicit-pillars `ChartContext` compatibility.
- Added a safe BirthInput build entrypoint that returns pending conversion trace instead of fabricating four-pillar facts.
- Added unknown-hour, timezone, late-night/子时, and true-solar-time boundary flags.

Validation:

```text
pytest -q tests/unit/test_core_chart_context.py tests/unit/test_birth_input_contract.py
5 passed

python3 -m py_compile v30/contracts.py v30/core/chart_context.py
passed

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

pytest -q tests/test_v30_scaffold.py
6 passed

pytest -q
161 passed, 1 skipped
```

Alignment:

- Work stayed aligned to P0.
- No LLM, training signal, synthetic draft, or feedback path can generate four-pillar facts.
- Explicit pillars remain the only ready `ChartContext` source until deterministic calendar conversion is implemented.

## Completed In P0.2 Deterministic Calendar Conversion Foundation

Completed:

- Added `lunar_python==1.4.8` as the deterministic calendar conversion dependency.
- Implemented solar BirthInput conversion to four pillars through `lunar_python`.
- BirthInput can now produce a ready `ChartContext` for supported solar inputs.
- Added timezone validation and local datetime parsing.
- Added late-night/子时 boundary recording.
- Kept unknown-hour input blocked from hour-pillar fabrication.
- Kept true-solar-time requests pending until longitude and conversion policy are implemented.
- Kept lunar conversion explicitly unsupported until a deterministic lunar branch is added.

Validation:

```text
pytest -q tests/unit/test_core_chart_context.py tests/unit/test_birth_input_contract.py
7 passed

python3 -m py_compile v30/contracts.py v30/core/chart_context.py
passed
```

Alignment:

- Work stayed aligned to P0.
- Four-pillar facts now come from deterministic calendar conversion for supported solar inputs.
- Unsupported branches return traceable pending/unsupported results instead of fallback facts.

## Completed In P0.3 Runtime/API And Synthetic Core Calculation Integration

Completed:

- Added `create_runtime_from_context()` so BirthInput-derived `ChartContext` uses the normal evidence, structure, mainline, question, answer, expression, and diagnostics chain.
- `POST /api/v30/readings` now accepts `birth_input`.
- Ready solar BirthInput persists a full runtime and trace.
- Pending/unsupported BirthInput returns chart-build trace without saving fake runtime facts.
- Presentation diagnostics now expose `chart_build_source` and `calendar_conversion_trace`.
- Added `core_calculation` synthetic suite with ready solar, unknown-hour pending, lunar unsupported, and true-solar-time pending cases.
- Added `v30.training_signal.birth_chart_conversion_boundary`.
- Synthetic `all` now includes 28 cases.

Validation:

```text
pytest -q tests/test_v30_scaffold.py tests/unit/test_training_signals.py tests/unit/test_birth_input_contract.py
13 passed

python3 scripts/run_synthetic_validation.py --tier core_calculation
v30.synthetic.core_calculation: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (28/28)

pytest -q
162 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521193133: eligible mode=standard checks=4
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed
```

Alignment:

- Work stayed aligned to P0.
- BirthInput is now in runtime/API and validation, not only core contracts.
- Training signal remains validation metadata and cannot create chart facts.

## Completed In P1-P3 Practical Measurement Baseline

Completed:

- Added deterministic BirthInput-derived luck-cycle context for supported solar inputs with gender.
- Added flow-year and flow-month context from the target runtime date.
- Added six-pillar context joining natal four pillars, current luck pillar, and current flow-year pillar.
- Added ranked practical decisions for strength, structure pattern, and useful-god candidate review.
- Added practical domain reading context for career, wealth, relationship, health, and timing.
- Added agent question flow stages for chart confirmation, time context confirmation, event-year discovery, domain follow-up, and final clarification.
- Exposed ranked decisions, practical reading context, and agent question flow through runtime policy effects, answer contracts, and presentation diagnostics.
- Added practical-domain question anchor and recommender/i18n support.
- Added synthetic practical mainline suites and training signals.
- Kept all luck/flow facts deterministic and all ranked decisions as bounded candidates, not final chart facts.

Validation:

```text
pytest -q tests/unit/test_luck_flow_context.py tests/unit/test_practical_reading_context.py tests/unit/test_birth_input_contract.py tests/unit/test_training_signals.py tests/unit/test_release_gate.py
12 passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (34/34)

pytest -q
165 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521195252: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service check after V30 restart:
/api/v30/health returned ok=true
/v30/ui/ returned 200
BirthInput runtime payload returned chart_build.status=ready and exposed six_pillar_context, ranked_decisions, practical_reading_context, agent_question_flow, and q_v30_practical_domain_focus
```

Alignment:

- Work stayed aligned to the practical Bazi mainline.
- Deterministic chart facts still come only from BirthInput/calendar/luck-flow code, not training, feedback, LLM, or synthetic drafts.
- Practical readings and useful-god outputs remain ranked candidates with guardrails.

## Executed Slice

```text
P4.2 Silent Projection And Training Validation Loop
-> role-locale-client projection contract
-> presentation projection training signal
-> synthetic observation of projection matrix
-> silent background training remains candidate-first and validation-gated
-> no chart-fact mutation from projection, training, or LLM
```

P4.2 implementation notes:

- Keep this on the mainline because every practical Bazi answer must be deliverable to different users, languages, and terminals.
- Do not treat multi-role/multi-locale/multi-client as UI decoration; it is the runtime delivery contract.
- Training and validation may tune projection density, labels, visibility, and question strategy.
- Training and validation still cannot create BirthInput, pillar, luck-cycle, flow, or six-pillar facts.

## Completed In P4.2 Silent Projection And Training Validation Loop

Completed:

- Added `ClientKey` contract for `web`, `mobile`, `admin`, and `lab`.
- Added `ClientProfile` contract with density, max question count, diagnostics visibility, actions, and projection boundary.
- Converted client profiles from loose dictionaries to contract-shaped profiles.
- Added `v30.role_locale_client_projection_matrix.v1` to enumerate supported roles, locales, clients, default sampled combinations, client profiles, diagnostic roles, compact clients, and projection boundary.
- Synthetic replay now observes `role_locale_client_projection_matrix`.
- Training extraction now emits `v30.training_signal.role_locale_client_projection_coverage`.
- Presentation output now exposes `client_profile` metadata in the layout while preserving chart-fact boundaries.

Validation:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_training_signals.py tests/unit/test_expression_framework.py tests/unit/test_portrait_projection.py tests/test_v30_scaffold.py
18 passed

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (34/34)

pytest -q tests/unit/test_release_gate.py
3 passed

pytest -q
166 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521200713: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed
```

Alignment:

- Work stayed aligned to the practical Bazi mainline because answer delivery is now role/language/client-contract validated.
- This remains a projection and training-signal layer, not a chart-fact layer.
- Silent training may use the signal for presentation-policy candidates after validation gates pass.

## Executed Slice

```text
P4.3 Real-Case Validation And Boundary Hardening
-> canonical real-case fixture set for common user scenarios
-> solar-term and late-night/子时 boundary fixture matrix
-> invalid timezone/date/time blocking tests
-> practical reading quality metrics from real-case validation
-> real-case synthetic training signal
```

P4.3 implementation notes:

- Keep deterministic chart-fact correctness ahead of answer richness.
- Add real-case fixture coverage before tuning practical reading weights.
- Do not implement broad lunar or true-solar-time behavior without explicit deterministic source policy.
- Document the exact supported and pending conversion branches.

## Completed In P4.3 Real-Case Validation And Boundary Hardening

Completed:

- Added `real_case_validation` synthetic suite with canonical solar male, solar female, unknown-gender partial, and invalid-timezone blocked cases.
- `synthetic all` now includes 38 contract-shaped cases.
- Added `v30.training_signal.real_case_feedback_alignment`.
- Added calendar boundary tests for invalid timezone, invalid date, invalid time, and late 子 hour recording.
- Preserved the boundary that invalid or unsupported real-case inputs cannot fabricate pillars.
- Preserved the boundary that unknown gender can still produce natal/practical context, but cannot force luck-cycle direction into ready state.

Validation:

```text
pytest -q tests/unit/test_birth_calendar_boundaries.py tests/unit/test_training_signals.py tests/unit/test_release_gate.py
8 passed

python3 scripts/run_synthetic_validation.py --tier real_case_validation
v30.synthetic.real_case_validation: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (38/38)

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521202109: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

pytest -q
170 passed, 1 skipped

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service check after V30 restart:
/api/v30/health returned ok=true
/v30/ui/ returned 200
Solar female real-case BirthInput returned chart_build.status=ready and admin view exposed client_profile, six_pillar_context, ranked_decisions, practical_reading_context, agent_question_flow, and q_v30_practical_domain_focus
```

Alignment:

- Work stayed aligned to the practical Bazi mainline.
- Real-case validation now checks that the measurement pipeline runs through chart build, six-pillar context, practical reading, question flow, and projection where supported.
- The training signal is a quality/policy signal, not a chart-fact source.

## Completed In P4.4 Calendar Policy Completion

Completed:

- Reused the proven V20 calendar approach at the algorithm level: `lunar_python.Lunar.fromYmdHms()` for lunar BirthInput and `Solar.fromYmdHms(...).getLunar()` for solar BirthInput.
- Kept V30 architecture clean: no V20 runtime import, no V20 object dependency, and all chart facts still originate inside V30 `core`.
- Added deterministic lunar BirthInput conversion, including `lunar_is_leap_month` input support.
- Added deterministic true-solar-time adjustment for known place names or numeric longitude, using longitude minus timezone standard meridian.
- Added known-place longitude support for Beijing, Shanghai, Guangzhou, Shenzhen, Hong Kong, Taipei, Seoul, and relevant Chinese/Korean labels.
- True-solar-time requests without resolvable place/longitude are blocked with trace, not fabricated.
- Updated synthetic `core_calculation` so lunar and known-place true-solar cases are ready, not unsupported/pending.
- Preserved boundary traces for timezone, lunar conversion, true-solar adjustment, late 子 hour, and blocked branches.

Validation:

```text
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_luck_flow_context.py tests/unit/test_training_signals.py tests/unit/test_release_gate.py
16 passed

python3 scripts/run_synthetic_validation.py --tier core_calculation
v30.synthetic.core_calculation: passed (4/4)

python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (38/38)

pytest -q
171 passed, 1 skipped

python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
v30.release_gate.standard.20260521203307: eligible
runtime_smoke passed; synthetic_all passed; 518k_sample passed; 518k_shard passed

set -a; source .env.v30.real; set +a; V30_RUN_REAL_ENV_TESTS=1 pytest -q tests/integration/test_real_environment.py
1 passed

Live service check after V30 restart:
/api/v30/health returned ok=true
lunar BirthInput returned chart_build.status=ready with pillars 己巳/丁丑/庚子/辛巳
known-place true-solar BirthInput returned chart_build.status=ready with adjusted time 1990-02-04T22:58:00 and pillars 庚午/戊寅/庚子/丁亥
```

Alignment:

- Work stayed aligned to the practical Bazi measurement mainline.
- We reused V20's proven calendar method conceptually, but implemented it natively in V30.
- Calendar conversion now supports explicit pillars, solar BirthInput, lunar BirthInput, known-place true-solar-time BirthInput, unknown-hour blocking, invalid date/time/timezone blocking, and unresolvable true-solar blocking.

## Forward Mainline Plan

Priority order:

1. `M8 User Presentation / API Projection`: keep API additive and customer-safe after the calculation modules are strong; do not let interaction/UI work lead the core calculation chain.
2. `M7 Follow-up Real Production Replay`: add production replay metadata only when real fixture tags are available; do not reopen the phase-sealed canonical pack for speculative cases.

Validation cadence:

- Subtask batches run targeted unit tests and the affected synthetic tier.
- Full pytest, synthetic all, and 518K sample run only at major module gates or policy-affecting promotion.

## Completed In P5 Reading Quality Upgrade Slice

Completed:

- Added customer-readable career, wealth, relationship, health, and timing domain summaries.
- Added domain `customer_takeaway`, `action_prompt`, `priority_score`, and `v30.practical_reading_quality.v1` contracts.
- Projected top domain cards into `v30.customer_reading_surface.v1` without exposing internal Bazi diagnostics.
- Fed practical reading gaps into recommended-question scoring and expected information gain.
- Expanded `v30.training_signal.practical_reading_quality` with readable-summary, takeaway, action-prompt, quality-contract, state, and priority-score coverage.
- Kept reading quality training scoped to ranking, expression, and question strategy; no chart facts are generated or mutated.

Validation:

```text
python3 -m py_compile v30/practical.py v30/presentation/client_model.py v30/questions/recommender.py v30/runtime.py v30/policy/comparison.py v30/validation/training_signals.py
passed

pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_presentation_projection.py tests/unit/test_question_anchor_selector.py tests/unit/test_training_signals.py tests/test_v30_scaffold.py
24 passed

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)
```

Alignment:

- Work stayed aligned to P5.
- The upgrade improves customer reading and question interaction quality while preserving deterministic chart-fact guardrails.
- User feedback and synthetic signals tune reading/question behavior, not pillars, luck-cycle facts, or flow facts.

## Completed In P5.1 Product Question Interaction Loop Slice

Completed:

- Added user-facing Bazi question anchors for career, wealth, relationship, timing, and decision blind spots.
- Added `interaction_type` and `answer_mode` to recommended question rows.
- Guest/user presentation now defaults to `user_question` rows and hides calibration probes from first-screen questions.
- Customer reading surface exposes structured `options` for domain focus.
- Answered user-facing questions are strongly suppressed so the next visible question changes.
- UI supports click-to-answer instead of requiring free-form text before the system responds.
- Added `docs/V30_BAZI_INTERACTION_SYSTEM.md` as the controlling design document for product question interaction.

Validation:

```text
node --check frontend/app.js
passed

pytest -q tests/unit/test_question_anchor_selector.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py
22 passed

local closed-loop smoke:
q_v30_user_career_direction -> q_v30_user_timing_pressure
visible user topics: career, wealth, relationship, timing, decision
internal hidden_factor recommendation retained
```

Alignment:

- Work stayed aligned to the practical Bazi mainline.
- UI remains a thin shell over stable reading/view/answer interfaces.
- Interaction state and question strategy are backend-owned and do not create chart facts.

## Completed In P5.2 Structured Interaction State Slice

Completed:

- Added structured selected-option handling to the answer loop.
- Persisted compact `known_user_signals` as dialogue context, not chart facts.
- Made `QuestionDialogueGraph` select the next customer question after structured answer submission.
- Preserved `actor_id` and `session_id` as the minimal multi-user/session hook.
- Exposed LLM runtime status for admin/practitioner diagnostics while keeping secrets and raw internals out of guest/user views.
- Kept direct question clicks and free text available while making structured option clicks the default product path.

Validation:

```text
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py tests/unit/test_question_dialogue_graph.py tests/unit/test_ten_god_energy_model.py
20 passed

python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)

pytest -q
181 passed, 1 skipped
```

Alignment:

- Work stayed aligned to P5/P6.
- User choices and `known_user_signals` tune question strategy, answer context, and expression only.
- They do not mutate pillars, luck-cycle facts, flow facts, ten-god facts, or deterministic chart foundations.

## Next Implementation Task

```text
P5.3 Interaction State Machine And Follow-up Policy
-> persist interaction_stage, selected_domain, answered_question_ids, and visible_next_question_id
-> separate internal_next_question_id diagnostics from customer-visible next_question_id
-> add synthetic interaction-loop validation cases
-> keep calibration probes diagnostic by default
```

## Validation Gates

P5 targeted gates:

```text
pytest -q tests/unit/test_core_chart_context.py
pytest -q tests/unit/test_birth_input_contract.py
pytest -q tests/unit/test_birth_calendar_boundaries.py
pytest -q tests/test_v30_scaffold.py
python3 scripts/run_synthetic_validation.py --tier core_calculation
python3 scripts/run_synthetic_validation.py --tier smoke
```

Full gates before promotion:

```text
pytest -q
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16
```

## Assumptions

- V30 does not import V20 runtime code.
- V20 algorithm ideas may be reviewed, but V30 contracts and implementation remain independent.
- No database schema change is required for P4.3.
- UI changes are not part of P4.3 unless needed to expose the practical runtime contract.
- Future tasks start by reading and updating this document.
