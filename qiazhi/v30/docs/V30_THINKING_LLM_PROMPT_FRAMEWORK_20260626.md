# V30 Thinking LLM Prompt Framework

Date: 2026-06-26

## Decision

Do not rely on Gemma/Ollama hidden thinking mode for product reasoning.

V30 should keep `think=false` for runtime LLM calls and expose its own public, auditable thinking flow:

```text
deterministic modules
-> Xuanming core reasoning model
-> central brain stage decision
-> task-bound context pack
-> prompt contract
-> LLM expression
-> acceptance / fallback
-> UI typewriter rendering
```

Reason:

- Hidden model thinking is not stable enough to become a product contract.
- It is harder to test, budget, cache, and explain.
- It can blur the boundary between calculation facts and language expression.
- The user-visible product value should be V30's structured reasoning steps, not the model's private chain.

Gemma4 can still be used as the expression model. It should receive strong context and produce polished customer-facing stage summaries.

## V20 Carryover

V20's prompt framework remains correct:

```text
Prompt handles task, output structure, and boundary.
Context provides verified Bazi understanding.
LLM integrates and expresses naturally.
```

V30 should not create long ad hoc prompts per page. It should compile a stage-specific prompt request.

## Thinking Task Type

Add a formal LLM task:

```text
thinking_step_summary
```

Purpose:

- Summarize one visible analysis page.
- Explain what the stage concluded.
- Explain why this stage matters for the next stage.
- Preserve uncertainty, contradiction, and boundary.
- Avoid internal IDs, raw diagnostics, and invented facts.

This task is expression-only. It cannot mutate chart facts, hidden-factor state, runtime payload, policy pointers, training candidates, or database rows.

## Stage Context Pack

Each page should compile a bounded context pack:

```text
version
task_type
reading_id
role_key
locale
client
stage
central_brain
xuanming_reasoning
module_context
output_policy
context_budget
boundary
```

### stage

```text
step_id
title
phase
confidence
analysis_result
summary_panel
evidence_digest
next_stage_id
```

### central_brain

```text
brain_state
role_state
session_phase
expression_voice
unknown_context
feedback_slots
```

Only public/sanitized fields are passed for customer roles.

### xuanming_reasoning

Use the existing `reasoning_model` as the core logic packet:

```text
chart_axis
strength_model
ten_god_model
structure_model
path_model
useful_god_model
timing_model
mainline
```

The prompt compiler should select only the subset relevant to the current stage.

### module_context

Stage-to-module mapping:

| step_id | Modules |
|---|---|
| chart_build | M1/M2 chart facts, time boundary |
| knowledge_library | M3 knowledge library summary |
| rule_matching | M3 rule signals, matched rules, counter-evidence |
| feature_extraction | feature evidence, element/ten-god summaries |
| portrait_projection | portrait projections and boundaries |
| path_reasoning | structure graph, path scores, diagnosis paths |
| structure_reasoning | M4/M5 strength, structure, ranked decisions |
| timing_layers | luck, flow, six-pillar context |
| domain_synthesis | M6 practical readings, diagnosis claims, domain cards |
| final_report | accepted stage summaries, answer result, role contract |

智能对话不再是 thinking stage。`current_dialogue_turn` 由中枢大脑挂载到相关阶段，只作为 dialogue surface，不进入阶段 summary LLM。

## Prompt Contract

The prompt should be short and stable:

```text
You are V30's Bazi stage expression layer.
Use only the supplied stage context.
Return one JSON object with key text.
Write 2-4 concise Chinese sentences.
State the stage judgment, strongest basis, boundary, and next-step relevance.
Do not invent chart facts, event years, user history, or hidden-factor confirmations.
Do not expose internal ids, JSON keys, diagnostics, or source ids.
```

The contract, not the prompt prose, should define:

```text
required_fields: text
max_chars: 360
forbidden_tokens
role_visibility
module_gate
fallback
acceptance_checks
```

## Context Budget

Default budget per stage:

