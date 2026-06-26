# V30 Knowledge, Rule, and Portrait Plan

Updated: 2026-06-10

## Current Runtime Slice

Current runtime target:

```text
ChartContext + FeatureEvidence
-> KnowledgeRulePortrait seed registry
-> KnowledgeEvidence + RuleEvidence + PortraitSignal
-> Runtime trace
-> Synthetic validation
```

Rules:

- V30 owns its knowledge/rule/portrait records.
- V30 may reference V20 concepts only as reviewed source material, not runtime import.
- Seed registry starts small and deterministic.
- Every emitted signal must cite evidence IDs and keep boundary text.
- This layer feeds structure/mainline/question training later; it must not bypass validation.

Current implementation status:

- Seed registry exists in V30 code.
- Runtime emits `knowledge`, `rule`, and `portrait` signals from feature evidence.
- Each signal has a V30 source ID, evidence IDs, confidence, and boundary.
- Synthetic smoke validates the K/R/P signal case.
- Structure state consumes signals into path scores, graph nodes, graph edges, and primary chain.
- Mainline state consumes signals into supporting mainlines and boundary explanations.
- Question recommendation consumes signals into score reasons.
- K/R/P library units now match from `FeatureEvidence.supports` and `FeatureEvidence.weakens`.
- K/R/P units now expose score and score reasons.
- Active `question_policy.krp_unit_weights` can tune K/R/P unit scores without changing chart facts.
- Runtime exposes matched K/R/P units through `question_plan.policy_effect.krp_library_units`.
- Runtime exposes K/R/P pack summary through `question_plan.policy_effect.krp_library_summary`.
- Baseline runtime now matches at least twenty-seven K/R/P library units.
- Feature evidence now marks ten-god families (`self`, `output`, `wealth`, `authority`, `resource`) for visible and hidden stems.
- Feature evidence now marks branch relation conflict/alignment families for clash, harm, break, punishment, harmony, three-harmony, and three-meeting.
- Feature evidence now emits `structure_pattern` review candidates for seasonal strength, 格局 candidate boundaries, day-master element share buckets, and useful-god candidate families.
- Feature evidence now emits `domain_rule` review candidates for wealth, career, relationship, health, and useful-god domain paths.
- User-calibrated hidden-factor feedback now adds counter-evidence K/R/P units while preserving traceability.
- Current pack includes chart context, day-master element context, visible ten-god context, ten-god family review units, hidden-stem hypothesis, useful-god candidate/resolution gates, useful-god family/domain candidates, seasonal strength review, 格局 candidate review, wealth/career/relationship/health domain rule candidates, time boundaries, element balance, branch conflict/alignment families, structure dynamics, path-resolution review, hidden-factor feedback, and rule counter-evidence trace.
- Current pack is identified as `v30.krp.pack.core_runtime` with version `2026-05-21`.
- K/R/P units now carry pack metadata, required context, counter context, mechanism hooks, question hooks, portrait dimensions, portrait tags, answer guidance, training tags, locale terms, and boundary text.
- Synthetic validation now checks K/R/P pack IDs and required portrait tags, not just unit IDs.
- Live real-runtime verification confirmed `krp_library_summary` is present from the Postgres/Redis-backed API.
- Multi-dimensional source inventory is documented in `docs/V30_KNOWLEDGE_SOURCE_INVENTORY.md`.
- First V30-owned macro taxonomy is available in `v30/knowledge/packs/multidimensional_taxonomy.py`.
- Macro taxonomy currently covers foundation, wealth, career, relationship, romance, health, and hidden-factor dimensions.
- First V30-owned macro pack loader is available in `v30/knowledge/loaders/macro_pack.py`.
- Runtime exposes macro pack consumption through `question_plan.policy_effect.core_macro_pack_summary`.
- Live real-runtime verification confirmed `v30.knowledge.pack.core_macro_zh_v1` with all 7 macro domains active.
- Runtime now emits `macro_dimension_signals` for active foundation, wealth, career, relationship, romance, health, and hidden-factor dimensions.
- Each macro dimension signal carries evidence IDs, matched evidence domains, question hooks, structure hooks, portrait dimensions, training tags, and boundary text.
- Macro dimension coverage now feeds `v30.training_signal.macro_dimension_coverage` and can participate in auto-training.
- Question recommendation now consumes macro dimension signals through matching `question_hooks` and emits `macro_dimension_context:*` reasons.
- Answer context now exposes matched macro dimension signals under `role_answer_contract.macro_dimension_signals`.
- Presentation now preserves recommender ordering so capped scores do not reorder missing-time boundary questions behind hidden-factor questions.
- V30 now has a first macro portrait projection module at `v30/portrait/projection.py`.
- Runtime emits `macro_portrait_projections` and `macro_portrait_summary` from macro dimension signals.
- Answer context exposes matched macro portrait projections under `role_answer_contract.macro_portrait_projections`.
- Portrait projections use `portrait_is_projection_not_fact_source` and keep evidence IDs plus boundaries traceable.
- Runtime now also emits role-aware `macro_portrait_projection_views` and `macro_portrait_view_summary`.
- `MacroPortraitProjectionView` applies role/client visibility: guest hides hidden-factor projection views, user sees hidden factor as boundary-visible, and admin/analyst/lab/practitioner get diagnostic projection views.
- Answer context exposes matched role-aware views under `role_answer_contract.macro_portrait_projection_views`.
- Presentation diagnostics rebuild portrait views for the requested role/client and keep the role-filter boundary `portrait_projection_view_is_role_filtered_not_chart_fact`.
- K/R/P now includes bounded 通关/制化 candidate review units for resource mediation, output-to-wealth bridge, output-controls-authority 制化, and wealth-authority-resource 制化 chains.
- These units hook into `dynamic_graph.path_resolution` and `dynamic_graph.tongguan_zhihua` while preserving candidate-review boundaries.

