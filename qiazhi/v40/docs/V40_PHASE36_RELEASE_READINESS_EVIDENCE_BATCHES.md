# V40 Phase 36: Release Readiness Evidence Batches

Date: 2026-06-30

## 目标

把发布准备度从 evaluation-only 扩展为双证据聚合：

```text
EvaluationBatchSummary
TrainingReplayBatchSummary
  ↓
ReleaseReadinessSummary
```

这一步解决一个关键边界：V40 不能只因为 evaluation batch 通过就认为候选权重可以上线，也不能只因为命理师反馈 replay 通过就认为生产可用。两条证据必须一起进入 release readiness。

## 新增入口

```text
build_release_readiness_from_evidence_batches
POST /api/v40/release-readiness/from-evidence-batches
```

旧入口仍保留：

```text
POST /api/v40/release-readiness/from-batches
```

它继续服务历史 evaluation-only 流程，不被破坏。

## 推荐规则

新入口的 approve 条件：

- 至少有一个 evaluation batch。
- 至少有一个 replay batch。
- 所有 batch 都是 `recommendation=approve`。
- 聚合平均分不低于 `0.82`。
- 没有失败原因。

缺少 evaluation 或 replay 时：

```text
recommendation=needs_review
failed_reason_counts.missing_evaluation_batch = 1
failed_reason_counts.missing_replay_batch = 1
```

存在 reject / rollback 时：

```text
recommendation=reject
```

## 分数

Evaluation batch 使用：

```text
average_overall_score
```

Replay batch 使用：

```text
(average_feedback_alignment_score + average_target_coverage_rate) / 2
```

最终 `average_batch_score` 是所有证据分数的平均值。

## 边界

- 不写 V30。
- 不激活 V40 production weight。
- 不改变 chart facts。
- 不让 LLM 当 judge。
- 不让单一证据流直接进入生产。

## 完成度更新

Phase 36 后，V40 当前估算：

```text
overall: ~69%
architecture: ~88%
user beta: ~58%
training validation: ~72%
v30 replacement: ~47%
```

实时查看：

```text
GET /api/v40/project/status
GET /admin/v40/api/project-status
```

Admin 页面顶部 `V40 Completion` 每 15 秒刷新。

## 下一步

Phase 37:

```text
Admin 展示 candidate weight 来源、readiness 风险、回滚路径和激活条件。
```
