# V30 Architecture Contract

Updated: 2026-05-20

## Design Position

V30 is a clean Bazi runtime with explicit separation between fact, inference, projection, rendering, and observation.

V30 keeps the successful V20 principles:

- Deterministic chart facts.
- Current-context binding.
- Structure dynamic mainline.
- Evidence-weighted arbitration.
- Anchored questions.
- Role-aware projection.
- Training changes only through policy pointers.
- LLM is assistive and bounded.

V30 removes the V20 failure modes:

- No single giant runtime payload for all consumers.
- No UI reading internal runtime fields directly.
- No question title as an internal/external mixed field.
- No role projection rewriting facts.
- No training artifact directly mutating runtime truth.
- No V20 runtime imports.

## Core Pipeline

V30 runtime pipeline:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> QuestionIntentPlan
-> BaziQuestionAnchor[]
-> AnswerContext
-> AnswerResult
```

Projection pipeline:

```text
CoreRuntimeResult
-> RoleProjection
-> LocaleRendering
-> ClientPresentationModel
```

Observation pipeline:

```text
RuntimeTrace
-> AdminTraceView
-> ValidationResult
-> FeedbackEvent
-> PolicyCandidate
-> PolicyPointer
```

## Contracts

### ChartContext

Current chart and supplied time context. It is immutable during one reading.

Required fields:

```text
context_id
reading_id
input_pillars
natal_pillars
day_master
day_master_element
time_layers
locale
created_at
```

Rules:

- No downstream module may change chart facts.
- Calendar and time expansion must be deterministic.
- Missing time layers must be represented explicitly.

### FeatureEvidence

Typed evidence extracted from the chart and time context.

Required fields:

```text
evidence_id
domain
kind
label
source
confidence
supports
weakens
boundary
```

Rules:

- Evidence supports or weakens a conclusion; it is not itself a verdict.
- Evidence must link back to `ChartContext`.

### StructureState

Current dynamic structure state.

Required fields:

```text
structure_id
primary_chain
candidate_chains
graph_nodes
graph_edges
path_scores
semantic_label
state
confidence
evidence_ids
boundary
```

Rules:

- Structure extraction is deterministic.
- Semantic naming must come from reviewed mechanism definitions.
- No fallback generic label may appear in user-facing output when a reviewed mechanism matches.

### MainlineState

Selected reading mainline.

Required fields:

```text
mainline_id
domain
title
state
score
primary_structure_id
evidence_ids
supporting_mainlines
rejected_mainlines
why_selected
quality_gate
```

Rules:

- Mainline arbitration can rank, not invent facts.
- The selected question can bias tie-breaking but cannot override strong structure evidence without a review flag.

### QuestionIntentPlan

Internal plan for what to ask next.

Required fields:

```text
plan_id
role_key
session_state
candidate_intents
suppressed_intents
policy_effect
```

Rules:

- Intent is not display text.
- Templates are never rendered directly to user UI.

### BaziQuestionAnchor

Evidence-bound display question contract.

Required fields:

```text
anchor_id
question_id
intent_id
context_id
role_key
anchor_status
day_master
time_binding
primary_structure_id
mainline_id
evidence_ids
why_this_question
missing_requirements
```

Allowed `anchor_status`:

```text
bound
weak
missing_time
missing_structure
unsupported
```

Rules:

- User and guest views show only `bound` anchors.
- Practitioner/admin views may show weak or missing anchors with diagnostics.
- Display labels are rendered from anchors, not from raw templates.

### AnswerContext

Compact verified context for deterministic answer and optional LLM.

Required fields:

```text
answer_context_id
selected_question_anchor
chart_summary
structure_summary
mainline_summary
evidence_summary
knowledge_boundaries
role_answer_contract
forbidden_drift
```

Rules:

- LLM may consume `AnswerContext`, not raw runtime trace.
- Day master, pillars, time layers, and selected anchor are immutable.
- Answer must explain why the selected question belongs to the current chart.

### CoreRuntimeResult

Internal runtime output.

Required fields:

```text
reading_id
chart_context
feature_evidence
structure_state
mainline_state
question_plan
question_anchors
answer_context
answer_result
trace_id
```

Rules:

- Used by backend and validation.
- Not directly sent to ordinary UI.

### RoleProjection

Role-scoped visibility and language density.

Supported roles:

```text
guest
user
practitioner
analyst
admin
lab
```

Rules:

- Role changes visibility and expression only.
- Role cannot change facts, structure, mainline, or evidence IDs.

### LocaleRendering

Locale-scoped rendered labels.

Initial locales:

```text
zh
en
ko
```

Rules:

- Rendering may explain terms.
- Rendering may not translate into new claims.
- Internal IDs are never exposed in guest/user views.

### ClientPresentationModel

Frontend-facing view model.

Required fields:

```text
reading_id
role_key
locale
client
layout
header
chart_summary
mainline_card
structure_card
questions
answer_panel
actions
diagnostics
```

Rules:

- Frontend renders this model directly.
- Frontend does not inspect raw runtime fields.
- Admin/lab diagnostics are explicit sections, not hidden fields in user cards.

### ValidationCase

Unified V30 validation schema.

Required fields:

```text
case_id
source
chart_context
expected_structure
expected_mainline
expected_questions
expected_answer_boundaries
negative_expectations
role_expectations
locale_expectations
client_expectations
```

Rules:

- V20 cases must be converted into this schema before V30 uses them.
- Validation checks positive expectations and forbidden drift.

## Service Isolation Contract

V30 service must use only V30 env names:

```text
V30_DATABASE_URL
V30_REDIS_URL
V30_REDIS_PREFIX
V30_RUNTIME_DIR
V30_HOST
V30_PORT
```

V30 Redis keys:

```text
v30:{env}:reading:{reading_id}
v30:{env}:trace:{trace_id}
v30:{env}:feedback:{event_id}
v30:{env}:policy:{family}
v30:{env}:lock:{name}
```

V30 DB names:

```text
v30_readings
v30_runtime_traces
v30_feedback_events
v30_validation_cases
v30_policy_pointers
v30_artifacts
```

## V30 First Acceptance Gate

V30 is allowed to become the active development target only when:

- The scaffold has no `v20.*` runtime imports.
- The V30 smoke service starts on a V30-only port.
- V30 creates no V20 DB table and reads no V20 table.
- V30 Redis keys all start with `v30:`.
- 10 converted synthetic cases pass.
- UI consumes `ClientPresentationModel`.
- User question labels all come from bound anchors.
