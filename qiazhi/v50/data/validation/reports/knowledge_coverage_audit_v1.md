# Knowledge Coverage Audit v1

## Final Conclusion

- Ready for LLM Synthetic Validation: **partial**
- Allowed topics: wealth, career
- Blocked topics: relationship, health, family, education
- Next recommended phase: LLM Synthetic Validation v1 with topic restrictions and visible blocked-topic reporting.

## Coverage Scores

| Domain | Score | Items | Status | High-risk gaps |
| --- | ---: | ---: | --- | --- |
| Bazi Foundation Coverage | 0.646 | 12 | implemented:1, missing:2, partial:4, tested:5 | 合冲刑害破, 三合 / 三会 / 六合, 墓库, 旺衰 / 得令 / 通根 / 透干 |
| Bazi Luck-Year Coverage | 0.0 | 7 | missing:7 | 大运介入, 流年触发, 冲合引动, 运年叠加, 阶段主题变化, 远近 / 宫位 / 原局优先级 |
| Bazi Mechanism Coverage | 0.222 | 18 | missing:13, partial:2, tested:3 | 杀印相生, 财官相生, 伤官见官, 官杀混杂, 财星入库, 身弱财旺 |
| Bazi Topic Mapping Coverage | 0.389 | 9 | missing:4, partial:3, tested:2 | 感情, 健康 |
| Evidence Coverage | 1.0 | 6 | tested:6 |  |
| Fusion Coverage | 0.917 | 6 | partial:1, tested:5 | 八字关系结构 vs 紫微夫妻宫 |
| Ziwei Foundation Coverage | 0.725 | 10 | implemented:3, missing:2, tested:5 | 宫干 |
| Ziwei Mechanism Coverage | 0.591 | 11 | missing:3, partial:3, tested:5 |  |
| Ziwei Time Coverage | 0.833 | 3 | partial:1, tested:2 |  |

## Must-fill Knowledge Gaps

- 合冲刑害破
- 三合 / 三会 / 六合
- 墓库
- 旺衰 / 得令 / 通根 / 透干
- 杀印相生
- 财官相生
- 伤官见官
- 官杀混杂
- 财星入库
- 身弱财旺
- 身旺财弱
- 调候
- 做功流通
- 体用
- 主线条 / 轨迹
- 大运介入
- 流年触发
- 冲合引动

## Audit Items

