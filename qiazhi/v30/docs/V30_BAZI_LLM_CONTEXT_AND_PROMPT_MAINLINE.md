# V30 Bazi LLM Context And Prompt Mainline

Updated: 2026-06-13

## Purpose

LLM must serve Bazi calculation, not replace the calculation engine.

V30 already has deterministic chart facts, M3 knowledge/rule/portrait/structure, M4 ten-god model signals, M5 ranked decisions, M6 practical readings, M8 customer projection, interaction state, training signals, and synthetic validation. The LLM layer now needs a stricter invocation model:

```text
reading_id
-> task_type
-> module-gated context_pack
-> prompt_contract
-> verifier / fallback
-> optional provider execution
-> drift check
-> accepted expression only
```

No LLM call should receive a raw runtime payload or a constantly growing prompt.

## UI-R1 Product Reading Audit Update

`UI-R1.1` added a product-facing acceptance audit:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=4/9
failed=basic_assertions_present, bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.2 Basic Assertion Projection
```

LLM implication:

- Existing BL context and prompt infrastructure remains valid.
- `UI-R1.2` now exposes `basic_assertions` through `reading_surface` and `core_bazi_reading`.
- `UI-R1.3` now exposes `bazi_features` and `bazi_portraits` through `reading_surface`.
- `UI-R1.4` now exposes `bazi_paths` through `reading_surface` and path summaries/assertions through domain cards.
- `UI-R1.8` now exposes role-specific reading/answer output and `reading_surface.role_contract`.
- LLM metadata now exposes product context layers through `context_pack_summary`.
- The compact prompt surface now includes basic assertions, domain cards, features, portraits, paths, time context, and role contract.
- Live LLM smoke remains explicit-only; UI-R1.7 validates context alignment without requiring provider execution.
- The next LLM-facing work is therefore not a larger prompt. It is aligning `domain_followup_answer` and `customer_initial_reading` prompts to the product context layers created by UI-R1.2 through UI-R1.4.

Latest UI-R1.2 validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=5/9
failed=bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.3 Bazi Feature And Portrait Projection
```

Latest UI-R1.3 validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=6/9
failed=bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.4 Bazi Path Reading Projection
```

Latest UI-R1.4 validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=7/9
failed=role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.8 Multi-Role Reading Surfaces
```

Latest UI-R1.8 validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=8/9
failed=llm_context_pack_has_product_layers
next=UI-R1.7 LLM Context And Prompt Upgrade
```

Latest UI-R1.7 validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
product_ready=True audit_ready=True
passed=9/9
next=UI-R1.10 Product-Level Synthetic Validation
```

Latest UI-R1.10 validation:

```text
python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_ui_core_reading_product_synthetic.py
9 passed
```

Implication:

- LLM answer metadata/context pack is now validated across product-level synthetic Bazi cases.
- Required product context layers are `basic_assertions`, `bazi_features`, `bazi_paths`, `bazi_portraits`, `domain_card`, `role_contract`, and `time_context`.

## Hard Rules

- Every LLM call must declare `task_type`.
- Every LLM call must use a task-specific `context_pack`.
- Every LLM call must bind to a `prompt_contract`.
- Every LLM call must bind to a `role_contract`.
- Context must be module-backed: M1/M2, M3, M4, M5, M6, M8, interaction state, hidden-factor state, locale terminology, or verified answer draft.
- LLM cannot create or mutate chart facts, luck-cycle facts, flow facts, hidden-factor facts, ranked decisions, interaction state, training candidates, or policy pointers.
- Hidden factors are feedback/dialogue signals only.
- Training signals from LLM output can tune expression/question strategy only; they cannot tune deterministic chart facts.

## Current Task Contracts

| Task type | Context pack | Included modules | Purpose |
|---|---|---|---|
| `customer_initial_reading` | `BaziCoreContext` | M1/M2, M4, M5, M6, M8 | Customer-facing first Bazi reading expression. |
| `domain_followup` | `BaziDomainContext` | M5, M6, interaction state, known user signals | Answer a selected domain follow-up without full runtime context. |
| `useful_god_candidate_explanation` | `BaziCandidatePathContext` | M3, M4, M5 | Explain candidate path and uncertainty, not a fixed verdict. |
| `hidden_factor_dialogue` | `BaziHiddenFactorDialogueContext` | hidden-factor state, interaction state | Ask/explain hidden-factor follow-up without turning it into fact. |
| `practitioner_analysis` | `BaziPractitionerContext` | M1/M2, M3, M4, M5, M6, diagnostics summary | Denser practitioner explanation and diagnostic boundaries. |
| `locale_rewrite` | `BaziLocaleRewriteContext` | verified answer draft, locale terminology | Rewrite verified text for locale/tone without changing facts. |

