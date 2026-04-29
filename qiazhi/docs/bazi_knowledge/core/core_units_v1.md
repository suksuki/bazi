# Core Bazi Knowledge Units v1

Date: 2026-04-28

Status: draft

Scope: A-only migration from legacy V17/V18 assets.

This document starts the clean Core Bazi Knowledge Base. It only keeps foundational facts and structural primitives.

It intentionally does not migrate legacy judgement plugins, pattern rules, scoring weights, narrative rules, or domain prediction rules.

## Governance

Core Knowledge Units are not runtime prediction rules.

Core Knowledge Units may be used to generate:

- chart structure facts
- structural feature extractors
- relation detectors
- evidence templates
- reviewer-facing documentation

Core Knowledge Units must not directly generate:

- fortune
- score
- narrative
- traditional prediction text
- good / bad judgement
- favorable / unfavorable judgement
- career / wealth / relationship / health conclusion

## Migration Policy

Allowed from legacy assets:

- stable constants
- structural tables
- relation pair tables
- layer boundaries
- pure feature definitions
- source references to old plugins or protocols

Rejected from legacy assets:

- pattern judgement
- yongshen / jishen judgement
- wealth-specific rules
- blind-school inference
- xiangfa inference
- shensha inference
- plugin match ratios
- old settlement weights
- old conflict-resolution weights
- old narrative prompts

## Unit Schema

```text
knowledge_id:
domain: chart_structure
category:
title:
statement:
structured_facts:
allowed_usage:
forbidden_usage:
source_refs:
status: draft
```

## Core Unit Index

```text
core.heavenly_stems
core.earthly_branches
core.five_elements
core.yin_yang
core.five_element_generation_control
core.stem_element_yinyang
core.branch_main_elements
core.ten_god_mapping
core.hidden_stems
core.pillar_structure
core.month_command
core.root_strength
core.visible_and_hidden_layers
core.six_combination
core.six_clash
core.three_harmony
core.three_meeting
core.branch_penalty
core.six_harm
core.six_break
core.stem_fusion
core.vault_structure
core.chang_sheng_12
core.time_structure_context
core.cross_layer_boundaries
```

## Knowledge Unit: core.heavenly_stems

```text
knowledge_id: core.heavenly_stems
domain: chart_structure
category: core_symbol
title: Heavenly Stems
statement: The ten heavenly stems are the visible stem symbols used in Bazi pillars.
structured_facts:
- stems: 甲, 乙, 丙, 丁, 戊, 己, 庚, 辛, 壬, 癸
allowed_usage:
- pillar construction
- stem relation detection
- ten god mapping input
forbidden_usage:
- direct prediction
- personality conclusion
- fortune conclusion
source_refs:
- v17_rebirth/backend/logic/configs/v17_core_constants.json
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
status: draft
```

## Knowledge Unit: core.earthly_branches

```text
knowledge_id: core.earthly_branches
domain: chart_structure
category: core_symbol
title: Earthly Branches
statement: The twelve earthly branches are the branch symbols used in Bazi pillars and branch relation detection.
structured_facts:
- branches: 子, 丑, 寅, 卯, 辰, 巳, 午, 未, 申, 酉, 戌, 亥
allowed_usage:
- pillar construction
- branch relation detection
- hidden stem lookup
- vault lookup
forbidden_usage:
- direct prediction
- fortune conclusion
source_refs:
- v17_rebirth/backend/logic/configs/v17_core_constants.json
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
status: draft
```

## Knowledge Unit: core.five_elements

```text
knowledge_id: core.five_elements
domain: chart_structure
category: core_symbol
title: Five Elements
statement: The five elements provide the base element classification used by stems, branches, hidden stems, and ten god mapping.
structured_facts:
- elements: wood, fire, earth, metal, water
allowed_usage:
- element classification
- generation/control relation lookup
- ten god mapping
- chart structure summary
forbidden_usage:
- direct good/bad judgement
- score generation
source_refs:
- v17_rebirth/backend/logic/configs/v17_core_constants.json
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
status: draft
```

