# V30 Xuanming Reasoning Engine Tasks

Date: 2026-06-26

## Problem

The current V30 thinking pages have the right interaction structure, but the content is weak:

- Stage summaries describe workflow status rather than Bazi judgment.
- Evidence is counted, but not converted into a meaningful命理判断.
- Knowledge, rules, features, portraits, paths, timing, and domain readings are parallel materials; they are not yet joined into a main reasoning line.
- LLM enhancement can only improve wording. It cannot create value if the backend judgment package is shallow.

## Decision

Add a backend `analysis_result` contract for every thinking step. This is the first version of the Xuanming reasoning layer.

The LLM expression layer must consume `analysis_result`, not raw scattered evidence.

## Contract

Each step should expose:

- `conclusion`: the stage-level judgment.
- `reasoning_points`: user-safe reasons behind the judgment.
- `contradictions`: unresolved tensions or counter-evidence.
- `next_focus`: what the next page should verify.
- `user_summary`: polished but deterministic customer-facing summary.
- `quality_flags`: whether the stage is strong enough or still mostly structural.

Boundary:

- No hidden chain of thought.
- No generated chart facts.
- No raw internal IDs.
- No fixed fatalistic predictions.

## Implementation Plan

1. Add `analysis_result` to `v30.presentation.thinking`.
2. Rebuild `summary_panel` from `analysis_result.user_summary` instead of static workflow copy.
3. Render `analysis_result` on each stage page as the main content judgment.
4. Keep LLM summary endpoint as expression-only; later update its prompt to prefer `analysis_result`.
5. Add regression tests ensuring chart/rule/path steps include real conclusion, reasons, next focus, and no internal IDs.

## First Scope

This pass focuses on deterministic reasoning quality for:

- `chart_build`: day master, month branch, four pillars, initial strength/tension framing.
- `rule_matching`: matched rule meaning and what it does or does not prove.
- `structure_reasoning`: selected structure, confidence, primary chain, counterweight.
- `path_reasoning`: force flow and real-world landing.
- `timing_layers`: current luck/flow activation.

Other steps receive a simpler but still structured analysis result.

## 2026-06-26 Batch LLM Expression Update

Implemented a batch expression endpoint for the thinking flow:

- `POST /api/v30/readings/{reading_id}/thinking/summary/llm`
- Input supports `role`, `locale`, `client`, optional `step_ids`, and bounded `max_steps`.
- Output returns the full thinking projection with selected steps enhanced by the LLM expression layer.
- The batch metadata records requested, accepted, fallback, and executed counts.
- The endpoint does not mutate runtime, chart facts, database records, or policy pointers.

Current local and 13 Ollama configuration:

- 13 server V30: `http://192.168.0.7:11434/v1`, model `gemma4:latest`.
- Local V30: `http://127.0.0.1:11435/v1`, SSH tunnel to the same model pool.
- Admin readiness status: `model_probe_ready`, 10 models visible.

Verification:

- `python -m compileall v30`
- `node --check frontend/app.js`
- `pytest tests/test_v30_scaffold.py -q` -> 67 passed
- Live local smoke: `local-batch-smoke` chart step accepted by `ollama_native/gemma4:latest`, source `central_brain_llm_expression`.

Next task:

- Connect the frontend to prefetch the active step and, optionally, the next one through the batch endpoint.
- Keep token charging as reserved metadata only; record estimated step count and future credit hooks without enforcing billing.
- Add UI state that distinguishes deterministic central-brain summary from LLM-polished expression.

## 2026-06-26 Prompt Framework Decision

The controlling prompt/framework design is now:

```text
docs/V30_THINKING_LLM_PROMPT_FRAMEWORK_20260626.md
```

Decision:

- Do not depend on Gemma/Ollama hidden thinking mode as product reasoning.
- Keep runtime calls expression-only and auditable.
- Use V30's own public thinking stages as the visible reasoning process.
- Move thinking page summaries into a formal `thinking_step_summary` task, with a stage context pack, prompt contract, module gate, acceptance checks, and fallback.

Implementation implication:

- The current direct `_thinking_step_summary_prompt()` has been replaced at runtime by a formal prompt request compiler.
- The batch endpoint now consumes the formal prompt request through `call_bazi_llm_thinking_step_summary()`.
- UI should show whether a summary is deterministic central-brain output or LLM-polished expression.

Implemented:

- `ThinkingStageContext`
- `thinking_step_summary` prompt contract
- thinking output acceptance gate
- live Gemma4 smoke with `raw_runtime_payload_included=False`
- `summary_policy` for each thinking stage:
  - decides full/compact/deferred/hidden summary mode
  - decides LLM enhancement auto/skip
  - exposes trainable signals for future synthetic validation and policy tuning
  - lets frontend prefetch current/next stage intelligently