```text
analysis_result: full
summary_panel: title/body/points
evidence_digest: max 5 readable items
xuanming_reasoning: max 2 relevant submodels
module_context: max 6 rows
accepted_previous_stage_summaries: max 3
raw_runtime_payload: never
```

## Acceptance

Accepted output must pass:

- non-empty text
- length cap
- no internal identifiers
- no new pillars, luck cycles, flow years, or event years
- no high-risk fatalistic claims
- role visibility gate
- chart-fact no-mutation metadata

Fallback:

- Keep deterministic `central_brain_rule_summary`.
- Record LLM metadata.
- Do not block the page.

## UI Strategy

The UI should render in layers:

```text
1. deterministic stage narration
2. central brain summary
3. LLM expression enhancement when ready
4. evidence digest and reasoning points
5. next-step navigation
```

Prefetch policy:

- Enhance active step first.
- Optionally prefetch the next step.
- Never call all steps by default on first load.
- Token/credit fields remain reserved metadata until billing is implemented.

## Stage Summary Policy

The central brain should not summarize every page mechanically.

Each stage now exposes:

```text
summary_policy
```

Contract:

```text
version: v30.stage_summary_policy.v1
mode: full | compact | deferred | hidden
display_summary: boolean
llm_enhancement: auto | skip
prefetch_next: boolean
reason
signals
training_signal
boundary
```

Signals:

```text
information_gain
evidence_delta
confidence
contradiction_count
stage_importance
reasoning_point_count
token_budget_class
```

Training target:

```text
v30.training_signal.stage_summary_policy
target: summary_mode_and_llm_prefetch_policy
allowed_updates:
  - summary_mode_weight
  - llm_enhancement_threshold
  - prefetch_next_weight
```

Runtime behavior:

- `llm_enhancement=auto`: frontend may request Gemma4 expression enhancement.
- `llm_enhancement=skip`: backend returns `stage_summary_policy_skipped_llm` without calling the provider.
- `prefetch_next=true`: frontend may batch current step and next step.
- The policy controls expression cost only; it cannot change Bazi facts.

Initial examples:

- `chart_build`: compact summary, LLM allowed for first-step professional feel.
- `knowledge_library`: compact summary, LLM skipped to save tokens.
- `path_reasoning`, `structure_reasoning`, `domain_synthesis`: full summary, LLM allowed.
- `final_report`: full summary, LLM allowed.

## Next Implementation Tasks

1. Add `thinking_step_summary` to the V30 LLM prompt registry. Done.
2. Add a `ThinkingStageContext` compiler instead of building the prompt directly in `llm/client.py`. Done.
3. Move forbidden-token and acceptance checks into a reusable thinking-output acceptance module. Done.
4. Let batch summary endpoint consume the formal prompt request. Done.
5. Update UI to show deterministic vs LLM-polished source. Next.
6. Add tests for module gating by step_id and no raw runtime payload. Partially done; expand with dedicated unit tests next.

## 2026-06-26 Implementation Snapshot

Implemented:

- `v30.llm.thinking_context.build_thinking_stage_context_pack()`
- `ThinkingStageContext`
- `prompt_contract_for_thinking_step()`
- `build_thinking_step_prompt_request()`
- `validate_thinking_step_summary_text()`
- Runtime `call_bazi_llm_thinking_step_summary()` now consumes the formal prompt request.
- `summary_policy` now controls per-stage summary mode, LLM enhancement, and next-step prefetch.
- The frontend respects `summary_policy.llm_enhancement` and uses the batch endpoint for current/next stage enhancement.
- The backend returns `stage_summary_policy_skipped_llm` instead of calling LLM when the central brain chooses to save tokens.

Live local smoke:

```text
accepted 1 fallback 0
status accepted executed True model gemma4:latest
prompt v30.thinking_step_summary_prompt.v2 thinking_step_summary v30.bazi_llm_prompt.thinking_step_summary.user.v1 ThinkingStageContext
modules 2 raw_runtime False
acceptance True []
source central_brain_llm_expression
```

Validation:

```text
python -m compileall v30
node --check frontend/app.js
pytest tests/test_v30_scaffold.py -q
67 passed
```

## Conclusion-First Summary Rule