## Knowledge Unit: core.yin_yang

```text
knowledge_id: core.yin_yang
domain: chart_structure
category: core_symbol
title: Yin Yang
statement: Yin/yang polarity is a base classification used by stems and ten god mapping.
structured_facts:
- polarity: yang, yin
allowed_usage:
- stem classification
- ten god mapping
forbidden_usage:
- personality conclusion
- auspicious/inauspicious judgement
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
status: draft
```

## Knowledge Unit: core.five_element_generation_control

```text
knowledge_id: core.five_element_generation_control
domain: chart_structure
category: element_relation
title: Five Element Generation and Control
statement: Element generation and control are structural relations between the five elements.
structured_facts:
- generates:
  - wood -> fire
  - fire -> earth
  - earth -> metal
  - metal -> water
  - water -> wood
- controls:
  - wood -> earth
  - earth -> water
  - water -> fire
  - fire -> metal
  - metal -> wood
allowed_usage:
- ten god mapping
- structural relation explanation
- feature extraction
forbidden_usage:
- standalone conclusion
- fortune text
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.stem_element_yinyang

```text
knowledge_id: core.stem_element_yinyang
domain: chart_structure
category: core_mapping
title: Stem Element and Yin Yang Mapping
statement: Each heavenly stem maps to one element and one polarity.
structured_facts:
- 甲: wood, yang
- 乙: wood, yin
- 丙: fire, yang
- 丁: fire, yin
- 戊: earth, yang
- 己: earth, yin
- 庚: metal, yang
- 辛: metal, yin
- 壬: water, yang
- 癸: water, yin
allowed_usage:
- pillar metadata
- day master classification
- ten god mapping
forbidden_usage:
- direct narrative
- direct fortune
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.branch_main_elements

```text
knowledge_id: core.branch_main_elements
domain: chart_structure
category: core_mapping
title: Branch Main Element Mapping
statement: Each earthly branch has a primary hidden stem that can be used for simplified branch element classification.
structured_facts:
- 子: 癸
- 丑: 己
- 寅: 甲
- 卯: 乙
- 辰: 戊
- 巳: 丙
- 午: 丁
- 未: 己
- 申: 庚
- 酉: 辛
- 戌: 戊
- 亥: 壬
allowed_usage:
- simplified branch element classification
- chart structure summary
forbidden_usage:
- replacing full hidden stem analysis
- direct conclusion
source_refs:
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
status: draft
```

## Knowledge Unit: core.ten_god_mapping

