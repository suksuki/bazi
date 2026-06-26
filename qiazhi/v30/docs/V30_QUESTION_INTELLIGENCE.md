# V30 Question Intelligence

Updated: 2026-06-13

## Current Runtime Implementation

The current V30 mainline now has a scored recommendation layer:

```text
BaziQuestionAnchor[]
+ FeatureEvidence
+ StructureState
+ MainlineState
+ active question_policy
-> QuestionIntentPlan.recommended_questions
```

The recommender does not only return a fixed template order. It scores each bound question by:

- Missing requirements.
- Mainline quality gate.
- Useful-god candidate evidence.
- Branch/structure dynamic evidence.
- Partial structure state.
- Active `question_policy` version.
- Active `question_policy.payload.weights` for topic, intent, stage, and question ID.
- Active `model_signal_summary.energy_bands`, which can shift the customer-visible top question by Bazi-specific ten-god family.

The UI/API view exposes:

```text
question_id
score
stage
topic
reasons
policy_weight
```

Questions are sorted by recommendation score in the API view. For the current missing-time smoke case, the time-context completion question is first because it blocks downstream timing claims.

The runtime now also builds a dialogue graph:

```text
QuestionIntentPlan.recommended_questions
+ hidden_factor_calibration
+ question_outcomes
-> QuestionDialogueGraph(nodes, edges, next_question_id, policy_notes)
```

This keeps the system from treating questions as a flat template list. The graph records what each question unlocks, for example:

- Missing time context unlocks hidden-factor dialogue.
- Missing time context unlocks useful-god candidate review.
- Structure dynamic review informs candidate-path review.
- Calibrated hidden-factor feedback can condition follow-up ordering without changing chart facts.
- Answered question outcomes can mark an answered node and lift same-topic follow-up candidates without mutating chart facts.

Current first priority is to keep recommendations bound to the Bazi core context while gradually replacing simple score rules with trained policy artifacts.

IQ5 closed the previous question-intelligence baseline. On 2026-06-13, product review selected a focused reopening under:

```text
UIB-1 Unified Interaction Brain Contract And Structured Constraint Plan
```

Reason: intelligent Q&A and hidden-factor calibration must become one constrained dialogue. This is not generic UI polish; unconstrained hidden-factor text can pollute calibration and training. The new work keeps M1-M8 chart facts sealed while adding bounded answer constraints, structured hidden-factor signals, and unified next-question selection.

Reference:

```text
docs/V30_UNIFIED_INTERACTION_BRAIN_PLAN.md
```

## Current Completion And Next Module Push

| Area | Completion | Current state | Next task |
|---|---:|---|---|
| Question recommendation | 98% | IQ5 complete: scored high-value questions consume chart/evidence/structure/mainline/policy/model-signal context, produce personalized top topics, expose quality contracts, and enter closeout with visible/internal layer separation. | UIB extends next-question scoring with hidden-factor uncertainty, dynamic-path uncertainty, invalid-input retry, and negative-evidence need. |
| Dialogue graph | 98% | IQ5 complete: graph nodes/edges, answered suppression, selected options, `known_user_signals`, explicit `interaction_state`, follow-up reason, next-question refresh, internal calibration pointer, and two-turn chain readiness are closed. | UIB adds one structured turn signal so user Q&A and hidden-factor calibration share the same turn model. |
| Product projection | 98% | IQ5 complete: guest/user default to `user_question`; calibration probes stay diagnostic or optional, `visible_next_question_id` is separated from `internal_next_question_id`, and multi-role chain projection keeps customer surface clean while admin sees diagnostics. | UIB projects calibration as bounded customer questions with `answer_constraints`, not a separate hidden-factor form. |
| Training linkage | 98% | IQ5 complete: `interaction_loop` passes 5/5; extraction emits `v30.training_signal.question_model_signal_personalization`; auto-training converts it into guarded `question_policy.weights.model_signal_question_policy`; chart-fact mutation remains blocked. | UIB adds accepted/rejected structured signals while blocking free-text pollution and chart-fact mutation. |
| LLM question context | 98% | IQ5 complete: multi-turn `domain_followup` and `hidden_factor_dialogue` Bazi LLM context packs include interaction state, known user signals, and relevant module sections while preserving expression-only boundaries. | UIB keeps LLM expression-only and passes structured signal summaries instead of raw unbounded hidden-factor claims. |

## UIB Additive Contract

The next implementation should add, without removing existing API fields:

```text
answer_constraints
structured_payload
interaction_turn_signal
interaction_brain_result
absorbed_signals
rejected_signals
```

Boundary:

```text
structured_interaction_signals_may_tune_question_strategy_and_hidden_factor_calibration_not_chart_facts
```

