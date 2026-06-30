# V40 Phase 19: Native Report Runtime

Date: 2026-06-30

## Goal

Phase 19 adds the first product-facing V40 runtime entry point.

Before this phase, callers had to run:

```text
native runtime
then expression
then acceptance
then telemetry
```

Now one endpoint composes that flow.

## Endpoint

```text
POST /api/v40/readings/native-report
```

Input:

```text
request_id
reading_id
chart_facts
user_question
topic
role_key
execution_mode = local | provider_text | ollama
provider_text / provider / model / raw_thinking
persist
```

Output:

```text
runtime
surface_bundle
accepted_text
accepted
expression.task
expression.result
expression.acceptance
expression.telemetry
```

## Runtime Binding

The returned `RuntimeResult` now binds:

```text
expression_task
expression_result
acceptance_result
expression_telemetry
```

This makes the report output auditable from one runtime object.

## Boundaries

The endpoint:

```text
runs V40 native Bazi only
does not read V30 runtime
does not write V30 state
does not let LLM change verdicts
does not let LLM create chart facts
does not write V40 production policy
persists only to v40_runtime_records when persist=true
```

If `execution_mode=ollama` and the model is unavailable, the endpoint returns `503`; it does not fall back to local expression.

## Tests

Added:

```text
tests/test_v40_phase19_native_report_runtime.py
```

Coverage:

```text
native report returns runtime + expression + telemetry
RuntimeResult contains expression_task/result/acceptance/telemetry
surface_bundle remains report-first
provider_text mode accepts external expression and thinking trace
no V30 writes and no V40 production writes
```

## Phase 20 Handoff

Phase 20 added:

```text
minimal V40 user page / UI route for native report
report accepted text as primary first-screen content
provider status lookup
expression telemetry display
no fallback display when explicit Ollama execution is unavailable
```

Still open after Phase 20:

```text
conversation seed generation after accepted report
telemetry persistence/history for report runs
safe public-thinking streaming contract
```
