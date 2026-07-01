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
→ Candidate TrainablePolicyRegistry
→ TrainingImpactDiff
→ Release Gate / Candidate Weight
```

也就是让 V40 从“可记录反馈”推进到“可生成候选策略”。

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
- 输出 candidate `TrainablePolicyRegistry`。
- 输出 `TrainingImpactDiff`。
- 跳过 fact refs。
- 将 local-only feedback 降权。
- 默认 `release_recommendation=needs_review`。

## 不做

BatchTrainerV1 不做：

- 不改命盘事实。
- 不写生产权重。
- 不激活 global policy。
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
persist_impact
```

输出：

```text
BatchTrainerV1Result
candidate_registry
impact
```

默认不持久化。即使 `persist_impact=true`，也只保存 `TrainingImpactDiff`，不保存 active policy，不写 production。

## 后续任务

1. 持久化 `TrainablePolicyRegistry` 版本。
2. Runtime 记录 `policy_version_used`。
3. Acceptance Window 支持 `baseline_policy vs candidate_policy` diff。
4. Admin 可从 replay batch 选择样本运行 BatchTrainerV1。
5. Release Gate 通过后再生成可激活的 `GlobalWeightVersion`。
