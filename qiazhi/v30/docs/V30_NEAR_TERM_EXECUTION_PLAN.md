# V30 Near-Term Execution Plan

Updated: 2026-05-21

## Purpose

This document locks the immediate implementation order so V30 does not drift into side branches.

## Fixed Next Steps

### Step 1: QuestionAnchor Selector

Goal:

```text
MainlineState + StructureState + FeatureEvidence
-> BaziQuestionAnchor[]
```

Acceptance:

- Anchor binds to `context_id`. Completed.
- Anchor binds to `structure_id`. Completed.
- Anchor binds to `mainline_id`. Completed.
- Anchor has evidence IDs. Completed.
- Missing time produces boundary-aware questions, not timing predictions. Completed.
- Useful-god remains candidate/review only. Completed.

Not included:

- Full question DAG.
- Training.
- LLM.
- Hidden factor dialogue.
- UI redesign.

### Step 2: Runtime Pointer Base

Goal:

```text
PolicyArtifact
-> RuntimePointer
-> runtime loads active policy family
```

Initial family:

```text
structure_policy
```

Acceptance:

- V30-only pointer paths. Completed for local runtime store.
- In-memory or local JSON baseline. Completed with local JSON baseline.
- Auto-apply contract represented. Completed locally for synthetic-smoke-passing candidates.
- Rollback metadata represented. Completed in pointer update payload.
- Runtime trace can report active policy versions. Completed through `question_plan.policy_effect`.
- Manual promotion command exists for `structure_policy`. Completed.

Not included:

- Full Postgres persistence.
- Full Redis cache.
- Training scheduler.
- Real generated candidates.

### Step 3: Postgres and Redis Adapters

Goal:

```text
v30_readings
v30_runtime_traces
v30_policy_pointers
v30_artifacts
v30:* Redis keys
```

Acceptance:

- DB table names are `v30_*`. Completed at adapter/SQL boundary.
- V30 database URL is independent and cannot point to obvious V20 database names. Guard added.
- Redis keys start with `v30:`. Completed at keyspace/cache boundary.
- Reading and trace can be persisted. Adapter record/payload boundary completed; Postgres repository boundary completed with explicit `V30_REPOSITORY=postgres`.
- API can persist readings through `memory` or `local_json` repository. Completed.
- Pointer can be persisted or cached. Local pointer store completed; DB/Redis persistence pending.
- No V20 DB, Redis, or runtime file access. Covered by tests.

Not included:

- 518K full validation.
- Heavy training jobs.
- Admin dashboard.
- Live Postgres/Redis integration tests.

Database isolation note:

```text
V30_DATABASE_URL must point to a V30 database, recommended qiazhi_v30.
V30 must not share the V20 runtime database.
```

## Deferred Until After Step 3

- Real weighted structure graph algorithm.
- Knowledge/rule/portrait integration.
- 518K validation.
- Full question intelligence.
- LLM role expansion.

## Completed Focus: Postgres Repository Boundary

Goal:

```text
RuntimeRepository(reading + trace)
-> PostgresRuntimeRepository
-> v30_readings + v30_runtime_traces
```

Acceptance:

- `V30_REPOSITORY=postgres` is explicit. Completed.
- `V30_DATABASE_URL` is required for Postgres repository. Completed.
- Repository writes only `v30_readings` and `v30_runtime_traces`. Completed.
- Unit tests use fake connections and do not require live Postgres. Completed.
- Live Postgres integration remains a marked, explicit test tier. Maintained.
- No V20 database, Redis, runtime, or import dependency is introduced. Covered by tests.

## Current Focus: Real Environment Runtime Loop

Goal:

```text
API runtime
-> PostgresRuntimeRepository
-> Redis runtime cache
-> RuntimePointer auto-apply
-> synthetic/training validation
-> immediate active runtime behavior
```

Acceptance:

- V30 has a real environment env file contract.
- V30 has a sudo bootstrap script for independent `qiazhi_v30` Postgres DB/user.
- V30 can apply `v30_*` schema through `V30_DATABASE_URL`.
- V30 can write/read readings and traces in real Postgres.
- V30 can write/read readings and traces in real Redis with `v30:*` keys.
- API uses Redis cache when `V30_REDIS_URL` is present.
- Training/promotion flow remains auto-apply after validation, with no manual review gate.

Status:

- Redis host service is reachable at `redis://127.0.0.1:6379/0`.
- API is currently restarted with `V30_REDIS_URL=redis://127.0.0.1:6379/0`.
- API writes readings and traces to `v30:local:*` Redis keys.
- Postgres host service is listening on `127.0.0.1:5432`, but requires password auth.
- Postgres runs in Docker container `rag-postgres`.
- Docker bootstrap created independent `qiazhi_v30` database and `qiazhi_v30_app` user.
- `scripts/real_env_smoke.py` passed against real Docker Postgres and Redis.
- V30 API is currently running with Postgres repository and Redis cache.

