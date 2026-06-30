# V40 Phase 20: User Report UI

Date: 2026-06-30

## Goal

Phase 20 adds the first V40 user-facing page.

It is intentionally small:

```text
enter chart facts
choose local or Gemma4 expression
call native report runtime
show accepted report text first
show expression telemetry
```

This is not the final product UI. It is the first report-first surface for validating the V40 runtime end to end.

## Route

```text
GET /v40/ui
```

The page calls:

```text
GET  /api/v40/expression/provider/ollama
POST /api/v40/readings/native-report
```

## UI Shape

The page keeps the flow simple:

```text
left: chart facts and question
right: accepted report text and telemetry
```

The report panel shows:

```text
accepted_text
model/provider
thinking trace character count
acceptance status
```

If Gemma4 is unavailable and `execution_mode=ollama`, the page shows the model error and does not substitute local fallback text.

## Boundary

The UI:

```text
does not authenticate users
does not manage profiles
does not write V30
does not write V40 production policy
does not let LLM change verdicts
does not hide model unavailability behind fallback
```

## Tests

Added:

```text
tests/test_v40_phase20_user_report_ui.py
```

Coverage:

```text
/v40/ui serves a report-first page
page references native report endpoint
page references Ollama provider status
page exposes execution_mode
```

## Next Phase

Phase 21 should make the report interactive:

```text
conversation seed generation after accepted report
question suggestions bound to verdict/advice/probes
separate conversation runtime endpoint
telemetry history for UI sessions
safe public-thinking streaming
```
