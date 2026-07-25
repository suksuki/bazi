# V50 Evidence Library

Status: active evidence asset

Ontology:

```text
docs/research/V50_EVIDENCE_ONTOLOGY.md
```

This file stores concrete evidence records.

It must follow the Evidence Ontology.

This is the main research asset after Theory Objects.

Theory without evidence is not enough.

V50 research should now accumulate evidence instead of adding abstraction layers.

## Core Principle

Theory must be evidence-driven.

Evidence is not only data.

Evidence is the semantic trust bridge between Collector and Theory.

Chinese:

```text
Evidence 不是数据，而是系统对不同来源信息的信任机制。
```

The primary research question is:

```text
What evidence supports or falsifies this theory?
```

## Evidence Object Schema

Each evidence item must contain:

```yaml
evidence_id:
collector_id:
evidence_class: structural | simulation | historical | behavior | statistical | counter
source_category: engine_generated | reality_generated
target_scope:
  - theory_confidence
  - runtime_validation
  - brain_confidence
  - probe_policy_calibration
supports_theories:
  - theory_id
weakens_theories:
  - theory_id
does_not_support_theories:
  - theory_id
falsifies_theories:
  - theory_id
reliability:
relevance:
  theory_id: score
research_program:
open_question:
lifecycle_status: collected | verified | referenced | promoted | archived
status: supports | weakens | falsifies | inconclusive
summary:
source_ref:
case_refs:
runtime_refs:
validation_refs:
observed:
expected_if_theory_true:
actual:
confidence_delta:
allowed_usage:
forbidden_usage:
notes:
```

Legacy field mapping:

```text
synthetic              -> structural or simulation
runtime_report         -> simulation
real_world             -> historical / behavior / statistical
discussion_observation -> historical or behavior, depending on source
counter_example        -> counter
```

## Evidence Collector Rule

Collector is not Evidence.

Examples:

```text
Synthetic Chart Generator -> Structural Evidence
State Simulator           -> Simulation Evidence
Probe                     -> Behavior Evidence
Historical Timeline       -> Historical Evidence
Population Analysis       -> Statistical Evidence
```

Probe answers can update current-person confidence and Twin Overlay.

Probe answers cannot freeze structural theory by themselves.

## Theory Evidence Summary Schema

Each theory should be summarized as:

```yaml
theory_id:
synthetic_evidence_count:
real_world_evidence_count:
counter_example_count:
supporting_evidence_count:
weakening_evidence_count:
falsifying_evidence_count:
confidence:
promotion_status:
runtime_status:
```

## Promotion Criteria

A theory can be promoted toward Runtime only when:

```text
[ ] Synthetic evidence exists
[ ] Real-world evidence exists or has an explicit collection plan
[ ] Counter examples are listed
[ ] Counter examples are explained or marked unresolved
[ ] Formalization exists
[ ] Data model implication exists
[ ] Runtime boundary exists
[ ] Validation plan exists
```

Promotion states:

```text
blocked
research_only
formalization_ready
runtime_candidate
runtime_active
```

## Active Evidence Seed

### EV001 — Mechanism AST Batch Role Coverage

```yaml
evidence_id: EV001
collector_id: synthetic_chart_taxonomy_v1 + mechanism_representation_batch_runner
evidence_class: simulation
source_category: engine_generated
target_scope:
  - theory_confidence
  - runtime_validation
supports_theories:
  - T004
weakens_theories: []
does_not_support_theories:
  - T005
falsifies_theories: []
reliability: 0.95
relevance:
  T004: 0.90
  T005: 0.40
research_program: RP002 Mechanism
open_question: OQ003
lifecycle_status: referenced
status: supports
summary: Mechanism Representation batch generated AST components across 17 taxonomy cases.
source_ref: scripts/v50_run_mechanism_representation_batch.py
case_refs:
  - synthetic_chart_taxonomy_v1
runtime_refs:
  - packages/core/mechanism/contracts.py
  - packages/core/mechanism/builder.py
validation_refs:
  - tests/test_v50_mechanism_representation.py
observed:
  - total representations: 63
  - role_count: 8
  - label_authority_violations: 0
  - representations_without_state_delta: 0
expected_if_theory_true:
  - mechanism can be represented as AST independent of label authority
actual:
  - source/path/target/state_delta exist on all sampled representations
confidence_delta: 0.04
allowed_usage:
  - mechanism representation validation
  - formalization gate support
  - synthetic validation support
forbidden_usage:
  - claiming mechanism discovery is solved
  - direct Brain policy training
notes: Supports T004 but does not prove discovery. Audit still required.
```