## Current Focus: Auto-Apply Training Loop

Goal:

```text
synthetic validation
-> policy candidates
-> validation
-> policy artifacts
-> runtime pointers
-> API runtime behavior immediately sees active versions
```

Acceptance:

- One command runs the current mainline training loop.
- Training covers `structure_policy`, `mainline_policy`, and `question_policy` first.
- Passing validation promotes artifacts immediately.
- No review/approval gate is inserted between validation and active runtime pointer.
- API exposes a V30 admin endpoint to run the same loop.
- Runtime traces show active policy versions after training.

Status:

- `scripts/run_auto_training.py` applies the current core training loop.
- `/api/v30/admin/training/run` applies the same loop from the running API.
- `api-auto-001` was applied through API with 3/3 promoted.
- A subsequent runtime trace showed active versions from `api-auto-001`.
- The main path remains validation -> artifact -> pointer -> runtime, with no review gate.

## Current Focus: 518K Artifact Search

Goal:

```text
518K validation artifact
-> JSON index fallback
-> v30_artifacts record when Postgres is configured
-> admin artifact search endpoint
-> release gate searchable metadata
```

Acceptance:

- 518K sample/shard runs keep writing `.runtime/validation/518k/index.json`. Completed.
- Per-run index entries keep working as local/dev fallback. Completed.
- Runs upsert into existing `v30_artifacts` when `V30_DATABASE_URL` is available. Completed.
- No new DB table or V20 dependency is introduced. Completed.
- `/api/v30/admin/validation/518k/artifacts` returns run id, mode, case count, artifact URI, index entry URI, coverage/drift summary, failure cluster count, and created time. Completed.
- Release gate summaries include `artifact_searchable` and `artifact_record_id`. Completed.

Status:

- DB indexing is additive and falls back to JSON when Postgres is not configured.
- Search filters currently cover `mode`, `promotion_signal`, `run_id`, and `limit`.
- The next mainline gap is richer central-brain and adaptive-question replay diagnostics.

## Current Focus: Central Brain Adaptive Question Diagnostics

Goal:

```text
CentralBrainTrace
-> QuestionDialogueGraph
-> recommended question rows
-> adaptive question replay diagnostics
-> admin question-replay endpoint
```

Acceptance:

- Runtime trace records a replayable adaptive-question diagnostic contract. Completed.
- Diagnostics include rank, score, topic, stage, policy weight, policy version, and reason categories. Completed.
- Diagnostics include central-brain strategy, runtime focus, graph next question, selected question, replay inputs, and boundaries. Completed.
- Admin diagnostics and presentation diagnostics consume the replay payload. Completed.
- `/api/v30/admin/runs/{reading_id}/question-replay` exposes replay drilldown. Completed.
- The diagnostic layer does not mutate chart facts or policy pointers. Completed.

Status:

- `v30.adaptive_question_diagnostics.v1` is active in runtime policy effects.
- Replay controls are trace-based and compare rank, score, policy weight, reasons, and question strategy.
- The next mainline gap is converting replay diagnostics into bounded adaptive question-policy candidates.

## Current Focus: Adaptive Question Policy Candidate Generation

Goal:

```text
AdaptiveQuestionDiagnostics
-> v30.training_signal.adaptive_question_replay
-> question_policy.weights.adaptive_question_policy
-> synthetic + 518K validation
-> RuntimePointer auto-apply
```

Acceptance:

- Synthetic observed payloads include adaptive question diagnostics. Completed.
- Training extraction emits `v30.training_signal.adaptive_question_replay`. Completed.
- Signal payload includes decision count, weighted decision coverage, alignment coverage, topics, stages, intents, strategies, and reason-category counts. Completed.
- `question_policy` candidates include bounded `adaptive_question_policy` weights. Completed.
- Existing auto-apply path validates and promotes the candidate without a manual review gate. Completed.
- Boundary remains replay diagnostics, not chart facts. Completed.

Status:

- Adaptive question replay now feeds conservative topic/stage/intent candidate weights.
- The next mainline gap is candidate comparison diagnostics for active-vs-candidate question order.

## Current Focus: Question Policy Comparison Diagnostics

Goal:

```text
active runtime trace
-> candidate question_policy payload
-> active/candidate recommendation replay
-> rank/score/weight/reason deltas
-> persisted comparison artifact
-> admin lookup
```

Acceptance:

- Comparison recomputes candidate recommendations without mutating the runtime trace. Completed.
- Comparison records rank delta, score delta, policy-weight delta, added reasons, and removed reasons. Completed.
- Question-policy promotion stores comparison summary in the promoted artifact. Completed.
- Comparison artifacts persist under `.runtime/validation/question_policy_comparisons/`. Completed.
- Admin API exposes latest or candidate-specific comparison lookup. Completed.
- Boundaries state comparison diagnostics are not chart facts or pointer mutations. Completed.

Status:

- `v30.question_policy_comparison.v1` is active for question-policy promotion.
- The next mainline gap is unifying comparison artifacts with the broader validation artifact search/admin discovery surface.

## Current Focus: Unified Validation Artifact Discovery

Goal:

```text
518K validation artifacts
+ question-policy comparison artifacts
-> v30_artifacts when Postgres is configured
-> JSON fallback indexes
-> unified admin artifact discovery
```

Acceptance:

- 518K artifacts remain searchable through the existing endpoint. Completed.
- Question-policy comparison artifacts index as `family=question_policy_comparison` when Postgres is configured. Completed.
- JSON fallback remains available for local/dev comparison artifacts. Completed.
- Unified endpoint filters by `family`, `candidate_id`, `run_id`, and `limit`. Completed.
- No new DB schema is introduced. Completed.

Status:

- `/api/v30/admin/validation/artifacts` is active for unified validation artifact discovery.
- The next mainline gap is promotion lineage graph diagnostics across policy artifact, validation artifact, runtime pointer, and live trace.

## Current Focus: Promotion Lineage Graph Diagnostics

Goal:

```text
RuntimePointer
-> PolicyArtifact
-> validation summaries and artifacts
-> active runtime trace consumption
-> admin lineage lookup
```

Acceptance:

- Active pointer can generate a lineage graph. Completed.
- Lineage includes active artifact, previous artifact, validation run id, rollback pointer, and policy artifact summary. Completed.
- Question-policy lineage links comparison artifacts and 518K validation evidence. Completed.
- Lineage confirms active policy versions are consumed by a runtime trace. Completed.
- `/api/v30/admin/policies/lineage?family=question_policy` exposes lineage lookup. Completed.
- Lineage is diagnostic only and does not retrain, promote, mutate pointers, or create chart facts. Completed.

Status:

- `v30.promotion_lineage.v1` is active for core runtime policy families.
- The next mainline gap is a compact admin operations dashboard that aggregates health, active lineage, validation artifact discovery, and latest gate status.

## Current Focus: Evidence-Driven Question Recommendation

Goal:

```text
FeatureEvidence + StructureState + MainlineState + active question_policy
-> scored question recommendations
-> runtime trace
-> UI presentation
```

Acceptance:

- Question ordering is driven by evidence, missing requirements, mainline quality gate, and active policy versions.
- Runtime stores a scored recommendation plan, not only a fixed anchor list.
- UI view exposes score, topic, stage, and reasons for each recommended question.
- Synthetic tests verify missing time and useful-god boundaries stay active.

Status:

- `QuestionIntentPlan.recommended_questions` stores scored recommendations.
- The recommender uses evidence domains, missing requirements, structure state, mainline quality gate, and active `question_policy`.
- Presentation view includes recommendation `score`, `stage`, `topic`, and `reasons`.
- Missing time context is prioritized ahead of general review when it blocks downstream timing claims.
- API view sorts questions by recommendation score.

## Current Focus: Hidden Factor Dialogue Discovery

Goal:

```text
hidden stem / boundary evidence
-> hidden factor probes
-> dialogue question anchor
-> user special-year/state feedback
-> hidden factor confidence update later
```

Acceptance:

- Hidden factor is represented as a hypothesis/probe, not a deterministic chart conclusion.
- The system asks for boundary years, special events, and repeated states to discover amplifiers.
- The question is bound to current Bazi context and evidence IDs.
- Runtime trace exposes hidden factor probes for future calibration.

Status:

- `HiddenFactorProbe` is generated from hidden-stem evidence.
- `q_v30_hidden_factor_boundary_discovery` is bound to the current context and evidence.
- Recommendation topic/stage are `hidden_factor` and `dialogue_discovery`.
- Required feedback includes special event year, repeated state pattern, and luck/flow context if available.
- Hidden-factor calibration now consumes feedback counter-evidence and marks amplifier candidates only after user-calibrated evidence is present.

## Current Focus: Locale and Client Presentation

Goal:

```text
CoreRuntimeResult
-> role projection
-> locale rendering
-> client profile
-> ClientPresentationModel
```

Acceptance:

- Presentation output supports `zh`, `en`, and `ko` labels for runtime-controlled UI text.
- Presentation output supports `web`, `mobile`, and `admin` client profiles.
- Mobile output is compact and action-light.
- Admin output exposes diagnostics and runtime policy versions.
- Locale/client adaptation remains downstream of runtime facts and does not mutate Bazi reasoning.

Status:

- Runtime-controlled labels now support `zh`, `en`, and `ko`.
- Client profiles now support `web`, `mobile`, and `admin`.
- Mobile uses compact density, fewer questions, and hides reasons.
- Admin uses diagnostic density, shows runtime policy versions, trace ID, hidden-factor probe count, and training/trace actions.
- The V30 UI at `/v30/ui/` now renders a mainline workbench with structure dynamics, K/R/P counts, answer boundary, question reasons, and active policies. The active UIB mainline moves customer hidden-factor calibration into the unified intelligent Q&A surface with structured constraints instead of a separate customer form.

## Current Focus: Knowledge/Rule/Portrait Seed Registry

Goal:

```text
FeatureEvidence
-> V30-owned knowledge/rule/portrait seed registry
-> bound signals
-> runtime trace
-> synthetic validation
```

Acceptance:

- Seed knowledge, rule, and portrait records live under V30 code/data.
- Runtime emits bound signals with source IDs and evidence IDs.
- No V20 runtime import or shared V20 data path.
- Synthetic smoke validates at least one knowledge/rule/portrait signal.

Status:

- V30 now has a first K/R/P library unit layer for ten-god context, useful-god candidate gates, hidden-factor feedback calibration, and dynamic structure paths.
- Runtime matches K/R/P units against `FeatureEvidence.supports` and exposes them in `question_plan.policy_effect.krp_library_units`.
- Unit tests cover K/R/P matching without importing or reading V20 runtime code.

## Current Focus: Consume Knowledge/Rule/Portrait Signals

Goal:

```text
FeatureEvidence
-> K/R/P signals
-> StructureState path scores/chains
-> MainlineState supporting lines/why
-> Question recommendation reasons
```

Acceptance:

- Structure state includes K/R/P signal counts and IDs.
- Mainline selection explains useful-god and hidden-stem boundaries through K/R/P signals.
- Question recommendations include K/R/P-driven reasons.
- Synthetic validation checks that K/R/P signals affect runtime behavior, not only diagnostics.

Status:

- K/R/P signals are already consumed by structure/mainline/question scoring.
- The new K/R/P library units are currently exposed to runtime trace and UI diagnostics; deeper per-unit scoring is next after P0-P7 vertical closure.

## Current Focus: Question Policy Weight Consumption

Goal:

```text
active question_policy artifact payload
-> recommendation weights
-> question score/order
-> ClientPresentationModel
```

Acceptance:

- [x] Runtime loads the active `question_policy` artifact payload.
- [x] Question recommender applies topic/intent/stage/question weights.
- [x] Auto-training generates a question policy weight candidate.
- [x] Runtime trace exposes consumed question policy payload.
- [x] Unit tests prove policy weights change recommendation scores/order.
- [x] Synthetic smoke and 518K sample rerun after this step.
- [x] Real Postgres/Redis service restarted and trace verified with `question_policy.question-weight-001.question_policy`.
- [x] Synthetic `all` gate added and verified at 10/10.
- [x] Auto-training re-applied through synthetic `all` as `synthetic-gradient-001`.
- [x] Real Postgres/Redis service restarted and trace verified with `question_policy.synthetic-gradient-001.question_policy`.
- [x] 518K sample gate added to policy promotion.
- [x] 518K candidate payload replay added before pointer activation.
- [x] Auto-training re-applied through synthetic `all` + 518K sample as `518k-gate-001`.
- [x] Real Postgres/Redis service restarted and trace verified with `question_policy.518k-gate-001.question_policy`.
- [x] Release gate runner added.
- [x] Release gate quick verified: runtime smoke + synthetic `all` + 518K sample.
- [x] Release gate standard verified: quick checks + selected 518K shard.
- [x] Real Postgres/Redis service restarted after release gate work and trace verified.

Synthetic validation status:

```text
SyntheticBaziCase schema, smoke runner, gradient runner, and all-tier promotion gate are now available.
Promotion replays candidate policy payloads before pointer activation.
Generator remains deferred.
```

## Current Runtime Chain