| Domain | Knowledge Item | Status | Runtime | Fixture | Risk | Source | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bazi Foundation Coverage | 天干 | tested | yes | yes | low | packages/core/engines/bazi/knowledge.py | Keep covered by regression. |
| Bazi Foundation Coverage | 地支 | tested | yes | yes | low | packages/core/engines/bazi/knowledge.py | Keep covered by regression. |
| Bazi Foundation Coverage | 藏干 | tested | yes | yes | low | packages/core/engines/bazi/knowledge.py | Keep covered by regression. |
| Bazi Foundation Coverage | 十神 | tested | yes | no | low | packages/core/engines/bazi/material_engine.py | Keep covered by regression. |
| Bazi Foundation Coverage | 五行 | tested | yes | no | low | packages/core/engines/bazi/knowledge.py | Keep covered by regression. |
| Bazi Foundation Coverage | 阴阳 | implemented | yes | no | medium | packages/core/engines/bazi/knowledge.py | Add fixture assertions for polarity-sensitive rules. |
| Bazi Foundation Coverage | 生克制化 | partial | yes | yes | medium | packages/core/engines/bazi/knowledge.py | Complete runtime semantics and add focused fixtures. |
| Bazi Foundation Coverage | 合冲刑害破 | partial | yes | no | high | packages/core/engines/bazi/knowledge.py | Only six clash / six harmony baseline exists; add 刑害破 coverage before relation-heavy judgments. |
| Bazi Foundation Coverage | 三合 / 三会 / 六合 | partial | no | no | high | packages/core/engines/bazi/knowledge.py | 六合 baseline exists; 三合 / 三会 are missing from runtime. |
| Bazi Foundation Coverage | 空亡 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Foundation Coverage | 墓库 | missing | no | no | high | - | Required before 财星入库 and storage-related wealth judgments. |
| Bazi Foundation Coverage | 旺衰 / 得令 / 通根 / 透干 | partial | yes | yes | high | packages/core/engines/bazi/material_engine.py | Complete runtime semantics and add focused fixtures. |
| Bazi Mechanism Coverage | 食伤生财 | tested | yes | yes | low | packages/core/flows/model.py | Keep covered by regression. |
| Bazi Mechanism Coverage | 食伤制杀 | tested | yes | yes | low | packages/core/flows/model.py | Keep covered by regression. |
| Bazi Mechanism Coverage | 杀印相生 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 财官相生 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 伤官见官 | partial | yes | no | high | packages/core/flows/model.py | Current output_controls_pressure can approximate pressure; it is not a dedicated 伤官见官 rule. |
| Bazi Mechanism Coverage | 官杀混杂 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 比劫夺财 | tested | yes | yes | low | packages/core/flows/model.py | Keep covered by regression. |
| Bazi Mechanism Coverage | 财星入库 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 印旺身强 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 身弱财旺 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 身旺财弱 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 羊刃驾杀 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 从格 / 假从 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 调候 | missing | no | yes | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 做功流通 | partial | yes | yes | high | packages/core/cognitive/mechanism_model.py | Complete runtime semantics and add focused fixtures. |
| Bazi Mechanism Coverage | 体用 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 家里 / 家外 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Mechanism Coverage | 主线条 / 轨迹 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 大运介入 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 流年触发 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 冲合引动 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 运年叠加 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 阶段主题变化 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 远近 / 宫位 / 原局优先级 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Luck-Year Coverage | 原局、大运、流年三层证据关系 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Topic Mapping Coverage | 事业 | tested | yes | yes | low | packages/core/cognitive/domain_mapping_model.py | Keep covered by regression. |
| Bazi Topic Mapping Coverage | 财富 | tested | yes | yes | low | packages/core/cognitive/domain_mapping_model.py | Keep covered by regression. |
| Bazi Topic Mapping Coverage | 感情 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Topic Mapping Coverage | 健康 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Topic Mapping Coverage | 学业 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Topic Mapping Coverage | 家庭 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Bazi Topic Mapping Coverage | 性格画像 | partial | no | no | medium | packages/core/portrait | Portrait exists as a boundary layer but is not driven by current Brain outputs in validation. |
| Bazi Topic Mapping Coverage | 风险 | partial | yes | yes | medium | packages/core/cognitive/domain_mapping_model.py | Complete runtime semantics and add focused fixtures. |
| Bazi Topic Mapping Coverage | 阶段建议 | partial | yes | yes | medium | packages/core/expression/experience_layer.py | Complete runtime semantics and add focused fixtures. |
| Ziwei Foundation Coverage | 十二宫 | tested | yes | no | low | packages/core/engines/ziwei/chart_builder.py | Keep covered by regression. |
| Ziwei Foundation Coverage | 主星 | implemented | yes | yes | medium | packages/core/engines/ziwei/knowledge.py | Add validation fixture coverage. |
| Ziwei Foundation Coverage | 辅星 | implemented | yes | no | medium | packages/core/engines/ziwei/knowledge.py | Add validation fixture coverage. |
| Ziwei Foundation Coverage | 四化 | tested | yes | yes | low | packages/core/engines/ziwei/knowledge.py | Keep covered by regression. |
| Ziwei Foundation Coverage | 三方四正 | implemented | yes | no | medium | packages/core/engines/ziwei/chart_builder.py | Add validation fixture coverage. |
| Ziwei Foundation Coverage | 宫干 | missing | no | no | high | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Ziwei Foundation Coverage | 命身宫 | tested | yes | no | low | packages/core/engines/ziwei/material_engine.py | Keep covered by regression. |
| Ziwei Foundation Coverage | 大限 | tested | yes | no | medium | packages/core/engines/ziwei/chart_builder.py | Keep covered by regression. |
| Ziwei Foundation Coverage | 流年 | tested | yes | no | medium | packages/core/engines/ziwei/chart_builder.py | Keep covered by regression. |
| Ziwei Foundation Coverage | 流月 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Ziwei Mechanism Coverage | 命宫画像 | partial | no | no | medium | packages/core/engines/ziwei/material_engine.py | Complete runtime semantics and add focused fixtures. |
| Ziwei Mechanism Coverage | 官禄事业 | tested | yes | no | low | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Mechanism Coverage | 财帛财富 | tested | yes | no | low | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Mechanism Coverage | 夫妻关系 | tested | yes | no | medium | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Mechanism Coverage | 疾厄健康 | tested | yes | no | medium | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Mechanism Coverage | 迁移外部机会 | tested | yes | no | medium | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Mechanism Coverage | 福德心理状态 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Ziwei Mechanism Coverage | 田宅资产 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Ziwei Mechanism Coverage | 父母 / 子女 / 兄弟 | missing | no | no | medium | - | Add knowledge model, runtime hook, and validation fixture before user-facing use. |
| Ziwei Mechanism Coverage | 大限主题 | partial | yes | yes | medium | packages/core/engines/ziwei/dynamic_evidence.py | Complete runtime semantics and add focused fixtures. |
| Ziwei Mechanism Coverage | 流年触发 | partial | yes | yes | medium | packages/core/engines/ziwei/dynamic_evidence.py | Complete runtime semantics and add focused fixtures. |
| Ziwei Time Coverage | 紫微短期压力 | tested | yes | no | low | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Time Coverage | 紫微主题激活 | tested | yes | yes | low | packages/core/engines/ziwei/dynamic_evidence.py | Keep covered by regression. |
| Ziwei Time Coverage | 紫微大限/流年并看 | partial | yes | yes | medium | packages/core/engines/ziwei/dynamic_evidence.py | Complete runtime semantics and add focused fixtures. |
| Fusion Coverage | 八字长期结构 vs 紫微阶段压力 | tested | yes | no | low | packages/core/brain/decision_policy.py | Keep covered by regression. |
| Fusion Coverage | 八字财富路径 vs 紫微财帛宫 | tested | yes | no | low | packages/core/brain/decision_policy.py | Keep covered by regression. |
| Fusion Coverage | 八字事业压力 vs 紫微官禄宫 | tested | yes | no | low | packages/core/brain/decision_policy.py | Keep covered by regression. |
| Fusion Coverage | 八字关系结构 vs 紫微夫妻宫 | partial | yes | no | high | packages/core/brain/decision_policy.py | Complete runtime semantics and add focused fixtures. |
| Fusion Coverage | 冲突时如何保留双证据 | tested | yes | no | low | packages/core/brain/decision_policy.py | Keep covered by regression. |
| Fusion Coverage | 一致时如何提升 confidence | tested | yes | no | low | packages/core/brain/decision_policy.py | Keep covered by regression. |
| Evidence Coverage | material_refs | tested | yes | no | low | packages/core/contracts/reasoning.py | Keep covered by regression. |
| Evidence Coverage | structure_refs | tested | yes | no | low | packages/core/contracts/reasoning.py | Keep covered by regression. |
| Evidence Coverage | flow_refs | tested | yes | no | low | packages/core/contracts/reasoning.py | Keep covered by regression. |
| Evidence Coverage | evidence_refs | tested | yes | yes | low | packages/core/cognitive/contracts.py | Keep covered by regression. |
| Evidence Coverage | must_not_say | tested | yes | no | low | packages/core/judgment/model.py | Keep covered by regression. |
| Evidence Coverage | user-facing verifier | tested | yes | no | low | packages/core/expression/verifier.py | Keep covered by regression. |