```text
knowledge_id: core.ten_god_mapping
domain: chart_structure
category: ten_god
title: Ten God Mapping
statement: Ten gods are derived from the relationship between the day master stem and another stem by element relation and polarity.
structured_facts:
- same element + same polarity -> peer
- same element + opposite polarity -> rob_wealth
- day generates target + same polarity -> eating_god
- day generates target + opposite polarity -> hurting_officer
- day controls target + same polarity -> indirect_wealth
- day controls target + opposite polarity -> direct_wealth
- target controls day + same polarity -> seven_killings
- target controls day + opposite polarity -> direct_officer
- target generates day + same polarity -> indirect_resource
- target generates day + opposite polarity -> direct_resource
allowed_usage:
- ten god count
- ten god feature extraction
- evidence template source
forbidden_usage:
- standalone theme conclusion
- wealth/career/relationship judgement
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.hidden_stems

```text
knowledge_id: core.hidden_stems
domain: chart_structure
category: hidden_stem
title: Hidden Stems
statement: Earthly branches contain hidden stems that may support root and latent structure analysis.
structured_facts:
- hidden_stems table required
- hidden stems must be represented as structured facts
- hidden stems are latent unless surfaced by explicit structural conditions
allowed_usage:
- root detection
- hidden stem evidence
- latent structure feature extraction
forbidden_usage:
- direct high-level judgement
- treating all hidden stems as visible stems
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_static_basis.py
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
- v17_rebirth/docs/V17_CROSS_LAYER_INTERACTION_PROTOCOL.md
status: draft
```

## Knowledge Unit: core.pillar_structure

```text
knowledge_id: core.pillar_structure
domain: chart_structure
category: pillar
title: Four Pillar Structure
statement: A natal chart is represented through year, month, day, and hour pillars, each containing one stem and one branch.
structured_facts:
- pillar_names: year, month, day, hour
- each pillar has stem
- each pillar has branch
- day stem is the day master
allowed_usage:
- chart structure construction
- source binding
- pillar-level relation detection
forbidden_usage:
- direct life-stage conclusion
- direct domain prediction
source_refs:
- v17_rebirth/frontend/lib/v19/chartStructureTypes.ts
- v17_rebirth/backend/logic/core_engine/pillar_graph_kernel.py
status: draft
```

## Knowledge Unit: core.month_command

```text
knowledge_id: core.month_command
domain: chart_structure
category: seasonal_structure
title: Month Command
statement: The month branch is a primary seasonal context input for structure analysis.
structured_facts:
- month branch is a seasonal context source
- month command may affect strength features
- month command must remain a structural input, not a conclusion
allowed_usage:
- seasonal feature extraction
- strength-context evidence
forbidden_usage:
- direct yongshen judgement
- direct favorable/unfavorable judgement
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_engine.py
- v17_rebirth/backend/logic/L2_structure_patterns/ziping_family.py
- v17_rebirth/backend/logic/configs/classical.ziping.month_command.v1.json
status: draft
```

## Knowledge Unit: core.root_strength

```text
knowledge_id: core.root_strength
domain: chart_structure
category: root_structure
title: Root Strength
statement: A visible stem may receive structural support from branch hidden stems and related root conditions.
structured_facts:
- root evidence depends on stem-to-hidden-stem relation
- root evidence must identify source branch
- root evidence must remain structural
allowed_usage:
- strength evidence
- rooted stem feature extraction
forbidden_usage:
- direct body strong/body weak conclusion without a separate reviewed protocol
- score generation
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/ten_gods_static_basis.py
- v17_rebirth/backend/logic/L0_physics_fields/foundation_projection.py
- v17_rebirth/docs/V17_TEN_GODS_ENERGY_DECOMPOSITION_PROTOCOL_2026-04-21.md
status: draft
```

## Knowledge Unit: core.visible_and_hidden_layers

```text
knowledge_id: core.visible_and_hidden_layers
domain: chart_structure
category: layer_boundary
title: Visible and Hidden Layer Boundary
statement: Visible stems, branches, hidden stems, and surfaced structures must remain distinct layers unless explicit surfacing conditions are met.
structured_facts:
- visible stem layer
- earthly branch layer
- hidden stem layer
- surfaced manifestation layer
allowed_usage:
- preventing cross-layer overreach
- source binding
- evidence audit
forbidden_usage:
- treating hidden stems as visible stems by default
- deriving high-level ten god conflicts from hidden stems alone
source_refs:
- v17_rebirth/docs/V17_CROSS_LAYER_INTERACTION_PROTOCOL.md
status: draft
```

## Knowledge Unit: core.six_combination

```text
knowledge_id: core.six_combination
domain: chart_structure
category: branch_relation
title: Six Combination
statement: Six combination is a structural pair relation between earthly branches.
structured_facts:
- 子丑
- 寅亥
- 卯戌
- 辰酉
- 巳申
- 午未
allowed_usage:
- relation detection
- Time Structure relations
- evidence binding
forbidden_usage:
- direct good/bad judgement
- direct fortune conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
- v17_rebirth/backend/logic/L1_atomic_ops/six_harmony.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.six_clash

