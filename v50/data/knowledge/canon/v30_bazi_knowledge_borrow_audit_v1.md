# V30 Bazi Knowledge Borrow Audit v1

Status: local source audit

Date: 2026-07-06

## Boundary

V50 remains a clean-room system.

V30 and older assets may be used only as:

1. Local source material for V50 Knowledge Canon.
2. Algorithm design reference.
3. Validation fixture inspiration.
4. Boundary / guardrail reference.

They must not be imported as V50 runtime dependencies.

```text
V30 asset
        ↓
manual extraction
        ↓
V50 Knowledge Card / Model Draft / Fixture
        ↓
validation
        ↓
Brain activation
```

Direct path is forbidden:

```text
V30 runtime code
        ↓
V50 production judgment
```

## Inventory Summary

| Asset group | Count / scale | Primary value |
| --- | ---: | --- |
| `qiazhi/docs/bazi_knowledge` | 69 files: 52 md, 17 json | Best source for V50 Canon, taxonomy, guardrails, topic boundaries |
| `qiazhi/docs/bazi_knowledge/packs` | 14 packs, 379 draft knowledge items | Convertible into Knowledge Cards after normalization |
| `qiazhi/v30/v30/knowledge/library.py` | 72 `KnowledgeRulePortraitUnit` records | Runtime-safe boundary, portrait, question hook, training tag ideas |
| `qiazhi/v30/v30/rules/evidence.py` | 20 `RuleEvidenceSpec` records | Guardrail / evidence boundary reference, not judgment rules |
| `qiazhi/docs/bazi_knowledge/legacy_algorithm_review.md` | legacy algorithm audit | Strongest map for what can be refactored vs only referenced |
| `qiazhi/v30/docs/*` | many V30 planning / audit docs | Useful for architecture history, less useful as runtime source |

## High-Value Assets

### 1. Knowledge Taxonomy

Source:

- `qiazhi/docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md`
- `qiazhi/docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json`

Reusable for V50:

- Knowledge domain taxonomy.
- P0/P1 priority ordering.
- Runtime boundary language.
- Topic queues and conversion stages.

Best V50 target:

```text
V50 Knowledge Canon taxonomy
V50 Coverage Audit baseline
V50 Runtime Fill List
```

Do not reuse as:

```text
active rules
Brain verdicts
user-facing text
```

### 2. Ten-God Interaction Packs

Sources:

- `qiazhi/docs/bazi_knowledge/interaction/ten_god_interaction_topics_v1.md`
- `qiazhi/docs/bazi_knowledge/interaction/ten_god_conflict_constraint_mixed_topic_v1.md`
- `qiazhi/docs/bazi_knowledge/interaction/ten_god_pathway_second_wave_topic_v1.md`
- `qiazhi/docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json`
- `qiazhi/docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json`
- `qiazhi/docs/bazi_knowledge/packs/p32_ten_god_pathway_second_wave_knowledge_draft_seeds_v1.json`

Reusable for V50:

- Mechanism candidate list.
- Condition / counter-condition drafts.
- Must-not-say boundaries.
- Synthetic fixture groups.

Priority conversions:

| V30 object | V50 target |
| --- | --- |
| 伤官见官 | `bazi.mechanism.shangguan_jian_guan` deeper condition model |
| 官杀混杂 | `bazi.mechanism.guan_sha_mixed` Knowledge Card + fixture |
| 杀印相生 / 印化杀 | `bazi.mechanism.sha_yin_xiang_sheng` Knowledge Card + mechanism model |
| 财官相生 | `bazi.mechanism.cai_guan_xiang_sheng` Knowledge Card + mechanism model |
| 比劫夺财 / 比劫分财 | expand `peer_competes_for_wealth` conditions |
| 财破印 / 财多坏印 | new conflict candidate, likely P1 |
| 官杀制比劫 / 官星护财 | future conflict-resolution mechanism |

Important V30 principle worth preserving:

```text
组合名不能直接等于断语。
先确认组合存在，再进入机制边界，再进入条件模型。
传统断语归档，不直接输出。
```

### 3. Branch / Timing Activation

