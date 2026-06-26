# V30 Rule, Knowledge, and Dynamics Review

Updated: 2026-05-20

## Scope

This review captures the V20 assets that should shape the V30 mainline without importing `v20.*` at runtime.

Reviewed V20 assets:

- `v20/rules/engine.py`
- `v20/knowledge/rule_library.py`
- `v20/decision/defeasible_model.py`
- `v20/dynamics/graph_engine.py`

## V20 Lessons to Keep

### Rule Runtime

V20 rule runtime has the right shape:

```text
evidence atoms
-> condition matching
-> rule match status
-> policy weight adjustment
-> runtime report
```

V30 should keep this principle:

- Rules consume evidence, not raw UI text.
- Policy changes adjust runtime scores, not chart facts.
- Rules emit boundaries and candidates, not fortune verdicts.
- Runtime output must be traceable by rule ID and evidence ID.

### Knowledge Rule Library

V20 knowledge rule library connects:

```text
knowledge unit
-> condition atoms
-> portrait outputs
-> question outputs
-> answer guidance
```

V30 should keep this direction, but rebuild the data model as V30-owned Markdown/JSON contracts. The current V30 seed registry is only the first layer.

### Defeasible Decision Model

V20 defeasible model is important because it separates:

- support evidence
- counter evidence
- decision state
- topic projection
- mainline candidates

V30 should use this as the target shape for rule/mainline evolution. The immediate V30 step is not a full argumentation engine; it is a rule evidence skeleton that preserves the same boundaries.

### Structure Dynamics

V20 structure dynamics graph contains mature ideas:

- ten-god family graph
- element generate/control edges
- path extraction
- path state
- runtime policy weights
- semantic candidates

V30 already has mechanism path v1. The next structure upgrade should move toward weighted dynamic graph extraction while keeping V30 contracts and validations.

Current V30 progress:

- `v30/structure/dynamic_graph.py` adds V30-owned dynamic graph v2.
- Dynamic graph v2 extracts ten-god family nodes, generate/control/day-master edges, rule-state edges, and deterministic paths.
- `structure_policy.weights["dynamic_graph.v2"]` can tune dynamic path scores.
- StructureState now exposes dynamic graph nodes, edges, paths, and path scores while preserving mechanism path v1.

## Current V30 Implementation

Implemented in this step:

```text
FeatureEvidence
-> RuleEvidenceSpec
-> rule FeatureEvidence
-> active rule_policy weights
-> rule_decision_state support/blocked/countered
-> StructureState rule_evidence_count
-> StructureState rule_countered_count
-> MainlineState rule_evidence support
-> QuestionRecommendation rule evidence reason
```

Files:

- `v30/rules/evidence.py`
- `v30/evidence/compiler.py`
- `v30/structure/selector.py`
- `v30/mainline/selector.py`
- `v30/questions/anchor_selector.py`
- `v30/questions/recommender.py`

Initial V30 rule evidence specs:

- `v30.rule.time_context.blocks_timing_claim`
- `v30.rule.useful_god.candidate_gate`
- `v30.rule.hidden_factor.requires_dialogue`
- `v30.rule.branch_relation.requires_dynamic_review`

## Guardrails

- V30 does not runtime import `v20.*`.
- Rule evidence does not mutate chart facts.
- Hidden factor remains dialogue-calibrated, not deterministic.
- Useful-god remains candidate review, not fixed verdict.
- Time claims remain blocked without explicit time layer.

## Validation

Default tests now cover:

- Rule evidence compiled from feature evidence.
- Rule policy weighting adjusts rule evidence confidence without mutating chart facts.
- Rule evidence can expose `rule_decision_state:*`.
- Explicit time-layer evidence counters the missing-time blocking rule while preserving traceability.
- User-confirmed hidden-factor feedback counters the dialogue-blocking hidden-factor rule while preserving traceability.
- Supplemental feedback evidence is consumed by rule replay as evidence, not as chart-fact mutation.
- Rule evidence consumed by structure path scores.
- Rule evidence consumed by mainline support and explanation.
- Rule evidence consumed by question recommendation reasons.
- Runtime trace exposes `rule_policy_payload`.
- Synthetic gradient validates hidden-factor rule policy weighting while preserving the dialogue boundary.
- Synthetic gradient validates dynamic graph v2 node/edge/path extraction.

Release validation remains:

```text
pytest
synthetic all
518K sample
release gate quick/standard
```

## Next Steps

1. Expand rule evidence from seed specs into a V30-owned rule library.
2. Expand counter-evidence into a fuller defeasible decision state model.
3. Connect dynamic graph v2 paths to mainline/question explanations.
4. Add synthetic cases that specifically validate broader useful-god, branch-relation, and hidden-factor conflicts.
