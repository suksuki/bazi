# V40 Phase 38: Shadow Compare Batch Risk

Date: 2026-06-30

## 目标

把 V30 -> V40 shadow compare 从单条对比扩展为批量迁移风险摘要。

新增：

```text
ShadowCompareBatchSummary
build_shadow_compare_batch_summary
POST /api/v40/shadow-compare/batch
```

## 输入

```text
batch_id
exports: V30ExportEnvelope[]
persist
```

每个 export 仍然必须是 plain JSON DTO：

```text
V30ExportEnvelope
```

V40 不 import V30 runtime，不读 V30 DB，不读 V30 Redis。

## 输出

```text
ShadowCompareBatchSummary
compares: ShadowCompareResult[]
runtime_refs
```

Summary 统计：

- compare_count
- passed_count
- review_count
- regression_count
- average_import_coverage_rate
- average_verdict_topic_overlap_rate
- product_projection_ready_rate
- failed_reason_counts
- recommendation

## 通过口径

单条 compare 通过条件：

- 没有 regression
- import coverage >= 0.9
- verdict topic overlap >= 0.8
- product projection ready
- leakage free

批量 summary：

- 有 regression -> reject
- 全部通过且无失败原因 -> approve
- 其他 -> needs_review

## 边界

- 不写 V30。
- 不写 V40 production。
- 不激活权重。
- 不把 shadow compare 当作最终产品验收。
- 不使用 LLM 当 judge。

## 完成度更新

Phase 38 后，V40 当前估算：

```text
overall: ~73%
architecture: ~91%
user beta: ~60%
training validation: ~75%
v30 replacement: ~55%
```

## 下一步

Phase 39:

```text
report-first UI 与命理师校准进入 beta 验收。
```
