# V30 Surface Orchestrator Mainline

Date: 2026-06-30

## Core Principle

V30 must separate four user-facing surfaces:

```text
Reading first.
Probe only when valuable.
Chat only when invited.
Thinking only when requested.
```

The Bazi calculation flow is not the dialogue flow. They can share runtime context, but they must not share page ownership.

## Four Surfaces

| Surface | Role | User Meaning | Auto Show |
| --- | --- | --- | --- |
| `ReadingSurface` | Main report and verdict/advice output | "Here is the current Bazi reading result." | Yes |
| `CalibrationSurface` | High-value Probe card | "Answer this only if it improves this judgment." | Collapsed or contextual |
| `ConversationSurface` | Continuous intelligent Bazi dialogue | "Ask another question or continue a question chain." | No |
| `ThinkingSurface` | Stage reasoning/process view | "Show how the system reached this result." | No |

## Boundary

`SurfaceOrchestrator` is a presentation router, not a metaphysics decision engine.

It may decide where a signal appears, but it must not:

- rewrite chart facts;
- change deterministic pillars, luck cycles, or natal facts;
- invent verdicts;
- treat a dialogue question as a report result;
- let the frontend pick questions from legacy arrays.

## Runtime Inputs

The orchestrator consumes already-produced runtime artifacts:

- `DecisionContract` / `final_synthesis`: verdict, advice, risk boundary, evidence summary.
- `SignalRegistry` / module outputs: features, rules, portrait, paths, timing, domain signals.
- `surface_decision_fields`: central brain surface route for calibration, conversation, and thinking.
- `current_dialogue_turn`: legacy central brain question decision retained only for diagnostic compatibility.
- `DialogueChain`: seed questions and user-initiated continuous sessions.
- `StagePoints`: fast calculation stages and optional reasoning trace.

## Output Pipeline Contract

`SurfaceOrchestrator` exposes `v30.surface_output_pipeline.v1` so product output is auditable:

```text
SignalRegistry
  -> DecisionContract
  -> Verdict
  -> Advice
  -> Explanation
  -> DialogueRefinement
```

Responsibilities:

- engines and `SignalRegistry` produce evidence-bound materials;
- `DecisionEngine` is the only Verdict authority;
- central brain orchestrates evidence weights, feedback, quality gates, and surface routing;
- LLM acts after core verdict as expression and dialogue language adapter;
- calibration and conversation feedback refines future context without mutating chart facts.

## Output Contract

`reading_surface.surface_orchestrator` is the new routing contract.

```text
reading_surface
  ├─ report content
  ├─ surface_orchestrator
  ├─ calibration_surface
  ├─ conversation_surface
  └─ thinking_surface
```

Legacy fields such as `current_dialogue_turn`, `next_question`, `dialogue`, and `options` are no longer direct customer product entries. Customer projections expose only `legacy_dialogue_surface.status=hidden_for_customer`; diagnostic roles may still receive the compatibility payload.

## ReadingSurface Rules

- Always show verdict/advice and page-specific facts before any question.
- Do not embed an active conversation question in the stage report body.
- Do not show engineering/debug language.
- Support concise list-style output for sidebar reuse and practitioner review.

## CalibrationSurface Rules

Probe appears only when it has high value of information.

Allowed triggers:

- hidden attribute calibration;
- conflicting evidence that blocks a verdict;
- an explicit branch where one user answer can materially change advice.

Constraints:

- default maximum visible cards: one;
- must be skippable;
- must name what it will refine;
- must produce structured output such as `AnswerSignal`, `HiddenAttributeUpdate`, `SignalConfidenceDiff`, or `VerdictAdviceRefinement`.

## ConversationSurface Rules

The continuous intelligent Bazi dialogue is independent from reading stages.

- It can appear on any page as an invited surface.
- It must not automatically interrupt a report stage.
- It can start from system seed questions or user questions such as "我今年财运如何？"
- Each answer should create the next relevant question candidates.
- It should update context and then refine future verdict/advice, not mutate chart facts.

## ThinkingSurface Rules

