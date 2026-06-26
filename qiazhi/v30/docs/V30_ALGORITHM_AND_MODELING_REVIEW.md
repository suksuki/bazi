# V30 Algorithm and Modeling Review

Updated: 2026-05-24

## Purpose

V20 introduced many advanced frameworks, algorithms, and modeling ideas over time. Some were strong; some were patched in under pressure.

V30 must review, integrate, and simplify them into one coherent architecture.

## Design Goal

V30 should not have many competing truth paths.

The current target is:

```text
BirthInput
-> ChartContext
-> TenGodEnergyModel
-> evidence
-> structure/strength/useful-god candidates
-> mainlines
-> structured interaction
-> answers
-> feedback/session state
-> training
-> validation
-> policy pointers
```

Each algorithm should have one clear place in this flow.

## Current Modeling Completion Review

| Algorithm family | Completion | Current state | Next modeling task |
|---|---:|---|---|
| Deterministic chart modeling | 85% | BirthInput, calendar conversion trace, four pillars, luck-cycle, flow-year/month, six-pillar context, and unknown-hour/true-solar boundaries are active. | Real-case calibration and solar-term edge validation. |
| Feature/rule evidence | 82% | Typed evidence and rule units support structure, mainline, reading, questions, model-signal consumers, and training signals. | Normalize calibration evidence before widening policy surfaces. |
| Weighted dynamic graph | 88% | Competition, suppression, conflict, path-resolution, domain paths, mechanism scores, and model-signal path adjustment are active. | Calibrate ten-god/time-layer stability weights with real-case replay. |
| Ten-god energy modeling | 88% | Phase sealed: energy, stability, volatility, interaction matrix, evidence ids, diagnostics, bounded `model_signal_summary`, interface contract, calibration profile, five-family calibration, real-case replay, band distributions, and auto-training model-signal weights are active. | Keep production threshold changes deferred until broader non-synthetic replay exists. |
| Ranked decision modeling | 88% | Phase sealed: strength, structure-pattern, and useful-god outputs are bounded candidate reviews with model-signal summaries, candidate scores, scoring basis, evidence boundaries, follow/disputed/regulation candidates, fixtures, replay weights, useful-god evidence calibration, M1/M2 root/vault basis, M4 interface/calibration basis, and no raw model-score leakage. | Keep production threshold changes deferred until broader non-synthetic replay exists. |
| Practical reading modeling | 85% | Phase sealed: career, wealth, relationship, health, and timing outputs consume chart facts, structure evidence, M4 signal bands, and M5 ranked decisions through calculation basis, evidence ids, explanation units, blocked claims, and quality contracts. | Calibrate wording and domain emphasis through M7 real-case replay. |
| Question graph and interaction | 82% | High-value question quality, structured options, selected options, `known_user_signals`, `interaction_state`, visible/internal next-question split, follow-up reason, and dedicated interaction-loop validation are active. | Calibrate question strategy and visible/internal next-question boundaries. |
| Answer and LLM expression | 72% | R4 complete: rule-bound answer comes first; LLM can rewrite expression inside drift checks and fallback safely; live smoke records unconfigured/configured/accepted/fallback/drift states, failure telemetry, artifacts, and no-mutation proof. | Add provider-specific failure taxonomy only from observed live failures. |
| Training and validation | 99% | Default tests, synthetic smoke/all, dedicated interaction-loop and real-case calibration tiers, release gate, release artifact review, post-seal status review, production replay intake and replay store/search, release-candidate review, standard candidate-gate review, release-boundary finalization, 518K sample/selected-shard artifacts, P7/P8/P9.1/R5 signals, auto-training candidates, and policy pointer lineage are active. | R13 should decide external full pytest and manual pointer-promotion boundaries. |

## Reviewed Algorithm Families

### Deterministic Chart Modeling

V20 examples:

```text
core/chart.py
core/time_context.py
core/ten_gods.py
core/relations.py
core/strength.py
core/useful_god.py
```

V30 use:

- Deterministic fact extraction.
- Immutable chart context.
- Original chart, luck cycle, and annual flow as first-class time layers.
- Missing time represented explicitly.

Modeling target:

```text
ChartContext
TimeLayer
PillarSet
TenGodRelation
ElementRelation
StrengthSignal
UsefulGodSignal
```

### Feature Evidence Model

V20 examples:

```text
features/compiler.py
features/state_model.py
orchestrator/evidence.py
```

V30 use:

- Convert raw chart facts into typed evidence.
- Support and weaken claims.
- Track confidence and boundary.
- Feed rules, structure dynamics, mainline arbitration, questions, and answers.

