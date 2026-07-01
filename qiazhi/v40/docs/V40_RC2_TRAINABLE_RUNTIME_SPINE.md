# V40-RC2 Trainable Runtime Spine

Date: 2026-07-01

## 核心原则

V40 的训练不是训练一个黑箱大脑来“学会算命”，而是让每个命理判断节点：

```text
可反馈
可归因
可调权
可验证
可回放
可回滚
```

底层边界：

```text
事实型基础模块只验证，不训练。
判断型基础模块可训练，但只能训练权重、阈值、排序、触发条件和显化映射。
```

## 不可训练的事实模块

这些属于 immutable facts：

- 四柱。
- 干支。
- 十神基础映射。
- 藏干。
- 节气。
- 大运。
- 流年。
- 合冲刑害破基础计算。
- 紫微宫位。
- 紫微星曜落宫。
- 生年四化。

它们可以有：

```text
standard_version
calculation_policy_version
golden cases
boundary cases
config switches
```

但用户反馈、LLM、命理师选择、训练流程都不能改命盘事实。

## 可训练对象

V40 第一批 `TrainableUnit`：

| Unit Type | 训练什么 | 不训练什么 |
| --- | --- | --- |
| `source_weight` | 来源信号可靠性 | 来源事实 |
| `rule_weight` | 规则权重和触发条件 | 规则事实本身 |
| `path_weight` | 做功路径强弱、阻断、通关 | 原局结构 |
| `claim_score` | 候选判断打分 | 用户断语 |
| `conflict_policy` | 分支冲突主次 | 反证消灭 |
| `assertion_threshold` | confirmed/supported/mixed 阈值 | 弱证据强断 |
| `advice_priority` | 建议排序和适配 | 脱离 Verdict 的 Advice |
| `probe_voi` | 什么时候问、问什么 | 为问而问 |
| `llm_acceptance` | 表达验收、修复和风格 | 命理裁决 |

## 新合约

本阶段新增：

```text
TrainableUnit
TrainablePolicyRegistry
TrainingAttribution
RuntimeSignal.trainable_refs
TrainingLabelEvent.affected_trainable_refs
```

`RuntimeSignal.trainable_targets` 保留兼容，但 `trainable_refs` 是新的语义名称。

## 训练链路

```text
RuntimeSignal
  -> trainable_refs
TrainingLabelEvent
  -> user_feedback / probe_answer / practitioner_selection / admin_label / real_outcome
TrainingAttribution
  -> signal / branch / verdict / advice / probe / trainable_refs
LocalOverlay
  -> current reading only
BatchTrainerV1
  -> candidate_policy_version
TrainingImpactDiff
  -> changed weights / thresholds / verdict / advice / probe
ReleaseGate
  -> approve / reject / needs_review / rollback
```

## Local First

单个用户反馈只能先进入当前 reading：

```text
TrainingLabelEvent(local_only=true)
LocalOverlay(global_update_allowed=false)
```

非本地训练必须：

```text
requires_batch_review=true
```

全局策略必须：

```text
candidate_policy_version
replay
golden case
regression
release gate
rollback version
```

## BatchTrainerV1 范围

第一版只做简单、可解释的训练：

```text
source_weight
rule_weight
advice_priority
probe_voi
assertion_threshold
```

不做：

- 端到端黑箱训练。
- LLM 直接学习命理裁决。
- 用户单次反馈直接改全局。
- 训练命盘事实。

## 验收 Gate

候选策略必须经过：

- Golden Case。
- Real Case Bank。
- Synthetic Case。
- Regression Case。
- Overclaim Gate。
- Advice Grounding Gate。
- Probe Yield Gate。
- Surface Leakage Gate。
- LLM Boundary Gate。

## Read Model

新增只读接口：

```text
GET /api/v40/project/trainable-runtime-spine
```

它展示：

- 不可训练事实模块。
- 可训练 unit types。
- 可训练模块边界。
- 反馈归因链路。
- 高迭代训练生效边界。
- 下一步 BatchTrainerV1 任务。

## 下一步任务

已完成：

1. 持久化 `TrainablePolicyRegistry` 版本。
2. Runtime 记录 `policy_version_used`。
3. 实现 `BatchTrainerV1`。
4. 把 `TrainingAttribution` 接入训练样本编译。
5. BatchTrainerV1 默认训练后直接生效，并保留 rollback registry。

后续：

1. Acceptance Window 增加 `previous_policy vs active_policy` diff。
2. Admin 展示 active policy 影响面和 rollback 入口。
3. 增加真实命例窗口的训练后补救记录。
