# V40 Phase 46: User Product Shell Runtime

Date: 2026-07-01

## Goal

Turn the Phase 45 UI product contract into the first real V40 user-side product shell.

This phase is not another design pass. It changes `/v40/ui` from a historical debug-like page into a report-first product runtime:

```text
Input Workspace
→ Reading Surface
→ Follow-up Hub
→ Conversation Surface
→ Probe Calibration Surface
→ Practitioner Lens drawer
```

## Implemented

### 1. Independent User UI Template

`/v40/ui` now reads:

```text
v40/api/user_ui.html
```

`v40/api/app.py` only serves the template. This separates the product surface from API routing and stops the user UI from growing inside the server file.

### 2. Input Workspace

The page now uses:

- Topic selector.
- Gender selector.
- Four-pillar stem/branch selectors.
- Collapsed luck/year settings.
- User question input.

Removed from ordinary user UI:

- Execution mode dropdown.
- Role dropdown.
- Provider/model status.
- Engineering readiness endpoint display.

Phase 46 originally used a temporary URL role hook:

```text
/v40/ui                  -> user
/v40/ui?role=practitioner -> practitioner Lens enabled
```

Phase 49 replaces this with `/api/v40/session/context`. The user app must no longer parse URL query parameters for role.

### 3. Reading Surface

Report rendering now consumes structured runtime projection first:

```text
runtime.product_projection.verdict_cards
runtime.product_projection.advice_cards
runtime.verdicts[].forbidden_assertions
runtime.probes
```

The main report is rendered as:

- VerdictHero.
- Topic judgment cards.
- Advice card with `适合做 / 暂时避免 / 需要确认`.
- RiskBoundary card.
- Folded ThinkingSummaryDisclosure.

LLM text is still allowed as expression output, but it is no longer the page's only structure.

### 4. Conversation After Report

Follow-up questions are generated only after the report is accepted.

Clicking a seed or typing a question calls:

```text
POST /api/v40/conversation/turn
```

The report remains stable:

- No page refresh.
- No report rerun.
- No verdict mutation.
- No chart fact mutation.

### 5. Probe Calibration Surface

Probe is now a separate calibration card, not part of ordinary conversation.

It can appear when:

- Runtime marks a Probe as `ask_now`.
- User feedback says "不太像".
- User picks a mismatch area such as 财富来源、事业方向、感情模式、建议不适合.

Current phase records Probe answers as `TrainingLabelEvent(local_only=true)`.

Phase 47 adds the full endpoint:

```text
POST /api/v40/probes/answer
```

and return:

```text
AnswerSignal
HiddenAttributeUpdate
LocalOverlay
refined advice
```

### 6. Practitioner Lens Drawer

Practitioner Lens is now a role-gated right drawer.

It shows:

- Main verdict.
- Branch candidates when present.
- Ziwei side signals when present.
- Human-language calibration actions.

It does not show:

- raw ids as primary labels.
- provider/model.
- prompt.
- acceptance internals.
- production weight.
- Admin links.

Actions call:

```text
POST /api/v40/calibration/practitioner-lens-action
```

The UI sends actions as local calibration material and does not directly mutate verdicts, chart facts, or production weights.

### 7. Hidden Information Scan

The rendered `/v40/ui` response no longer contains:

```text
execution_mode
Gemma4
Local
Ollama
provider
model
acceptance
policy
debug
telemetry
TrainingLabelEvent
roleKey
表达方式
/admin/v40
```

The page still uses the LLM runtime internally by sending `ollama` mode through a non-visible JavaScript key construction. The ordinary user does not see the execution mode.

## Tests

Updated test coverage:

```text
tests/test_v40_phase20_user_report_ui.py
tests/test_v40_phase29_practitioner_ui_calibration.py
tests/test_v40_phase39_user_surface_beta_readiness.py
```

The checks now assert:

- report-first surface exists.
- execution mode and role dropdown are not exposed.
- follow-up and conversation endpoints are wired.
- Practitioner Lens is a drawer-style role surface.
- Admin remains separated.
- surface beta readiness remains ready under the new UI vocabulary.

## Remaining Work

1. Feed `ProbeAnswerResult` into later conversation context. Done in Phase 48.
2. Replace temporary URL role hook with auth-derived role context. Done in Phase 49.
3. Run browser visual QA across desktop and mobile.
4. Add consent contracts before human practitioner review.
5. Continue real case evaluation and training replay before production cutover.

## Boundary

Phase 46 changes the user product surface. It does not:

- Write V30 state.
- Activate production weights.
- Change chart facts.
- Give LLM verdict authority.
- Merge Admin back into the user app.
