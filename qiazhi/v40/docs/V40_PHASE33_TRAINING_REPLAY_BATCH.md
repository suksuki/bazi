# V40 Phase 33: Training Replay Batch

Date: 2026-06-30

## 目标

Phase 32 可以 replay 单条 `TrainingExampleV2`。本阶段把多条 replay 聚合成 batch summary：

```text
TrainingExampleReplayResult[]
  -> TrainingReplayBatchSummary
  -> batch recommendation
```

这一步是 candidate weight 之前的前置门禁。

## 新增合约

```text
TrainingReplayBatchSummary
```

核心字段：

- `replay_count`
- `passed_count`
- `review_count`
- `blocked_count`
- `average_feedback_alignment_score`
- `average_target_coverage_rate`
- `failed_reason_counts`
- `recommendation`

## 推荐规则

```text
有 blocked -> reject
全部 passed -> approve
其他情况 -> needs_review
```

空 batch 不允许创建。

## 新增 API

```text
POST /api/v40/training/replay-batches
GET  /api/v40/training/replay-batches
```

## 新增表

```text
v40_training_replay_batches
```

## Admin

`/admin/v40` 的 Training Feedback 增加：

- `training_replay_batches`
- `latest_training_replay_batches`

## 边界

- 不写 V30。
- 不写 V40 production weight。
- 不改 chart facts。
- 不让 LLM 评判 replay。
- `approve` 只代表“这批反馈 replay 具备进入候选训练的资格”，不是发布生产权重。

## 测试

```text
tests/test_v40_phase33_training_replay_batch.py
```

覆盖：

- 全部 replay passed 时 batch approve。
- 混入 review 时 batch needs_review。
- API 可以保存和查询 batch。
- schema / repository / admin / manifest 只使用 V40 边界。

## 下一步

1. Candidate weight 生成时可消费 approved replay batch。
2. Release readiness 聚合 evaluation batch 与 replay batch。
3. Admin 增加 replay batch 筛选和详情视图。
