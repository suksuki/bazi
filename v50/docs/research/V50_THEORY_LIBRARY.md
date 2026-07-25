# V50 Theory Library

Status: active theory asset

This is not a knowledge library.

This is not a rule library.

This is the library of theory objects that can later enter Data Model and Runtime.

## Principle

Open Questions produce Theories.

Runtime implements Theories.

Runtime must not implement Open Questions directly.

Theory must be evidence-driven.

Canonical evidence file:

```text
research/V50_EVIDENCE_LIBRARY.md
```

## Theory Object Schema

Each theory object must contain:

```yaml
theory_id:
name:
research_program:
open_questions:
status: candidate | frozen | rejected | archived
priority: P0 | P1 | P2 | later
description:
scope:
what_changes_if_true:
evidence:
counter_evidence:
competing_theories:
formalization:
data_model_implication:
runtime_implication:
synthetic_validation_plan:
real_world_validation_plan:
confidence:
related_theories:
rejected_reason:
```

Evidence fields should point to Evidence IDs when available.

Do not keep increasing the number of theories without adding evidence.

## Status Rules

### Candidate

The theory is being explored.

It cannot enter Runtime.

### Frozen

The theory passed Theory Freeze and Formalization.

It can enter Data Model and Runtime.

### Rejected

The theory failed counter examples or formalization.

It should be preserved so V50 does not circle back.

### Archived

The theory is not wrong, but not active.

## Priority Rules

```text
P0: blocks current V50 intelligence mainline
P1: important but not blocking current runtime
P2: useful later
later: outside current scope
```

## Active Theory Objects

Active theory rule:

```text
Each Research Program should have one primary active theory at a time.
Competing theories may exist, but they must be candidate / rejected / archived,
not equally active.
```

Current primary active theories:

```text
RP001 Timing: T001 Long-term Field Theory
RP002 Mechanism: T004 Mechanism AST Theory
RP003 Ziwei: T007 Ziwei Palace State Space Theory
RP004 Xiangfa: T009 Xiangfa Explanation Theory
RP005 Context: T008 Context Overlay Theory
RP007 Semantic Diversity: T010 Semantic Narrowness Theory
RP008 Decision Intelligence: T011 Life Decision Intelligence Theory
```

### T001 — Long-term Field Theory

```yaml
theory_id: T001
name: Long-term Field Theory
research_program: RP001 Timing
open_questions:
  - OQ001
status: candidate
priority: P0
description: 大运可能是长期环境场，而不是简单的第二月令。
scope:
  - timing
  - state_delta
  - mechanism_shift
what_changes_if_true:
  - Timing runtime should model luck as long-term field overlay.
  - Luck should modify node energy, edge strength, and mechanism ranking gradually.
  - Luck should not mutate natal structure.
evidence:
  - Timing discussions suggest luck changes the operating environment.
  - Some charts appear to shift dominant flow without changing natal structure.
counter_evidence:
  - insufficient
competing_theories:
  - T002 Second Month Command Theory
  - T003 Stage Dominant Variable Theory
formalization:
  - TimingModelCandidate
  - TemporalState
  - StateEvolution
data_model_implication:
  - luck_state overlay
  - state_delta confidence
runtime_implication:
  - simulator policy must support luck as overlay, not rewrite
synthetic_validation_plan:
  - create controlled charts where luck strengthens or weakens a non-month node
real_world_validation_plan:
  - compare long-period user event clusters against predicted state trend
confidence: 0.62
related_theories:
  supports:
    - T006 State Evolution Theory
  depends_on: []
rejected_reason: ""
```

### T002 — Second Month Command Theory

