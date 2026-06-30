# V40 Phase 18: LLM Observability And Evaluation

Date: 2026-06-30

## Goal

Phase 18 turns the live Ollama/Gemma expression path into a visible, measurable runtime component.

The boundary remains:

```text
DecisionEngine decides.
LLM expresses.
Acceptance gates.
Evaluation measures.
```

LLM output still cannot mutate chart facts, verdicts, weights, V30 state, or V40 production policy.

## New Contract

```text
ExpressionTelemetry
```

It records:

```text
execution_mode
provider / model
accepted / acceptance_status
thinking_trace_available / thinking_trace_chars
repair_reasons
leakage_hits / overclaim_hits
verdict_mutation_detected
chart_fact_mutation_detected
llm_decision_authority
```

This is observability only. It is not a decision source.

## Expression API

```text
POST /api/v40/expression/from-runtime
```

now returns:

```text
task
result
acceptance
telemetry
accepted
```

The telemetry can be passed into evaluation.

## Evaluation Metrics

`MetricSummary` now includes:

```text
expression_acceptance_rate
expression_thinking_trace_rate
```

When no expression telemetry is supplied, legacy deterministic evaluation keeps `expression_acceptance_rate = 1.0`.

When expression telemetry is supplied:

```text
accepted expression -> expression_acceptance_rate = 1.0
rejected / repair expression -> expression_acceptance_rate = 0.0
Ollama thinking trace captured -> expression_thinking_trace_rate = 1.0
```

Hard LLM boundary failures still set:

```text
llm_boundary_violation_rate = 1.0
```

Release gate now requires:

```text
llm_boundary_violation_rate == 0
expression_acceptance_rate >= 1.0
```

## Ollama Model Discovery

New runtime endpoint:

```text
GET /api/v40/expression/provider/ollama/models
```

It calls:

```text
GET {base_url}/api/tags
```

and reports:

```text
configured_model
models
configured_model_available
```

No secrets are exposed and no runtime state is written.

## Admin Visibility

New Admin proxy endpoints:

```text
GET /admin/v40/api/llm
GET /admin/v40/api/llm-models
```

The Admin page now includes an LLM section showing:

```text
configured model
base URL
effective thinking max tokens / timeout
discovered model list
configured model availability
```

## Tests

Added:

```text
tests/test_v40_phase18_llm_observability.py
```

Coverage:

```text
Ollama model discovery parses /api/tags
runtime model discovery API returns non-mutating catalog
Admin page exposes LLM status/model endpoints
accepted expression telemetry enters MetricSummary and release gate
rejected expression telemetry blocks LLM gate
```

## Next Phase

Phase 19 should connect this into the product runtime:

```text
report-first user result endpoint with optional execution_mode=ollama
conversation seed generation after accepted report output
expression telemetry persistence/history
live streaming of safe public thinking lines
larger golden/synthetic expression corpus
```
