# V30 LLM Interaction Performance Plan

Updated: 2026-06-30

## Problem

智能问答和测算慢，不是八字核心计算慢，而是 API 请求同步等待远端 Ollama/Gemma 完整生成。

Observed:

```text
V30_LLM_PROVIDER=ollama_native
V30_LLM_HOST=192.168.0.10
V30_LLM_MODEL=gemma4:latest
```

Direct Ollama probe:

```text
gemma4:latest JSON chat, num_predict=120
wall time: 14.7s
Ollama total_duration: 14.7s
Ollama eval_duration: 0.9s
```

The model token generation is not the main cost. The request waits on remote Ollama scheduling/queue/service overhead, and V30 currently waits synchronously before returning the answer API response.

## Mainline Fix

### LLM-PERF1 Product Blocking Expression Path

Status: Active

Rules:

- Bazi calculation, RBD claims, domain cards, paths, portraits, and rule-bound answer remain synchronous.
- LLM expression is part of the customer-visible product answer and should run by default.
- Default product mode is `V30_LLM_SYNC_MODE=blocking`.
- In `blocking` mode, the answer API waits for bounded Gemma/Ollama expression and accepts it only after drift/acceptance checks.
- Explicit fast mode remains available with `V30_LLM_SYNC_MODE=fast` for tests, offline validation, and emergency performance mode.
- Fast mode returns the RBD/rule answer with `llm_metadata.status=deferred`; it must not be treated as the normal product experience.

### LLM-PERF2 Smaller Synchronous Budget

Status: Complete

Rules:

- Lower `V30_LLM_MAX_TOKENS` for answer expression.
- Lower `V30_LLM_HTTP_TIMEOUT_SEC`.
- Do not force Ollama timeout to 30 seconds when operator configured a smaller value.

### LLM-PERF2.5 Deferred Enhancement Endpoint

Status: Complete

Rules:

- Main product answer should now use blocking LLM expression by default.
- Deferred enhancement endpoint remains available when an operator explicitly enables fast mode:

```text
POST /api/v30/readings/{reading_id}/questions/{question_id}/answer/llm
```

- The endpoint is allowed to wait for LLM because it is called after a fast-mode response.
- Accepted LLM output updates the runtime answer panel.
- Fallback output does not replace the existing RBD answer.
- Frontend calls this endpoint when `answer_panel.llm_metadata.status=deferred`.

Observed after implementation:

```text
main answer: 0.371s
main answer llm_status: deferred
optional enhancement: 9.923s
optional enhancement status: accepted
```

This split is now an explicit performance fallback, not the default customer experience.

### LLM-PERF3 Future True Streaming

Status: Planned

Rules:

- Add a dedicated streaming endpoint later.
- Frontend typewriter should consume true streamed chunks, not simulate streaming after a full response.
- Streaming must still be bounded by chart facts and RBD context.

## Verification

Targeted only:

```text
pytest -q tests/unit/test_bazi_llm_answer_generator_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py
pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading tests/test_v30_scaffold.py::test_admin_bazi_llm_answer_generator_readiness_endpoint_is_read_only
node --check frontend/app.js
python3 scripts/run_bazi_llm_answer_generator_readiness.py
python3 scripts/run_bazi_llm_output_acceptance_readiness.py
curl -fsS http://127.0.0.1:9030/api/v30/health
```

No full pytest, synthetic-all, or full 518K for this subtask.

2026-06-30 live LLM smoke:

```text
POST /api/v30/admin/runtime/llm/test
status: ok
provider: ollama_native
model: gemma4:latest
executed: true
duration_ms: 4459.29
```