```yaml
theory_id: T002
name: Second Month Command Theory
research_program: RP001 Timing
open_questions:
  - OQ001
status: candidate
priority: P0
description: 大运可能像第二月令一样改变长期旺衰环境。
scope:
  - timing
what_changes_if_true:
  - Luck should be weighted similarly to month command in some calculations.
  - Node energy could be recalculated with luck branch as secondary seasonal anchor.
evidence:
  - traditional descriptions often compare luck to period environment
counter_evidence:
  - may over-mechanize luck and fail when observed events show activation rather than season replacement
competing_theories:
  - T001 Long-term Field Theory
  - T003 Stage Dominant Variable Theory
formalization:
  - TimingModelCandidate
data_model_implication:
  - secondary_month_command_weight
runtime_implication:
  - simulator must support this as candidate policy, not default doctrine
synthetic_validation_plan:
  - compare against Long-term Field on controlled charts
real_world_validation_plan:
  - verify cases where luck branch behaves like season replacement
confidence: 0.42
related_theories:
  conflicts:
    - T001
rejected_reason: ""
```

### T003 — Stage Dominant Variable Theory

```yaml
theory_id: T003
name: Stage Dominant Variable Theory
research_program: RP001 Timing
open_questions:
  - OQ001
status: candidate
priority: P0
description: 大运可能不是整体环境，而是阶段性主变量。
scope:
  - timing
  - decision_policy
what_changes_if_true:
  - Runtime should identify what domain or node the luck period makes dominant.
  - Luck can reprioritize mechanism candidates without changing all node scores.
evidence:
  - some periods appear to highlight a topic rather than globally reweight the chart
counter_evidence:
  - insufficient
competing_theories:
  - T001
  - T002
formalization:
  - TimingModelCandidate
  - TopicActivationProfile
data_model_implication:
  - stage_variable_ref
runtime_implication:
  - simulator needs topic / mechanism ranking perturbation
synthetic_validation_plan:
  - generate charts where one luck variable reroutes main mechanism
real_world_validation_plan:
  - compare period themes in longitudinal case logs
confidence: 0.55
related_theories:
  supports:
    - T006
rejected_reason: ""
```

### T004 — Mechanism AST Theory

```yaml
theory_id: T004
name: Mechanism AST Theory
research_program: RP002 Mechanism
open_questions:
  - OQ003
status: candidate
priority: P0
description: 机制不是标签，而是 Source / Path / Converter / Bridge / Anchor / Target / Counter Force / State Delta 的结构表示。
scope:
  - mechanism
  - graph
  - simulation
what_changes_if_true:
  - Runtime must not rank mechanism labels directly.
  - Discovery should operate on AST shape.
  - Mechanism labels become presentation-only.
evidence:
  - Mechanism Representation v1 can represent classic and temporary mechanisms with same grammar.
  - Batch report shows role coverage across taxonomy charts.
counter_evidence:
  - AST audit not yet complete
competing_theories:
  - T005 Mechanism Label Library Theory
formalization:
  - MechanismRepresentation
  - MechanismComponent
data_model_implication:
  - mechanism components with role and evidence_refs
runtime_implication:
  - Mechanism Discovery v3 must consume AST, not labels
synthetic_validation_plan:
  - Mechanism Representation Audit v1
real_world_validation_plan:
  - verify whether AST-derived mechanisms produce better probe and reading differentiation
confidence: 0.74
related_theories:
  supports:
    - T006
    - T009 Xiangfa Explanation Theory
rejected_reason: ""
```

### T005 — Mechanism Label Library Theory

```yaml
theory_id: T005
name: Mechanism Label Library Theory
research_program: RP002 Mechanism
open_questions:
  - OQ003
status: rejected
priority: later
description: 机制可以主要由命名库管理，例如不断增加 output_to_wealth / resource_support 等标签。
scope:
  - mechanism
what_changes_if_true:
  - Runtime would mainly map detected labels to judgments.
evidence:
  - Quick semantic expansion is possible.
counter_evidence:
  - It recreates Rule Library risk.
  - It does not prove mechanisms are discovered from graph state.
  - It encourages adding names before formal representation.
competing_theories:
  - T004 Mechanism AST Theory
formalization:
  - label map
data_model_implication:
  - mechanism_code registry
runtime_implication:
  - high risk of brittle rule mapping
synthetic_validation_plan:
  - not recommended
real_world_validation_plan:
  - not recommended
confidence: 0.2
related_theories:
  conflicts:
    - T004
rejected_reason: "Rejected as primary V50 mechanism strategy because it turns discovery back into a rule/name library."
```

### T006 — State Evolution Theory

