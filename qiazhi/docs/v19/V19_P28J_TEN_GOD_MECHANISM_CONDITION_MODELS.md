# V19 P28J 十神组合机制条件模型

## 目标

P28J 批量处理 P28H 剩下的机制类候选，把它们从“知识/规则候选”推进到“可测试的条件模型”。P31B 已把新增的印化杀、财官相生一并纳入本链路。

本阶段不启用机制规则。原因很明确：机制类知识不是只看“同见”，还必须验证来源层、强弱承载、同层作用、救应/反制路径、宫位语境和时间层。

## 批量结果

| 指标 | 数量 |
| --- | ---: |
| 机制候选 | 20 |
| 条件模型 | 20 |
| 可直接启用 | 0 |
| 阻断等待 P28K 合成回归 | 20 |

按家族分布：

- direct_conflict：3
- constraint_deprivation：6
- mixed_structure：1
- selection_rescue：10

## 通用条件轴

每条机制候选都必须具备以下条件轴：

- source_layer：区分透干、藏干、本命、大运、流年来源。
- capacity_strength：检查月令、根气、印比支持、克泄耗压力。
- same_layer_action：确认作用双方是否在同一可作用层。
- palace_position：记录发生柱位和宫位语境。
- answer_boundary：只输出结构路径，不输出吉凶、应期、职业、健康、财富断语。

## 专题条件轴

P28J 额外补了专题条件轴：

- 枭神夺食：resource_controls_output_target
- 财滋杀：wealth_feeds_pressure_boundary
- 印化杀：seal_transform_kill_capacity
- 合杀留官 / 合官留杀：combine_effectiveness_and_keep_remove_path
- 羊刃驾杀：blade_control_pressure_model
- 伤官配印：output_resource_balance
- 财生官：wealth_to_official_continuity
- 财官相生：wealth_official_continuity
- 食伤生财：output_to_wealth_continuity

## 合成数据要求

P28K 必须为每条机制生成正反碰撞样本。最低要求包括：

- 透干成立 vs 仅藏干背景
- 本命成立 vs 仅大运/流年触发
- 承载力足 vs 承载力不足
- 同层可作用 vs 跨层不可直接作用
- 有救应/制化路径 vs 无救应路径
- 路径连续 vs 路径断裂

财富相关机制还必须加入：

- 财星可达 vs 财星被冲合牵制

合化去留相关机制还必须加入：

- 合化/去留条件成立 vs 只有合的关系名

羊刃驾杀还必须加入：

- 禄刃与七杀压力同见并可作用 vs 只有禄刃背景

## 代码入口

```text
v19.synthetic_validation.ten_god_conflict_matrix.build_p28j_ten_god_mechanism_condition_models
```

输出是条件模型注册表，不改变运行态，不启用机制规则。

## 下一步

P28K：按照 P28J 的 synthetic_pair_requirements 批量生成正反合成盘，跑精准命中、误触发、漏触发和回答文本禁词回归。只有通过 P28K 的机制，才能进入下一轮 smart gate。
