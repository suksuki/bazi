# V30 Knowledge Source Inventory

Updated: 2026-05-21

## Purpose

V30 needs a larger multi-dimensional Bazi knowledge base, but it must stay independent from V20 runtime.

The rule is:

```text
V20 assets and public references
-> reviewed source inventory
-> V30-owned taxonomy
-> V30 pack conversion
-> synthetic + 518K validation
-> active V30 runtime consumption
```

Runtime must not import `v20.*` and must not read V20 runtime paths.

## Current V30 Knowledge Directory

```text
v30/knowledge/
  __init__.py
  library.py
  seed_registry.py
  loaders/__init__.py
  loaders/macro_pack.py
  packs/__init__.py
  packs/multidimensional_taxonomy.py

v30/rules/
  __init__.py
  evidence.py
```

Current runtime pack:

```text
pack_id: v30.krp.pack.core_runtime
pack_version: 2026-05-21
```

Current macro pack:

```text
pack_id: v30.knowledge.pack.core_macro_zh_v1
pack_version: 2026-05-21
taxonomy_version: v30.knowledge.multidimensional_taxonomy.20260521
```

## V20 Local Source Assets

Reusable as source material after conversion:

| Source | Reuse mode | Notes |
|---|---|---|
| `../v20/docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md` | convert to V30 pack | L0-L12 high-level Bazi knowledge outline. |
| `../v20/knowledge/macro_dimensions.py` | extract records then convert | Wealth, career, relationship, romance, health dimensions. |
| `../v20/knowledge/feature_model.py` | extract records then convert | Topic projection boundaries and feature model. |
| `../v20/knowledge/loader.py` | extract records then convert | Large catalog with applied topics and answer boundaries. |
| `../v20/knowledge/structure_mechanisms.py` | extract records then convert | Structure path mechanisms such as output-controls-authority and output-generates-wealth. |
| `../v20/rules/catalog.py` | extract records then convert | Rule concepts for V30 `RuleEvidenceSpec` and policy candidates. |
| `../v20/validation/rule_portrait_batch.py` | convert to V30 synthetic cases | Representative wealth/career/relationship validation cases. |
| `../v20/interaction/latent_event_calibration.py` | convert to V30 hidden-factor cases | Wealth, career, relationship, stress/recovery latent event calibration. |

These are not runtime dependencies.

## Public Reference Sources

Public references are cross-check material only; V30 should not copy long text from them.

| Source | Use |
|---|---|
| https://en.wikipedia.org/wiki/Four_Pillars_of_Destiny | Cross-check Four Pillars and Ten Gods terminology. |
| https://zh.wikipedia.org/wiki/%E5%85%AB%E5%AD%97%E5%91%BD%E5%AD%A6 | Cross-check Chinese terminology and pillar/palace associations. |

Search results also show common public grouping around Ten Gods as peer/output/wealth/authority/resource and their career, wealth, and relationship interpretations. V30 should treat these as reference categories, not as final runtime claims.

## V30 Multi-Dimensional Taxonomy

The first V30-owned taxonomy lives at:

```text
v30/knowledge/packs/multidimensional_taxonomy.py
```

Current dimensions:

| Dimension | Domain | Scope |
|---|---|---|
| 基础八字 | `foundation` | 排盘事实、五行、十神、强弱、格局、用神、地支、岁运。 |
| 财富 | `wealth` | 财星显隐、食伤生财、财库、比劫分夺、承载、现金流、资产主题。 |
| 事业 | `career` | 官杀规则、印星平台、食伤表达、格局承接、学业考试、创业管理。 |
| 关系 | `relationship` | 人际、合作、比劫互动、资源分配、宫位互动、家庭父母、子女家庭。 |
| 感情 | `romance` | 伴侣星、夫妻宫、日支、合冲引动、亲密关系边界。 |
| 健康 | `health` | 五行偏性、寒暖燥湿、压力恢复、作息节律、医疗禁断边界。 |
| 隐藏属性与放大因子 | `hidden_factor` | 特殊年份、重复状态、边界事件、用户反馈校准。 |

## Import Rule

Allowed:

```text
Read V20 source material
Extract records
Normalize into V30 schema
Write V30-owned pack files
Validate with synthetic + 518K
Runtime reads only V30 pack/artifact
```

Not allowed:

```text
from v20.xxx import ...
Runtime reads ../v20/...
V30 API depends on V20 DB/Redis/runtime
V20 rule output becomes V30 verdict without validation
```

## Next Conversion Target

The next mainline conversion target is:

```text
../v20/knowledge/macro_dimensions.py
../v20/knowledge/feature_model.py
../v20/knowledge/structure_mechanisms.py
-> v30/knowledge/packs/multidimensional_taxonomy.py
-> v30/knowledge/loaders/macro_pack.py
-> Runtime policy_effect.core_macro_pack_summary
-> synthetic cases for wealth/career/relationship/romance/health
```

First loader slice completed:

- `load_core_macro_pack()` builds a V30-owned macro pack from the taxonomy.
- `summarize_core_macro_pack()` exposes domains, active domains, hooks, portrait dimensions, training tags, and boundary count.
- `build_macro_dimension_signals()` emits runtime-consumable macro dimension signals with evidence IDs and boundaries.
- Runtime now exposes `question_plan.policy_effect.core_macro_pack_summary`.
- Runtime now exposes `question_plan.policy_effect.macro_dimension_signals`.
- Live real API confirmed all 7 macro domains are present in `v30.knowledge.pack.core_macro_zh_v1`.
