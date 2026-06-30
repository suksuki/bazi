# V40 Phase 5: Evaluation And Training Repository

更新时间：2026-06-30

## 目标

让 V40 的质量闭环具备可保存、可查询、可回放的最小控制面。

Phase 5 接入三类资产：

```text
EvaluationCaseSpec
TrainingLabelEvent
ReleaseGateResult
```

这些资产进入 V40 数据库，但不直接改变生产权重、Verdict、Advice 或 chart facts。

## 新增能力

```text
POST /api/v40/evaluation/cases
GET  /api/v40/evaluation/cases

POST /api/v40/training/labels
GET  /api/v40/training/labels

POST /api/v40/release-gates
GET  /api/v40/release-gates
```

## 仓储映射

| Contract | Table | 作用 |
| --- | --- | --- |
| `EvaluationCaseSpec` | `v40_evaluation_cases` | 保存 golden / synthetic / regression / feedback 样本定义 |
| `TrainingLabelEvent` | `v40_training_label_events` | 保存用户、命理师、Admin、真实结果产生的训练反馈 |
| `ReleaseGateResult` | `v40_release_gates` | 保存候选版本质量门禁结果 |

## 边界

Phase 5 仍然禁止：

```text
读取或写入 V30 runtime
写入 V40 production weight
训练改写 chart facts
LLM 作为评测 judge
```

`TrainingLabelEvent` 只是反馈信号；真正训练必须进入：

```text
TrainingExampleV2
TrainingImpactDiff
ReleaseGateResult
```

通过门禁后才允许产生新的候选权重版本。

## 下一阶段

Phase 6 已进入：

1. `EvaluationRunResult` 持久化；
2. `MetricSummary` 聚合；
3. `TrainingExampleV2` 构建器；
4. `TrainingImpactDiff` 生成与保存；
5. Release Gate 从 metrics 自动生成并入库；
6. Admin/Lab 只读视图进入后续阶段。
