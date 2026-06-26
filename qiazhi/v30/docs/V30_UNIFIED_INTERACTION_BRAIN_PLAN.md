# V30 Unified Interaction Brain Mainline Plan

Updated: 2026-06-13

## Purpose

V30 must stop treating "智能问答" and "隐藏属性/隐藏因子反馈" as two separate product flows.

The product experience should be one continuous Bazi dialogue:

```text
User asks or selects a bounded question
-> Unified Interaction Brain parses the turn
-> structured signals update interaction state and hidden-factor calibration
-> Bazi reading answer refreshes
-> next question is selected from chart uncertainty, hidden-factor uncertainty, domain focus, and training value
```

The user should feel they are discussing one Bazi chart. Internally, the system may calibrate hidden factors, dynamic paths, useful-god candidates, and domain reading confidence, but these must remain support signals and must never mutate deterministic chart facts.

HF-R1.1 alignment:

```text
structured answer
-> interaction_turn_signal
-> hidden_factor_feedback_payload
-> HiddenFactorState
-> LatentBaziProfile
-> RBD / question strategy / training calibration
```

Downstream modules should consume `v30.latent_bazi_profile.v1` instead of treating raw hidden-factor state as a measurement input. Customer-facing language uses “校准线索/背景校准线索”; admin diagnostics may keep internal keys for traceability.

## Controlling Requirement

All hidden-factor and interaction calibration must be constrained.

Free text is allowed only as a note for expression and practitioner/admin review. It must not directly update hidden-factor weights, chart facts, pillars, luck cycles, flow years, or fixed Bazi verdicts.

Structured fields are the only inputs allowed to update hidden-factor calibration:

```text
year selections
state tag selections
domain selections
intensity selection
recurrence selection
confidence selection
negative / not-like-me selections
```

If a user answer does not satisfy the active constraint, the UI/API must ask the user to reselect or correct the input instead of silently accepting noisy data.

## Current Mainline

```text
UIB-7 Closeout
```

Status: UIB-1 through UIB-6 complete; UIB-7 selected next.

Reason: this is not UI polish. It affects the core Bazi measurement loop because uncontrolled free-form hidden-factor answers can pollute calibration, training, question strategy, and LLM context. The system needs one coordinated interaction brain that can ask bounded questions while still supporting natural Bazi reading.

## Target Architecture

```text
Question / option / structured payload / note
-> InteractionTurnParser
-> ConstraintValidator
-> UnifiedInteractionBrain
   -> HiddenFactorSignal
   -> InteractionStateUpdate
   -> QuestionStrategyUpdate
   -> AnswerContextRefresh
   -> TrainingObservation
-> Presentation / UI
```

### Core Object: InteractionTurnSignal

```json
{
  "version": "v30.interaction_turn_signal.v1",
  "question_id": "q_v30_user_career_direction",
  "question_type": "domain_followup",
  "selected_domain": "career",
  "structured_payload": {
    "years": [2021, 2024],
    "state_tags": ["career_pressure", "credential_pressure"],
    "intensity": "medium",
    "recurrence": "repeated",
    "confidence": "approximate"
  },
  "free_note": "当时换岗并准备证书",
  "valid": true,
  "allowed_to_update_hidden_factor": true,
  "allowed_to_update_chart_facts": false
}
```

### Constraint Contract

Every customer-visible question may carry an `answer_constraints` payload:

```json
{
  "version": "v30.answer_constraints.v1",
  "constraint_type": "structured_hidden_factor",
  "required_fields": ["state_tags", "recurrence"],
  "optional_fields": ["years", "intensity", "confidence", "free_note"],
  "year_range": [1900, 2100],
  "allowed_state_tags": [
    "career_pressure",
    "role_change",
    "wealth_fluctuation",
    "partnership_distribution",
    "relationship_repetition",
    "family_pressure",
    "health_rhythm",
    "credential_pressure",
    "relocation_change"
  ],
  "free_note_policy": "store_as_note_only",
  "invalid_input_action": "ask_user_to_reselect"
}
```

## Structured Hidden-Factor Inputs

### Year Selection

- Use chips for recent years and a controlled add-year field.
- Only four-digit years inside the allowed range are accepted.
- Invalid years block submission and show a correction message.

### State Tags

Allowed initial tags:

| Tag | User label | Purpose |
|---|---|---|
| `career_pressure` | 事业压力 | Career/authority pressure calibration. |
| `role_change` | 岗位/职责变化 | Career path and authority-resource path calibration. |
| `wealth_fluctuation` | 财务波动 | Wealth path and resource distribution calibration. |
| `partnership_distribution` | 合作/分配问题 | Wealth/relationship boundary calibration. |
| `relationship_repetition` | 关系反复 | Relationship dynamic calibration. |
| `family_pressure` | 家庭压力 | Relationship/resource context calibration. |
| `health_rhythm` | 作息/身心节律波动 | Health rhythm and pressure calibration. |
| `credential_pressure` | 学习/证书/资质压力 | Resource/authority conversion calibration. |
| `relocation_change` | 迁移/环境变化 | Timing and external context calibration. |