## Role Contracts

LLM must target different users through explicit role contracts, not ad hoc prompt wording.

| Role | Audience | Density | Terminology | Diagnostics | Allowed LLM scope |
|---|---|---|---|---|---|
| `guest` | Preview customer | Brief | Low | Hidden | Initial reading preview and locale rewrite only. |
| `user` | Customer reading | Standard | Medium | Hidden | Initial reading, domain follow-up, useful-god candidate explanation, hidden-factor dialogue, locale rewrite. |
| `practitioner` | Practitioner review | Dense | High | Visible | Customer tasks plus practitioner analysis. |
| `analyst` | Diagnostic analysis | Diagnostic | High | Visible | Practitioner analysis and locale rewrite. |
| `admin` | Operator diagnostics | Diagnostic | High | Visible | Practitioner analysis and locale rewrite. |
| `lab` | Validation/training lab | Diagnostic | High | Visible | Practitioner analysis and locale rewrite. |

Customer roles cannot receive `diagnostics_summary`, training, policy weights, policy pointer writes, or raw runtime payloads. Guest context is additionally capped to 3 sections and excludes structure/evidence internals.

## Implementation Status

### BL1 Task-Based Bazi Context Pack Compiler

Completed:

- Added `v30.bazi_llm_context_pack.v1`.
- Added `build_bazi_llm_context_pack()`.
- Added six task-specific packs.
- Added context budgets:
  - max context sections: 5
  - max evidence items: 8
  - max ranked candidates per domain: 3
  - max user history items: 3
- Excludes `raw_runtime_payload`, chart fact generation, policy pointer writes, training, policy weights, and admin diagnostics where not allowed.
- Added role contracts for `guest`, `user`, `practitioner`, `analyst`, `admin`, and `lab`.
- Role contracts gate allowed tasks, expression density, terminology depth, diagnostics visibility, forbidden sections, and max context sections.

### BL2 Prompt Contract Registry

Completed:

- Added `v30.bazi_llm_prompt_contract_registry.v1`.
- Added `prompt_contract_for_task()`.
- Added `build_bazi_llm_prompt_request()`.
- Each task declares required context pack, allowed modules, forbidden modules, output schema, verifier, fallback, and boundary.
- Each prompt contract includes the matching `role_contract`; prompt IDs are task+role specific.

### BL3 Context Budget And Module-Gating Verifier

Completed:

- Added `v30.bazi_llm_context_prompt_readiness.v1`.
- Added `scripts/run_bazi_llm_context_prompt_readiness.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-context-prompt-readiness
```

- Verifies task coverage, role coverage, context-pack version, prompt registry version, pack/contract match, forbidden module absence, role visibility gates, budget limits, read-only boundary, verifier presence, and fallback presence.
- Does not execute LLM.
- Does not run full pytest, synthetic all, or full 518K.

### BL4 Customer Bazi Reading LLM Answer Generator

Completed:

- Added `v30.bazi_llm_answer_draft_call.v1` runtime metadata.
- Runtime answer generation now uses Bazi task+role prompt requests through `compose_bazi_llm_answer_draft()`.
- Customer initial answers use `customer_initial_reading` and `BaziCoreContext`.
- Answer refresh after question outcome uses `domain_followup` and `BaziDomainContext`.
- `guest`, `user`, and `practitioner` role contracts are preserved in answer metadata.
- Rule-bound fallback is preserved when provider execution is disabled, unavailable, or rejected.
- Prompt request metadata records context pack, prompt contract, role contract, budget, raw-runtime exclusion, and chart-fact no-mutation boundary.
- Added `v30.bazi_llm_answer_generator_readiness.v1`.
- Added `scripts/run_bazi_llm_answer_generator_readiness.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-answer-generator-readiness
```

- BL4 readiness uses a disabled provider and does not execute live LLM.

### BL5 Bazi LLM Output Schema And Drift Acceptance Gate

Completed:

- Added `v30.bazi_llm_output_acceptance.v1`.
- Added `validate_bazi_llm_output_payload()`.
- Accepted LLM text must now pass:
  - task output schema required fields
  - role visibility gate
  - existing drift/no-mutation check