### EV002 — Mechanism Label Library Rejection

```yaml
evidence_id: EV002
collector_id: mechanism_v2_review + semantic_coverage_gate
evidence_class: counter
source_category: engine_generated
target_scope:
  - theory_confidence
  - theory_status
supports_theories:
  - T004
weakens_theories: []
does_not_support_theories: []
falsifies_theories:
  - T005
reliability: 0.86
relevance:
  T005: 0.92
  T004: 0.48
research_program: RP002 Mechanism
open_question: OQ003
lifecycle_status: archived_historical
status: falsifies
summary: Expanding mechanism labels improved coverage but risked recreating a rule/name library.
source_ref: discussion.review.mechanism_v2_brake
case_refs:
  - mechanism_v2
runtime_refs: []
validation_refs:
  - archived-review: semantic_coverage_gate_mechanism_v2
observed:
  - mechanism_count: 7
  - semantic coverage improved
  - reviewer flagged label-first expansion risk
expected_if_theory_true:
  - adding labels should be sufficient for discovery
actual:
  - label expansion needs AST audit before more discovery
confidence_delta: -0.20
allowed_usage:
  - theory falsification
  - promotion blocking
  - mechanism representation audit requirement
forbidden_usage:
  - deleting runtime labels that are only presentation labels
  - using label risk to reject AST representation
notes: Supports rejecting T005 as primary strategy.
```

### EV003 — Reading Slice Semantic Expansion Without Prompt

```yaml
evidence_id: EV003
collector_id: intelligent_reading_slice_batch_runner
evidence_class: simulation
source_category: engine_generated
target_scope:
  - theory_confidence
  - runtime_validation
supports_theories:
  - T004
  - T006
weakens_theories: []
does_not_support_theories: []
falsifies_theories: []
reliability: 0.90
relevance:
  T004: 0.72
  T006: 0.45
research_program: RP002 Mechanism
open_question: OQ003
lifecycle_status: archived_historical
status: supports
summary: Reading Slice batch reduced structural_baseline_pending from 18 to 0 without Prompt, UI, LLM, or weight tuning.
source_ref: archived-evidence:intelligent_reading_slice_batch_v1
case_refs:
  - synthetic_chart_taxonomy_v1
runtime_refs: []
validation_refs:
  - archived-test:test_v50_intelligent_reading_slice_batch
observed:
  - total readings: 34
  - passed: 34
  - structural_baseline_pending_count: 0
  - top_mechanism_ratio: 0.352941
expected_if_theory_true:
  - better mechanism representation should improve semantic diversity before Prompt work
actual:
  - semantic diversity improved without Expression layer changes
confidence_delta: 0.03
allowed_usage:
  - semantic coverage review
  - reading slice validation
  - mechanism representation confidence update
forbidden_usage:
  - prompt optimization justification
  - proof of real-world accuracy
notes: Supports AST/formal mechanism direction, but needs evidence-origin audit.
```

### EV004 — Timing Evidence Insufficient

```yaml
evidence_id: EV004
collector_id: timing_discussion_observation
evidence_class: historical
source_category: reality_generated
target_scope:
  - theory_confidence
  - timing_validation_plan
supports_theories:
  - T001
weakens_theories: []
does_not_support_theories:
  - T004
falsifies_theories: []
reliability: 0.55
relevance:
  T001: 0.48
  T004: 0.05
research_program: RP001 Timing
open_question: OQ001
lifecycle_status: collected
status: inconclusive
summary: Long-term Field Theory is plausible but currently lacks enough synthetic and real-world evidence.
source_ref: discussion.timing_luck_year_brake
case_refs:
  - personal_cases_limited
runtime_refs:
  - packages/core/state/delta.py
validation_refs:
  - data/validation/fixtures/timing_synthetic_validation_v1.json
observed:
  - theory explains some discussions about luck changing environment
  - evidence base is thin
expected_if_theory_true:
  - luck should produce gradual state_delta and mechanism_shift
actual:
  - current validation is synthetic and limited
confidence_delta: 0.0
allowed_usage:
  - motivating timing research
  - defining evidence collection need
forbidden_usage:
  - Theory Freeze
  - structural mechanism validation
  - runtime timing policy promotion
notes: Blocks Theory Freeze for T001.
```