Thinking is process visibility, not a mandatory report section.

- Stage reasoning can be shown on request.
- It must not contain raw JSON, schema checks, prompt fragments, or internal debug text.
- It should be short, customer-safe, and tied to visible evidence.

## State Machine

```text
reading_first
  -> optional_calibration_probe
  -> refined_reading
  -> optional_conversation
  -> context_update
  -> refined_reading
```

Probe and conversation can both feed the central brain, but they enter different channels:

- Probe feeds structured calibration.
- Conversation feeds user intent, domain focus, and lived-context signals.

## Acceptance Checks

- A calculation step page must not render a generic `current_dialogue_turn`.
- Customer `reading_surface` must not directly expose `current_dialogue_turn`, `next_question`, or `options`.
- Diagnostic roles may inspect those legacy fields through `legacy_dialogue_surface.payload`.
- A stage page may render only a `CalibrationSurface` card when the orchestrator marks it contextual and valuable.
- Continuous dialogue must live in `ConversationSurface`, not inside the calculation step.
- The frontend must render `ConversationSurface` as an invitation launcher first; it may load seeds and sessions only after the user opens it.
- Answer submission must carry an explicit surface source. `CalibrationSurface` uses `v30.surface_submit_contract.v1`; `ConversationSurface` uses dialogue session endpoints.
- `ReadingSurface` stays readable without LLM dialogue text.
- Legacy compatibility fields are retained until old clients are removed.

## Implementation Plan

| Task | Status | Result |
| --- | --- | --- |
| `SO-1` | Done | Added this mainline design document and indexed it. |
| `SO-2` | Done | Added backend `SurfaceOrchestrator` projection contract. |
| `SO-3` | Done | Routed `calibration_surface`, `conversation_surface`, and `thinking_surface` into `reading_surface`. |
| `SO-4` | Done | Updated frontend stage slot to read only `CalibrationSurface`. |
| `SO-5` | Done | Added unit tests for routing, probe gating, projection contract, and frontend source boundary. |
| `SO-6` | Done | Removed direct stage-page usage of legacy `current_dialogue_turn`; field remains only for compatibility. |
| `SO-7` | Done | Changed frontend `ConversationSurface` to invitation-first launcher; seed/session loading starts only after user opens it. |
| `SO-8` | Done | Added explicit surface submit contracts. Calibration cards carry `submit_surface=calibration_surface`; continuous chat stays on dialogue endpoints; legacy answer source is compatibility-only. |
| `SO-9` | Done | Customer projections hide direct legacy `current_dialogue_turn / next_question / options`; diagnostic roles keep them under `legacy_dialogue_surface.payload`. |
| `SO-10` | Done | Updated `QuestionDialogueGraph`, `DialoguePlan`, `CentralReadingState`, DCA checks, and quality audit labels from `reading_surface.current_dialogue_turn` to `reading_surface.conversation_surface` plus `surface_decision_fields`; old field is now `legacy_customer_decision_field`. |
| `SO-11` | Done | Added API-level regression gate: ordinary `/view` and `/answer` responses must not expose direct `current_dialogue_turn / next_question / options`; practitioner diagnostic payload remains available. |
| `SO-12` | Done | Added `v30.surface_output_pipeline.v1` contract to runtime projection and tests: SignalRegistry -> DecisionContract -> Verdict -> Advice -> Explanation -> DialogueRefinement. |

## 2026-06-30 Closeout

SO-10 to SO-12 are complete.

Validation:

```text
node --check frontend/app.js
/tmp/qiazhi-v30-py312-test/bin/python -m py_compile ...
/tmp/qiazhi-v30-py312-test/bin/python -m pytest -q \
  tests/unit/test_surface_orchestrator.py \
  tests/unit/test_presentation_projection.py \
  tests/unit/test_decision_centered_architecture.py \
  tests/unit/test_text_to_option_interaction.py \
  tests/unit/test_dialogue_chain_mainline.py \
  tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params
```

Result: `33 passed`, one known Starlette/httpx deprecation warning.
