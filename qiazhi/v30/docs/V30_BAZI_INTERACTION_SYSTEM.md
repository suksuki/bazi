# V30 Bazi Interaction System

Updated: 2026-06-13

## Purpose

V30's customer interaction loop must feel simple while the backend remains intelligent.

The product interaction is:

```text
BirthInput
-> concise Bazi reading surface
-> user-facing recommended questions
-> direct answer
-> next recommended questions
-> structured calibration when needed
```

The user should not see internal calibration as the primary first-screen experience.

## Current Mainline: Unified Interaction Brain

The unified interaction mainline is now closed at baseline:

```text
UIB-1 through UIB-7 complete
```

Reference:

```text
docs/V30_UNIFIED_INTERACTION_BRAIN_PLAN.md
```

The goal is to merge intelligent Q&A and hidden-factor calibration into one customer-visible dialogue. The customer should not see a separate hidden-factor form. Instead, the question brain chooses bounded Bazi questions, and some questions may collect structured hidden-factor signals through constrained controls.

Free-form text remains optional context only. It cannot update hidden-factor weights by itself.

## Question Layers

V30 separates question behavior into three layers:

```text
user_question
structured_option
calibration_probe
```

`user_question` is the normal customer-facing question. It should be phrased as something the user wants to ask the system, for example:

- 事业适合稳定发展还是转型突破？
- 财运更适合主动争取还是保守积累？
- 感情关系里最容易反复的问题是什么？
- 当前大运和流年压力主要体现在哪里？
- 这个八字最需要注意的决策盲点是什么？

`structured_option` is a standardized button choice. It helps the system record user intent without relying on free-form text. Examples:

- 事业
- 财务
- 关系
- 时机

`calibration_probe` is internal or advanced. It includes hidden factors, special-year confirmation, repeated-state discovery, useful-god candidate review, and structure dynamic review. Under the UIB mainline, customer-visible calibration probes must be projected as bounded Bazi questions with `answer_constraints`, not as an unstructured free-text form.

## Answer Constraints

Customer-visible questions may carry:

```text
answer_constraints
```

The UI must render these as structured controls. Examples:

- Year chips and valid add-year input.
- State-tag chips such as 事业压力, 财务波动, 关系反复, 作息波动, 学习/证书压力.
- Intensity selection.
- Recurrence selection.
- Confidence selection.
- Negative evidence options such as "不像我" or "没有明显发生".

If the user response does not satisfy the constraint, the UI/API must ask the user to correct the input rather than updating hidden-factor state.

Free text is saved as a note only.

## Runtime State

Question state is stored under `QuestionIntentPlan.session_state` and policy effects.

The intended state model is:

```text
interaction_stage
selected_domain
answered_question_ids
selected_option_ids
known_user_signals
suppressed_calibration_topics
visible_next_question_id
internal_next_question_id
next_question_strategy
```

Current implementation stores `question_outcomes`, selected options, and compact `known_user_signals`, then consumes them when recomputing recommendations. Answered user questions are strongly suppressed so the next visible recommendation changes. The recommender also consumes `model_signal_summary.energy_bands`, so different Bazi contexts can produce different customer-visible top questions instead of a fixed template order.

Current explicit state payload:

```text
v30.interaction_state.v1
interaction_stage
selected_domain
answered_question_ids
selected_option_ids
known_user_signals
visible_next_question_id
internal_next_question_id
followup_reason
```

`QuestionDialogueGraph.next_question_id` remains backward compatible. `QuestionDialogueGraph.internal_next_question_id` is the internal strategy pointer. Presentation projects `visible_next_question_id` for guest/user surfaces.

## API Contract

The UI should remain stable and thin:

```text
GET /api/v30/ui/capabilities
POST /api/v30/readings
GET /api/v30/readings/{reading_id}/view
POST /api/v30/readings/{reading_id}/questions/{question_id}/answer
```

`GET /ui/capabilities` exposes the public projection contract for a thin UI:

```text
locales: zh, en, ko
clients: web, mobile, admin
roles: guest, user, practitioner, admin
boundary: ui_capabilities_describe_projection_not_bazi_facts
```

The API contract also declares:

```text
structured_answer_contract: v30.answer_constraints.v1
interaction_brain_result_contract: v30.unified_interaction_brain_result.v1
diagnostic_summary_contract: v30.interaction_brain_diagnostics_summary.v1
synthetic_tier: interaction_brain_structured_constraints
dedicated_interactions_endpoint: deferred_until_answer_endpoint_stable
```

The UI may pass `locale` and `client` through create, view, and answer calls. These parameters only change wording, density, question count, and layout projection. They do not mutate chart facts, pillars, hidden-factor state, or policy decisions.

Role is also a projection parameter:

```text
guest -> preview surface, compact customer-safe content
user -> customer reading surface, six-pillar display, question loop
practitioner -> practitioner review surface, bounded diagnostics, no admin actions
admin -> operations surface, diagnostics and admin actions
```

V30 uses one role-aware presentation contract instead of separate V20-style workbench pages. The frontend can switch pages by changing `role`, `locale`, and `client` on `GET /view`; backend role gating decides what is visible. Guest/user views stay customer-safe. Practitioner/admin views may inspect diagnostics, but still cannot mutate chart facts through projection.

`GET /view` returns:

```text
reading_surface
questions[]
answer_panel
actions[]
next_question_id
```

For guest/user roles:

- `questions[]` contains user-facing `user_question` rows.
- `reading_surface.options[]` contains structured choices.
- Calibration probes are hidden from default questions.
- `next_question_id` is always the customer-visible next question.

For practitioner/admin/lab roles:

- Diagnostics may expose calibration probes, internal Bazi context, question graph, policy reasons, and replay payloads.
- Diagnostics may include `internal_next_question_id` for strategy inspection.
- Customer-facing presentation must still use `next_question_id`, not `internal_next_question_id`.

## Interaction Rules

1. The first screen should answer user intent, not ask internal calibration questions.
2. A user can click a question directly; free text is optional supplemental context.
3. After a question is answered, it must not remain the top visible question.
4. The next question should follow from the selected domain, answered question, and current chart gaps.
5. Hidden factor and useful-god probes can condition follow-up ordering but cannot become chart facts.
6. LLM output is expression only. It cannot create pillars, luck-cycle facts, flow facts, hidden-factor facts, or fixed verdicts.
7. Hidden-factor calibration can only consume structured payloads that pass whitelist validation.
8. Free-text-only answers can refresh expression context but cannot update hidden-factor weights.
9. Invalid constrained answers keep the current question active with correction guidance.

## Current V1 Implementation

Implemented:

- User-facing product question anchors for career, wealth, relationship, timing, and decision blind spots.
- `recommend_questions()` emits `interaction_type` and `answer_mode`.
- Guest/user presentation filters default visible questions to `interaction_type=user_question`.
- Calibration probes remain in runtime recommendations and diagnostics.
- Answered questions receive strong suppression, so visible next question changes.
- Customer reading surface exposes structured `options`.
- Structured selected options are recorded as dialogue state.
- Compact `known_user_signals` are retained for question strategy and answer context.
- `QuestionDialogueGraph.next_question_id` drives the customer-visible next question after answer submission.
- Admin diagnostics can inspect internal next-question strategy separately from the customer-visible next question.
- Runtime emits `interaction_state`.
- Customer reading surface exposes `visible_next_question_id`, `interaction_stage`, and `selected_domain`.
- Answer API returns `interaction_state` together with the refreshed view.
- UI uses click-to-answer behavior instead of requiring free-form text first.
- IQ1 verifies the 8-point intelligent question interaction audit and passes 8/8.

Boundary:

```text
user_question_and_structured_options_drive_question_strategy_not_chart_facts
```

## Next Targets

- `UIB-2` answer constraint schema and validator: completed baseline.
- `UIB-3` unified interaction brain runtime: completed baseline.
- `UIB-4` unified customer UI: completed baseline.
- `UIB-5` next-question scoring: completed baseline.
- `UIB-6` interaction brain structured constraints synthetic/training tier: completed baseline.
- `UIB-7` closeout and diagnostics/API documentation: completed baseline.
- Add a dedicated `/interactions` endpoint only after the existing answer endpoint additive contract is stable.