## Current Completion And Module Push

2026-06-10 status clarification:

The M3 main module is complete for the current runtime scope, because knowledge/rule/portrait/feature evidence is active, traceable, bounded, tested, and consumed by downstream Bazi calculation modules. The internal K/R/P rows below are still kept as depth indicators, because knowledge content, rule coverage, portrait expression density, and real-case calibration must keep growing through validation and training.

Current verified inventory:

```text
K/R/P units: 54 total
- knowledge: 14
- rule: 35
- portrait: 5

Rule evidence specs: 9
Source families: 6
Runtime domains: 14
Macro portrait domains: 7
Portrait dimensions: 47
Portrait tags: 54
```

| Area | Completion | Current state | Next task |
|---|---:|---|---|
| K/R/P runtime library | 100% current-scope / 85% depth | 54 runtime units cover ten-god, branch relation, seasonal strength, 格局, useful-god candidates, domain rules, path resolution, 通关/制化, and P7/P8 hook consumers. | Add real-case calibration tags without creating a second truth source. |
| Macro taxonomy and portraits | 100% current-scope / 72% depth | Macro dimensions and role-aware portrait projection views are active, with `model_signal_summary` available for explanation density only. | Tune explanation density with calibration evidence. |
| Rule/domain depth | 100% current-scope / 80% depth | Domain-rule depth, unit-derived policy weights, rule counter-evidence, and interaction-stage hooks are active. | Add real-case calibration tags and synthetic expectations. |

Latest targeted validation:

```text
pytest -q tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py tests/unit/test_portrait_projection.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_structure_mechanism_graph.py tests/unit/test_knowledge_source_registry.py
22 passed
```

2026-06-10 persistence update:

M3 K/R/P data now has dedicated Postgres persistence, not only runtime trace storage.

```text
v30_m3_knowledge_units: 54
v30_m3_rule_specs: 9
v30_m3_portrait_assets: 7
v30_m3_validation_snapshots: 2
```

The snapshot CLI is:

```text
python3 scripts/run_m3_core_spine_snapshot.py --sample-limit 1
```

Latest successful DB write:

```text
v30.m3.snapshot.20260610045211763673: krp=54 rules=9 portrait_assets=7 synthetic=8/8
db: postgres searchable=True rows={'knowledge_units': 54, 'rule_specs': 9, 'portrait_assets': 7, 'validation_snapshots': 1}
```

M3 518K summary snapshot:

```text
v30.m3.snapshot.518k.20260610044238766995
db: postgres searchable=True rows={'knowledge_units': 0, 'rule_specs': 0, 'portrait_assets': 0, 'validation_snapshots': 1}
```

