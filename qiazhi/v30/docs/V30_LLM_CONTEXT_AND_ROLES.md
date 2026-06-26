# V30 LLM Context and Roles

Updated: 2026-06-10

## Purpose

V30 should let LLM do more useful work than V20, but through structured contracts.

LLM should support different roles, richer dialogue, synthetic generation, training assistance, and answer composition without mutating runtime facts.

## Core Rule

LLM consumes structured V30 context.

LLM should not consume raw runtime traces for ordinary user answers.

As of BL1-BL3, Bazi-facing LLM calls must go through a task-specific context pack and prompt contract. The controlling plan is:

```text
docs/V30_BAZI_LLM_CONTEXT_AND_PROMPT_MAINLINE.md
```

## Context Stack

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> HiddenFactorState
-> BaziQuestionAnchor
-> AnswerContext
-> ExpressionFrame
-> NarrativePlan
-> RenderedNarrative
-> RoleContext
-> DialogueContext
-> LLMTask
-> BaziLLMContextPack
-> PromptContract
-> Verifier / Fallback
```

## LLM Roles

Initial runtime roles:

| Role | Purpose |
|---|---|
| `user_answerer` | Produce user-facing answer from `AnswerContext`. |
| `practitioner_answerer` | Produce denser practitioner explanation. |
| `question_renderer` | Render a bound question in natural language. |
| `question_explainer` | Explain why a bound question is recommended. |
| `analyst_explainer` | Explain diagnostics for analyst/admin users. |

Initial training roles:

| Role | Purpose |
|---|---|
| `synthetic_case_generator` | Generate candidate cases for validation expansion. |
| `failure_clusterer` | Summarize validation failure clusters. |
| `policy_candidate_assistant` | Propose policy adjustments for training jobs. |
| `knowledge_pack_assistant` | Draft knowledge units for later validation. |

Training roles do not directly update runtime pointers.

## AnswerContext

Answer context should include:

```text
answer_context_id
selected_question_anchor
chart_summary
structure_summary
mainline_summary
evidence_summary
knowledge_boundaries
role_answer_contract
forbidden_drift
```

## Prompt Policy

Prompt policy should define:

- Allowed source fields.
- Required citations to evidence IDs where needed.
- Forbidden claims.
- Role tone.
- Output shape.
- Max context size.
- Drift checks.

## Output Contracts

LLM outputs should be typed by task:

```text
AnswerDraft
QuestionRendering
QuestionExplanation
SyntheticCaseDraft
FailureClusterSummary
PolicyCandidateSuggestion
```

Each output has validation before use.

## Boundaries

LLM may:

- Explain evidence.
- Improve expression.
- Adapt answer density by role.
- Ask or render boundary questions for hidden factor discovery.
- Propose next training candidates.
- Generate draft synthetic cases.

LLM may not:

- Change chart facts.
- Change selected structure.
- Change selected mainline.
- Mark weak anchors as bound.
- Update runtime pointers.
- Invent unsupported evidence.
- Treat hypothesized hidden factors as confirmed user state.

## Drift Detection

LLM output should be checked for:

- Unsupported chart claims.
- Role visibility leak.
- Answering outside selected question.
- Contradicting structure state.
- Overstating confidence.
- Medical/legal/financial overreach where relevant.

## Test Strategy

LLM tests are tiered:

- Contract tests with fake deterministic outputs.
- Prompt construction tests.
- Drift checker tests.
- Optional live LLM smoke tests.

Live LLM tests are never default tests.

## Acceptance

- LLM tasks use V30 contracts.
- User answers use compact context.
- Role output differences are intentional and testable.
- LLM training assistance cannot bypass validation.
- Prompt/context docs update whenever role contracts change.

## Current Implementation Slice

Completed:

- `AnswerContext` is produced from the selected, highest-scored question anchor.
- `AnswerResult` is rule-bound and carries `rule_bound_answer_no_llm_fact_mutation`.
- `LLMRolePromptContext` now converts `AnswerContext` into role-specific prompt context.
- Role directives exist for `guest`, `user`, `practitioner`, `analyst`, `admin`, and `lab`.
- Prompt context carries allowed blocks, evidence IDs, answer boundaries, and hard system constraints.
- Unit tests verify that role prompt construction preserves answer boundaries.
- `check_llm_answer_drift()` now provides a deterministic first-pass drift check.
- The drift checker blocks unsupported deterministic timing claims and unsupported hidden-factor confirmations.
- `v30.expression` now sits before LLM output. LLM should consume expression plans/rendered narratives for surface language rather than raw runtime engineering fields.
- `AnswerResult.text` now uses expression-layer rendering, so ordinary output uses Bazi consultation language and preserves boundaries without exposing runtime internals.
- Task-specific output contracts are active for `AnswerDraft` and `QuestionExplanation`.
- Runtime policy effect now exposes `llm_output_contract_version`, `llm_output_contracts`, and `llm_output_contract_summary`.
- Output contracts now cover `AnswerDraft`, `QuestionExplanation`, `SyntheticCaseDraft`, and `FailureClusterSummary`.
- Synthetic validation checks LLM output contract status, and training emits `v30.training_signal.llm_output_contract_quality` with four-task coverage.
- `v30.bazi_llm_context_pack.v1` is active for `customer_initial_reading`, `domain_followup`, `useful_god_candidate_explanation`, `hidden_factor_dialogue`, `practitioner_analysis`, and `locale_rewrite`.
- `v30.bazi_llm_prompt_contract_registry.v1` binds each task to allowed modules, forbidden modules, output schema, verifier, fallback, and no-mutation boundary.
- Role-specific LLM contracts are active for `guest`, `user`, `practitioner`, `analyst`, `admin`, and `lab`; they gate allowed tasks, expression density, terminology depth, diagnostics visibility, forbidden sections, and context budget.
- `v30.bazi_llm_context_prompt_readiness.v1` verifies task coverage, role coverage, context budget, module gating, context-pack/prompt-contract match, role visibility gates, and read-only boundaries without executing LLM.
- `compose_bazi_llm_answer_draft()` is active in runtime answer generation. Initial answers use `customer_initial_reading`; answer refresh after user feedback uses `domain_followup`.
- `v30.bazi_llm_answer_generator_readiness.v1` proves runtime answer metadata carries task, role, context pack, prompt contract, role contract, no raw runtime payload, and no chart-fact mutation.
- `v30.bazi_llm_output_acceptance.v1` gates accepted text by task schema, role visibility, drift, and no-mutation metadata.
- `v30.bazi_llm_output_acceptance_readiness.v1` proves schema-valid fake-provider outputs can be accepted and schema/role/drift failures are rejected without live LLM.
- `bazi_llm_acceptance` synthetic tier is active with 5/5 passing cases.
- `v30.training_signal.bazi_llm_output_acceptance_quality` extracts accepted/rejected output quality for expression and question-strategy tuning only.
- `v30.bazi_llm_role_locale_production_smoke.v1` covers guest/user/practitioner across zh/en/ko with disabled-provider fallback, customer diagnostics hidden, practitioner dense context, and locale terminology boundaries.
- `v30.bazi_llm_closeout.v1` accepts BL1-BL7 evidence and enters `BL-S1 Bazi LLM Steady State`.

Current boundary:

```text
LLM may change expression and role density.
LLM may not create chart facts, timing claims, hidden-factor confirmations, or runtime pointer updates.
```

Next hardening:

- Current state is BL-S1. Reopen only for new LLM tasks, role/locale requirements, observed live-provider failures, or explicit release-boundary live smoke.
- Optional live LLM smoke remains outside default pytest.
