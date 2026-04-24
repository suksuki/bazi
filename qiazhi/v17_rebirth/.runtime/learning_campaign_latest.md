# V17 Auto Learning Campaign Report

日期：2026-04-23

- 协议：`v17.learning_campaign.v1`
- 主审：`codex`
- 复核：`analyst`
- 总状态：`green`
- 可自动应用参数：`False`
- 运行预算：`under_3_hours`

## Executive Review
- Codex 主审结论：当前学习活动全绿，建议保持参数冻结，不生成调参候选。
- 分析师复核建议：无需分析师介入；没有 gate / 法理 / 语义冲突项。
- LLM 复核建议：无需调用 LLM；本轮没有需要语义裁决的异常。
- 安全状态：`can_auto_apply=False`，所有参数候选仍为 review-only。

## Learning Value
- 本轮学习价值：`baseline_validated`
- 学习密度：`0.692`
- 已验证参数族：authority.core, climate_field, pattern_specialization, relation_dynamics.anhe, relation_dynamics.banhe_muwang, relation_dynamics.banhe_shengwang, relation_dynamics.chong, relation_dynamics.gonghe, relation_dynamics.hai, relation_dynamics.ke, relation_dynamics.liuhe, relation_dynamics.po, relation_dynamics.sanhe, relation_dynamics.sanhui, relation_dynamics.stem_fusion_transform, relation_dynamics.xing, relation_formation.anhe, relation_formation.banhe_muwang, relation_formation.banhe_shengwang, relation_formation.gonghe, relation_formation.liuhe, relation_formation.sanhe, relation_formation.sanhui, risk_matrix, work_authority_core
- 主要盲区：格局/专题样盘仍偏少，需要增加调候破格、格局互斥和混合格局。; 真实校盘基准仍偏薄：当前 3 例，尚不足以代表命理师审盘分歧。

## Scorecard
- Synthetic Batch：11/11 passed
- Extended Synthetic：38/38 passed
- Practitioner Benchmark：3/3 passed
- Findings：0
- High Priority Findings：0
- Parameter Experiments：0

## Coverage Matrix
- Synthetic Batch 覆盖：代表性关系、运流、冲害、调候场，共 11 例。
- Extended Synthetic 覆盖：base=26 / risk=2 / authority=3 / pattern=3 / core=4。
- Practitioner Benchmark 覆盖：真实复杂盘 3 例。

## Learning Signals
- `runtime.relation.banhe.interruption` · synthetic · top=正印/偏印/食神；families=anhe,banhe_muwang,liuhe,sanhui；climate=偏暖(thermal=0.39, moisture=0.02) · 参数族：`relation_formation.anhe`
- `l1.relation.stem_fusion.runtime` · synthetic · top=七杀/比肩/正官；families=banhe_muwang,liuhe,chong,hai；climate=偏燥(thermal=-0.15, moisture=-0.26) · 参数族：`relation_formation.banhe_muwang`
- `l0.static.rooted_peer` · synthetic · top=比肩/食神/正官；families=anhe,liuhe,sanhe,chong；climate=偏湿(thermal=0.24, moisture=0.28) · 参数族：`relation_formation.anhe`
- `l0.static.floating_peer` · synthetic · top=正官/伤官/七杀；families=anhe,liuhe,sanhe,chong；climate=偏暖(thermal=0.32, moisture=-0.42) · 参数族：`relation_formation.anhe`
- `l1.relation.anhe.baseline` · synthetic · top=劫财/偏印/正印；families=anhe,banhe_shengwang,liuhe,chong；climate=偏暖(thermal=0.47, moisture=-0.13) · 参数族：`relation_formation.anhe`
- `runtime.relation.liuhe.luck_background` · synthetic · top=正印/偏印/食神；families=banhe_muwang,liuhe,sanhui,hai；climate=偏暖(thermal=0.39, moisture=-0.01) · 参数族：`relation_formation.banhe_muwang`
- `runtime.relation.liuhe.flow_trigger` · synthetic · top=正印/偏印/伤官；families=banhe_muwang,liuhe,sanhui,hai；climate=偏暖(thermal=0.38, moisture=-0.01) · 参数族：`relation_formation.banhe_muwang`
- `l1.relation.banhe.muwang` · synthetic · top=伤官/劫财/正财；families=anhe,banhe_muwang,liuhe,hai；climate=偏暖(thermal=0.35, moisture=-0.29) · 参数族：`relation_formation.anhe`
- `real.audit.metal_mix_gengzi_bingwu` · practitioner · top=正官/伤官/七杀/食神；focus=巳酉丑三合金 / 子丑六合 / 子巳暗合 · 参数族：`practitioner_benchmark`
- `real.audit.metal_mix_xinchou_yiwei` · practitioner · top=七杀/伤官/比肩/正官；focus=辛金透干 / 丑支重叠 / 三合金满配 · 参数族：`practitioner_benchmark`
- `real.audit.fire_water_gengxu_bingwu` · practitioner · top=劫财/比肩/偏印/正官；focus=寅午戌三合火 / 子辰半合水 / 火水并存 · 参数族：`practitioner_benchmark`

## Next Hard Cases
- 构造“食伤制杀 vs 食伤生财”双主线抢权样盘，验证盲派体用与子平 authority 是否一致。
- 构造寒湿、炎燥两组极端调候样盘，验证 climate_field 是否只影响效率/稳定/优先级，不回写 L0 base。
- 构造 Level 3 soft bias 试图推翻 Level 1 hard constraint 的越权样盘，验证 authority gate。
- 新增 5 张命理师校盘基准，覆盖官杀混杂、财印交战、强弱与结构流通分歧。

## Plugin Governance Coverage
- 插件数：90
- 未分类插件：0
- Governance Class：
  - `climate_structure_enhancement`：4
  - `narrative_or_strategy`：1
  - `physical_foundation`：4
  - `physical_relation_operator`：24
  - `risk_guard`：4
  - `semantic_only_topic`：4
  - `soft_bias_topic`：5
  - `structure_enhancement`：37
  - `ziping_umbrella`：7
- Authority Level：
  - `level_0_physics`：4
  - `level_1_hard`：2
  - `level_1_relation`：24
  - `level_2_risk_guard`：4
  - `level_2_structure`：41
  - `level_2_ziping_axis`：5
  - `level_3_narrative`：1
  - `level_3_semantic`：4
  - `level_3_soft_bias`：5
- Learning Family Top：
  - `pattern_specialization`：37
  - `relation.general`：12
  - `ziping_authority`：7
  - `blind_theme`：5
  - `climate_field`：4
  - `l0_static_basis`：4
  - `risk_matrix`：4
  - `xiangfa_theme`：4
  - `relation.stem_fusion`：3
  - `narrative`：1
  - `relation.anhe`：1
  - `relation.banhe`：1

## Parameter Health
- 当前没有触发参数族异常，不建议为了“学习感”而调参。
- 本轮结论：冻结当前参数，继续积累更难的 synthetic / benchmark 样盘。

## Parameter Experiments
- 当前没有生成影子参数实验。

## Analyst Feedback Items
- （无）

## System Feedback Package
- 系统反馈：无异常，无需生成新的参数族调优任务。

## LLM Review Package
- 建议调用 LLM：`False`
- Payload Policy：`summarized_findings_only_no_raw_large_metadata`
- Forbidden Output：`direct_config_patch, authority_override, l0_l1_mutation`

## Safety Gates
- `sandbox_only`
- `do_not_write_real_config`
- `codex_primary_review_required`
- `analyst_review_for_uncertain_or_conflicting_cases`
- `manual_approval_required_before_apply`