This persistence layer is support data only. It does not promote policies, mutate chart facts, or turn rule candidates into fixed Bazi verdicts.

P7/P8/P9 support work:

- P7/P8 hooks for `model_signal_summary`, `interaction_stage`, `selected_domain`, and `followup_reason` are now baseline runtime support.
- Add real-case calibration tags for canonical fixtures and explanation-density tuning.
- Keep training tags for `ten_god_energy_fusion`, `ranked_decision_fusion`, `interaction_loop_quality`, and `real_case_calibration_pack`.
- Keep all K/R/P outputs as evidence, projection, or guidance; none may mutate chart facts.

## Purpose

V30 needs an integrated but separated design for:

- Bazi knowledge.
- Rule catalog.
- Feature evidence.
- Portrait modeling.
- Structure mechanisms.
- Question and answer support.

These systems should support each other without becoming competing truth sources.

## Core Rule

Only `ChartContext` owns chart facts.

Knowledge, rules, and portraits may interpret, classify, and project evidence. They may not mutate or replace chart facts.

## Layer Responsibilities

### Knowledge Packs

Purpose:

- Store reviewed Bazi concepts.
- Define mechanism descriptions.
- Provide answer boundaries.
- Support rule extraction and LLM context.

Output:

```text
KnowledgeUnit
KnowledgeBoundary
MechanismDefinition
```

### Rule Catalog

Purpose:

- Convert knowledge into testable conditions.
- Emit rule evidence and conflict sets.
- Support defeasible reasoning.

Output:

```text
RuleSpec
RuleEvidence
ConflictSet
ResolutionTrace
```

### Portrait Model

Purpose:

- Project current chart evidence into role-facing Bazi portrait dimensions.
- Support user understanding and question recommendation.

Output:

```text
PortraitDimension
PortraitTag
PortraitEvidence
RolePortraitProjection
```

### Structure Mechanisms

Purpose:

- Name and bound graph-extracted dynamic paths.
- Explain path semantics and missing requirements.

Output:

```text
MechanismMatch
StructureSemanticCandidate
```

## Data Flow

```text
KnowledgePack
-> RuleSpec
-> RuleEvidence
-> StructureMechanism
-> PortraitMapping
-> QuestionIntent support
-> Answer boundary support
```

Runtime flow:

```text
ChartContext
-> FeatureEvidence
-> RuleEvidence
-> StructureState
-> PortraitEvidence
-> MainlineState
-> QuestionAnchor
-> AnswerContext
```

## Knowledge Unit Schema

Required fields:

```text
knowledge_id
pack_id
pack_version
family
title
statement
required_context
counter_context
evidence_inputs
rule_atoms
structure_mechanisms
portrait_mappings
question_intents
answer_boundaries
training_tags
locale_terms
version
```

## Rule Spec Schema

Required fields:

```text
rule_id
knowledge_id
domain
conditions
positive_examples
counter_examples
emits
weakens
conflicts_with
boundary
policy_weights
version
```

## Portrait Dimension Schema

Required fields:

```text
dimension_id
domain
label
evidence_requirements
structure_requirements
rule_requirements
confidence_policy
role_visibility
answer_boundaries
question_intents
```

## Generation Strategy

V30 should generate these assets as candidate artifacts:

```text
knowledge_pack candidate
rule_catalog candidate
portrait_policy candidate
structure_mechanism candidate
```

Promotion requires integrated validation.

## Runtime Library Slice

Current V30-owned library units:

| Unit | Domain | Purpose |
|---|---|---|
| `v30.krp.ten_god.visibility_context` | `ten_god` | Treat visible ten-god markers as bound context, not personality verdicts. |
| `v30.krp.chart.context_bound` | `chart` | Keep chart facts immutable for downstream models. |
| `v30.krp.element.day_master_context` | `element` | Separate deterministic day-master element context from strength interpretation. |
| `v30.krp.ten_god.output_expression_review` | `ten_god` | Treat output markers as expression/release context, not personality claims. |
| `v30.krp.ten_god.wealth_resource_review` | `ten_god` | Keep wealth markers as reviewed allocation context, not financial prediction. |
| `v30.krp.ten_god.authority_pressure_review` | `ten_god` | Route authority markers through pressure-path review before outcome language. |
| `v30.krp.ten_god.resource_support_review` | `ten_god` | Treat resource markers as support context, not fixed useful-god verdicts. |
| `v30.krp.ten_god.self_competition_review` | `ten_god` | Treat self/peer markers as competition context, not temperament verdicts. |
| `v30.krp.ten_god.hidden_stem_context` | `ten_god` | Treat hidden-stem markers as dialogue hypotheses. |
| `v30.krp.useful_god.candidate_gate` | `useful_god` | Keep useful-god as a candidate review path until evidence resolves it. |
| `v30.krp.useful_god.resolved_counter` | `useful_god` | Preserve resolved useful-god feedback as bounded counter-evidence. |
| `v30.krp.time_context.missing_boundary` | `time_context` | Block timing and special-year claims until explicit time layers are available. |
| `v30.krp.time_context.activation_review` | `time_context` | Treat explicit time layers as review context, not fixed-event proof. |
| `v30.krp.element.balance_review` | `element` | Treat element distribution as bounded review context, not a standalone strength verdict. |
| `v30.krp.strength.seasonal_review` | `structure_pattern` | Treat seasonal support/pressure as strength-review input, not final旺衰 verdict. |
| `v30.krp.structure.pattern_candidate_review` | `structure_pattern` | Keep 格局 signals as candidate review language until paths validate them. |
| `v30.krp.useful_god.family_candidate_review` | `useful_god` | Represent useful-god families as review candidates, not fixed favorable labels. |
| `v30.krp.hidden_factor.feedback_calibration` | `hidden_factor` | Require user feedback before hidden factors become amplifier candidates. |
| `v30.krp.hidden_factor.dialogue_boundary` | `hidden_factor` | Keep hidden-factor conclusions blocked until boundary-event dialogue. |
| `v30.krp.hidden_factor.user_calibrated_counter` | `hidden_factor` | Preserve user-confirmed hidden-factor counter-evidence as hypothesis-strengthening feedback. |
| `v30.krp.branch_relation.dynamic_review` | `branch_relation` | Require layered dynamic review before single-factor branch reading. |
| `v30.krp.branch_relation.conflict_family` | `branch_relation` | Treat clash/harm/break/punishment as conflict-family evidence requiring context. |
| `v30.krp.branch_relation.alignment_family` | `branch_relation` | Treat harmony/meeting as alignment-family context, not automatic good outcomes. |
| `v30.krp.structure.dynamic_path` | `structure_dynamic` | Explain dynamic graph paths as structure context, not single-factor verdicts. |
| `v30.krp.structure.path_resolution_review` | `structure_dynamic` | Explain generate/control path-resolution candidates without final structure claims. |
| `v30.krp.wealth.domain_path_review` | `wealth` | Keep wealth paths as pressure/allocation review, not financial outcome prediction. |
| `v30.krp.wealth.competition_path_review` | `wealth` | Review wealth competition as allocation pressure, not gain/loss prediction. |
| `v30.krp.wealth.output_generation_path_review` | `wealth` | Review output-to-wealth generation paths without monetization claims. |
| `v30.krp.wealth.authority_bridge_path_review` | `wealth` | Review wealth-authority bridge pressure without financial or career verdicts. |
| `v30.krp.career.authority_path_review` | `career` | Keep authority/career paths as pressure/resolution review, not career outcome prediction. |
| `v30.krp.career.authority_pressure_path_review` | `career` | Review authority pressure as responsibility context, not job-status prediction. |
| `v30.krp.career.resource_resolution_path_review` | `career` | Review resource-resolution support paths without promotion or role claims. |
| `v30.krp.relationship.relation_path_review` | `relationship` | Keep relationship paths as interaction-structure review, not event prediction. |
| `v30.krp.relationship.conflict_path_review` | `relationship` | Review conflict paths as interaction friction, not relationship events. |
| `v30.krp.relationship.alignment_path_review` | `relationship` | Review alignment paths as continuity candidates, not outcomes. |
| `v30.krp.relationship.marker_path_review` | `relationship` | Treat authority/wealth markers as relationship context prompts, not verdicts. |
| `v30.krp.health.element_imbalance_review` | `health` | Keep health element imbalance as cautionary review, not medical claim. |
| `v30.krp.health.excess_review` | `health` | Keep element excess as balance review, not medical inference. |
| `v30.krp.health.thin_review` | `health` | Keep element thinness as balance review, not medical inference. |
| `v30.krp.health.conflict_pressure_review` | `health` | Review conflict pressure as general caution, not illness claim. |
| `v30.krp.useful_god.domain_path_candidate_review` | `useful_god` | Use domain paths to prioritize useful-god review, not finalize useful-god. |
| `v30.krp.rule.counterevidence.trace` | `rule_counterevidence` | Keep countered rules visible instead of deleting the original boundary. |

