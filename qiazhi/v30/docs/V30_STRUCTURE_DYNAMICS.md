# V30 Structure Dynamics

Updated: 2026-05-22

## Purpose

V30 structure dynamics rebuilds the strongest V20 idea: weighted dynamic graph reasoning over current Bazi context.

The goal is to identify the current dynamic structure from original chart, luck cycle, annual flow, and optional current time layer.

## Core Rule

V30 structure dynamics is a fact/evidence layer, not a public verdict layer.

It outputs:

- Graph nodes.
- Graph edges.
- Candidate paths.
- Path scores.
- Structure state.
- Semantic mechanism candidates.
- Diagnostics.

It does not output final life conclusions by itself.

## Data Flow

```text
ChartContext
-> TenGodEnergyModel / model_signal_summary
-> FeatureEvidence
-> RuleEvidence
-> DynamicGraphBuilder
-> PathExtractor
-> PathStateEvaluator
-> MechanismMatcher
-> StructureState
-> MainlineArbitration
```

## Graph Nodes

Initial node types:

```text
day_master
stem
hidden_stem
branch
ten_god
element
time_layer
structure_candidate
```

## Graph Edges

Initial edge types:

```text
reveal
hide
generate
control
root
activate
combine
clash
block
support
drain
transform
```

## Path Extraction

V30 should not start with fixed templates as the primary algorithm.

It should:

1. Build graph from current context.
2. Score nodes and edges.
3. Extract top-k candidate paths.
4. Evaluate path state.
5. Match semantic mechanisms.
6. Select structure state.

## Path Score

Initial scoring dimensions:

```text
node_strength
edge_strength
visibility
continuity
time_activation
terminal_convergence
support_quality
blockage_penalty
volatility_penalty
semantic_match_score
ten_god_energy_alignment
ten_god_stability_adjustment
ten_god_volatility_penalty
```

These dimensions are tuned by `structure_policy`.

## Path States

Allowed states:

```text
closed
partial
blocked
leaking
volatile
overdriven
collapsed
unsupported
```

## Mechanism Matching

Mechanism definitions come from V30 knowledge packs.

Mechanism match output:

```text
mechanism_id
label
required_context
matched_context
missing_context
counter_evidence
confidence
boundary
```

## StructureState Contract

Required fields:

```text
structure_id
primary_chain
candidate_chains
graph_nodes
graph_edges
path_scores
semantic_label
state
confidence
evidence_ids
boundary
```

## Synthetic Validation

Structure dynamics requires:

- Positive prototype cases.
- Negative counter cases.
- Metamorphic pairs.
- Boundary gradient cases.
- Composite conflict cases.

Initial target cases:

- Output controls authority.
- Resource receives authority pressure.
- Wealth channel with bearing capacity.
- Wealth visible but weak bearing.
- Peer competition around wealth.
- Branch clash activation.
- Luck cycle activates hidden structure.
- Annual flow destabilizes stable path.
- Missing time suppresses timing certainty.
- Composite output/wealth/authority conflict.

## Training and Parameters

Policy family:

```text
structure_policy
```

Tunable parameters:

- Node weights.
- Edge weights.
- Time activation weights.
- Root continuity weights.
- Blockage penalties.
- Volatility thresholds.
- Semantic match thresholds.
- Stability floors.

Promotion:

```text
candidate weights
-> synthetic validation
-> 518K sample validation
-> policy artifact
-> runtime pointer
```

## Acceptance

- Structure graph is generated from V30 `ChartContext`.
- No V20 runtime import.
- Structure labels come from V30 mechanism definitions.
- User-facing output never receives generic fallback labels when a reviewed mechanism matches.
- Mainline consumes `StructureState`, not graph internals.
- Structure policy can be pointer-loaded.

## Current Implementation Slice

Next target:

```text
FeatureEvidence + K/R/P signals
-> MechanismPath graph
-> StructureState.graph_nodes/graph_edges/path_scores
-> Mainline + Question recommendation
```

Initial mechanisms:

- `mechanism.ten_god_visibility_context`
- `mechanism.useful_god_candidate_gate`
- `mechanism.hidden_factor_dialogue_probe`
- `mechanism.branch_relation_dynamic_review`

These are still evidence-bound mechanism candidates, not public life verdicts.

Current implementation status:

- `MechanismPath` contract exists.
- Mechanism graph builder emits scored mechanism paths from FeatureEvidence and K/R/P signals.
- StructureState graph includes mechanism path nodes and evidence/signal edges.
- StructureState path scores include `mechanism_path_count` and `top_mechanism_score`.
- Mainline explains when mechanism paths are scored.
- Question recommender can add `mechanism_paths_scored` as a reason.
- Synthetic smoke validates required mechanism paths.
- Dynamic graph v2 paths now carry `competition_rank`, `suppression`, and `score_reasons`.
- Dynamic graph v2 paths now carry `conflict_families` derived from control pressure, rule blockage/counter-evidence, and branch relation conflict families.
- Dynamic graph v2 paths now carry `resolution_families` derived from day-master reachability, generate/control sequences, resource support paths, conflict-with-continuity review, and counter-evidence resolution.
- Dynamic graph v2 scoring explains node score, edge score, terminal bonus, blockage penalty, counter-evidence penalty, conflict-family penalty, policy weight, and competition suppression.
- StructureState path scores now expose dynamic competing/suppressed/blocked/countered path counts plus conflict-family, path-resolution-family, branch-conflict-edge, branch-alignment-edge, strength-pattern-review, and domain path counts.

## Current Focus: Structure Policy Weight Consumption

Goal:

```text
active structure_policy artifact payload
-> mechanism path weights
-> MechanismPath.score
-> StructureState.path_scores
-> Mainline/Question behavior
```

Acceptance:

- Runtime loads the active `structure_policy` artifact payload.
- Mechanism scores are multiplied by policy weights.
- Auto-training generates a structure policy weight candidate.
- Synthetic/518K sample can observe policy-driven score changes.

Status:

- RuntimePointerStore can load the active policy artifact payload.
- `structure_policy.weights` affects `MechanismPath.score`.
- Runtime trace exposes `structure_policy_payload`.
- `structure_policy_weighted` path score marks policy consumption.
- Auto-training now emits default structure mechanism weights.
- `structure-weight-001` was auto-applied and changed top mechanism score.

## Current Focus: Dynamic Path Competition and Suppression

Completed:

- Competing dynamic paths are grouped by starting family.
- Lower-ranked paths in the same family group receive deterministic competition suppression.
- Blockage edges apply stronger path penalty than counter-evidence edges.
- Counter-evidence remains traceable and does not delete the original rule path.
- Path score reasons are emitted into graph nodes for diagnostics and validation.

Current exposed metrics:

```text
dynamic_competing_path_count
dynamic_suppressed_path_count
dynamic_blocked_path_count
dynamic_countered_path_count
dynamic_conflict_path_count
dynamic_conflict_family_count
dynamic_path_resolution_family_count
dynamic_branch_conflict_edge_count
dynamic_branch_alignment_edge_count
strength_pattern_review_count
dynamic_wealth_path_count
dynamic_wealth_competition_path_count
dynamic_wealth_output_generation_path_count
dynamic_wealth_authority_bridge_path_count
dynamic_career_path_count
dynamic_career_authority_pressure_path_count
dynamic_career_resource_resolution_path_count
dynamic_relationship_path_count
dynamic_relationship_conflict_path_count
dynamic_relationship_alignment_path_count
dynamic_relationship_marker_path_count
dynamic_health_review_path_count
dynamic_health_element_excess_review_count
dynamic_health_element_thin_review_count
dynamic_health_conflict_pressure_review_count
dynamic_useful_god_candidate_path_count
dynamic_useful_god_ranked_candidate_count
top_dynamic_path_suppression
```

Synthetic validation now checks dynamic graph v2 path competition and suppression coverage.

Training integration:

```text
dynamic_competing_path_count
dynamic_suppressed_path_count
dynamic_blocked_path_count
dynamic_countered_path_count
dynamic_conflict_family_count
dynamic_path_resolution_family_count
dynamic_branch_conflict_edge_count
dynamic_branch_alignment_edge_count
dynamic_wealth_path_count
dynamic_wealth_competition_path_count
dynamic_wealth_output_generation_path_count
dynamic_wealth_authority_bridge_path_count
dynamic_career_path_count
dynamic_career_authority_pressure_path_count
dynamic_career_resource_resolution_path_count
dynamic_relationship_path_count
dynamic_relationship_conflict_path_count
dynamic_relationship_alignment_path_count
dynamic_relationship_marker_path_count
dynamic_health_review_path_count
dynamic_health_element_excess_review_count
dynamic_health_element_thin_review_count
dynamic_health_conflict_pressure_review_count
dynamic_useful_god_candidate_path_count
dynamic_useful_god_ranked_candidate_count
-> v30.training_signal.structure_dynamic_competition
-> structure_policy.weights.dynamic_graph.v2
-> structure_policy.weights.dynamic_graph.competition_suppression
-> structure_policy.weights.dynamic_graph.conflict_family
-> structure_policy.weights.dynamic_graph.path_resolution
-> structure_policy.weights.dynamic_graph.domain_path
-> structure_policy.weights.dynamic_graph.domain_rule_depth
-> structure_policy.weights.dynamic_graph.useful_god_candidate_path
-> structure_policy.weights.dynamic_graph.useful_god_candidate_path
```

The current loop keeps this deterministic and validation-gated: the signal proposes weights, promotion still replays synthetic `all` and 518K sample before pointer activation.

Latest applied policy:

```text
training_run_id: domain-rule-depth-001
active structure_policy: structure_policy.domain-rule-depth-001.structure_policy
dynamic_graph.v2: 1.04
dynamic_graph.competition_suppression: 1.07
dynamic_graph.conflict_family: 1.015
dynamic_graph.path_resolution: 1.036
dynamic_graph.domain_path: 1.06
dynamic_graph.useful_god_candidate_path: 1.06
```

Live runtime verification on the real V30 service confirmed:

- Dynamic graph path nodes include policy score reasons.
- `dynamic_competing_path_count` is exposed in `StructureState.path_scores`.
- `dynamic_suppressed_path_count` is exposed in `StructureState.path_scores`.
- `dynamic_conflict_family_count`, `dynamic_branch_conflict_edge_count`, and `dynamic_branch_alignment_edge_count` are exposed in `StructureState.path_scores`.
- `dynamic_path_resolution_family_count` and `strength_pattern_review_count` are exposed in `StructureState.path_scores`.
- `dynamic_tongguan_path_count`, `dynamic_tongguan_resource_mediator_path_count`, `dynamic_tongguan_output_wealth_bridge_path_count`, `dynamic_zhihua_path_count`, `dynamic_zhihua_output_authority_path_count`, and `dynamic_zhihua_wealth_authority_resource_path_count` are now exposed in `StructureState.path_scores`.
- Auto-training now emits `structure_policy.weights.dynamic_graph.tongguan_zhihua` from those bounded 通关/制化 path metrics.
- Wealth, career, relationship, health, and useful-god domain path counts are exposed in `StructureState.path_scores`.
- Mainline and question layers still consume the same `StructureState` boundary instead of reaching into graph internals.

## Current Completion And P7 Module Push

| Area | Completion | Current state | Next task |
|---|---:|---|---|
| Dynamic graph v2 | 87% | Competition, suppression, conflict family, path-resolution family, domain paths, domain-rule depth, and 通关/制化 metrics are active. | Add ten-god model-signal inputs through a bounded summary. |
| Structure policy consumption | 84% | Active pointer weights affect mechanism and dynamic graph path scores. | Add model-fusion weights only after synthetic and 518K sample validation. |
| Ranked decision handoff | 58% | Strength, structure, and useful-god ranked decisions exist but remain partly separate heuristics. | Feed structure and ten-god model summary into one candidate scoring layer. |

P7 deliverables:

- Consume `model_signal_summary` instead of raw ten-god score maps.
- Add path-score reasons for energy alignment, stability support, and volatility weakening.
- Keep raw score detail diagnostic-only.
- Emit training observations for `v30.training_signal.ten_god_energy_fusion`.
- Expose `model_signal_summary_ready`, `model_signal_energy_band_count`, `model_signal_structure_path_adjustment`, and `top_dynamic_path_model_signal_adjusted_score` in `StructureState.path_scores`.
- Read `structure_policy.weights.dynamic_graph.model_signal_fusion` for bounded model-signal path adjustment.

P7 validation:

- Unit tests for bounded model-signal path scoring.
- Synthetic cases where energy strengthens, weakens, or leaves a candidate unresolved.
- 518K sample coverage fields for model-signal distribution before pointer promotion.

Current P7 status:

- Runtime structure selection accepts `model_signal_summary` as an additive input.
- Auto-training candidates can emit `dynamic_graph.model_signal_fusion`.
- No raw score is projected to customer views.
