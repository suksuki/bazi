# V30 From V20 Asset Review

Updated: 2026-05-20

## Purpose

This document classifies V20 assets for V30. The default rule is conservative:

```text
Reuse ideas and validation assets first.
Reuse code only when it is small, deterministic, typed, and free of V20 runtime coupling.
```

## Migration Categories

| Category | Meaning |
|---|---|
| Direct reuse | Code can be copied with minimal rename after review. |
| Reimplement from idea | Algorithm or contract is good, but V20 implementation is too coupled. |
| Convert data | Data or cases are useful but need V30 schema conversion. |
| Reference only | Read for behavior comparison, do not migrate. |
| Retire | Do not carry forward. |

## Asset Decisions

### Core Chart Facts

V20 modules:

```text
core/chart.py
core/schemas.py
core/ten_gods.py
core/relations.py
core/time_context.py
core/strength.py
```

Decision: direct reuse candidate / light reimplementation.

Rationale:

- Deterministic and relatively isolated.
- Central to all versions.
- Needs V30 naming and stricter `ChartContext` contract.

V30 target:

```text
v30/core/chart_context.py
v30/core/time_context.py
v30/core/ten_gods.py
```

### Feature Compilation

V20 modules:

```text
features/compiler.py
features/schema.py
features/state_model.py
```

Decision: reimplement from idea.

Rationale:

- Feature spine is useful.
- V20 feature layer carries historical coupling to questions, knowledge, answer, and learning.
- V30 should emit `FeatureEvidence` directly.

V30 target:

```text
v30/evidence/features.py
v30/evidence/schema.py
```

### Structure Dynamics SDE v2

V20 modules:

```text
dynamics/graph_engine.py
dynamics/engine.py
knowledge/structure_mechanisms.py
validation/structure_dynamics_synthetic.py
validation/structure_dynamics_corpus_distribution.py
```

Decision: reimplement from idea, reuse synthetic cases by conversion.

Rationale:

- Weighted Dynamic Graph is one of the strongest V20 assets.
- Implementation is good but tied to V20 report shape and runtime pointer loader.
- V30 should separate graph extraction, semantic naming, policy weights, and presentation.

V30 target:

```text
v30/structure/graph.py
v30/structure/mechanisms.py
v30/structure/policy.py
v30/validation/structure_cases.py
```

### Rule Runtime

V20 modules:

```text
rules/engine.py
rules/catalog.py
decision/engine.py
decision/defeasible_model.py
decision/knowledge_bridge.py
```

Decision: mixed.

- Rule condition matching: reimplement from idea.
- Rule catalog data: convert data.
- Legacy seed decisions in `decision/engine.py`: reference only.
- Knowledge bridge: reimplement from idea.

Rationale:

- V20 has two layers: legacy seed decisions plus RuleSpec runtime.
- V30 should have one evidence/rule path and no compatibility bridge.

V30 target:

```text
v30/rules/catalog.py
v30/rules/evaluator.py
v30/evidence/rule_evidence.py
```

### Knowledge Units

V20 modules:

```text
knowledge/loader.py
knowledge/schema.py
knowledge/retrieval.py
knowledge/rule_library.py
docs/bazi_knowledge/
```

Decision: convert data / reimplement loader.

Rationale:

- Knowledge content and reviewed boundaries are valuable.
- `knowledge/loader.py` is too large and hard-coded.
- V30 needs file-backed or data-backed knowledge packs with versioned loading.

V30 target:

```text
v30/knowledge/schema.py
v30/knowledge/loaders/
v30/knowledge/packs/
```

### Orchestrator Evidence

V20 modules:

```text
orchestrator/evidence.py
orchestrator/schema.py
```

Decision: reimplement from idea.

Rationale:

- Unified evidence item is a strong concept.
- V30 should make it foundational earlier in the pipeline.

V30 target:

```text
v30/evidence/compiler.py
v30/evidence/schema.py
```

### Mainline Arbitration

V20 modules:

```text
orchestrator/mainline.py
orchestrator/brain_state.py
orchestrator/question_focus.py
orchestrator/runtime_policy.py
```

Decision: reimplement from idea.

Rationale:

- Evidence-weighted arbitration works.
- V20 code mixes candidate collection, structure alignment, question focus, runtime policy, practitioner review, and public state.
- V30 should split these into separate services.

V30 target:

```text
v30/mainline/candidates.py
v30/mainline/arbitration.py
v30/mainline/state.py
v30/policy/runtime_pointer.py
```

### Question System