Scoring contract:

```text
matched_support_count
-> base score
-> question_policy.krp_unit_weights
-> scored K/R/P library unit
```

This keeps K/R/P optimization inside V30 policy and validation instead of hard-coding final interpretations.

Runtime summary contract:

```text
krp_library_units
-> unit_count
-> pack_ids
-> pack_versions
-> by_type
-> by_domain
-> boundary_count
-> portrait_tags
-> portrait_dimensions
-> question_hooks
-> mechanism_hooks
-> training_tags
```

Macro pack summary contract:

```text
core_macro_pack_summary
-> pack_id
-> pack_version
-> taxonomy_version
-> item_count
-> active_item_count
-> domains
-> active_domains
-> question_hooks
-> structure_hooks
-> portrait_dimensions
-> training_tags
-> boundary_count
```

Macro dimension signal contract:

```text
macro_dimension_signals[]
-> signal_id
-> pack_id
-> pack_version
-> dimension_id
-> domain
-> label_zh
-> matched_evidence_domains
-> evidence_ids
-> question_hooks
-> structure_hooks
-> portrait_dimensions
-> training_tags
-> boundaries
-> score
-> boundary
```

Macro portrait projection contract:

```text
macro_portrait_projections[]
-> projection_id
-> version
-> source_signal_id
-> domain
-> label_zh
-> portrait_dimensions
-> evidence_ids
-> matched_evidence_domains
-> confidence
-> boundaries
-> source_policy
```

Current portrait source policy:

```text
portrait_is_projection_not_fact_source
```

Current live sample:

```text
unit_count: 11
pack_ids: v30.krp.pack.core_runtime
pack_versions: 2026-05-21
mechanism_hooks: dynamic_graph.v2, mechanism.branch_relation_dynamic_review,
                 mechanism.hidden_factor_dialogue_probe,
                 mechanism.ten_god_visibility_context,
                 mechanism.useful_god_candidate_gate
```

## Synthetic Validation

Each knowledge/rule/portrait family needs:

- Positive prototype cases.
- Negative counter cases.
- Metamorphic pairs.
- Boundary gradient cases.
- Composite conflict cases.

Examples:

- Clear wealth channel should trigger wealth evidence but not unconditional wealth success.
- Resource support added to an authority-pressure case should change portrait and structure interpretation.
- Missing time should suppress unsupported timing questions.
- Branch clash should increase volatility without inventing a new mainline.

## 518K Role

518K is used for:

- Coverage distribution.
- Rare pattern detection.
- Over-trigger detection.
- Similar case references.
- Parameter stability.

518K is not used to declare single-chart truth.

## LLM Role

LLM may:

- Draft knowledge units.
- Propose rule atoms.
- Suggest portrait wording.
- Cluster failures.
- Generate candidate synthetic cases.

LLM may not:

- Activate knowledge directly.
- Promote rules directly.
- Mark portraits as evidence without validation.
- Update runtime pointers.

## First Milestone

Build a small reviewed seed set covering:

- Day master support.
- Output controls authority.
- Resource supports authority pressure.
- Wealth channel and bearing capacity.
- Peer support and wealth competition.
- Missing time boundary.
- Luck/annual activation.

Acceptance:

- Each seed has rule atoms.
- Each seed has at least one positive and one negative synthetic case.
- Each seed has answer boundary.
- Each seed can support at least one question intent.

## Acceptance

- Knowledge, rules, and portraits are versioned artifacts.
- Runtime consumes only active V30 artifacts.
- Every user-facing portrait binds to evidence.
- No portrait can override structure state.
- No knowledge text becomes unbounded prompt filler.