## Product Interaction Layer

V30 now separates recommendation rows into product-facing and calibration-facing layers:

```text
user_question
structured_option
calibration_probe
```

Guest/user views should default to `user_question` rows. These are questions the user can click and expect the system to answer directly, such as career direction, wealth tendency, relationship pattern, timing pressure, and decision blind spots.

`structured_option` rows are standardized user choices that guide session state without relying on free-form text.

`calibration_probe` rows include hidden-factor discovery, special-year/repeated-state confirmation, useful-god candidate review, and structure dynamic review. They remain valuable for policy, diagnostics, and optional follow-up, but they should not dominate the first customer screen.

The runtime now also emits replay diagnostics:

```text
QuestionIntentPlan.recommended_questions
+ QuestionDialogueGraph
+ CentralBrainTrace
+ active question_policy payload
-> AdaptiveQuestionDiagnostics
```

`v30.adaptive_question_diagnostics.v1` records per-question rank, score, topic, stage, policy weight, policy version, categorized reasons, central-brain strategy, runtime focus, replay inputs, and boundaries. It is trace replay metadata only; it does not mutate chart facts or policy pointers.

## Current Focus: Question Policy Runtime Consumption

Implemented:

```text
question_policy.payload.weights
-> recommendation scorer
-> question order
-> UI/API view
```

Question policy weights must affect behavior immediately after training promotion. They are not only version metadata.

Runtime status:

- `RuntimePointerStore.load_active_artifact("question_policy")` is loaded during runtime creation.
- `recommend_questions()` consumes `topic_weights`, `intent_weights`, `stage_weights`, and `question_weights`.
- `recommend_questions()` consumes `model_signal_question_policy` only at `user_question_entry`; it is blocked when core context completion, such as missing time context, is still required.
- Auto-training emits question-policy weight candidates and promotes them without a review gate after validation.
- Runtime traces expose `policy_effect.question_policy_payload`.
- Runtime traces expose `policy_effect.question_dialogue_graph`.
- Runtime traces expose `policy_effect.adaptive_question_diagnostics`.
- `POST /api/v30/readings/{reading_id}/questions/{question_id}/answer` stores bounded question outcomes in `QuestionIntentPlan.session_state.question_outcomes`.
- Runtime recommendations emit `interaction_type` and `answer_mode`.
- User-facing presentation filters default visible questions to `interaction_type=user_question`.
- Answered questions receive strong suppression, so the next visible question changes instead of repeating the same prompt.
- Question outcome feedback is copied into `policy_effect.question_outcomes` for diagnostics and training extraction.
- Synthetic validation includes a question-dialogue-graph case.
- `GET /api/v30/admin/runs/{reading_id}/question-replay` exposes the replay diagnostics for drilldown.
- Training now emits `v30.training_signal.adaptive_question_replay`.
- Auto-training converts that signal into `question_policy.weights.adaptive_question_policy` with bounded topic/stage/intent deltas.
- Auto-training converts `v30.training_signal.question_model_signal_personalization` into `question_policy.weights.model_signal_question_policy`.
- Promotion now emits `v30.question_policy_comparison.v1` artifacts for active-vs-candidate question order, score, weight, and reason deltas.
- `GET /api/v30/admin/policies/question/comparison` returns the latest comparison artifact, or a candidate-specific artifact with `candidate_id`.
- `GET /api/v30/admin/validation/artifacts?family=question_policy_comparison` exposes comparison artifacts through unified validation artifact discovery.

## Completed P8 Baseline And Active P8.2 Plan

The interaction state contract is now an additive layer over the existing API:

```text
interaction_stage
selected_domain
answered_question_ids
selected_option_ids
known_user_signals
visible_next_question_id
internal_next_question_id
followup_reason
```

Ownership:

- `QuestionDialogueGraph` owns internal next-question strategy.
- Presentation owns what `guest/user` can see.
- Admin/practitioner diagnostics may inspect `internal_next_question_id`.
- Customer surfaces always use `next_question_id` / `visible_next_question_id`.

Synthetic validation:

- direct question click
- structured domain choice
- hidden calibration hidden from user
- visible next-question change
- internal next-question diagnosable

Training signal:

```text
v30.training_signal.interaction_state_machine
v30.training_signal.interaction_loop_quality
```

P8.2 current status:

- Dedicated `interaction_loop` tier is active and passes 5/5.
- Calibrate question strategy and visible/internal next-question boundaries.
- Keep interaction training signals scoped to question strategy and follow-up policy; they must not alter deterministic chart facts.

## IQ1 Intelligent Question Interaction Audit

IQ1 validates the current question interaction against the business requirements:

- Tailored to different Bazi contexts: model-signal energy families change customer-visible top question order.
- Module-backed: M3, M4, M5, M6, central brain, and dialogue graph are consumed by question strategy.
- Not flat templates: user questions carry evidence ids, reasons, expected information gain, and quality contracts.
- Chainable: answered questions update `interaction_state`, `known_user_signals`, answer panel, and next question.
- Trainable: `interaction_loop` synthetic tier passes 5/5 and emits interaction training signals.
- Multi-role: guest/user see user questions; admin/practitioner can inspect internal strategy.
- LLM-supported: Bazi LLM context packs include interaction state and known user signals without fact mutation.
- Core-calculation centered: question interaction follows `core_bazi_reading`, not the other way around.

Current validation:

```text
python3 scripts/run_intelligent_question_interaction_audit.py
v30.intelligent_question_interaction_audit.v1: passed (8/8) iq1_intelligent_question_interaction_ready

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)
```

## IQ2 Model-Signal Question Training Readiness

IQ2 makes the model-signal personalized question layer trainable and observable instead of only visible in runtime ordering.

Implemented:

- Synthetic question observations record `model_signal_focus_reason_count`, focus pairs, focus topics, top question id/topic, and whether the top question was model-signal focused.
- Training extraction emits `v30.training_signal.question_model_signal_personalization`.
- The signal domain is `question_intelligence`; it can tune question strategy and visible next-question policy only.
- The signal cannot tune chart facts, pillars, luck-cycle facts, flow facts, or base fact explanations.
- IQ2 keeps the customer-visible top question personalized when appropriate, but does not force personalization to override missing-time or required core-context completion questions.

Current validation:

```text
python3 scripts/run_question_model_signal_training_readiness.py
v30.question_model_signal_training_readiness.v1: passed (5/5) iq2_question_model_signal_training_ready

python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)
```

## IQ3 Model-Signal Question Policy Candidate

IQ3 connects the IQ2 signal to the normal auto-training and candidate review path.

Implemented:

- `question_policy.weights.model_signal_question_policy` is generated from `v30.training_signal.question_model_signal_personalization`.
- The policy carries focus topics, focus pairs, coverage, signal strength, and the boundary `model_signal_question_policy_trains_question_strategy_not_chart_facts`.
- Runtime recommendation consumes the policy only for `user_question_entry`.
- A context-completion guard blocks model-signal personalization from outranking required core Bazi inputs such as missing time context.
- F2 targeted candidate review now reports `has_model_signal_question_policy`.
- Normal question-policy promotion still requires synthetic all and 518K sample validation.

Current validation:

```text
question candidate synthetic all override
passed 100/100

pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers tests/unit/test_targeted_calibration_candidate_review.py::test_targeted_calibration_candidate_review_ready tests/unit/test_question_model_signal_training_readiness.py
5 passed
```

## IQ4 Intelligent Question Chain Readiness

IQ4 validates the question system as a multi-turn Bazi consultation chain, not only a single next-question selector.

Implemented:

- Two consecutive question answers update `question_outcomes`, `known_user_signals`, `interaction_state`, answer panel, and visible next question.
- The chart/core Bazi fingerprint remains unchanged after answers.
- Guest/user projection stays customer-clean while admin diagnostics include interaction state and question outcomes.
- `domain_followup` and `hidden_factor_dialogue` LLM context packs include the required chain state without raw runtime payload or chart-fact mutation.
- `interaction_loop` training signals remain available for question strategy only.
- The chain stays centered on core Bazi reading modules: M4 model signal, M5 ranked decisions, and M6 practical reading context.

Current validation:

```text
python3 scripts/run_intelligent_question_chain_readiness.py
v30.intelligent_question_chain_readiness.v1: passed (6/6) iq4_intelligent_question_chain_ready

pytest -q tests/unit/test_intelligent_question_chain_readiness.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
3 passed
```

## IQ5 Intelligent Question Closeout

IQ5 closes the intelligent question module for the current V30 scope.

Implemented:

- IQ1, IQ2, and IQ4 are accepted together as prerequisites.
- User-visible questions, structured options, internal calibration probes, admin diagnostics, LLM follow-up context, and training signals are verified as separate layers.
- `question_policy` candidates include adaptive, interaction-followup, and model-signal question policies.
- Customer projection remains clean; admin diagnostics expose question graph, interaction state, and replay diagnostics.
- No default full pytest, full synthetic all, full 518K, live LLM, pointer write, or chart-fact mutation is required by the steady-state gate.

Current validation:

```text
python3 scripts/run_intelligent_question_closeout.py
v30.intelligent_question_closeout.v1: passed (6/6) iq5_intelligent_question_closeout_ready

pytest -q tests/unit/test_intelligent_question_closeout.py tests/unit/test_intelligent_question_chain_readiness.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed
```

Current state: `IQ-S1 Question Intelligence Steady State`.

Updated: 2026-05-21

## Purpose

V30 must replace template-driven question generation with intelligent, evidence-bound question recommendation.

The question system should start from seed questions, but training and runtime context must decide what to ask next.

## Core Principle

Questions are not display templates.

A displayed question must come from:

```text
QuestionIntent
-> QuestionRecommendation
-> BaziQuestionAnchor
-> Role/Locale Rendering
```

Guest and user views show only bound anchors.

## Inputs

The recommender consumes:

- Natal chart.
- Luck cycle.
- Annual flow.
- Hidden factor hypotheses.
- Confirmed hidden attributes.
- Missing time state.
- Feature evidence.
- Rule evidence.
- Structure state.
- Mainline state.
- Previous questions.
- User answers.
- Structured option selections.
- Role.
- Client.
- Active question policy.
- Synthetic and 518K validation feedback.

## Outputs

The recommender produces:

```text
question_id
intent_id
anchor_status
priority
evidence_ids
mainline_id
structure_id
why_this_question
expected_information_gain
question_value
quality_contract
missing_requirements
role_visibility
interaction_type
answer_mode
```

## Recommendation Model

Initial scoring dimensions:

- Context binding strength.
- Evidence support.
- Mainline relevance.
- Information gain.
- User/session timing.
- Role appropriateness.
- Missing requirement risk.
- Synthetic validation confidence.
- 518K distribution confidence.
- Training policy score.
- Hidden factor information gain.
- Customer reading loop usefulness.
- Whether the answer can refresh next question and answer context.

## V30 High-Value Question Contract

Every runtime recommendation must explain why it is worth asking now.

Required fields:

```text
question_value
expected_information_gain.score
expected_information_gain.primary_gain
expected_information_gain.reduces
expected_information_gain.uses_answer_for
quality_contract.version = v30.high_value_question.v1
quality_contract.boundary
```

For user-facing rows:

```text
interaction_type = user_question
answer_mode = direct_answer
```

For internal calibration rows:

```text
interaction_type = calibration_probe
answer_mode = calibration_feedback
```

This contract is a question-policy and training signal. It is not a chart fact and cannot mutate pillars, luck-cycle facts, flow facts, or hidden-factor facts.

## Seed Questions

Seed questions are starting material, not final templates.

Initial product-facing seed families:

- career direction
- wealth tendency
- relationship pattern
- current timing pressure
- decision blind spot

Each seed should define:

```text
seed_id
intent_family
required_context
evidence_requirements
expected_unlocks
role_allowed
negative_conditions
```

The runtime should not display a seed directly.

## Anchors

Anchors bind a recommendation to the current chart context.

Anchor statuses:

- `bound`
- `weak`
- `missing_time`
- `missing_structure`
- `unsupported`

Visibility:

- Guest/user: `bound` only.
- Practitioner/admin/lab: may inspect weak or missing anchors with diagnostics.

## Training Loop

Question training should use:

- User interactions.
- Role question clicks.
- Synthetic question validation.
- 518K question coverage.
- Failure clusters.
- Relevance scoring.

Promotion target:

```text
question_policy
```

Hidden factor discovery may also update:

```text
hidden_factor_policy
```

Training must distinguish user-facing question quality from calibration-probe value. A calibration probe can influence policy and diagnostics without becoming the default first-screen customer question.

This policy controls which boundary question or special-year question to ask, not chart facts.

Auto-apply path:

```text
QuestionTrainingRun
-> QuestionPolicyCandidate
-> SyntheticValidation
-> 518KSampleValidation
-> QuestionPolicyArtifact
-> RuntimePointer(question_policy)
```

## What V30 Must Avoid

- Raw title fields as display source.
- Template-only recommendation.
- Questions unbound to chart context.
- Role projection inventing questions.
- Fallback chains over legacy field names.
- LLM inventing unsupported questions for user views.
- Treating unconfirmed hidden factors as facts.

## LLM Role

LLM can help:

- Render a bound question naturally.
- Explain why a question matters.
- Generate candidate seed questions for training.
- Cluster question failures.

LLM cannot:

- Mark unsupported questions as bound.
- Override evidence requirements.
- Replace the recommender policy.

## Acceptance

- Every user-visible question has a bound anchor.
- Every question can explain evidence and expected information gain.
- Synthetic question smoke cases pass.
- Unsupported question rate is tracked.
- Question policy can auto-apply after validation.