- `customer_initial_reading` accepted output requires `answer_text`, `evidence_ids`, `boundaries`, and `next_question_hint`.
- `domain_followup` accepted output requires `domain`, `answer_text`, `used_user_signals`, and `boundaries`.
- Missing schema fields now fallback with `output_acceptance_failed`.
- Customer role diagnostics/policy/internal-id leakage now fallback with `output_acceptance_failed`.
- Drift failures still fallback before text replacement.
- Accepted fake-provider tests prove schema-valid initial reading and domain follow-up can replace rule-bound text.
- Added `v30.bazi_llm_output_acceptance_readiness.v1`.
- Added `scripts/run_bazi_llm_output_acceptance_readiness.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-output-acceptance-readiness
```

- BL5 readiness uses deterministic payloads and does not execute live LLM.

### BL6 Bazi LLM Training Signals And Synthetic Tier

Completed:

- Added dedicated synthetic tier:

```text
python3 scripts/run_synthetic_validation.py --tier bazi_llm_acceptance
v30.synthetic.bazi_llm_acceptance: passed (5/5)
```

- Added `SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES`.
- The tier covers:
  - customer initial accepted output
  - domain follow-up accepted output
  - missing schema rejection
  - customer role leak rejection
  - deterministic timing drift rejection
- Added `v30.training_signal.bazi_llm_output_acceptance_quality`.
- Training signal can tune only:
  - expression
  - question strategy
- Training signal cannot tune:
  - chart facts
  - calendar conversion
  - luck cycle
  - flow timing
- Added `v30.bazi_llm_training_synthetic_readiness.v1`.
- Added `scripts/run_bazi_llm_training_synthetic_readiness.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-training-synthetic-readiness
```

- BL6 readiness does not execute live LLM and does not require full pytest, synthetic all, or 518K.

### BL7 Bazi LLM Role And Locale Production Smoke

Completed:

- Added `v30.bazi_llm_role_locale_production_smoke.v1`.
- Added `scripts/run_bazi_llm_role_locale_production_smoke.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-role-locale-production-smoke
```

- Smoke covers 3 roles x 3 locales:
  - `guest`
  - `user`
  - `practitioner`
  - `zh`
  - `en`
  - `ko`
- Customer roles keep diagnostics hidden and do not receive `diagnostics_summary`.
- Practitioner role receives denser structure context while still excluding `policy_pointer_write`.
- Locale rewrite prompt requests prove `BaziLocaleRewriteContext` includes `locale_terminology`.
- Disabled provider fallback preserves rule-bound answer and no-mutation metadata.
- No live provider execution is required.

### BL8 Bazi LLM Closeout And Optional Live Smoke Boundary

Completed:

- Added `v30.bazi_llm_closeout.v1`.
- Added `scripts/run_bazi_llm_closeout.py`.
- Added admin API:

```text
GET /api/v30/admin/llm/bazi-closeout
```

- BL8 accepts BL1-BL7 evidence:
  - `v30.bazi_llm_context_prompt_readiness.v1`
  - `v30.bazi_llm_answer_generator_readiness.v1`
  - `v30.bazi_llm_output_acceptance_readiness.v1`
  - `v30.bazi_llm_training_synthetic_readiness.v1`
  - `v30.bazi_llm_role_locale_production_smoke.v1`
- Default validation remains non-live and lightweight.
- Optional live provider smoke is allowed only as explicit operator or release-boundary work:

```text
python3 scripts/run_llm_live_smoke.py --json
```

- Full pytest, synthetic all, and 518K remain major-node or release-boundary checks.
- No chart facts, deterministic calculation modules, policy pointers, or training pointers are reopened.

Current state:

```text
BL-S1 Bazi LLM Steady State
```

Post-BL integrated coverage:

- IR1 `v30.bazi_intelligence_requirements_coverage.v1` passes 6/6.
- Bazi LLM is accepted as one expression component inside the integrated Bazi intelligence backend.
- LLM still cannot generate or mutate chart facts, ranked decisions, hidden-factor conclusions, policy pointers, or training pointers.
- Default validation remains targeted and non-live unless a release boundary or observed provider failure explicitly reopens live smoke.

## Completion Review

