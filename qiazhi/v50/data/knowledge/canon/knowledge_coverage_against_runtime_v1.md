# Knowledge Coverage Against Runtime v1

Status: seed gap map

This document maps the first Internet Knowledge Canon seed against current V50 Runtime.

## Ready / Tested

- `bazi.mechanism.output_to_wealth`
- `bazi.mechanism.output_controls_pressure`
- `bazi.mechanism.peer_competes_for_wealth`
- `ziwei.foundation.twelve_palaces`
- `ziwei.foundation.four_transformations`
- `ziwei.topic.career_official_palace`
- `ziwei.topic.wealth_property_palace`
- `fusion.bazi_structure_ziwei_timing`

## Partial

- `bazi.foundation.wang_shuai_root_transparent`
- `bazi.relation.chong_he_xing_hai_po`
- `bazi.relation.sanhe_sanhui_liuhe`
- `bazi.mechanism.shangguan_jian_guan`
- `bazi.model.flow_mainline`
- `ziwei.foundation.major_stars_14`
- `ziwei.foundation.san_fang_si_zheng`
- `ziwei.timing.major_annual_cycle`

## Missing P0 Runtime Fill List

1. `bazi.timing.luck_year_activation`
2. `bazi.storage.mu_ku`
3. `bazi.mechanism.guan_sha_mixed`
4. `bazi.mechanism.sha_yin_xiang_sheng`
5. `bazi.mechanism.cai_guan_xiang_sheng`
6. `bazi.mechanism.weak_body_strong_wealth`
7. `bazi.mechanism.strong_body_weak_wealth`
8. `bazi.model.tiao_hou`
9. `bazi.model.ti_yong`
10. `bazi.model.flow_mainline` deeper scoring

## Not Recommended For Runtime Yet

- `bazi.model.ti_yong`: high value but low consensus; requires explicit model version.
- `bazi.model.tiao_hou`: important, but should first enter Structure / Character, not user-facing judgment.
- Advanced Ziwei flying transformations: future scope after basic four transformation evidence is stable.

## Conflict / Controversy List

- 旺衰 priority vs 格局 priority.
- 调候用神 vs 扶抑用神.
- 体用 definitions across schools.
- 墓库 open / close conditions.
- 伤官见官 as pure risk vs modern innovation / institution friction.
- Ziwei four transformation systems beyond basic year-stem transformations.

## Source Summary

Primary public sources used for seed cards:

- Four Pillars of Destiny: https://en.wikipedia.org/wiki/Four_Pillars_of_Destiny
- Heavenly Stems: https://en.wikipedia.org/wiki/Heavenly_Stems
- Earthly Branches: https://en.wikipedia.org/wiki/Earthly_Branches
- Sexagenary cycle: https://en.wikipedia.org/wiki/Sexagenary_cycle
- 三命通会: https://zh.wikisource.org/wiki/三命通會
- 渊海子平: https://zh.wikisource.org/wiki/淵海子平
- 滴天髓: https://zh.wikisource.org/wiki/滴天髓
- Zi Wei Dou Shu: https://en.wikipedia.org/wiki/Zi_wei_dou_shu
- 紫微斗数: https://zh.wikipedia.org/wiki/紫微斗数
- 紫微斗数全书: https://zh.wikisource.org/wiki/紫微斗數全書

## Local V30 Source Overlay

V30 contains reusable local Bazi knowledge assets that should be treated as local source material, not runtime dependencies.

See:

```text
qiazhi/v50/data/knowledge/canon/v30_bazi_knowledge_borrow_audit_v1.md
```

Key borrowable areas:

- Bazi taxonomy and knowledge directory from `qiazhi/docs/bazi_knowledge/catalog/`.
- Ten-god interaction / conflict / pathway packs from `qiazhi/docs/bazi_knowledge/packs/p28e`, `p28f`, and `p32`.
- Branch and luck-flow activation packs from `qiazhi/docs/bazi_knowledge/packs/p35`.
- Legacy algorithm reuse map from `qiazhi/docs/bazi_knowledge/legacy_algorithm_review.md`.
- Hidden attribute and probe design from `qiazhi/v30/docs/V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md`.

V50 may convert these into Knowledge Cards, fixtures, and model drafts after review.

V50 must not import V30 runtime modules directly.

## Final Review

DeepBeing Knowledge Canon v1 is a seed canon, not a Runtime rule package.

Next recommended Runtime phase:

```text
Bazi Timing + Core Mechanism Fill v1
```

Do not promote cards directly. Promotion path remains:

```text
Knowledge Card
        ↓
Model / Rule Draft
        ↓
Validation Fixture
        ↓
Synthetic Regression
        ↓
Brain Activation
```