```text
knowledge_id: core.six_clash
domain: chart_structure
category: branch_relation
title: Six Clash
statement: Six clash is a structural pair relation between earthly branches.
structured_facts:
- 子午
- 丑未
- 寅申
- 卯酉
- 辰戌
- 巳亥
allowed_usage:
- relation detection
- Time Structure relations
- evidence binding
forbidden_usage:
- direct disruption conclusion
- fortune text
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
- v17_rebirth/backend/logic/L1_atomic_ops/six_clash.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.three_harmony

```text
knowledge_id: core.three_harmony
domain: chart_structure
category: branch_relation
title: Three Harmony
statement: Three harmony is a structural branch group relation.
structured_facts:
- 申子辰 -> water
- 亥卯未 -> wood
- 寅午戌 -> fire
- 巳酉丑 -> metal
allowed_usage:
- relation detection
- structural combination evidence
- Time Structure relations
forbidden_usage:
- direct transformation conclusion without separate reviewed transform protocol
- direct fortune conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_structured.py
- v17_rebirth/backend/logic/L1_atomic_ops/three_harmony.py
- v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
status: draft
```

## Knowledge Unit: core.three_meeting

```text
knowledge_id: core.three_meeting
domain: chart_structure
category: branch_relation
title: Three Meeting
statement: Three meeting is a seasonal branch group relation.
structured_facts:
- 寅卯辰 -> wood
- 巳午未 -> fire
- 申酉戌 -> metal
- 亥子丑 -> water
allowed_usage:
- relation detection
- seasonal structure evidence
forbidden_usage:
- direct judgement
- direct domain conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_structured.py
- v17_rebirth/backend/logic/L1_atomic_ops/three_meeting.py
status: draft
```

## Knowledge Unit: core.branch_penalty

```text
knowledge_id: core.branch_penalty
domain: chart_structure
category: branch_relation
title: Branch Penalty
statement: Branch penalty is a structural relation family that must be detected separately from clash, combination, harm, and break.
structured_facts:
- penalty relations require explicit pair/group tables
- penalty detection must identify participating branches
allowed_usage:
- relation detection
- risk feature input after reviewed protocol
forbidden_usage:
- direct risk conclusion in Core layer
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
- v17_rebirth/backend/logic/L2_structure_patterns/triple_branch_penalty.py
status: draft
```

## Knowledge Unit: core.six_harm

```text
knowledge_id: core.six_harm
domain: chart_structure
category: branch_relation
title: Six Harm
statement: Six harm is a branch relation family that must remain a structural fact until interpreted by a reviewed inference layer.
structured_facts:
- harm relations require explicit pair table
- detection output must identify participating branches
allowed_usage:
- relation detection
- evidence binding
forbidden_usage:
- direct hidden risk conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
- v17_rebirth/backend/logic/L1_atomic_ops/six_pierce.py
status: draft
```

## Knowledge Unit: core.six_break

```text
knowledge_id: core.six_break
domain: chart_structure
category: branch_relation
title: Six Break
statement: Six break is a branch relation family that must remain a structural fact until interpreted by a reviewed inference layer.
structured_facts:
- break relations require explicit pair table
- detection output must identify participating branches
allowed_usage:
- relation detection
- evidence binding
forbidden_usage:
- direct damage conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/relation_geometry_pairs.py
- v17_rebirth/backend/logic/L1_atomic_ops/six_break.py
status: draft
```

## Knowledge Unit: core.stem_fusion

```text
knowledge_id: core.stem_fusion
domain: chart_structure
category: stem_relation
title: Stem Fusion
statement: Heavenly stem fusion is a stem pair relation; transformation state must not be assumed from pair presence alone.
structured_facts:
- 甲己
- 乙庚
- 丙辛
- 丁壬
- 戊癸
- pair detection and transformation assessment are separate steps
allowed_usage:
- stem relation detection
- transform-protocol input
forbidden_usage:
- assuming transformation from pair hit alone
- direct conclusion
source_refs:
- v17_rebirth/backend/logic/L1_atomic_ops/stem_fusion.py
- v17_rebirth/backend/logic/L1_atomic_ops/stem_fusion_geometry.py
- v17_rebirth/backend/logic/configs/l1.physics.op_stem_fusion.json
status: draft
```

## Knowledge Unit: core.vault_structure

```text
knowledge_id: core.vault_structure
domain: chart_structure
category: storage_structure
title: Vault Structure
statement: 辰, 戌, 丑, 未 may function as storage branches for element-specific structural material.
structured_facts:
- 辰: water vault
- 戌: fire vault
- 丑: metal vault
- 未: wood vault
allowed_usage:
- storage branch detection
- structural evidence
forbidden_usage:
- wealth conclusion
- opened/closed judgement without reviewed relation context
source_refs:
- v17_rebirth/backend/logic/knowledge/bazi_symbolic_primitives.v1.json
- v17_rebirth/backend/logic/L1_atomic_ops/muku_gate.py
status: draft
```

## Knowledge Unit: core.chang_sheng_12

```text
knowledge_id: core.chang_sheng_12
domain: chart_structure
category: lifecycle_stage
title: Twelve Growth Stages
statement: The twelve growth stages are structural lifecycle-stage labels used as feature inputs, not standalone predictions.
structured_facts:
- chang_sheng_12 table required
- output must be stage labels and source bindings
allowed_usage:
- lifecycle-stage feature extraction
- structure evidence
forbidden_usage:
- direct fortune conclusion
- direct good/bad judgement
source_refs:
- v17_rebirth/backend/logic/L0_physics_fields/chang_sheng_12.py
- v17_rebirth/backend/logic/configs/l1.physics.op_status.json
status: draft
```

## Knowledge Unit: core.time_structure_context

```text
knowledge_id: core.time_structure_context
domain: chart_structure
category: time_structure
title: Time Structure Context
statement: Luck cycle and flow year are time-context structures for later inference; they are not prediction conclusions.
structured_facts:
- natal chart remains the base structure
- luck_cycle may provide background time context
- flow_year may provide selected-year structure
- time relations must be represented as clashes and combinations before inference
allowed_usage:
- TimeContext construction
- FlowYear relation display
- P5 time-aware inference input
forbidden_usage:
- direct flow-year prediction
- direct ResultCard modification in P4
- direct fortune text
source_refs:
- docs/v19_ui_prototype.md
- v17_rebirth/frontend/lib/v19/timeStructureTypes.ts
- v17_rebirth/frontend/lib/v19/timeStructureEngine.ts
status: draft
```

## Knowledge Unit: core.cross_layer_boundaries

```text
knowledge_id: core.cross_layer_boundaries
domain: chart_structure
category: layer_boundary
title: Cross Layer Boundaries
statement: Heavenly stem, earthly branch, hidden stem, and surfaced manifestation layers must be kept separate to prevent invalid inference.
structured_facts:
- stem layer: visible stems and stem relations
- branch layer: branch relations and branch structures
- hidden stem layer: latent branch contents and root support
- manifestation layer: explicitly surfaced structure only
allowed_usage:
- verifier checks
- inference input validation
- evidence source classification
forbidden_usage:
- hidden stem overreach
- branch relation directly becoming stem-layer judgement
- legacy plugin shortcut inference
source_refs:
- v17_rebirth/docs/V17_CROSS_LAYER_INTERACTION_PROTOCOL.md
status: draft
```

## Explicitly Excluded Legacy Assets

The following legacy assets are not migrated into Core Knowledge Units v1:

```text
classical.pattern.*
classical.ziping.yongshen.v1
classical.ziping.balance.v1 judgement outputs
classical.blind.*
xiangfa theme outputs
shensha judgement
wealth_code_knowledge.v1.json
wealth domain rules
match_ratio configs
plugin settlement configs
conflict-resolution weights
narrative prompt contracts
```

Reason:

```text
They contain judgement, inference, weights, domain conclusions, or narrative behavior.
Core v1 only accepts foundational structure.
```

## Next Step

```text
1. Review this draft with analyst.
2. Convert approved units to structured JSON seed.
3. Seed V19 Knowledge Kernel as draft/reviewed units.
4. Keep V18.1 wealth knowledge separate as domain knowledge.
```