Modeling target:

```text
FeatureEvidence
EvidenceClaim
EvidenceBoundary
EvidenceConfidence
```

### Defeasible Reasoning

V20 examples:

```text
decision/defeasible_model.py
decision/fusion.py
rules/engine.py
```

V30 use:

- Resolve conflicting evidence.
- Express exceptions and overrides.
- Avoid brittle yes/no rule outcomes.

Modeling target:

```text
RuleEvidence
ConflictSet
Defeater
ResolutionTrace
```

V30 rule:

Defeasible reasoning can rank and qualify conclusions. It cannot invent chart facts.

### Weighted Dynamic Graph

V20 examples:

```text
dynamics/graph_engine.py
dynamics/engine.py
graph/scoring.py
knowledge/structure_mechanisms.py
```

V30 use:

- Model structure dynamics as graph paths.
- Score competing mechanism chains.
- Bind semantic labels to reviewed mechanism definitions.
- Feed mainline arbitration.

Modeling target:

```text
StructureGraph
StructureNode
StructureEdge
MechanismDefinition
PathScore
StructureState
```

V30 improvement:

Separate:

- Graph extraction.
- Mechanism lookup.
- Policy weights.
- State selection.
- Presentation rendering.

### Evidence-Weighted Mainline Arbitration

V20 examples:

```text
orchestrator/mainline.py
orchestrator/brain_state.py
orchestrator/question_focus.py
```

V30 use:

- Choose the current reading mainline.
- Explain why selected.
- Preserve rejected candidates.
- Connect question recommendation to current context.

Modeling target:

```text
MainlineCandidate
MainlineState
ArbitrationTrace
RejectedMainline
QualityGate
```

V30 improvement:

Mainline arbitration is not a UI payload. UI receives a projected presentation model.

### Knowledge Graph and Rule Library

V20 examples:

```text
knowledge/schema.py
knowledge/rule_library.py
knowledge/retrieval.py
knowledge/structure_mechanisms.py
graph/rule_graph.py
```

V30 use:

- Build versioned knowledge packs.
- Connect knowledge units to rules and structure mechanisms.
- Retrieve bounded context for answers and LLM.

Modeling target:

```text
KnowledgeUnit
KnowledgePack
RuleSpec
MechanismDefinition
RetrievalResult
KnowledgeBoundary
```

V30 improvement:

Knowledge content can support reasoning and language, but runtime facts still come from `ChartContext`.

### Bazi Portrait Modeling

V20 examples:

```text
interaction/portrait_ontology.py
interaction/portrait_graph.py
interaction/portrait_projection.py
interaction/portrait_tags.py
```

V30 use:

- Create user-facing and practitioner-facing portrait dimensions.
- Bind portraits to evidence and structure state.
- Avoid personality-style generic outputs detached from chart context.

Modeling target:

```text
PortraitDimension
PortraitTag
PortraitGraph
PortraitEvidence
RolePortraitProjection
```

V30 improvement:

Portraits are derived projections, not another fact source.

### Integrated Knowledge-Rule-Feature-Portrait-Structure Pipeline

V20 examples:

```text
knowledge/
rules/
features/
dynamics/
interaction/portrait_*.py
validation/
corpus/
learning/
```

V30 use:

- Generate feature, rule, portrait, and structure candidates from the same chart context.
- Validate them with the same synthetic Bazi case suite.
- Tune parameters by policy family.
- Promote artifacts through runtime pointers.

Modeling target:

```text
SyntheticBaziCase
FeaturePolicy
RulePolicy
StructurePolicy
PortraitPolicy
IntegratedValidationRun
ParameterCandidate
RuntimePointerUpdate
```

V30 improvement:

Subsystems may compute in parallel, but they must be validated together before promotion.

### Question Graph and Recommendation

V20 examples:

```text
interaction/question_atoms.py
interaction/question_dag.py
interaction/question_anchor.py
interaction/question_ranker.py
interaction/question_source_record.py
learning/question_dag_training.py
learning/question_runtime_pointer.py
```

V30 use:

- Start from seed questions.
- Use graph state and training policy to recommend next questions.
- Bind every displayed question to current chart context.
- Learn from user answers and synthetic validation.

Modeling target:

```text
QuestionSeed
QuestionIntent
QuestionGraph
QuestionAnchor
QuestionRecommendation
QuestionPolicy
QuestionTrainingTrace
```

V30 improvement:

Recommendation is not template rendering. It is a scored decision from context, evidence, missing requirements, role, and policy.

### Runtime Pointer Model

V20 examples:

