# V30 Roadmap

Updated: 2026-05-24

## Purpose

V30 is a new independent runtime built from V20 lessons. It is not a V20 rename, patch branch, or compatibility layer.

The roadmap has two jobs:

1. Keep V30 fully isolated from V20 at runtime.
2. Rebuild the system around high iteration, automatic self-training, synthetic validation, 518K validation, intelligent question recommendation, and stronger LLM role/context capability.

## Non-Negotiable Direction

V30 must satisfy these rules throughout development:

- Code package is `v30`.
- API prefix is `/api/v30`.
- UI prefix is `/v30/ui`.
- Runtime files live under `v30/.runtime`.
- Postgres names are `v30_*`.
- Redis keys are `v30:*`.
- Runtime code must not import `v20.*`.
- V20 may be used only as reference, offline export source, or migration input.
- Every migration decision must be documented in Markdown before implementation.
- Training is designed for automatic validation and automatic application, not a manual review-first workflow.
- Tests are tiered so ordinary development remains fast.

## Current State

### Completed

- V30 scaffold exists under `/home/hlsystem/bazi/qiazhi/v30`.
- V30 API smoke service is available on port `9030`.
- Nginx can route `https://dblife.com/v30/ui/` to V30 independently.
- Initial contract models exist in `v30/contracts.py`.
- Initial storage guards exist for `v30_*` tables and `v30:` Redis keys.
- Initial tests reject runtime import from `v20.*`.

### Current Built Runtime Slices

- Core V30 Bazi context, BirthInput, calendar conversion trace, luck/flow context, six-pillar context, ten-god energy model, and evidence compiler are active.
- V30 knowledge/rule/portrait library is active with 39+ matched baseline units, including ten-god family, branch conflict/alignment family, seasonal strength, 格局 candidate, useful-god family candidate, path-resolution, domain-rule depth, and wealth/career/relationship/health domain rule units.
- Structure dynamics v2 is active with mechanism paths, dynamic graph paths, competition suppression, conflict-family metrics, path-resolution-family metrics, domain path coverage metrics, and domain-rule depth metrics.
- Mainline arbitration consumes structure, evidence, rules, K/R/P, macro signals, and dynamic graph diagnostics.
- Runtime pointer and auto-apply training loop are active for `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy`.
- Synthetic validation and 518K sample/shard validation are active release gates; 518K runs now persist artifact/index URIs and searchable `v30_artifacts` records when Postgres is configured.
- Intelligent question recommendation, dialogue graph, central brain context, selected structured options, compact `known_user_signals`, graph-selected next question, and hidden-factor event-year modeling are active; hidden-factor alignment stays feedback-conditioned and cannot become a chart fact.
- Multi-role LLM context and expression guardrails are active as bounded contracts; bounded LLM answer draft status is exposed through admin diagnostics when configured.
- Multi-locale and multi-client presentation projection supports initial `zh/en/ko` and `web/mobile/admin/lab`.
- Actor/session hooks exist as identity/session anchors; full login and historical reading retrieval remain open.
- Persistent service management and deeper deployment observability remain open.

## Architecture Spine

V30 should converge on this runtime spine:

```text
ChartContext
-> TenGodEnergyModel
-> FeatureEvidence
-> KnowledgeEvidence + RuleEvidence
-> StructureState
-> Strength/Structure/UsefulGod RankedDecision
-> MainlineState
-> QuestionIntelligenceState
-> BaziQuestionAnchor[]
-> StructuredInteractionState
-> AnswerContext
-> RoleProjection
-> LocaleRendering
-> ClientPresentationModel
```

The learning spine is separate but always connected:

```text
RuntimeTrace
-> FeedbackEvent + SyntheticCase + 518KShardResult
-> TrainingRun
-> ValidationRun
-> PolicyCandidate
-> PolicyArtifact
-> ArtifactSearch
-> RuntimePointer
-> AutoApplyResult
-> RuntimeTrace
```

## Phase Plan

### Phase 0: Independent Scaffold

Goal: make V30 independently reachable and testable.