### Intensity

```text
light
medium
strong
```

### Recurrence

```text
single
repeated
continuous
```

### Confidence

```text
certain
approximate
uncertain
```

### Free Note

Free note is preserved for:

- LLM expression context.
- Practitioner/admin review.
- Low-weight observation.

Free note is not allowed to:

- Update hidden-factor weights by itself.
- Create event facts.
- Change chart facts.
- Promote a fixed verdict.

## Question Types

| Type | Purpose | Input mode |
|---|---|---|
| `domain_followup` | Answer user-facing Bazi domain questions. | Structured domain option + optional note. |
| `structured_hidden_factor` | Calibrate hidden-factor hypotheses through controlled signals. | Years, state tags, recurrence, intensity, confidence. |
| `dynamic_path_calibration` | Clarify which dynamic path is active. | Candidate path options + not-like-me option. |
| `useful_god_candidate_calibration` | Compare useful-god candidate directions. | Candidate options + counter-evidence option. |
| `timing_context_check` | Clarify luck/flow relevance without inventing events. | Year selections + domain tags. |
| `negative_evidence_check` | Prevent self-confirming loops. | "不像我" / "没有明显发生" selections. |

## Scoring Model

The brain selects the next question by bounded information gain:

```text
next_question_score =
  domain_relevance * 0.25
+ hidden_factor_uncertainty * 0.25
+ dynamic_path_uncertainty * 0.20
+ user_recent_focus * 0.15
+ training_value * 0.10
+ negative_evidence_need * 0.05
```

Rules:

- Hidden-factor uncertainty can raise a question's priority, but it cannot override deterministic chart facts.
- Recently answered questions are suppressed.
- If structured constraints are unmet, the same question can be re-shown with correction guidance.
- Negative evidence checks must appear periodically for high-confidence but weakly supported hidden-factor hypotheses.

## UI Plan

The UI will expose one section:

```text
智能问答
```

It will contain:

1. Current question.
2. Structured answer controls based on `answer_constraints`.
3. Optional free-note field.
4. Submit button.
5. Answer panel with the current question shown at the top.
6. Historical question-answer list.

Remove the separate hidden-factor form from the customer flow. Hidden-factor calibration becomes a question type inside the same intelligent dialogue.

### UI Validation

If input is invalid:

- Do not submit the turn.
- Highlight the missing/invalid field.
- Tell the user to select from provided options or enter a valid year.
- Do not send a free-text-only hidden-factor update.

## API Plan

Short-term: extend the existing stable endpoint.

```text
POST /api/v30/readings/{reading_id}/questions/{question_id}/answer
```

Additive payload:

```json
{
  "answer": "optional free note",
  "selected_option": "domain:career",
  "structured_payload": {
    "years": [2021, 2024],
    "state_tags": ["career_pressure"],
    "intensity": "medium",
    "recurrence": "repeated",
    "confidence": "approximate"
  }
}
```

Additive response:

```json
{
  "interaction_brain_result": {
    "version": "v30.unified_interaction_brain_result.v1",
    "valid": true,
    "absorbed_signals": ["hidden_factor", "selected_domain"],
    "rejected_signals": [],
    "chart_fact_mutation_allowed": false
  }
}
```

Long-term: add a dedicated `/interactions` endpoint only after the additive answer endpoint is stable.

## Training And Synthetic Validation

Training may consume:

- Structured years.
- State tags.
- Recurrence.
- Intensity.
- Confidence.
- Selected domain.
- Question ID.
- Accepted/rejected constraint outcome.

Training may tune:

- Question strategy.
- Hidden-factor calibration weights.
- LLM answer specificity.
- Dynamic path confidence review ordering.

Training may not tune:

- Four pillars.
- Luck-cycle facts.
- Flow-year/month facts.
- Calendar conversion.
- Deterministic ten-god facts.

## Task Breakdown

### UIB-1 Contract And Mainline Documentation

Status: completed.

Deliverables:

- This plan.
- Current mainline task update.
- Interaction system doc update.
- Question intelligence doc update.

Acceptance:

- Mainline points to UIB as the next selected product-measurement task.
- Boundaries explicitly block chart-fact mutation and free-text hidden-factor updates.

### UIB-2 Constraint Schema And Validator

Status: completed.

Deliverables:

- `answer_constraints` projection on customer-visible questions.
- `StructuredInteractionPayload` / validator.
- Whitelist state tags.
- Year parser and range guard.

Acceptance:

- [x] Invalid year blocks hidden-factor update.
- [x] Unknown state tag blocks hidden-factor update.
- [x] Free-text-only hidden-factor answer is stored as note only.
- [x] Answer API accepts additive `structured_payload`.
- [x] Runtime emits `v30.interaction_turn_signal.v1`.
- [x] Runtime emits `v30.unified_interaction_brain_result.v1`.
- [x] Customer/admin question projection exposes `v30.answer_constraints.v1`.

Evidence:

```text
pytest -q tests/unit/test_interaction_constraints.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
9 passed

pytest -q tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context
2 passed
```

### UIB-3 Unified Interaction Brain Runtime

Status: completed baseline.

Deliverables:

- `process_interaction_turn(...)`.
- `InteractionTurnSignal`.
- `UnifiedInteractionBrainResult`.
- Hidden-factor update integration.
- Interaction-state update integration.

Acceptance:

- One answer turn can update selected domain and hidden-factor calibration.
- Chart fact fingerprint is unchanged.
- Rejected signals are visible in diagnostics.

Verification:

```text
python3 -m compileall -q v30/interaction_brain.py v30/interaction_constraints.py v30/runtime.py v30/api/app.py v30/presentation/client_model.py
pytest -q tests/unit/test_interaction_constraints.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
9 passed

pytest -q tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context
2 passed
```

### UIB-4 Unified UI

Status: completed baseline.

Deliverables:

- Remove separate hidden-factor customer form.
- Render structured controls from `answer_constraints`.
- Keep optional free note.
- Show absorbed/rejected signal summary in history.

Acceptance:

- Customer sees one intelligent question area.
- Hidden-factor calibration questions look like normal bounded Bazi questions.
- Invalid input asks user to reselect.

Verification:

```text
node --check frontend/app.js
pytest -q tests/unit/test_interaction_constraints.py tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
5 passed
```

### UIB-5 Next-Question Scoring

Status: completed baseline.

Deliverables:

- Score formula using domain relevance, hidden-factor uncertainty, dynamic-path uncertainty, recent focus, training value, and negative evidence need.
- Suppression for answered questions.
- Correction retry for invalid constrained input.

Acceptance:

- Next question changes after valid answer.
- Invalid constrained answer keeps the same question with correction prompt.
- Hidden-factor uncertainty can influence, but not dominate, the question queue.

Verification:

```text
python3 -m compileall -q v30/questions/recommender.py v30/runtime.py
pytest -q tests/unit/test_question_anchor_selector.py tests/unit/test_interaction_constraints.py tests/unit/test_question_dialogue_graph.py
18 passed

pytest -q tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions
3 passed
```

### UIB-6 Training And Synthetic Tier

Status: completed baseline.

Deliverables:

- `interaction_brain_structured_constraints` synthetic tier.
- Training extraction for accepted/rejected structured signals.
- Pollution-guard tests.

Acceptance:

- Structured hidden-factor case passes.
- Free-text pollution case passes.
- Negative evidence case passes.
- Chart facts remain unchanged.

Verification:

```text
python3 -m compileall -q v30/presentation/client_model.py v30/validation/synthetic_case.py v30/validation/training_signals.py
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_interaction_brain_structured_constraints_tier_passes
1 passed

python3 scripts/run_synthetic_validation.py --tier interaction_brain_structured_constraints
v30.synthetic.interaction_brain_structured_constraints: passed (3/3)

pytest -q tests/unit/test_interaction_constraints.py tests/unit/test_question_anchor_selector.py tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context
16 passed

pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_training_pipeline_tier_passes_training_contracts tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
2 passed
```

### UIB-7 Closeout

Status: completed baseline.

Deliverables:

- Admin diagnostics summary.
- Documentation sync.
- Targeted test baseline.

Acceptance:

- Targeted tests pass.
- Synthetic tier passes.
- No full pytest, synthetic-all, 518K full, or live LLM required unless selected as major node.

Verification:

```text
python3 -m compileall -q v30/api/app.py v30/presentation/client_model.py
pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context tests/unit/test_presentation_projection.py::test_practitioner_projection_can_inspect_bazi_context_without_admin_actions
4 passed
```

Closeout result:

- `/ui/capabilities` now declares `v30.unified_interaction_brain_result.v1`, `v30.interaction_brain_diagnostics_summary.v1`, invalid-input retry behavior, the dedicated synthetic tier, and the deferred `/interactions` endpoint decision.
- Admin/practitioner diagnostics now expose `interaction_brain_summary`; guest/user projections still hide diagnostics.
- The existing additive answer endpoint remains the stable integration point.

## Closeout Status

```text
UIB-1 through UIB-7 complete.
```

The unified interaction brain mainline is closed at baseline. Future work should return to core Bazi reading quality and synthetic archetype calibration unless a regression appears in structured interaction.

## Verification Plan

Routine targeted checks:

```text
pytest -q tests/unit/test_question_dialogue_graph.py tests/unit/test_training_signals.py
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
python3 scripts/run_synthetic_validation.py --tier interaction_brain_structured_constraints
node --check frontend/app.js
python3 -m compileall -q v30
```

Major-node explicit checks only:

```text
pytest -q
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode full --confirm-full
python3 scripts/run_llm_live_smoke.py --json
```

## Non-Goals

- Do not create or mutate chart facts from user feedback.
- Do not treat free text as hidden-factor evidence by itself.
- Do not add a full login/permission redesign.
- Do not run full 518K by default.
- Do not make LLM the hidden-factor authority.
