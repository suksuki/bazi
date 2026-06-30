# V40 Phase 10: Release Readiness And Activation Review

更新时间：2026-06-30

## 目标

把单个 batch 的候选结论提升为多 batch release readiness，并建立候选权重激活审核协议。

Phase 10 新增：

```text
ReleaseReadinessSummary
WeightActivationReview
POST /api/v40/release-readiness/from-batches
GET  /api/v40/release-readiness
POST /api/v40/weights/activation-reviews
GET  /api/v40/weights/activation-reviews
v40_release_readiness
v40_weight_activation_reviews
```

## Release Readiness

输入：

```text
EvaluationBatchSummary[]
```

输出：

```text
ReleaseReadinessSummary
```

聚合内容：

```text
batch_count
approved_batch_count
review_batch_count
rejected_batch_count
average_batch_score
failed_reason_counts
recommendation
```

只有所有 batch 都 approve、平均分达标、且没有失败原因时，readiness 才会给出 `approve`。

## Activation Review

输入：

```text
GlobalWeightVersion(active=false)
ReleaseReadinessSummary
```

输出：

```text
WeightActivationReview
```

即便 review decision 是 `approve`：

```text
activation_applied=false
production_write_allowed=false
```

Phase 10 只记录审核结果，不执行激活。

## 下一阶段

Phase 11 应进入：

1. Admin Console 独立前端；
2. candidate activation 执行端点，但必须需要显式人工动作和 rollback version；
3. synthetic case generator；
4. V40 原生命理引擎骨架；
5. V30 DTO batch export 工具。