| Area | Completion | Current state |
|---|---:|---|
| Bazi LLM context compiler | 78% | BL4 proves runtime answer generation consumes the task+role context/prompt layer; deeper per-domain compression remains future tuning. |
| Prompt contract registry | 74% | BL4 proves answer metadata carries task+role prompt request contracts; provider-specific prompt templates remain future work. |
| Context budget/module verifier | 72% | BL4 keeps readiness gates active and proves runtime answer metadata excludes raw runtime and chart mutation. |
| Bazi LLM answer generator | 78% | Customer initial reading and domain follow-up route through Bazi LLM prompt requests with rule-bound fallback and accepted fake-provider coverage. |
| Bazi LLM output acceptance | 78% | BL6 adds dedicated synthetic coverage and training-signal extraction for accepted/rejected output paths. |
| Bazi LLM training signal | 72% | `v30.training_signal.bazi_llm_output_acceptance_quality` is active and limited to expression/question-strategy tuning. |
| Bazi LLM synthetic tier | 75% | `bazi_llm_acceptance` passes 5/5 and remains a dedicated tier outside routine full validation. |
| Bazi LLM role/locale production smoke | 86% | BL7 covers guest/user/practitioner across zh/en/ko with disabled-provider fallback and locale terminology boundaries. |
| Bazi LLM closeout | 88% | BL8 accepts BL1-BL7 evidence and enters BL-S1 steady state with optional live smoke explicit-only. |
| Bazi LLM mainline | 88% | BL1-BL8 scope is closed, but UI-R1 reopens task-specific Bazi reading synthesis because product review found LLM output too weak and insufficiently bound to selected domain, features, portraits, paths, and role. |

## Next Mainline Task

### UI-R1 LLM Bazi Reading Synthesis Reopen

UI-R1 does not allow LLM to generate chart facts. It reopens LLM as a stronger Bazi expression and synthesis layer.

Required change:

- LLM must receive a curated task context, not the full runtime payload.
- LLM must bind to selected question domain.
- LLM must consume product reading layers:
  - `basic_assertions`
  - `domain_card`
  - `bazi_features`
  - `bazi_portraits`
  - `bazi_paths`
  - `time_context`
  - `role_contract`
- LLM must return structured JSON with answer text, Bazi basis, used paths, used features, uncertainty boundary, and next question hint.
- LLM output must fail acceptance if it answers a different domain from the selected question.

New or tightened task types:

| Task | Purpose |
|---|---|
| `customer_initial_reading` | Synthesize the first customer reading from assertions/cards/features/paths. |
| `domain_followup_answer` | Answer one selected-domain question directly. |
| `practitioner_review` | Produce denser evidence-chain wording for practitioner review. |
| `portrait_feature_explanation` | Explain Bazi traits, feature rows, portrait dimensions, and hidden-factor clues. |

Default cadence:

- Run targeted UI-R1 and BL readiness when LLM context/prompt/role/output code changes.
- Run `bazi_llm_acceptance` and `ui_core_reading_product` synthetic tiers when output acceptance changes.
- Keep live provider smoke explicit-only.
- Do not reopen M1-M8 deterministic Bazi calculation modules for LLM work.

Non-goals:

- No raw runtime prompt.
- No full login/auth work.
- No visual-only UI redesign.
- No policy pointer promotion.
- No deterministic chart fact changes.

Reference:

```text
docs/V30_UI_CORE_READING_PRODUCTIZATION_PLAN.md
```

## Validation Cadence

Routine BL subtasks run targeted tests:

```text
python3 scripts/run_bazi_llm_context_prompt_readiness.py
python3 scripts/run_bazi_llm_answer_generator_readiness.py
python3 scripts/run_bazi_llm_output_acceptance_readiness.py
python3 scripts/run_bazi_llm_training_synthetic_readiness.py
python3 scripts/run_bazi_llm_role_locale_production_smoke.py
python3 scripts/run_bazi_llm_closeout.py
python3 scripts/run_synthetic_validation.py --tier bazi_llm_acceptance
pytest -q tests/unit/test_bazi_llm_closeout.py tests/unit/test_bazi_llm_role_locale_production_smoke.py tests/unit/test_bazi_llm_training_synthetic_readiness.py tests/unit/test_bazi_llm_output_acceptance_readiness.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_bazi_llm_closeout_endpoint_is_read_only
python3 -m compileall -q v30
```

Full `pytest -q`, synthetic all, live provider smoke, and 518K sample remain major-node or explicit release-boundary checks.