```yaml
theory_id: T006
name: State Evolution Theory
research_program: RP001 Timing
open_questions:
  - OQ001
  - OQ002
  - OQ003
status: candidate
priority: P0
description: Case cognition needs temporal observations beyond a snapshot: current state, delta, trend, velocity, and activated_by.
scope:
  - research_state
  - timing
  - mechanism
what_changes_if_true:
  - Research state observations must include StateDelta and StateTrend.
  - Mechanism should include state_delta component.
  - Context Compiler should expose direction and activation to the LLM Mingli Agent.
evidence:
  - State research experiments distinguish CurrentState from StateDelta.
  - Mechanism Representation batch includes state_delta components.
counter_evidence:
  - synthetic state_delta may be too templated until audited
competing_theories:
  - snapshot-only state theory
formalization:
  - StateEvolution
  - TemporalState
  - MechanismComponent(state_delta)
data_model_implication:
  - delta_by_dimension
  - trend
  - velocity
runtime_implication:
  - Temporal observations may be supplied as non-authoritative tools after explicit promotion review.
synthetic_validation_plan:
  - Timing Synthetic Validation v1
  - Mechanism Representation Audit v1
real_world_validation_plan:
  - compare predicted trend with longitudinal user feedback
confidence: 0.69
related_theories:
  supported_by:
    - T001
    - T003
    - T004
rejected_reason: ""
```

### T007 — Ziwei Palace State Space Theory

```yaml
theory_id: T007
name: Ziwei Palace State Space Theory
research_program: RP003 Ziwei
open_questions:
  - OQ004
status: candidate
priority: P1
description: 紫微计算宫位状态空间与激活，而不是复制八字做功流。
scope:
  - ziwei
  - unified_state
what_changes_if_true:
  - Ziwei Engine should output PalaceStateSpace.
  - Stars become behavior modifier functions.
  - Four transformations become state transition operators.
evidence:
  - Ziwei research docs define palace/star/four transformations as computational objects.
counter_evidence:
  - detailed star and transformation functions are not yet audited
competing_theories:
  - Ziwei as second report theory
formalization:
  - PalaceStateSpace
  - BehaviorModifierFunction
  - TransformationOperator
data_model_implication:
  - palace dimensions
  - transformation refs
runtime_implication:
  - Ziwei contributes state evidence to UnifiedState, not final report text
synthetic_validation_plan:
  - Ziwei State Synthetic Lab v1
real_world_validation_plan:
  - compare palace activation against timed life events
confidence: 0.66
related_theories:
  supports:
    - T006
rejected_reason: ""
```

### T008 — Context Overlay Theory

```yaml
theory_id: T008
name: Context Overlay Theory
research_program: RP005 Context
open_questions:
  - OQ006
status: candidate
priority: P1
description: 地理、职业、现实事件作为 Context Overlay 影响现实落点，但不改变原局事实。
scope:
  - context
  - domain_mapping
  - decision_policy
what_changes_if_true:
  - Runtime can use geography / profession / events to adjust domain landing.
  - Birth facts and natal graph remain immutable.
evidence:
  - Context architecture defines geography/profession/reality event overlays.
counter_evidence:
  - validation not yet built
competing_theories:
  - context-as-engine-fact theory
formalization:
  - RealityState
  - ContextOverlayCandidate
data_model_implication:
  - context refs and evidence refs
runtime_implication:
  - Brain can use context but engines cannot mutate chart
synthetic_validation_plan:
  - context-aware fixture matrix
real_world_validation_plan:
  - compare advice relevance with / without context
confidence: 0.63
related_theories:
  supports:
    - T009
rejected_reason: ""
```

### T009 — Xiangfa Explanation Theory