Sources:

- `qiazhi/docs/bazi_knowledge/time_context/time_context_units_v1.md`
- `qiazhi/docs/bazi_knowledge/time_context/luck_flow_activation_units_v1.md`
- `qiazhi/docs/bazi_knowledge/time_context/branch_time_activation_first_wave_topic_v1.md`
- `qiazhi/docs/bazi_knowledge/packs/p35_branch_time_activation_first_wave_knowledge_draft_seeds_v1.json`

Reusable for V50:

- Luck / flow as time layer.
- Cross-layer relation trigger design.
- Relation hit vs relation effect boundary.
- Tomb/vault open-close conditions as candidates.

Best V50 target:

```text
Bazi Timing Activation Model
TimingResult fixtures
DecisionPolicy timing evidence
```

Priority conversions:

| V30 object | V50 target |
| --- | --- |
| 大运引动本命 | `bazi.timing.luck_year_activation` |
| 流年引动本命 | `bazi.timing.luck_year_activation` |
| 流年引动大运 | `bazi.timing.luck_year_activation` |
| 墓库开闭 | `bazi.storage.mu_ku` |
| 冲合刑害时间触发 | Timing / activation evidence |

### 4. Legacy Algorithm Review

Source:

- `qiazhi/docs/bazi_knowledge/legacy_algorithm_review.md`

This is the most useful local map for separating stable feature extractors from old judgment code.

Most reusable after refactor:

| Legacy asset described in V30 audit | V50 reuse mode |
| --- | --- |
| 天干/地支/五行/阴阳/十神映射 | constants / deterministic material engine |
| 藏干表与藏干权重 | Bazi material constants |
| 日主与十神计算 | pure function |
| 透干 / 通根 / 得令 | feature extractors |
| 六合 / 冲 / 害 / 破 / 刑 | branch relation geometry |
| 三合 / 三会 / 半合 / 拱合 | group relation geometry |
| 墓库 / 财库 | storage/vault structure feature |
| 大运 / 流年动态场 | timing activation protocol |
| 财富路径 / 财富库 / 泄漏点 | wealth evidence layer |

Reference only:

| Legacy asset | Reason |
| --- | --- |
| old strength verdicts | standards must be redesigned |
| old useful-god verdicts | too easy to overrule Brain |
| old pattern conclusions | high school-controversy risk |
| old narrative text | expression layer only, not evidence |
| old scores / impact ratios | old scale, must not become V50 confidence |

### 5. Hidden Attribute Design

Source:

- `qiazhi/v30/docs/V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md`

Reusable for V50:

- Hidden attributes as reality variables.
- Probe answers as evidence, not chart mutation.
- User dialogue as active evidence gathering.

Best V50 target:

```text
twin/HiddenAttribute
conversation/ProbeQuestion
training/conversation
```

Directly aligned with V50:

```text
User Answer
        ↓
Hidden Attribute
        ↓
Twin Overlay
        ↓
Brain Re-evaluation
```

## What Can Be Borrowed Now

### P0 Borrow List

1. `bazi_knowledge_taxonomy_master_zh_v1.md` as V50 Bazi taxonomy seed.
2. `legacy_algorithm_review.md` as algorithm reuse map.
3. `p28e`, `p28f`, `p32` packs as mechanism Knowledge Card source.
4. `p35` pack as timing / branch activation Knowledge Card source.
5. `V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md` as conversation / Twin design source.
6. `source_registry.py` as local classic-source-family map.
7. `rules/evidence.py` as guardrail / decision boundary reference.

### P1 Borrow List

1. `p33_pattern_expansion_first_wave_knowledge_draft_seeds_v1.json` for pattern candidates.
2. `p34_blind_lifa_expansion_first_wave_knowledge_draft_seeds_v1.json` for blind-method research only.
3. `p36_domain_application_first_wave_knowledge_draft_seeds_v1.json` for topic mapping boundaries.
4. `macro_pack.py` and `multidimensional_taxonomy.py` for user-topic / portrait dimensions.

### Not For Runtime Import

