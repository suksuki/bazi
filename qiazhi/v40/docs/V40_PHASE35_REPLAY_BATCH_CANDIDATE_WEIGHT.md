# V40 Phase 35: Replay Batch Candidate Weight Gate

Date: 2026-06-30

## 目标

把 `TrainingReplayBatchSummary` 接入候选权重登记链路，让命理师反馈和训练样本回放不再停留在验证报表里。

本阶段新增：

```text
build_candidate_weight_version_from_replay_batch
POST /api/v40/weights/candidates/from-replay-batch
```

## 设计原则

Replay batch 的 `approve` 只代表：

```text
反馈样本可以被当前 runtime 找回
反馈目标覆盖率达标
反馈方向与候选输出一致
```

它不代表：

```text
生产权重已经生效
最终命理判断已经改变
用户报告会立刻变化
```

因此 Phase 35 只生成：

```text
GlobalWeightVersion(active=false)
```

后续仍必须经过 release readiness、Admin/Control Plane 风险展示和显式激活。

## 输入

```text
TrainingReplayBatchSummary(recommendation=approve)
weight_version_id
source_training_run_id
release_gate_id
```

要求：

- `recommendation=approve`
- `production_write_allowed=false`
- `replay_count > 0`
- `release_gate_id` 非空

不满足条件时返回 `422`。

## 输出

```text
GlobalWeightVersion(
  active=false,
  source_training_run_id=...,
  release_gate_id=...
)
```

API response 明确声明：

```text
writes_v30_state=false
writes_v40_production=false
```

## 边界

- 不写 V30。
- 不激活 V40 production weight。
- 不改变四柱、大运、流年等命盘事实。
- 不让 LLM 当训练裁判。
- 不让 replay batch 绕过 release readiness。

## 完成度更新

Phase 35 后，V40 当前估算：

```text
overall: ~67%
architecture: ~86%
user beta: ~58%
training validation: ~68%
v30 replacement: ~45%
```

`/admin/v40` 顶部 `V40 Completion` 面板会通过 `/admin/v40/api/project-status` 每 15 秒刷新。

## 下一步

Phase 36:

```text
release readiness 同时聚合 evaluation batch 与 replay batch
```
