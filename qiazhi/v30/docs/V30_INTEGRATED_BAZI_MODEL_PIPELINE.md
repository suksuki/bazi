# V30 Integrated Bazi Model Pipeline

Updated: 2026-05-24

## Purpose

V30 must integrate the Bazi knowledge base, rule base, portrait model, feature model, and structure dynamics into one coherent generation, validation, tuning, and runtime application pipeline.

In V20, these systems became useful but were added over time. V30 should not keep them as loosely connected branches.

V30 target:

```text
ChartContext + KnowledgePacks + SyntheticBaziCase
-> TenGodEnergyModel
-> FeatureEvidence
-> RuleEvidence
-> StructureDynamics
-> PortraitModel
-> Strength/Structure/UsefulGod RankedDecision
-> MainlineState
-> QuestionIntelligence
-> InteractionState
-> AnswerContext
-> Validation
-> Training
-> RuntimePointer
```

## Current Pipeline Completion Review

| Pipeline layer | Completion | Current state | Next action |
|---|---:|---|---|
| Fact layer | 85% | BirthInput supports explicit pillars, solar, lunar, leap-month, known-place true-solar, unknown-hour blocking, invalid input traces, luck-cycle, flow-year/month, and six-pillar context. | Add canonical real-case calibration and stronger boundary fixtures. |
| Ten-god model-signal layer | 88% | Phase sealed: ten-god energy, stability, volatility, dominant/high-volatility/low-stability lists, interaction matrix, diagnostics, shared `model_signal_summary`, interface contract, calibration profile, calibration tier, real-case replay, and auto-training model-signal weights are active pipeline layers. | Keep production threshold changes deferred until broader non-synthetic replay exists. |
| Feature/rule/structure layer | 88% | Feature evidence, rule evidence, K/R/P signals, structure graph paths, mechanism scores, model-signal path adjustment, and mainline arbitration are connected. | Calibrate time-layer and ten-god model-signal weights through validation replay. |
| Ranked decision layer | 85% | Strength, structure-pattern, and useful-god outputs are bounded candidate reviews with shared model-signal summaries, candidate scores, scoring basis, follow/disputed/regulation candidates, fixtures, score floors, replay weights, and useful-god evidence calibration. | Broaden replay before production threshold changes. |
| Customer reading layer | 74% | Customer surface, domain cards, structured options, answer panel, role-gated diagnostics, and actor/session context are active. | Stabilize field versions and error states. |
| Interaction layer | 82% | Question graph, `InteractionState`, visible/internal next-question split, follow-up reason, selected options, `known_user_signals`, and dedicated interaction-loop validation are active pipeline layers. | Calibrate question strategy and visible/internal next-question boundaries. |
| Validation/training layer | 96% | Synthetic smoke/all, dedicated interaction-loop and real-case calibration tiers, release gate, 518K sample/shard artifact search, P7/P8/P9.1 signals, and policy pointer lineage are active. | Add release/518K summaries for interaction-loop and calibration coverage. |

## V20 Diagnosis

V20 had valuable pieces:

- Knowledge units.
- Rule extraction.
- Feature compiler.
- Portrait ontology and graph.
- Structure dynamics graph.
- Synthetic cases.
- 518K corpus coverage.
- Question DAG and role interaction training.
- Runtime pointers.

The issue was not that these pieces were wrong. The issue was that they were not designed from the beginning as one system.

Observed problems:

- Knowledge, rules, portraits, features, and structure dynamics could evolve at different speeds.
- Some validation was domain-specific but not promotion-wide.
- Synthetic cases existed, but were not strong enough as a shared parameter tuning loop.
- 518K statistics were useful, but not always tied directly to policy promotion.
- Runtime pointers existed by family, but the promotion contract was not unified enough.
- Question recommendation was improved later, but still carried template-era pressure.

## V30 Design Principle

The V30 Bazi model should have one shared generation contract and one shared validation contract.

Different subsystems may generate in parallel, but they cannot apply to runtime independently without cross-validation.

## Pipeline Layers

