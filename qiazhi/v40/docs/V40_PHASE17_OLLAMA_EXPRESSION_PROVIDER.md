# V40 Phase 17: Ollama Expression Provider

Date: 2026-06-30

## Goal

Phase 17 connects the Phase 16 expression contract to a real Ollama provider.

The boundary remains unchanged:

```text
DecisionEngine decides.
Ollama/Gemma expresses.
AcceptanceResult gates.
```

There is no fallback when Ollama execution is requested and unavailable. The caller receives an explicit error.

## Configuration

V40 uses its own LLM environment variables:

```text
V40_LLM_ENABLED=1
V40_LLM_EXECUTE=1
V40_LLM_PROVIDER=ollama_native
V40_LLM_HOST=127.0.0.1
V40_LLM_PORT=11434
V40_LLM_MODEL=gemma4:latest
V40_LLM_HTTP_TIMEOUT_SEC=30
V40_LLM_TEMPERATURE=0.2
V40_LLM_MAX_TOKENS=600
```

These are independent from V30.

The V40 start scripts load local configuration automatically when present:

```text
.env.v40.local
```

The file is ignored by Git.

## New Module

```text
v40/expression/ollama_provider.py
```

Main functions:

```text
resolve_ollama_expression_config()
build_ollama_expression_prompt()
render_ollama_expression_result()
```

The provider follows the V30 `ollama_native` thinking path. It calls:

```text
POST {base_url}/api/chat
```

with:

```text
model
messages = system + user
stream=false
think=true
options.temperature
options.num_predict = max(V40_LLM_MAX_TOKENS, 2400)
```

It parses:

```text
message.content
message.thinking or message.reasoning_content
embedded <think>...</think>, if a model emits it inside content
```

The thinking timeout follows V30's operational rule:

```text
timeout = max(V40_LLM_HTTP_TIMEOUT_SEC, 180)
```

This matters for Gemma4 thinking models: a small `num_predict` can be consumed by internal thinking before visible content appears. V40 therefore never uses the plain `/api/generate` path for `ollama_native` expression.

The returned `LLMExpressionResult` still must pass:

```text
accept_expression_result()
```

## API

Existing endpoint extended:

```text
POST /api/v40/expression/from-runtime
```

New request field:

```text
execution_mode = local | provider_text | ollama
```

Modes:

```text
local         = deterministic local expression adapter
provider_text = caller supplies external provider text for acceptance scan
ollama        = V40 calls configured Ollama provider
```

If `execution_mode=ollama` and Ollama is disabled or unreachable, API returns `503`.

Provider status:

```text
GET /api/v40/expression/provider/ollama
```

This reports non-secret runtime config only, including both configured and effective thinking execution values:

```text
max_tokens / timeout_seconds = env configuration
effective_thinking_max_tokens / effective_thinking_timeout_seconds = values used by Gemma4 thinking calls
```

## CLI

The existing expression command now supports:

```bash
python scripts/v40_artifact_cli.py render-native-expression \
  --path data/synthetic/native_bazi_seeds.json \
  --seed-id native.career.bingchen.001 \
  --reading-id reading.local.expression.001 \
  --mode ollama
```

Default remains:

```text
--mode local
```

## No Fallback Rule

If a user explicitly requests model execution:

```text
do not silently use local expression
do not use template text as a substitute
return model unavailable
```

This follows the product principle:

```text
No LLM, no fake intelligence.
```

## Tests

Added:

```text
tests/test_v40_phase17_ollama_expression_provider.py
```

Coverage:

```text
prompt keeps expression-only boundary
fake Ollama chat transport returns accepted expression
chat payload requests think=true and at least 2400 num_predict
message.thinking and embedded <think> content are captured
length-exhausted empty visible content reports a model/token error
disabled Ollama raises without fallback
provider status exposes no secrets and writes no state
```

## Phase 18 Handoff

Phase 18 added the first pass of:

```text
Ollama model discovery endpoint
Admin LLM status/model visibility
ExpressionTelemetry returned by expression runtime
expression acceptance metrics inside EvaluationRunResult
```

Still open after Phase 18:

```text
streaming expression/thinking contract
larger synthetic/golden expression corpus
expression telemetry persistence/history
product runtime report endpoint using execution_mode=ollama
```
