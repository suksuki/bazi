# V40-RC2 BatchTrainerV1

Date: 2026-07-01

## 当前完成度判断

V40 有两个完成度：

```text
Architecture Completion: 98%
Mingli Depth Index: 51%
```

后续主线不再追逐架构完成度，而是补齐命理纵深。

## 本轮主线

本轮目标是实现：

```text
TrainingLabelEvent
→ TrainingAttribution
→ BatchTrainerV1
→ Active TrainablePolicyRegistry
→ TrainingImpactDiff
→ Runtime policy_version_used
```

也就是让 V40 从“可记录反馈”推进到“训练后直接生效的可回滚策略”。

## 已实现

新增：

```text
BatchTrainerV1Result
build_batch_trainer_v1
POST /api/v40/training/batch-trainer-v1
```

BatchTrainerV1 能做：

- 聚合 `TrainingAttribution.affected_trainable_refs`。
- 根据 `TrainingLabelEvent.label / confidence / local_only` 计算有限 delta。
- 自动创建缺失的 `TrainableUnit`。
- 输出 active `TrainablePolicyRegistry`。
- 输出 `TrainingImpactDiff`。
- 默认把新 `TrainablePolicyRegistry` 标记为 active。
- 保存 previous registry / previous policy，支持回滚和补救。
- 跳过 fact refs。
- 将 local-only feedback 降权。
- 默认 `release_recommendation=needs_review` 只表示需要继续观察，不阻止训练策略生效。

## 不做

BatchTrainerV1 不做：

- 不改命盘事实。
- 不裸写无法回滚的生产权重。
- 不让 LLM 参与训练判断。
- 不直接替换 DecisionEngine。

## 训练范围

第一版只支持简单、可解释的 policy 调整：

```text
source_weight
rule_weight
path_weight
claim_score
conflict_policy
assertion_threshold
advice_priority
probe_voi
llm_acceptance
```

## API

```text
POST /api/v40/training/batch-trainer-v1
```

输入：

```text
training_run_id
base_registry
attributions
label_events
candidate_policy_version
persist_registry
persist_impact
```

输出：

```text
BatchTrainerV1Result
candidate_registry
impact
registry_persisted
impact_persisted
active_policy_applied
rollback_registry_id
```

默认持久化。`persist_registry=true` 时保存并激活新的 `TrainablePolicyRegistry`；`persist_impact=true` 时保存 `TrainingImpactDiff`。这是命理高迭代系统的默认模式：允许训练后直接生效，同时保留 previous registry、previous policy 和 impact diff 作为补救与回滚依据。

## 后续任务

已完成：

1. 持久化 `TrainablePolicyRegistry` 版本。
2. Runtime 记录 `policy_version_used`。
3. Admin 可读取 active/history policy registry。
4. BatchTrainerV1 默认训练后直接生效。

后续任务：

1. Acceptance Window 支持 `previous_policy vs active_policy` diff。
2. Admin 可从 replay batch 选择样本运行 BatchTrainerV1。
3. 增加一键回滚到 previous registry 的补救动作。