```yaml
theory_id: T009
name: Xiangfa Explanation Theory
research_program: RP004 Xiangfa
open_questions:
  - OQ005
status: candidate
priority: P1
description: 象法是对已确认结构、机制、状态和状态演化的解释层，不产生裁决。
scope:
  - xiangfa
  - expression
  - portrait
what_changes_if_true:
  - Xiangfa renderer reads MechanismRepresentation and UnifiedState.
  - Xiangfa cannot invent judgment.
  - LLM can express scene but not decide structure.
evidence:
  - Mechanism AST provides source/path/converter/bridge/state_delta components that can map to scene symbols.
counter_evidence:
  - formal Xiangfa symbol grammar not started
competing_theories:
  - fixed metaphor library theory
formalization:
  - XiangfaScene
  - SymbolMapping
data_model_implication:
  - symbol refs must link to evidence refs
runtime_implication:
  - Xiangfa remains explanation layer
synthetic_validation_plan:
  - Xiangfa symbol fixture after mechanism audit
real_world_validation_plan:
  - test whether users understand mechanism better with scene explanation
confidence: 0.58
related_theories:
  depends_on:
    - T004
    - T006
    - T008
rejected_reason: ""
```

### T010 — Semantic Narrowness Theory

```yaml
theory_id: T010
name: Semantic Narrowness Theory
research_program: RP007 Semantic Diversity
open_questions:
  - OQ007
status: candidate
priority: P0
description: V50 expression repetition is primarily caused by narrow upstream Brain / UnifiedState / winning-claim semantics, not by LLM wording alone.
scope:
  - unified_state
  - brain_verdict
  - semantic_coverage
  - expression_adapter
  - product_probability_field
what_changes_if_true:
  - Prompt tuning should pause until semantic coverage improves.
  - Runtime needs richer DomainState / ProbabilityField semantics.
  - Theme Discovery and State Evolution become prerequisites for product-level diversity.
  - Long-run expression validation must track semantic_repetition separately from expression_repetition.
evidence:
  - EV005
counter_evidence:
  - insufficient; needs multi-topic and richer fixture runs
competing_theories:
  - Prompt Repetition Theory
  - Model Style Collapse Theory
formalization:
  - SemanticSignature
  - UnifiedStateCoverageReport
  - ProbabilityFieldDimension
data_model_implication:
  - DomainState should expose product-level dimensions such as expansion, learning, management, volatility, relationship maintenance, health risk.
runtime_implication:
  - BrainVerdict should not only expose mechanism claim codes; it should expose probability-field semantics when supported by evidence.
synthetic_validation_plan:
  - build semantic diversity fixtures across career / wealth / relationship / health
real_world_validation_plan:
  - compare whether richer DomainState improves user decision clarity and probe convergence
confidence: 0.31
related_theories:
  supports:
    - T006
    - T007
  depends_on:
    - T004
rejected_reason: ""
```

### T011 — Life Decision Intelligence Theory

```yaml
theory_id: T011
name: Life Decision Intelligence Theory
research_program: RP008 Decision Intelligence
open_questions:
  - OQ008
status: candidate
priority: P0
description: DeepBazi's product object is Decision Field / Decision Intelligence, not raw Probability Field.
scope:
  - product
  - cognitive_ux
  - decision_policy
  - probability_field
  - probe
what_changes_if_true:
  - Runtime contracts should distinguish ProbabilityField from DecisionField.
  - Probe should measure Decision Convergence, not only probability update.
  - User-facing output should prioritize strategy, risk, timing, next action, and decision confidence.
evidence:
  - product philosophy discussion identifies Probability Field as engine intermediate state
counter_evidence:
  - no user validation yet
competing_theories:
  - Probability Field as Product Theory
formalization:
  - DecisionField
  - DecisionConfidence
  - DecisionConvergence
data_model_implication:
  - decision_field should reference probability_field, evidence_refs, uncertainty, timing_window, and probe_needed
  - decision_confidence should describe informed confidence under uncertainty
  - confidence_update should show how Probe changed the decision state
runtime_implication:
  - Brain should eventually emit decision-oriented contract after ProbabilityField
  - User-facing output should end in DecisionConfidence and ActionRecommendation, not raw probability
synthetic_validation_plan:
  - create decision scenarios where same probability field yields different decision strategy based on context and timing
real_world_validation_plan:
  - measure whether users report higher decision clarity after DecisionField vs ProbabilityField-only output
confidence: 0.34
related_theories:
  depends_on:
    - T006
    - T010
  supports:
    - T008
rejected_reason: ""
```