### Layer 1: Fact Layer

Input:

- Birth data.
- Natal pillars.
- Luck cycle.
- Annual flow.
- Optional monthly/current time layer.

Output:

```text
ChartContext
```

Rules:

- Immutable during one reading.
- Deterministic.
- No training artifact may mutate chart facts.
- Missing time context is explicit.

### Layer 2: Feature Layer

Input:

- `ChartContext`
- Active feature policy.

Output:

```text
FeatureEvidence[]
```

Examples:

- Day master strength signals.
- Five element balance.
- Ten god visibility.
- Root/support signals.
- Branch interactions.
- Time activation signals.

Tunable parameters:

- Strength thresholds.
- Visibility weights.
- Root continuity weights.
- Time trigger weights.
- Hidden stem weights.

### Layer 2.5: Ten-god Model-Signal Layer

Input:

- `ChartContext`
- `SixPillarContext`
- `FeatureEvidence`
- Time-layer activation context.

Output:

```text
TenGodEnergyModel
model_signal_summary
```

Rules:

- Ten-god energy is a deterministic model signal, not a chart fact.
- Stability and volatility can strengthen or weaken candidate scoring.
- Raw scores stay diagnostic; customer surfaces receive only bounded summaries.
- Training may tune weights and thresholds, not pillars or ten-god relations.

Consumers:

- Strength candidate scoring.
- Structure pattern candidate scoring.
- Useful-god candidate scoring.
- Answer context.
- Practitioner/admin diagnostics.

### Layer 3: Rule Layer

Input:

- `ChartContext`
- `FeatureEvidence`
- Knowledge-derived rule catalog.
- Active rule policy.

Output:

```text
RuleEvidence[]
ConflictSet[]
ResolutionTrace[]
```

Rules:

- Rules produce evidence and conflicts, not final public claims.
- Rules must have positive cases, counter cases, and boundary cases.
- Rule parameters are tuned by synthetic validation and 518K coverage.

### Layer 4: Structure Dynamics Layer

Input:

- `ChartContext`
- `FeatureEvidence`
- `RuleEvidence`
- Knowledge mechanism definitions.
- Active structure policy.

Output:

```text
StructureGraph
PathScore[]
StructureState
```

Rules:

- Graph extracts dynamic paths before semantic naming.
- Knowledge mechanisms name and bound paths after graph extraction.
- Training tunes weights and thresholds, not facts.

Tunable parameters:

- Node weights.
- Edge weights.
- Time activation weights.
- Blockage penalty.
- Terminal convergence weight.
- Semantic match threshold.
- Stability floor.
- Volatility threshold.

### Layer 5: Portrait Layer

Input:

- `ChartContext`
- `FeatureEvidence`
- `RuleEvidence`
- `StructureState`
- Active portrait policy.

Output:

```text
PortraitDimension[]
PortraitTag[]
PortraitEvidence[]
```

Rules:

- Portraits are derived projections.
- Portraits cannot become a second source of truth.
- Portraits must remain bound to current chart evidence.

Examples:

- Day master load bearing.
- Wealth channel pressure.
- Resource support.
- Career pressure conversion.
- Relationship interaction.
- Health boundary.
- Luck/annual activation theme.

### Layer 6: Mainline Layer

Input:

- Feature evidence.
- Rule evidence.
- Structure state.
- Portrait evidence.
- Active mainline policy.

Output:

```text
MainlineState
RejectedMainline[]
ArbitrationTrace
```

Rules:

- Mainline ranks current evidence.
- Mainline does not invent facts.
- Portraits may support presentation but cannot overrule stronger structure evidence.

### Layer 6.5: Unified Candidate Scoring Layer

Input:

- `ChartContext`
- `FeatureEvidence`
- `RuleEvidence`
- `TenGodEnergyModel`
- `StructureState`
- Time-layer context.

Output:

```text
RankedDecision[]
model_signal_summary
candidate_boundaries
```

Rules:

- Strength, structure pattern, and useful-god use one candidate scoring contract.
- Every candidate must expose supporting evidence, weakening evidence, unresolved requirements, and boundary text.
- The layer can rank candidates; it cannot produce an absolute useful-god verdict for the customer surface.
- User-visible output receives explanation and next-step framing, not raw numeric scores.

### Layer 7: Question Intelligence Layer

Input:

- `MainlineState`
- `StructureState`
- `PortraitEvidence`
- User/session state.
- Role/client.
- Active question policy.

Output:

```text
QuestionRecommendation[]
BaziQuestionAnchor[]
```

Rules:

- Recommendations come from evidence and information gain.
- Seed questions are training material, not display templates.
- User-visible questions must be bound anchors.
- `QuestionDialogueGraph` owns internal strategy.
- Presentation owns role-visible next-question projection.

### Layer 7.5: Interaction State Layer

Input:

- Selected question.
- Selected option.
- Free-text supplemental answer.
- Current presentation role/client.
- Previous session state.

Output:

```text
interaction_stage
selected_domain
answered_question_ids
known_user_signals
visible_next_question_id
internal_next_question_id
followup_reason
```

Rules:

- Customer surfaces always use `next_question_id` / `visible_next_question_id`.
- `internal_next_question_id` is diagnostics-only.
- Known user signals affect question and answer strategy only; they cannot mutate chart facts.

### Layer 8: Answer and LLM Layer

Input:

- Selected question anchor.
- Chart summary.
- Structure summary.
- Mainline summary.
- Evidence summary.
- Role context.
- Active answer policy.

Output:

```text
AnswerContext
AnswerResult
```

Rules:

- LLM receives structured context.
- LLM may enrich expression and role tone.
- LLM may not mutate facts, structure, mainline, or pointer state.

## Parallel Generation Model

Some V30 subsystems can generate in parallel after `ChartContext` is ready:

```text
ChartContext
├── Feature generation
├── Rule matching
├── Knowledge retrieval
├── Time activation extraction
└── Corpus similarity lookup
```

But later layers have dependencies:

```text
FeatureEvidence + RuleEvidence + KnowledgeMechanisms
-> StructureState
-> MainlineState
-> PortraitProjection + QuestionRecommendation + AnswerContext
-> RoleAwarePortraitProjectionView + PresentationDiagnostics
```

V30 should allow parallel compute but not parallel truth.

## Unified Artifact Model

Every generated model artifact should use the same lifecycle:

```text
draft
-> candidate
-> synthetic_validated
-> corpus_validated
-> artifact
-> active_pointer
-> observed
-> retired
```

Artifacts:

- Knowledge pack.
- Rule catalog.
- Feature policy.
- Structure policy.
- Portrait policy.
- Mainline policy.
- Question policy.
- Answer policy.

## Synthetic Bazi Validation Strategy

The simple version is correct: generate obvious cases and test whether the system recognizes them.

V30 should expand that into five synthetic case types.

### Type 1: Positive Prototype Cases

Purpose: verify obvious structures.

Examples:

- Clear output controls authority.
- Clear wealth channel.
- Clear resource supports self.
- Clear peer support.
- Clear missing support.

Expected behavior:

- Required features fire.
- Required rules fire.
- Structure path is selected.
- Portrait includes target theme.
- Question recommendation focuses on target theme.

### Type 2: Negative Counter Cases

Purpose: prevent over-triggering.

Examples:

- Wealth visible but day master cannot bear it.
- Authority visible but no output control path.
- Resource present but blocked.
- Relationship signal present but time layer does not activate it.

Expected behavior:

- Overbroad rules do not fire.
- Portrait does not overstate.
- Questions include boundary or missing requirement.

### Type 3: Metamorphic Pairs

Purpose: test whether the system reacts to controlled changes.

Example:

```text
base: authority pressure without resource
mutation: add resource support
expected: structure shifts from pressure/conflict to pressure conversion
```

This is stronger than checking one label because it tests causal sensitivity.

### Type 4: Boundary Gradient Cases

Purpose: tune thresholds.

Generate a sequence:

```text
very weak -> weak -> neutral -> strong -> overstrong
```

Expected behavior:

- Feature confidence changes smoothly.
- Rule activation does not jump erratically.
- Structure state changes at explainable thresholds.

### Type 5: Composite Conflict Cases

Purpose: test real-world complexity.

Examples:

- Output, wealth, and authority all visible.
- Resource supports but branch clash destabilizes.
- Time layer activates both opportunity and conflict.
- Strong portrait theme conflicts with structure mainline.

Expected behavior:

- Defeasible reasoning records conflicts.
- Mainline explains why selected.
- Questions focus on resolving high-value uncertainty.

## Synthetic Case DSL

V30 should use a DSL that supports constraints and expectations.

Example:

```yaml
case_id: v30_wealth_visible_weak_dm_001
domain: wealth_channel
case_type: negative_counter

constraints:
  day_master_strength: weak
  wealth_visible: true
  resource_support: low
  peer_support: low
  time_activation: optional

expect:
  feature_evidence:
    include:
      - wealth_visible
      - day_master_support_low
  rules:
    forbid:
      - direct_wealth_gain_assertion
  structure:
    require_state:
      - partial
      - weak
  portraits:
    include:
      - wealth_pressure
    forbid:
      - wealth_success_assertion
  questions:
    include_intent:
      - assess_bearing_capacity
    forbid_intent:
      - assume_wealth_gain

negative_expectations:
  - no_unqualified_fortune_claim
  - no_unsupported_question
```

## Parameter Tuning Loop

Synthetic validation should tune parameters in small families.

```text
parameter_family
-> candidate parameter set
-> synthetic validation
-> metamorphic validation
-> 518K sample validation
-> artifact
-> runtime pointer
```

Examples:

| Parameter family | Tuned by |
|---|---|
| Feature thresholds | Boundary gradient cases. |
| Rule activation weights | Positive/counter cases. |
| Structure graph weights | Prototype, metamorphic, composite cases. |
| Portrait mapping weights | Prototype and counter cases. |
| Question ranking weights | Information gain and role cases. |
| Answer boundary policy | Negative expectation cases. |

## Seamless Generate-Validate-Tune-Apply Loop

V30 should support one command or job per family:

```text
generate synthetic cases
-> run current runtime
-> identify failures
-> propose parameter candidates
-> validate candidates
-> publish artifact
-> update runtime pointer
```

Conceptual command:

```bash
python scripts/run_model_training_loop.py --family structure_policy --tier smoke --auto-apply
```

The loop must output:

```text
coverage_report
failure_report
candidate_report
validation_report
pointer_update_report
```

## 518K Role in This Pipeline

518K validation should not define truth for a single chart.

It should provide:

- Distribution coverage.
- Rare pattern detection.
- Over-trigger detection.
- Shard-level drift.
- Similar case references.
- Parameter stability checks.

Synthetic validation asks:

```text
does the system behave correctly on known targeted structures?
```

518K validation asks:

```text
does the system remain stable across broad distribution?
```

Both are required for high-impact promotion.

## Acceptance

- Knowledge, rules, features, portraits, structure dynamics, questions, and answers share one validation lifecycle.
- Ten-god energy, stability, and volatility flow through a shared model-signal summary before they influence ranked decisions.
- Strength, structure, and useful-god candidates use one scoring contract.
- Interaction state separates visible customer next question from internal strategy diagnostics.
- Synthetic cases include positive, negative, metamorphic, gradient, and composite forms.
- Parameter tuning is family-scoped and artifact-based.
- Passing candidates auto-apply through V30 runtime pointers.
- 518K validation supports sample, shard, and full modes.
- Runtime never imports V20 or reads V20 artifacts.

## Next Design Tasks

1. Add M3 evidence-path and counter-evidence coverage across M4 ten-god signals, M5 ranked decisions, and M6 practical reading domains.
2. Broaden real-case calibration after M3 evidence-spine coverage is stable, without changing deterministic chart facts.
3. Refresh full pytest, synthetic all, and 518K sample only at the next major module gate.