Status: in progress, mostly complete.

Acceptance:

- `/api/v30/health` returns V30 metadata.
- `/v30/ui/` serves V30 UI.
- No runtime import from `v20.*`.
- No V20 Redis or DB naming appears in V30 runtime code.
- V30 nginx routing does not fall through to `/v20/ui/`.
- `V30_DATABASE_URL` points to an independent V30 database, recommended `qiazhi_v30`.

### Phase 1: Documentation and V20 Deep Review

Goal: document the V30 design before moving major runtime behavior.

Required docs:

- `docs/V30_MASTER_MAINLINE_PLAN.md`
- `docs/V30_ROADMAP.md`
- `docs/V30_MODULE_REVIEW.md`
- `docs/V30_TEST_ARCHITECTURE.md`
- `docs/V30_ALGORITHM_AND_MODELING_REVIEW.md`
- `docs/V30_TRAINING_ARCHITECTURE.md`
- `docs/V30_SYNTHETIC_VALIDATION.md`
- `docs/V30_518K_VALIDATION_PLAN.md`
- `docs/V30_KNOWLEDGE_RULE_PORTRAIT_PLAN.md`
- `docs/V30_INTEGRATED_BAZI_MODEL_PIPELINE.md`
- `docs/V30_STRUCTURE_DYNAMICS.md`
- `docs/V30_QUESTION_INTELLIGENCE.md`
- `docs/V30_HIDDEN_FACTORS_AND_DIALOGUE_DISCOVERY.md`
- `docs/V30_LLM_CONTEXT_AND_ROLES.md`
- `docs/V30_RUNTIME_POINTERS.md`

Acceptance:

- Each V20 module family has a migration decision.
- Each advanced framework or algorithm has a V30 target design.
- Each heavy test or validation path has a non-default execution tier.
- No implementation task starts without a documented contract or migration decision.

### Phase 2: Core Bazi Context

Goal: build the deterministic fact layer.

Scope:

- Chart context.
- Original natal chart.
- Luck cycle.
- Annual flow.
- Missing time state.
- Ten gods.
- Five elements.
- Relationships.
- Strength and useful-god signals.
- Feature evidence.

Acceptance:

- Core facts are immutable during a reading.
- Missing time context is explicit.
- Feature evidence links back to chart context.
- Unit tests are fast and deterministic.
- Converted V20 core cases pass.

### Phase 3: Knowledge, Rules, Portraits, and Structure Dynamics

Goal: rebuild the reasoning base as V30-native modules and integrate them into one generate-validate-tune-apply pipeline.

Scope:

- Knowledge packs.
- Rule catalog.
- Rule evidence.
- Feature policy.
- Bazi portrait ontology.
- Bazi feature model.
- Structure mechanism definitions.
- Weighted dynamic graph.
- Mainline arbitration.
- Synthetic Bazi case validation.
- Parameter family tuning.

Acceptance:

- Knowledge and rules are versioned.
- Knowledge, rules, features, portraits, and structure dynamics share one validation lifecycle.
- Structure labels come from reviewed mechanism definitions.
- Mainline arbitration ranks evidence instead of inventing facts.
- Runtime pointer reads V30 artifacts only.
- Synthetic structure cases pass at smoke tier.
- Positive, negative, metamorphic, boundary gradient, and composite synthetic cases exist for high-signal patterns.

### Phase 4: Training, Synthetic Validation, and 518K Validation

Goal: make self-training and validation a first-class runtime loop.

Scope:

- Training run schema.
- Validation run schema.
- Policy candidate schema.
- Policy artifact registry.
- Runtime pointer families.
- Synthetic validation runner.
- 518K shard validation runner.
- Promotion criteria.
- Rollback metadata.

Core rule:

```text
validated training output auto-applies through V30 runtime pointers
```

Manual review is allowed as observation, debugging, and override. It is not the primary application path.

Acceptance:

- Training produces versioned artifacts.
- Validation gates are automated.
- Passing candidates update V30 runtime pointers.
- Failing candidates are rejected with machine-readable reasons.
- 518K validation can run in sample, shard, and full modes.
- Default local tests do not run 518K validation.