```text
learning/*_runtime_pointer.py
learning/*_policy_promotion.py
learning/artifact_registry.py
```

V30 use:

- Decouple runtime behavior from training jobs.
- Let validated artifacts auto-apply.
- Keep version lineage and rollback.

Modeling target:

```text
PolicyFamily
PolicyCandidate
PolicyArtifact
RuntimePointer
PointerUpdate
RollbackRecord
```

Initial V30 policy families:

```text
structure_policy
mainline_policy
question_policy
answer_policy
presentation_policy
knowledge_policy
rule_policy
portrait_policy
```

V30 improvement:

Training validation and runtime pointer update use one shared contract across policy families.

### Synthetic Data Validation

V20 examples:

```text
validation/synthetic_schema.py
validation/synthetic_replay.py
validation/structure_dynamics_synthetic.py
validation/next_question_synthetic.py
```

V30 use:

- Test expected behavior without massive corpus runs.
- Generate and replay cases.
- Validate positive expectations and forbidden drift.
- Drive training feedback.

Modeling target:

```text
ValidationCase
SyntheticCase
SyntheticSuite
ValidationRun
ValidationFailureCluster
```

V30 improvement:

Synthetic validation is not just a test suite. It is part of training promotion.

### 518K Corpus Validation

V20 examples:

```text
corpus/enumerator.py
corpus/full_precompute.py
corpus/coverage.py
corpus/storage.py
```

V30 use:

- Validate broad distribution.
- Measure coverage and drift.
- Stress-test structure, question, and answer policies.
- Support sample, shard, and full validation.

Modeling target:

```text
CorpusShard
CorpusCaseSummary
CorpusValidationRun
CoverageMetric
DriftMetric
FailureCluster
```

V30 improvement:

518K validation should be callable by training promotion and release gate, but never be part of default tests.

### LLM Context and Role Modeling

V20 examples:

```text
llm/context.py
llm/contracts.py
llm/prompts.py
llm/enforcement.py
role_view/narrative_prompt_framework.py
```

V30 use:

- Give LLM more useful role-aware scope.
- Keep chart facts and selected evidence immutable.
- Support answer, recommendation explanation, synthetic generation, and training assistance.

Modeling target:

```text
AnswerContext
RoleContext
UserContext
DialogueContext
LLMTask
PromptPolicy
OutputContract
DriftCheck
```

V30 improvement:

LLM should receive structured context and explicit task contracts, not broad raw runtime traces.

## Integration Map

```text
ChartContext
  -> TenGodEnergyModel
  -> FeatureEvidence
  -> RuleEvidence
  -> StructureGraph
  -> StructureState
  -> Strength/Structure/UsefulGod RankedDecision[]
  -> MainlineCandidate[]
  -> MainlineState
  -> QuestionRecommendation[]
  -> BaziQuestionAnchor[]
  -> InteractionState
  -> AnswerContext
  -> LLMTask
  -> AnswerResult
  -> RoleProjection
  -> ClientPresentationModel
```

Training integration:

```text
RuntimeTrace
  -> FeedbackEvent
  -> SyntheticValidation
  -> 518KValidation
  -> TrainingRun
  -> PolicyCandidate
  -> ValidationRun
  -> PolicyArtifact
  -> RuntimePointer
```

## Design Risks From V20

- Multiple parallel truth sources.
- Runtime payload becoming too large.
- UI depending on internal field names.
- Training artifacts mutating runtime behavior without shared contract.
- Manual review becoming the main promotion path.
- Question templates hiding unsupported recommendations.
- LLM prompts receiving too much unbounded context.
- Heavy validation mixed into ordinary tests.

## V30 Design Corrections

- One core fact model.
- One ten-god model-signal summary.
- One evidence model.
- One structure state contract.
- One ranked candidate scoring contract for strength, structure, and useful-god.
- One mainline arbitration contract.
- One question anchor display path.
- One interaction state contract separating customer-visible next question from internal diagnostics.
- One policy pointer mechanism.
- Explicit role projection.
- Explicit validation tiers.
- Automatic validated promotion.

## Next Review Tasks

1. `M3 Evidence / Rule / Knowledge / Structure Spine Hardening`: require ranked decisions, model-signal influence, and practical reading domains to expose evidence paths and counter-evidence boundaries.
2. `M7 Real-case Calibration Expansion`: broaden canonical fixtures after M3 evidence coverage is stable, without hard-coding final Bazi conclusions.
3. `Major Gate Refresh`: run full pytest, synthetic all, and 518K sample only at the next module milestone or policy-affecting promotion.
