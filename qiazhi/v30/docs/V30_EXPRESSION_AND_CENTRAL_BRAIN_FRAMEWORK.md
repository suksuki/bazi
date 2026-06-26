# V30 Expression and Central Brain Framework

Updated: 2026-05-21

## Purpose

V30 needs to solve user-facing language at framework level, not by patching isolated strings.

The core rule is:

```text
internal runtime language != user-facing Bazi language
```

Runtime may keep precise engineering fields for validation, training, policy pointers, and traces. UI, LLM, question display, and answer text should consume a V30-owned expression layer.

## Mainline Position

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> QuestionIntentPlan
-> AnswerContext
-> ExpressionFrame
-> NarrativePlan
-> RenderedNarrative
-> UI / LLM / API
```

Expression is now a standard mainline outlet. It does not replace reasoning, knowledge, rules, portrait, hidden factors, or training. It projects their bounded output into role-aware Bazi language.

## Current Implementation

Code:

- `v30/brain/contracts.py`
- `v30/brain/orchestrator.py`
- `v30/brain/__init__.py`
- `v30/expression/contracts.py`
- `v30/expression/style.py`
- `v30/expression/planner.py`
- `v30/expression/renderer.py`
- `v30/expression/__init__.py`

Runtime outputs:

- `question_plan.policy_effect.expression_framework_version`
- `question_plan.policy_effect.expression_plan`
- `question_plan.policy_effect.rendered_narrative`
- `question_plan.policy_effect.central_brain_version`
- `question_plan.policy_effect.central_brain_trace`
- `question_plan.policy_effect.adaptive_question_diagnostics`

Answer output:

- `AnswerResult.text` now uses `RenderedNarrative.text`.
- User-facing answer text no longer exposes terms such as `Quality gate`, `policy_effect`, or runtime policy internals.

## Layer Contracts

### ExpressionFrame

Purpose: turn runtime facts into semantic intent units.

Examples:

- `mainline_summary`
- `question_recommendation`
- `answer_boundary`
- `portrait_projection`

Frame rules:

- It references source IDs.
- It keeps boundaries.
- It carries Bazi terms and user meaning.
- It is not allowed to mutate runtime facts.

### NarrativePlan

Purpose: choose frames for a role, locale, and client.

Current roles:

- `guest`
- `user`
- `practitioner`
- `analyst`
- `admin`
- `lab`

### RenderedNarrative

Purpose: produce final text for UI, LLM prompt context, and API consumers.

Rendered text must preserve:

- chart facts
- structure state
- mainline state
- evidence boundary
- hidden factor uncertainty
- portrait-as-projection boundary

## Style Policy

User and guest output should sound like Bazi consultation language.

Practitioner output can expose denser Bazi concepts.

Analyst, admin, and lab output can expose diagnostics, but still through V30-owned contracts.

Forbidden ordinary-user leakage:

```text
policy_effect
rule_decision_state
macro_dimension_context
krp_unit_weights
dynamic_graph_paths_scored
quality_gate
runtime pointer
trace_id
```

## Central Brain V30 Direction

V20 had a "brain/orchestrator" direction, but parts were added gradually. V30 should not copy it as a monolith.

V30 central brain should be a layered coordinator:

```text
BrainState
-> RuntimePlanner
-> EvidenceRouter
-> Structure/Mainline Arbiter
-> QuestionDialogue Strategist
-> Expression Orchestrator
-> TrainingSignal Emitter
-> RuntimePointer Auto-Apply
```

The central brain should coordinate, not replace specialist modules.

Current implementation version:

```text
v30.central_brain.v1
```

Current runtime trace:

```text
CentralBrainTrace
-> BrainState
-> SessionMemory
-> RoleState
-> RuntimePlannerDecision
-> QuestionDialogueStrategy
-> ExpressionOrchestration
-> FeedbackStrategy
-> TrainingSignalRoute[]
```

It should own:

- session state
- role state
- user known/unknown context
- user-facing interaction stage
- structured option state
- hidden factor dialogue state
- current mainline focus
- next best question strategy
- expression strategy
- feedback-to-training signal routing

Current ownership implemented:

- `SessionMemory` tracks known context, unknown context, selected question, and feedback slots.
- `RoleState` tracks role visibility, answer density, diagnostics visibility, and expression voice.
- `FeedbackStrategy` tracks capture targets, immediate effects, training routes, and keeps `no_review_gate=true`.
- Admin/analyst/lab presentation diagnostics consume central brain focus, question strategy, expression surface status, feedback targets, and training routes.
- `recommend_questions()` consumes central brain recommendation context, including unknown context, feedback slots, and question strategy.
- `build_runtime_narrative_plan()` can consume central brain role state to drive expression density and voice.
- Guest/user question projection now separates user-facing questions from calibration probes.
- Answered user-facing questions are suppressed so the central-brain/question loop can progress.

It should not own:

- chart calculation
- raw rule facts
- structure graph scoring internals
- database adapter internals
- Redis adapter internals
- direct policy pointer mutation without validation replay

## Brain and Expression Relationship

The central brain chooses what should be said next.

The expression layer decides how it should be said.

Product boundary:

```text
Central Brain selects user_question / structured_option / calibration_probe behavior.
Expression renders only the user-facing wording.
Calibration probes remain diagnostic or optional unless explicitly promoted into a user-facing follow-up.
```

Runtime now records this relationship in `central_brain_trace.expression_orchestration`, which references the expression plan, rendered narrative, style profile, and leakage status.

This separation prevents two failure modes:

- Brain becomes a prompt/string generator.
- Expression layer starts making reasoning decisions.

## Training and Validation

Expression must join the normal V30 validation path.

Required signals:

- engineering-token leakage
- role density mismatch
- boundary omission
- unsupported hidden-factor certainty
- weak Bazi terminology fit
- question recommendation phrasing mismatch
- central brain route coverage

Synthetic validation should include:

- missing time cases
- hidden factor candidate cases
- conflicting feedback cases
- macro portrait projection cases
- practitioner/admin role contrast

No manual review gate is introduced. Passing synthetic + 518K replay can auto-apply expression policy pointers once expression policies become runtime artifacts.

## Current Completion

Completed:

- Framework-level expression package.
- Runtime policy effect includes expression version, plan, and rendered narrative.
- Answer text consumes rendered narrative.
- Unit tests cover Bazi-language rendering and role-density differences.
- Central brain package added as a coordinator contract.
- Runtime policy effect includes central brain version and trace.
- Central brain now includes session memory, role state, and feedback strategy.
- Presentation diagnostics consume central brain coordination output.
- Question recommendation consumes central brain context and records brain reasons in recommendation traces.
- Expression planning consumes central brain role state.
- Runtime now emits `v30.adaptive_question_diagnostics.v1` to replay central-brain/question-policy decisions from trace state.
- Admin API exposes `GET /api/v30/admin/runs/{reading_id}/question-replay`.
- Synthetic validation now observes expression quality: Bazi term count, forbidden engineering-token leakage, boundary language, voice, and density.
- Training signal extraction emits `v30.training_signal.expression_quality`.
- Runtime now exposes LLM output contracts for answer drafts and question explanations.
- Runtime now exposes LLM output contracts for answer drafts, question explanations, synthetic case drafts, and failure cluster summaries.
- Synthetic validation and training now track `v30.training_signal.llm_output_contract_quality` across all four contract task types.
- Expression and presentation can now consume role-aware portrait projection views, keeping hidden-factor portrait language boundary-visible for users and diagnostic for admin/analyst/lab roles.
- Synthetic validation observes central brain training route domains.
- Training signal extraction emits `v30.training_signal.central_brain_route_coverage`.
- Mainline docs updated.

Next:

- Add expression policy artifact family when tunable style parameters appear.
- Presentation now consumes deterministic expression-rendered question labels with role/client density and boundary diagnostics.
- Extend LLM prompt context to consume `NarrativePlan` instead of raw answer strings.
- Add remaining LLM output contracts for synthetic case drafts and failure summaries.
- Convert adaptive question diagnostics into bounded adaptive question policy candidates.
- Add expression policy artifact family when tunable style parameters appear.
- Expand hidden-factor event-year modeling and train it from synthetic boundary cases.