Current:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> BaziQuestionAnchor
-> RuntimePointer
-> RuntimeRepository(reading)
```

## Current Focus: Rule Evidence Skeleton

Goal:

```text
V20 rule/knowledge/dynamics review
-> V30 RuleEvidenceSpec
-> rule FeatureEvidence
-> Structure/Mainline/Question consumption
-> synthetic/release validation
```

Acceptance:

- [x] Review V20 rule runtime, knowledge rule library, defeasible model, and structure dynamics graph.
- [x] Add V30-owned rule evidence specs without runtime importing `v20.*`.
- [x] Compile rule evidence into `FeatureEvidence`.
- [x] Consume rule evidence in `StructureState.path_scores`.
- [x] Consume rule evidence in `MainlineState.supporting_mainlines` and `why_selected`.
- [x] Consume rule evidence in question recommendation reasons.
- [x] Real Postgres/Redis service restarted and trace verified with rule evidence consumption.
- [x] Add rule policy payload weighting for rule evidence scores.
- [x] Add rule policy gradient synthetic case.
- [x] Auto-training re-applied through synthetic `all` + 518K sample as `rule-policy-001`.
- [x] Real Postgres/Redis service restarted and trace verified with `rule_policy.rule-policy-001.rule_policy`.
- [x] Add counter-evidence skeleton through `rule_decision_state`.
- [x] Add synthetic counter-evidence case for explicit time layer.
- [x] Real Postgres/Redis service restarted and trace verified with `rule_decision_state:*`.
- [x] Add hidden-factor user-feedback counter-evidence case.
- [x] Add supplemental feedback evidence channel for rule replay.
- [x] Real Postgres/Redis service restarted after hidden-factor feedback counter-evidence work.
- [x] Add broader rule conflict synthetic cases for useful-god and branch-relation feedback.

P0 completion status:

- [x] Rule evidence supports `blocked`, `requires_review`, `requires_dialogue`, and `countered`.
- [x] Time, useful-god, hidden-factor, and branch-relation counter-evidence are covered by synthetic cases.
- [x] Synthetic `all` verifies 15 cases.
- [x] Release gate standard passes after P0.

## Current Focus: Structure Dynamics v2

Goal:

```text
FeatureEvidence + RuleEvidence + K/R/P signals
-> weighted dynamic path extraction
-> StructureState graph/path scores
-> Mainline/Question consumption
-> structure_policy tuning
```

Acceptance:

- [x] Add V30-owned dynamic graph nodes and edges.
- [x] Add deterministic path extraction.
- [x] Apply `structure_policy` weights to dynamic graph path scores.
- [x] Preserve current mechanism path v1 during migration.
- [x] Add synthetic structure v2 path case.
- [x] Real Postgres/Redis service restarted and trace verified with dynamic graph v2 path scores.
- [x] Connect dynamic graph v2 paths to mainline/question explanations.

## P0-P7 Mainline Completion Snapshot

Status after the latest mainline batch:

- P0 Rule conflict/counter-evidence: completed for time, useful-god, hidden-factor, and branch-relation feedback.
- P1 Structure Dynamics v2: completed first vertical slice; dynamic graph nodes/edges/path scores feed structure, mainline, questions, UI, and trace.
- P2 Knowledge/Rule/Portrait library: completed first V30-owned library layer and runtime matching.
- P3 Hidden Factor calibration: completed first feedback-to-amplifier calibration path.
- P4 Question Intelligence v2: completed first dynamic-graph/K/R/P-aware recommendation scoring path.
- P5 LLM/Answer skeleton: completed rule-bound answer context/result contract; LLM fact mutation remains explicitly blocked by boundary fields.
- P6 UI workbench: completed first V30-only workbench view with diagnostics and active policies.
- P7 518K canonical source interface: completed JSONL/CSV source adapter while preserving deterministic generated fallback.

Latest mainline increment:

- P2 K/R/P library now has policy-weighted unit scores and score reasons.
- P2 K/R/P library now matches supports and weakens, expanding baseline coverage from 4 to 8+ units.
- P2 K/R/P library now covers time-boundary, time-activation, element-balance, branch-dynamic, hidden-dialogue, hidden-feedback-counter, and rule-counterevidence trace units.
- P2 K/R/P library now includes chart context, day-master element context, hidden-stem hypothesis, and useful-god resolved-counter units; baseline coverage is 11+ units.
- P2 K/R/P library now exposes `v30.krp.pack.core_runtime` pack metadata, version, required/counter context, mechanism hooks, portrait dimensions, portrait tags, training tags, locale terms, and `krp_library_summary`.
- P2 Synthetic validation now checks K/R/P pack ID and required portrait tags through the normal runtime chain.
- P2 Knowledge source inventory now records reusable V20 assets and public reference sources without creating runtime V20 dependencies.
- P2 Multi-dimensional macro taxonomy now covers foundation, wealth, career, relationship, romance, health, and hidden-factor dimensions as V30-owned pack metadata.
- P2 Core macro pack loader now exposes `v30.knowledge.pack.core_macro_zh_v1` through `question_plan.policy_effect.core_macro_pack_summary`.
- P2 Synthetic validation now checks required macro domains through the normal runtime chain.
- P2 Runtime now emits `macro_dimension_signals` for foundation, wealth, career, relationship, romance, health, and hidden-factor dimensions.
- P2/P4 Training now extracts `v30.training_signal.macro_dimension_coverage` from synthetic macro dimension signals.
- P2/P4 Auto-training re-applied through synthetic `all` + 518K sample as `macro-signal-001`; active pointers now use `structure_policy.macro-signal-001.structure_policy`, `mainline_policy.macro-signal-001.mainline_policy`, `question_policy.macro-signal-001.question_policy`, and `rule_policy.macro-signal-001.rule_policy`.
- P4 Question recommendation now consumes macro dimension signals and records `macro_dimension_context:*` reasons without overriding missing-time priority.
- P5 Answer context now exposes matched macro dimension signals and boundaries to the role answer contract.
- P6 Presentation now respects recommender order instead of re-sorting capped scores.
- P4/P2 Macro portrait projection v1 now emits bounded portrait projections for foundation, wealth, career, relationship, romance, health, and hidden-factor domains.
- P5 Answer context now exposes matched macro portrait projections to the role answer contract.
- P4/P2 Training now extracts `v30.training_signal.portrait_projection_coverage` from synthetic portrait projections.
- P4 Question Intelligence now emits a dialogue graph with nodes, edges, next question, and policy notes.
- P4/P2 Training now extracts synthetic K/R/P coverage and question graph edge signals before candidate generation.
- P4 Training now feeds those signals into `question_policy.krp_unit_weights`.
- P3 Hidden Factor now has persistent `HiddenFactorState` with special years, repeated states, feedback IDs, amplifier strength, and V30-only storage.
- P3 Hidden Factor API now supports `/api/v30/readings/{reading_id}/hidden-factor/feedback` and `/state`.
- P3 Synthetic validation now checks calibrated hidden-factor feedback becomes `amplifier_candidate`.
- P3 Hidden Factor state now rehydrates runtime view/admin trace, question recommendations, question dialogue graph, and answer context.
- P3 Hidden Factor state now supports `user_denied` and `conflicting` paths; synthetic validation covers year-only, state-only, amplifier, and denial states.
- P3 Hidden Factor event-year modeling now exposes `event_year_signal`, `repeated_state_signal`, and `alignment_score`; only year + repeated-state alignment can become `amplifier_candidate`.
- P3 Training now extracts `v30.training_signal.hidden_factor_event_alignment` from synthetic hidden-factor states.
- P1 Structure Dynamics v2 now emits path competition rank, competition suppression, and score reasons.
- P1 StructureState now exposes dynamic competing/suppressed/blocked/countered path metrics.
- P3 Training now extracts `structure_dynamic_competition` signals from synthetic path metrics.
- P3 Training now feeds structure dynamic signals into `structure_policy.dynamic_graph.v2` and `structure_policy.dynamic_graph.competition_suppression`.
- P3 Training auto-applied `structure-signal-001` after synthetic `all` + 518K sample validation; active pointers now use `structure_policy.structure-signal-001.structure_policy`, `mainline_policy.structure-signal-001.mainline_policy`, `question_policy.structure-signal-001.question_policy`, and `rule_policy.structure-signal-001.rule_policy`.
- P1 Structure Dynamics v2 live API verification confirmed `dynamic_graph.v2=1.04`, `dynamic_graph.competition_suppression=1.03`, 8 dynamic path graph nodes, 3 competing paths, and 3 suppressed paths in the real Postgres/Redis runtime.
- P5 LLM context now has a V30-owned role prompt context contract for `guest/user/practitioner/analyst/admin/lab`.
- P5 LLM guardrail now has a deterministic drift checker for unsupported timing and hidden-factor confirmation claims.
- P7 518K validation now writes V30 artifact JSON files under `.runtime/validation/518k/`.

Latest verification:

- `pytest -q`: 128 passed, 1 skipped.
- `python3 scripts/run_release_gate.py --mode standard --shard-id 7 --sample-limit 8 --shard-limit 16`: eligible.
- `V30_RUN_REAL_ENV_TESTS=1 pytest tests/integration/test_real_environment.py -q`: 1 passed against Docker Postgres and Redis.
- `GET /v30/ui/`: 200 from the restarted real V30 service on port 9030.
- Live API `v30-krp-live` confirmed `krp_library_summary.unit_count=11`, pack ID `v30.krp.pack.core_runtime`, and active `structure-signal-001` policy pointers.
- Live API `v30-core-macro-live` confirmed `core_macro_pack_summary.pack_id=v30.knowledge.pack.core_macro_zh_v1`, 7 macro domains, and UI 200.
- Live API `v30-macro-signal-policy-live` confirmed 7 `macro_dimension_signals`, `macro_dimension_coverage` in active question policy training signals, active `macro-signal-001` pointers, and UI 200.
- Live API `v30-macro-consumption-live` confirmed top question remains `q_v30_time_context_boundary`, recommendation reasons include `macro_dimension_context:*`, answer contract can use `macro_dimension_signals`, and UI preserves top question order.
- Live API `v30-portrait-live` confirmed 7 `macro_portrait_projections`, source policy `portrait_is_projection_not_fact_source`, answer contract portrait projections, and UI 200.

Latest mainline update:

- P5 Expression framework added as `v30.expression`.
- Runtime now emits `expression_framework_version`, `expression_plan`, and `rendered_narrative`.
- `AnswerResult.text` now consumes the expression layer instead of direct engineering string composition.
- P0 Central brain minimum vertical slice added as `v30.brain`.
- Runtime now emits `central_brain_version` and `central_brain_trace`.
- Central brain trace now includes session memory, role state, and feedback strategy.
- Admin diagnostics now consume central brain focus, question strategy, expression surface, feedback targets, and training routes.
- Question recommendation now consumes central brain recommendation context and emits central brain reasons.
- Expression planning now consumes central brain role state for role density and voice.
- Synthetic validation now checks expression quality, including Bazi term coverage, boundary language, and engineering-token leakage.
- Training signals now include `v30.training_signal.expression_quality`.
- Synthetic training signals now include `v30.training_signal.central_brain_route_coverage`.
- New design doc: `docs/V30_EXPRESSION_AND_CENTRAL_BRAIN_FRAMEWORK.md`.
- P2 K/R/P library expanded from 11+ to 18+ matched runtime units.
- P2 Feature evidence now emits ten-god family supports for visible/hidden stems and branch relation conflict/alignment family supports.
- P2 K/R/P library now includes ten-god output/wealth/authority/resource/self family units plus branch conflict/alignment family units.
- P1 Structure Dynamics v2 now emits conflict-family path explanations and exposes branch conflict/alignment edge metrics.
- P3 Training now feeds conflict-family coverage into `structure_policy.weights.dynamic_graph.conflict_family`.
- P2/P1 Synthetic validation now checks expanded K/R/P unit coverage and dynamic conflict-family metrics.
- Auto-training run `krp-conflict-family-001` applied 4/4 policy families after validation.
- Live real-runtime trace confirmed active `krp-conflict-family-001` pointers, `krp_library_summary.unit_count=18`, `dynamic_path_count=12`, `dynamic_branch_conflict_edge_count=7`, `dynamic_branch_alignment_edge_count=7`, and `dynamic_graph.conflict_family=1.015`.
- P2 K/R/P library expanded again from 18+ to 22+ matched runtime units.
- P2 Feature evidence now emits `structure_pattern` review candidates for seasonal strength, 格局 candidate boundaries, day-master share buckets, and useful-god candidate families.
- P2 K/R/P library now includes seasonal strength review, 格局 candidate review, useful-god family candidate review, and path-resolution review units.
- P1 Structure Dynamics v2 now emits `resolution_families` and exposes `dynamic_path_resolution_family_count` plus `strength_pattern_review_count`.
- P3 Training now feeds path-resolution coverage into `structure_policy.weights.dynamic_graph.path_resolution`.
- Auto-training run `strength-path-resolution-001` applied 4/4 policy families after validation.
- Live real-runtime trace confirmed active `strength-path-resolution-001` pointers, `krp_library_summary.unit_count=22`, `dynamic_path_resolution_family_count=3`, `strength_pattern_review_count=1`, and `dynamic_graph.path_resolution=1.036`.
- P2 K/R/P library expanded from 22+ to 27+ matched runtime units.
- P2 Feature evidence now emits `domain_rule` review candidates for wealth, career, relationship, health, and useful-god domain paths.
- P2 K/R/P library now includes wealth path review, career authority path review, relationship relation path review, health element imbalance review, and useful-god domain path candidate review units.
- P1 Structure Dynamics v2 now exposes `dynamic_wealth_path_count`, `dynamic_career_path_count`, `dynamic_relationship_path_count`, `dynamic_health_review_path_count`, and `dynamic_useful_god_candidate_path_count`.
- P3 Training now feeds domain-path coverage into `structure_policy.weights.dynamic_graph.domain_path` and `structure_policy.weights.dynamic_graph.useful_god_candidate_path`.
- P4 Training now feeds domain K/R/P coverage into question policy weights for wealth, career, relationship, and health.
- Auto-training run `domain-rule-depth-001` applied 4/4 policy families after validation.
- Live real-runtime trace confirmed active `domain-rule-depth-001` pointers, `krp_library_summary.unit_count=27`, wealth/career/relationship/health/useful-god domain path counts, `dynamic_graph.domain_path=1.06`, and `dynamic_graph.useful_god_candidate_path=1.06`.
- P2 K/R/P library expanded from 27+ to 35+ matched runtime units with wealth competition/output/authority bridge, career authority-pressure/resource-resolution, relationship conflict/alignment/marker, and health excess/thin/conflict-pressure review units.
- P1 Structure Dynamics v2 now exposes fine-grained domain-rule depth metrics and training payload `average_domain_rule_depth_path_count`.
- P3 Training now feeds domain-rule depth coverage into `structure_policy.weights.dynamic_graph.domain_rule_depth`.
- P3 Hidden Factor state now has `expires_at`, `stale_after_days`, and `time_layer_alignment_score`; expired candidates rehydrate as refresh-needed instead of amplifier candidates.
- P7 518K validation now writes a persistent run index (`index.json`) plus per-run index entries and exposes those URIs through release gate summaries.
- P4 Question Intelligence now persists answer feedback as bounded `question_outcomes`, recomputes graph/recommendations, and emits `v30.training_signal.question_dialogue_outcome`.
- P4 Training now feeds question dialogue outcome signals into conservative `question_policy` topic/intent weights.
- P5 LLM output contracts now validate `AnswerDraft` and `QuestionExplanation` through deterministic drift checks and emit `v30.training_signal.llm_output_contract_quality`.
- P4 Portrait projection now emits role-aware `macro_portrait_projection_views`; synthetic role contrast validates guest/admin hidden-factor visibility and training emits `v30.training_signal.portrait_projection_view_coverage`.
- P5 LLM output contracts now also validate `SyntheticCaseDraft` and `FailureClusterSummary`; training quality records four-task coverage.
- P3 Hidden Factor training now converts event-year/repeated-state alignment into conservative `hidden_factor_event_policy` weights for question/rule policies; conflicts and denials downweight before positive alignment can boost.
- Auto-training run `hidden-factor-policy-001` applied 4/4 policy families after synthetic/release validation.
- Live real-runtime trace confirmed active `question_policy.hidden-factor-policy-001.question_policy`, `candidate_alignment_multiplier=1.029`, `conflict_multiplier=0.885`, `denial_multiplier=0.825`, and boundary `hidden_factor_policy_weights_feedback_conditioned_not_chart_fact`.
- P1/P2 Structure and K/R/P now include bounded 通关/制化 path-resolution candidates with `dynamic_tongguan_*` and `dynamic_zhihua_*` scores.
- P3 Training now feeds those metrics into `structure_policy.weights.dynamic_graph.tongguan_zhihua`.
- Auto-training run `tongguan-zhihua-001` applied 4/4 policy families after validation.
- Live real-runtime trace confirmed active `structure_policy.tongguan-zhihua-001.structure_policy`, `dynamic_graph.tongguan_zhihua=1.06`, `dynamic_tongguan_path_count=9.0`, `dynamic_zhihua_path_count=11.0`, and K/R/P `unit_count=42`.
- P5/P8 Presentation now consumes deterministic expression-rendered question labels and exposes rendered-label diagnostics.
- P3 Training now emits `v30.training_signal.per_unit_parameter_tuning` and feeds bounded rule/domain/mechanism weights into rule and structure policy candidates.
- Auto-training run `per-unit-tuning-001` applied 4/4 policy families after validation.
- Live real-runtime trace confirmed active `structure_policy.per-unit-tuning-001.structure_policy` and `rule_policy.per-unit-tuning-001.rule_policy`, `mechanism.useful_god_candidate_gate=1.035`, `v30.rule.useful_god.candidate_gate=1.03`, `domain_weights.structure_dynamic=1.015`, and `per_unit_parameter_policy.unit_count=46`.

Next mainline hardening:

- Promote 518K JSON run index into DB-backed artifact search once schema ownership is scheduled.
- Expand central brain question strategy into adaptive question policy candidates.
- Promote hidden-factor event-year tuning into policy weighting once enough real feedback distribution exists.
- Continue expanding K/R/P source mapping and deeper 通关/制化 path resolution beyond current 35+ matched runtime units.
- Expand per-unit parameter tuning from synthetic case feedback beyond `question_policy`.
- Tune hidden-factor expiration windows and deeper time-layer decay from real feedback distribution.
- Extend structure dynamic v2 from current path-resolution candidates into richer 通关/制化 and path-resolution explanations.
- Add persistent DB artifact indexing for 518K source runs.
- Promote 518K JSON run index into DB-backed artifact search once schema ownership is scheduled.
- Feed expression-rendered question labels into presentation models.

Completed focused task:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> BaziQuestionAnchor
-> RuntimePointer
-> RuntimeRepository(reading + trace)
```

Acceptance:

- Runtime trace is stored through the repository boundary. Completed.
- API admin trace reads through the repository boundary. Completed.
- Local JSON trace files stay under `V30_RUNTIME_DIR/traces/`. Completed.
- Default tests stay lightweight. Completed, `pytest` remains under a few seconds.
- No V20 database, Redis, runtime, or import dependency is introduced. Covered by tests.