### EV005 — Night Long-Run Semantic Narrowness Evidence

```yaml
evidence_id: EV005
collector_id: night_longrun_v2 + unified_state_coverage_analysis_v1
evidence_class: simulation
source_category: engine_generated
target_scope:
  - theory_confidence
  - runtime_validation
  - semantic_coverage
supports_theories:
  - T010
weakens_theories: []
does_not_support_theories:
  - Prompt Repetition Theory
falsifies_theories: []
reliability: 0.88
relevance:
  T010: 0.82
  T004: 0.30
  T006: 0.48
research_program: RP007 Semantic Diversity
open_question: OQ007
lifecycle_status: archived_historical
status: supports
summary: Night Long-Run Validation v2 and Unified State Coverage Analysis show 300 cases collapsed into 3 semantic signatures and 4 winning claim codes.
source_ref: archived-evidence:unified_state_coverage_analysis_v1
case_refs:
  - night_model_compare_wealth_career_longrun_v2
runtime_refs: []
validation_refs:
  - archived-run:night_model_compare_wealth_career_longrun_v2
  - archived-run:unified_state_coverage_analysis_v1
observed:
  - total_cases: 300
  - unique_semantic_signatures: 3
  - unique_claim_codes: 4
  - semantic_top_ratio: 0.5
  - semantic_repetition_rate: 0.99
  - expression_repetition_warnings: 252
  - semantic_repetition_warnings: 297
expected_if_theory_true:
  - many chart structures collapse into a small number of upstream semantic signatures
actual:
  - 300 cases produced only 3 semantic signatures
  - product-level probability field dimensions are not present as winning claims
confidence_delta: 0.08
allowed_usage:
  - support Semantic Narrowness research
  - block premature Prompt tuning
  - motivate UnifiedState / ProbabilityField coverage work
forbidden_usage:
  - claiming LLM is solved
  - changing Prompt without semantic coverage work
  - changing Brain weights directly
notes: Historical evidence explaining why the retired deterministic Brain and Product Projection chain was removed. It cannot support promotion in the current LLM Agent runtime.
```

## Theory Evidence Summary

```yaml
T001:
  synthetic_evidence_count: 1
  real_world_evidence_count: 0
  counter_example_count: 0
  supporting_evidence_count: 0
  weakening_evidence_count: 0
  falsifying_evidence_count: 0
  confidence: 0.62
  promotion_status: research_only
  runtime_status: synthetic TemporalState only

T004:
  synthetic_evidence_count: 1
  real_world_evidence_count: 0
  counter_example_count: 0
  supporting_evidence_count: 2
  weakening_evidence_count: 0
  falsifying_evidence_count: 0
  confidence: 0.81
  promotion_status: formalization_ready
  runtime_status: representation implemented; audit required before discovery

T005:
  synthetic_evidence_count: 1
  real_world_evidence_count: 0
  counter_example_count: 1
  supporting_evidence_count: 0
  weakening_evidence_count: 0
  falsifying_evidence_count: 1
  confidence: 0.0
  promotion_status: blocked
  runtime_status: rejected as primary strategy

T010:
  synthetic_evidence_count: 1
  real_world_evidence_count: 0
  counter_example_count: 0
  supporting_evidence_count: 1
  weakening_evidence_count: 0
  falsifying_evidence_count: 0
  confidence: 0.31
  promotion_status: research_only
  runtime_status: no runtime change; coverage analysis only
```

## Next Evidence Work

Priority:

```text
1. Mechanism Representation Audit evidence for T004
2. Timing synthetic counterexamples for T001 / T002 / T003
3. Ziwei Palace State Space synthetic evidence for T007
4. Semantic Diversity evidence for T010
5. Decision Intelligence evidence for T011
```
