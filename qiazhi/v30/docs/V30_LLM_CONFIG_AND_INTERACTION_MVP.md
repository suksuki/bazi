# V30 LLM Config And Interaction MVP

Updated: 2026-06-10

## Purpose

P6 connects the customer reading loop to bounded LLM expression without changing V30 architecture.

V20 may be used as a reference for provider configuration shape and operational experience. V30 must not import V20 runtime code.

This document now also anchors the post-P6 LLM/interaction hardening work: LLM remains an expression layer while P7/P8 model-signal fusion, explicit interaction state, and better diagnostics are runtime context available to the answer path.

## Runtime Flow

```text
BirthInput
-> deterministic chart / luck / flow
-> TenGodEnergyModel / model_signal_summary
-> internal BaziContext
-> customer reading surface
-> high-value recommended question
-> structured option or user answer
-> interaction state update
-> refreshed answer context
-> rule-bound answer
-> optional bounded LLM answer draft
-> drift check / fallback
```

## Current Completion Review

| Area | Completion | Current state | Next hardening |
|---|---:|---|---|
| V30 LLM config | 78% | V30 reads `V30_LLM_*` first, supports V20 env-shape fallback without importing V20 code, and live smoke reports configured/unconfigured state without exposing secrets. | Add provider-specific failure taxonomy only after live failures appear. |
| Rule-bound answer path | 84% | Rule answer is composed first, consumes bounded `model_signal_summary`, and remains the deterministic fallback. | Keep raw model scores hidden while tuning explanation density. |
| Bounded LLM answer draft | 88% | Provider/client can produce bounded drafts, drift check them, record fallback/accepted status, emit `v30.llm_live_smoke.v1`, and write live-smoke artifacts. BL8 accepts BL1-BL7 evidence and enters BL-S1 steady state with live provider smoke explicit-only. | Reopen only on new LLM tasks, role/locale requirements, observed live-provider failures, or release-boundary live smoke. |
| Interaction integration | 74% | Structured option submission refreshes answer context and next question with explicit `interaction_stage`, `selected_domain`, and `followup_reason`. | Add interaction-loop validation and failure observation. |
| Safety boundary | 90% | LLM cannot create chart facts, event facts, hidden-factor facts, fixed verdicts, ranked decisions, model signals, or interaction state; R4 smoke records `v30.llm_no_mutation_proof.v1`. | Expand forbidden-pattern checks only from observed failures. |

## Configuration

V30 reads `V30_LLM_*` first:

```text
V30_LLM_ENABLED
V30_LLM_EXECUTE
V30_LLM_PROVIDER
V30_LLM_BASE_URL
V30_LLM_HOST
V30_LLM_PORT
V30_LLM_MODEL
V30_LLM_API_KEY or V30_LLM_API_KEY_ENV
V30_LLM_HTTP_TIMEOUT_SEC
V30_LLM_TEMPERATURE
V30_LLM_MAX_TOKENS
```

Current real-environment default:

```text
V30_LLM_PROVIDER=ollama_native
V30_LLM_HOST=192.168.0.10
V30_LLM_PORT=11434
V30_LLM_MODEL=gemma4:latest
```

For migration compatibility, if no V30 LLM variables are present, V30 can read the existing `V20_LLM_*` environment variable shape. This is configuration compatibility only; V30 does not import or execute V20 runtime modules.

## Boundaries

- LLM can rewrite expression only.
- LLM cannot create pillars, luck-cycle facts, flow facts, event years, hidden-factor facts, or fixed verdicts.
- LLM cannot turn ten-god energy scores into raw user-visible numeric claims.
- LLM cannot decide `visible_next_question_id` or `internal_next_question_id`; it may only explain a backend-selected follow-up.
- LLM output must pass drift checks.
- Failed, disabled, or unavailable LLM calls keep the deterministic rule answer.
- LLM signals train expression and question policy, not chart facts.
- Customer answer text must not expose internal diagnostic sections, evidence counts, source ids, or LLM acceptance/fallback labels. Practitioner/admin diagnostics stay in structured fields such as `role_adaptation`, not in the reading paragraph.
- Runtime answer selection prefers `user_question` anchors for the product answer panel. Hidden-attribute calibration probes remain available to the brain and diagnostics, but they do not replace the default Bazi measurement answer.

## Next Mainline Tasks

Completed in R4:

1. Added `v30.llm_live_smoke.v1`.
2. Added `scripts/run_llm_live_smoke.py`.
3. Added release-gate check `llm_live_smoke`.
4. Added status taxonomy: `unconfigured`, `configured_not_executed`, `accepted`, `fallback`, `drift_rejected`.
5. Added no-mutation proof for chart facts, ranked decisions, model signal, and interaction state.
6. Added tests for unconfigured, configured-not-executed, and drift-rejected paths.

Validation 2026-06-05:

```text
pytest -q tests/unit/test_llm_context.py tests/unit/test_expression_framework.py
12 passed
python3 scripts/run_llm_live_smoke.py --reading-id r4-llm-live-smoke-20260605 --json
v30.llm_live_smoke.20260605062559199852: passed, smoke_status=unconfigured
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605062559: eligible, checks=6, llm_live_smoke=passed
```

Next hardening:

1. BL-S1 Bazi LLM Steady State: keep targeted non-live readiness as default; live provider smoke remains explicit-only.
2. Add provider-specific failure taxonomy when real provider failures appear.
3. Add expression-density tuning from real-case replay, not from LLM output as fact source.
