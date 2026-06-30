# V40 Phase 9: Candidate Weight Version

更新时间：2026-06-30

## 目标

把 batch evaluation 的结果推进到“候选权重版本登记”，但仍不自动启用。

Phase 9 新增：

```text
GlobalWeightVersion candidate builder
POST /api/v40/weights/candidates/from-batch
GET  /api/v40/weights/candidates
v40_global_weight_versions
```

## 核心规则

只有 `EvaluationBatchSummary.recommendation=approve` 的 batch，才能登记候选权重版本。

即便登记成功：

```text
active=false
writes_v40_production=false
```

也就是说，Phase 9 完成的是：

```text
训练候选可追踪
门禁来源可追踪
候选版本可审计
```

不是：

```text
自动启用生产权重
自动覆盖测算逻辑
自动修改 chart facts
```

## API

```text
POST /api/v40/weights/candidates/from-batch
GET  /api/v40/weights/candidates
```

请求需要：

```text
weight_version_id
source_training_run_id
release_gate_id
batch_summary
```

## 下一阶段

Phase 10 已进入：

1. 多 batch release readiness；
2. Candidate weight activation 审核协议；
3. Admin Console 独立前端进入后续阶段；
4. Synthetic case generator 进入后续阶段；
5. V40 runtime 原生命理引擎骨架进入后续阶段。