User-facing stage text must prefer conclusion and advice over process narration.

Required visible order:

1. Conclusion: what this step can safely assert.
2. Advice: what the user should focus on or do next.
3. Evidence: the strongest readable basis.
4. Boundary: what should not be over-claimed yet.

Forbidden on the customer surface:

- Internal source labels such as central brain, LLM polish, token saving, prompt, context pack, diagnostics.
- Process filler such as "current stage", "the system is analyzing", "later we can", or "please note".
- Evidence copy that says the system adopted rows or exposes internal identifiers.

Implementation notes:

- Backend `stage.narration` now starts with `结论：` and includes `建议：` when available.
- `summary_panel.body` appends action-oriented advice from `analysis_result.next_focus`.
- `evidence_digest` uses readable evidence labels and no longer says "system adopted evidence".
- The frontend hides LLM/source/cost policy labels from the user-facing stage page while preserving metadata for training and diagnostics.

## 2026-06-26 Stage UI Cleanup

Review finding:

- The stage page was showing too many layers at once: stage narration, static summary, analysis result, support boards, diagnostics, and old thinking overview.
- LLM enhancement was happening in the background, but the customer surface did not clearly show "thinking in progress".
- Expired product sessions could repeatedly request profiles and pollute the page state.
- A later rule-page review found that the visible "Thinking" panel had become process copy rather than actual analysis; it described enhancement state instead of showing rule reasoning.

Implemented:

- Stage pages now render only two main analysis sections: active public reasoning/typewriter and conclusion/advice/evidence/boundary.
- Removed per-stage support boards and diagnostics from the customer stage page.
- Removed dead legacy thinking overview render code and its CSS.
- Removed unused static stage summary card and the separate Thinking status panel.
- Typewriter text now prioritizes `analysis_result.summary_decision.public_trace` / `analysis_result.public_trace`, not LLM status text.
- When a product session is invalid, the frontend clears the stale local session and stops retrying profile fetches.

Current visible stage contract:

```text
1. Typewriter public reasoning trace
2. Conclusion and advice
3. Matched evidence, boundary, next focus
```

## Central Brain Summary Decision Framework

Stage summaries and advice are owned by the intelligent central brain, not by ad hoc UI copy and not by the LLM.

Runtime contract:

```text
analysis_result.summary_decision
  owner: central_brain
  user_value_order: conclusion -> advice -> evidence -> boundary
  conclusion
  advice
  evidence
  boundary_text
  public_trace
  llm_task
  training_target
```

Responsibilities:

- Central brain decides what the user should know at this step.
- Central brain selects the explicit conclusion, actionable advice, evidence, and boundary.
- Central brain exposes a public reasoning trace such as matched rules, portrait tendency, path conclusion, and domain landing.
- Every stage must expose a concrete `测算作用` and `执行建议`; rule matching is only one example, the same contract applies to chart, knowledge, feature, portrait, path, structure, timing, domain, question, and report pages.
- Main conclusions and advice must be assertive. Uncertainty belongs in `boundary_text` / `判断边界`, not in the primary conclusion.
- LLM receives `summary_decision` as the source of truth and may only polish expression.
- Gemma/Ollama stage-summary calls request provider thinking mode with `think=true`.
- Raw model thinking is not a customer-facing source of truth; the customer sees public reasoning generated from deterministic modules.

Examples:

- Rule step must say which rule meanings matched and what those matches do for the Bazi reading: useful-god validation, ten-god expression entry, branch-relation/path review, hidden-factor follow-up, or domain verification.
- Portrait step must say what portrait tendency was formed, not only "portrait generated".
- Path step must say which path/mechanism and domain landing are currently strongest.
- Advice must be selected by the central brain based on the stage role and current uncertainty, not appended as generic next-step text.
- Forbidden primary-answer style: vague process copy such as "next step will look", "not yet confirmed", "maybe later", or internal ids. The user-facing stage must say what has been concluded, what it does for the reading, and what action follows.

Training target:

```text
v30.training_signal.central_brain_stage_summary_decision
target: stage_conclusion_advice_evidence_boundary_selection
```
