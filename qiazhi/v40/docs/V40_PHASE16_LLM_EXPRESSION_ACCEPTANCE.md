# V40 Phase 16: LLM Expression Acceptance

Date: 2026-06-30

## Goal

Phase 16 connects the expression layer without giving LLM decision authority.

The core rule remains:

```text
DecisionEngine decides.
LLM expresses.
AcceptanceResult gates.
```

LLM output may improve wording, rhythm and readability. It may not:

```text
change DecisionVerdict
create chart facts
invent year-specific outcomes
exceed forbidden assertions
leak internal engineering terms
write training weights
write V30 state
```

## New Module

```text
v40/expression/engine.py
```

Main functions:

```text
build_expression_task_from_runtime()
render_local_expression_result()
accept_expression_result()
```

`render_local_expression_result()` is a local expression adapter for contract testing and smoke runs. Real Ollama/Gemma provider integration should later return the same `LLMExpressionResult` contract and pass through the same acceptance scanner.

## Runtime Contracts

`RuntimeResult` now has optional fields:

```text
expression_task
expression_result
acceptance_result
```

They are optional so native runtime can still produce pure deterministic output without calling an LLM.

## Acceptance Scanner

The scanner checks:

```text
internal leakage terms
overclaim terms
forbidden assertions from DecisionVerdict
chart fact mutation phrases
whether allowed assertions were preserved
```

Accepted output requires:

```text
status = accepted
accepted_text is present
no leakage hits
no overclaim hits
no verdict mutation
no chart fact mutation
```

Rejected or repair-needed output can record hits and reasons:

```text
hard_reject
repair
reask
salvage
```

## API

New endpoint:

```text
POST /api/v40/expression/from-runtime
```

It accepts:

```text
RuntimeResult
optional provider_text
provider/model metadata
task_id/result_id/acceptance_id
```

If `provider_text` is empty, V40 uses the local expression adapter.

If `provider_text` is provided, V40 treats it as an external LLM result and only runs acceptance.

The endpoint returns:

```text
LLMExpressionTask
LLMExpressionResult
AcceptanceResult
accepted boolean
```

It does not persist or write production state.

## CLI

New command:

```bash
python scripts/v40_artifact_cli.py render-native-expression \
  --path data/synthetic/native_bazi_seeds.json \
  --seed-id native.career.bingchen.001 \
  --reading-id reading.local.expression.001
```

## Product Boundary

This phase is not yet full live LLM streaming.

It establishes the protocol needed for live LLM:

```text
prepare prompt task
call provider
capture text/thinking if available
acceptance scan
only accepted text reaches user surface
```

## Tests

Added:

```text
tests/test_v40_phase16_expression_acceptance.py
```

Coverage:

```text
local expression accepted
overclaim/internal leakage rejected
API returns task/result/acceptance
no V30 write
no V40 production write
```

## Next Phase

Phase 17 should add:

```text
real Ollama/Gemma provider adapter
streaming thinking/display contract
Admin and UI controls for expression runs
expression acceptance metrics in evaluation
larger synthetic/golden expression tests
```