V20 modules:

```text
decision/questions.py
interaction/questions.py
interaction/question_atoms.py
interaction/question_dag.py
interaction/question_anchor.py
interaction/question_agent.py
interaction/question_ranker.py
role_view/narrative_prompt_framework.py
```

Decision:

- `question_anchor.py`: reimplement from idea.
- `question_atoms.py` and DAG data: convert data.
- `question_agent.py`: retire.
- `interaction/questions.py` raw title path: retire.
- `decision/questions.py` source logic: reference only.
- Ranking policies: reimplement from idea.

Rationale:

- V20 proved that anchors must be the only display question source.
- V30 should distinguish `QuestionIntent` from `DisplayQuestion`.

V30 target:

```text
v30/questions/intents.py
v30/questions/atoms.py
v30/questions/dag.py
v30/questions/anchor.py
v30/questions/rendering.py
```

### Answer System

V20 modules:

```text
answer/plan.py
answer/composer.py
answer/domain_reading.py
llm/prompts.py
llm/practitioner.py
llm/enforcement.py
validation/answer_safety_evaluator.py
```

Decision: reimplement from idea, reuse safety cases.

Rationale:

- AnswerPlan and deterministic answer are valuable.
- V20 LLM prompt context grew too large and too coupled.
- V30 should define `AnswerContext` as a compact verified contract.

V30 target:

```text
v30/answer/context.py
v30/answer/planner.py
v30/answer/composer.py
v30/llm/contracts.py
v30/validation/answer_safety.py
```

### Role, Locale, Client Projection

V20 modules:

```text
access/projection.py
access/roles.py
role_view/projection.py
role_view/policy.py
role_view/narrative_prompt_framework.py
i18n/ui_labels.py
frontend/app.js
```

Decision: reimplement.

Rationale:

- V20 projection helped clarify requirements but also caused title rewrite conflicts.
- V30 needs explicit `RoleProjection`, `LocaleRendering`, and `ClientPresentationModel`.

V30 target:

```text
v30/presentation/roles.py
v30/presentation/locales.py
v30/presentation/client_model.py
v30/frontend/
```

### Frontend

V20 modules:

```text
frontend/app.js
frontend/admin.js
frontend/styles.css
frontend/workbench-*.html
```

Decision: reimplement.

Rationale:

- V20 UI is functional but directly reads many runtime internals.
- V30 UI should consume a stable presentation model only.

V30 target:

```text
v30/frontend/index.html
v30/frontend/app.js
v30/frontend/admin.html
v30/frontend/styles.css
```

### Training and Runtime Pointers

V20 modules:

```text
learning/*_runtime_pointer.py
learning/*_training.py
learning/training_iteration.py
learning_orchestrator/
validation/
corpus/
```

Decision: reuse architecture idea; convert validation data; do not copy training orchestrator initially.

Rationale:

- Runtime pointer model is good.
- V20 training surface is too broad for V30 bootstrap.
- V30 first needs a smaller policy family.

Initial V30 policy families:

```text
structure_policy
mainline_policy
question_policy
answer_policy
presentation_policy
```

### Storage

V20 modules:

```text
storage/postgres_schema.py
redis/runtime_cache.py
storage/local_jsonl.py
```

Decision: reimplement.

Rationale:

- V30 requires separate table names, Redis prefix, runtime directory, and migration scripts.
- V20 schema should not be extended for V30.

V30 target:

```text
v30/storage/postgres_schema.py
v30/storage/redis_cache.py
v30/storage/events.py
```

## Initial Conversion Priority

Phase 1 conversion:

1. Core chart cases.
2. Structure dynamics synthetic cases.
3. Mainline expectation cases.
4. Question anchor smoke cases.
5. Answer safety cases.

Phase 2 conversion:

1. Question DAG replay.
2. Role view expectations.
3. 518K shard summaries.
4. Runtime pointer candidate reports.
5. Feedback ledgers.

## Retire List

Do not migrate these patterns:

- Raw `QuestionCandidate.title` as display source.
- `question_agent` follow-up compatibility layer.
- V20 all-in-one runtime payload for normal UI.
- Role projection that rewrites facts or selected structure.
- Knowledge loader as a giant hard-coded Python function.
- Runtime code reading V20 pointer files.
- Frontend fallback chains over many legacy field names.

## V30 Starting Rule

Every migrated asset must answer:

```text
What contract does this support?
What current chart fact does it bind to?
What role can see it?
What test proves it does not drift?
```

If those answers are unclear, the asset remains reference-only.