### Phase 5: Intelligent Question Recommendation

Goal: replace template-driven question generation with context-bound intelligence.

Scope:

- Seed questions.
- Question intents.
- Question graph.
- Question anchors.
- User/session state.
- Hidden factor hypotheses.
- Special-year and boundary confirmations.
- Role-aware visibility.
- Training-informed ranking.
- Question recommendation evaluator.

Inputs:

- Natal chart.
- Luck cycle.
- Annual flow.
- Feature evidence.
- Structure state.
- Mainline state.
- Known answers.
- Missing requirements.
- Role and client.
- Training policy.

Outputs:

- Recommended question intent.
- Bound question anchor.
- Why this question now.
- What evidence supports it.
- What information it can unlock.
- Which hidden factor, if any, it is testing.
- Role-specific presentation.

Acceptance:

- Guest/user views show only bound anchors.
- No raw template title is used as display source.
- Recommendation is explainable from current chart context.
- Synthetic question cases measure relevance and drift.

### Phase 6: LLM Role and Context System

Goal: give LLM more useful scope while preserving V30 facts and evidence boundaries.

Scope:

- Answer context.
- Role context.
- User context.
- Dialogue context.
- Knowledge boundaries.
- Prompt policies.
- Output contracts.
- Drift detection.
- Role-specific answer style.

LLM may:

- Explain.
- Ask follow-up questions.
- Compare alternatives.
- Adapt tone by role.
- Help propose policy candidates.
- Help generate synthetic cases.

LLM may not:

- Mutate chart facts.
- Override structure evidence.
- Change runtime pointers directly.
- Read raw traces for ordinary user answers.
- Invent unbound questions as if they are evidence-backed.

Acceptance:

- LLM consumes compact `AnswerContext`, not all runtime internals.
- Role-specific output is testable.
- LLM output has boundary checks.
- Answer safety tests run separately from default unit tests.

### Phase 7: Release and Continuous Improvement

Goal: make V30 a durable high-iteration system.

Scope:

- Release gate.
- Runtime health.
- Training health.
- Validation dashboards.
- Artifact lineage.
- Pointer rollback.
- Corpus distribution monitoring.

Acceptance:

- Release gate composes tiered tests without making every local test heavy.
- Training and validation status are observable.
- Runtime can identify active policy versions.
- Failed training cannot silently corrupt runtime truth.

## Task Plan

The task plan is controlled by `docs/V30_MASTER_MAINLINE_PLAN.md`. This roadmap keeps phase-level direction; the master plan owns track ordering, slice ordering, and task ledger.

### Immediate Tasks

1. Advance `M3 Evidence / Rule / Knowledge / Structure Spine Hardening`: every M4/M5 judgment must trace through evidence, rule, KRP, and structure paths without becoming a fixed verdict.
2. Broaden M4/M5 replay only after evidence-spine coverage is stable; keep weights bounded to candidate policy and never mutate chart facts.
3. Continue `M7 Core Calculation Validation / Real-case Calibration`: widen canonical fixtures before changing production thresholds.
4. Keep full gates at major nodes only: subtask work uses targeted unit tests and affected synthetic tiers; full pytest, synthetic all, and 518K sample are reserved for module milestones.

### Next Implementation Tasks

1. Add M3 evidence-path assertions for ranked decisions, model-signal influence, and practical reading domains.
2. Add rule/KRP weakening-evidence checks for useful-god and structure outputs.
3. Add synthetic observations and training signals for evidence coverage and counter-evidence across M4, M5, and M6.
4. Defer full pytest, synthetic all, and 518K sample until the next major gate.

## Open Decisions

- Which M3 evidence gaps block module promotion versus remain bounded training candidates.
- Whether `model_signal_summary` tuning eventually needs a dedicated `model_signal_policy`.
- Storage shape for durable interaction state beyond the current no-login read-history projection.
- Which LLM smoke checks can be mandatory when no provider is configured locally.
- How much real-case calibration should gate release before full conclusion quality is mature.