1. V30 API route handlers.
2. V30 LLM prompt / expression implementation.
3. V30 training activation code.
4. V30 admin projections.
5. Old narrative / report text.
6. Old confidence values or physics impact ratios.

## Runtime Gap Mapping

Current V50 missing P0 items that can be supported by V30 local assets:

| V50 gap | V30 local support | Suggested next action |
| --- | --- | --- |
| `bazi.timing.luck_year_activation` | `time_context/*`, `p35`, `legacy_algorithm_review.md` | Build Knowledge Cards + fixtures before model code |
| `bazi.storage.mu_ku` | `time_context/*`, `legacy_algorithm_review.md` | Build storage/vault feature contract |
| `bazi.mechanism.guan_sha_mixed` | `ten_god_conflict_constraint_mixed_topic_v1.md`, `p28e/p28f` | Convert to Knowledge Card + mechanism fixture |
| `bazi.mechanism.sha_yin_xiang_sheng` | `ten_god_interaction_topics_v1.md`, `p28e/p28f` | Convert to Knowledge Card + mechanism fixture |
| `bazi.mechanism.cai_guan_xiang_sheng` | `ten_god_conflict_constraint_mixed_topic_v1.md`, `p31b` manifest entries | Convert to Knowledge Card + mechanism fixture |
| `bazi.mechanism.weak_body_strong_wealth` | `strength_units_v1.md`, `legacy_algorithm_review.md` | Define strength evidence first, avoid direct verdict |
| `bazi.mechanism.strong_body_weak_wealth` | `strength_units_v1.md`, `wealth_units_v1.md` | Define strength evidence first, avoid direct verdict |
| `bazi.model.tiao_hou` | `useful_god/*`, `strength/*`, source registry climate source | Enter Character / adjustment layer, not final verdict |
| `bazi.model.ti_yong` | blind/lifa docs, hidden-factor docs | Research only before runtime |
| `bazi.model.flow_mainline` | interaction packs + legacy dynamic graph notes | Expand mechanism path model |

## Recommended Borrow Pipeline

### Step 1: Convert Local V30 Packs To Draft Knowledge Cards

Do not auto-activate.

Target first:

```text
p28e
p28f
p32
p35
```

Output:

```text
KnowledgeCardDraft
source_refs: local_v30
runtime_status: draft
requires_validation: true
```

Current conversion output:

```text
v50/data/knowledge/canon/v30_pack_knowledge_card_drafts_v1.jsonl
v50/data/knowledge/canon/v30_pack_knowledge_card_drafts_v1.md
v50/data/validation/fixtures/v30_pack_knowledge_card_drafts_v1.json
v50/data/validation/reports/v30_pack_knowledge_card_drafts_v1.md
```

Current converted scope:

```text
p28e: 24 drafts
p28f: 20 drafts
p32:  24 drafts
p35:  36 drafts
total: 104 drafts
```

P0 target IDs now covered as drafts:

```text
bazi.mechanism.shangguan_jian_guan
bazi.mechanism.guan_sha_mixed
bazi.mechanism.sha_yin_xiang_sheng
bazi.mechanism.cai_guan_xiang_sheng
bazi.mechanism.output_to_wealth
bazi.mechanism.output_controls_pressure
bazi.mechanism.peer_competes_for_wealth
bazi.storage.mu_ku
bazi.timing.luck_year_activation
```

### Step 2: Build Mechanism Fixtures

For every converted card:

```text
positive case
negative case
counter-condition case
must_not_say case
```

### Step 3: Promote Only After V50 Contract Exists

Promotion path:

```text
KnowledgeCardDraft
        ↓
Mechanism Model Draft
        ↓
Validation Fixture
        ↓
Brain Decision Fixture
        ↓
Runtime Fill
```

## Final Judgment

YES, V30 has substantial Bazi knowledge assets worth borrowing.

But the highest-value material is not old V30 runtime code. It is:

1. The Bazi knowledge taxonomy.
2. The ten-god mechanism packs.
3. The timing / branch activation packs.
4. The legacy algorithm reuse audit.
5. The hidden-attribute question design.
6. The rule boundary / guardrail records.

V50 should cite and convert these assets as local source material, not inherit them as live logic.
