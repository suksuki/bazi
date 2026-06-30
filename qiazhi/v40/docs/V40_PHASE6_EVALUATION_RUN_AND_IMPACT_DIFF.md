# V40 Phase 6: Evaluation Run And Impact Diff

更新时间：2026-06-30

## 目标

把 V40 的质量闭环从“能保存样本和反馈”推进到“能评测一次运行，并产生候选训练影响差异”。

Phase 6 新增：

```text
EvaluationCaseSpec + RuntimeResult -> EvaluationRunResult / MetricSummary / ReleaseGateResult
EvaluationRunResult -> TrainingImpactDiff
```

这一步仍然不自动写生产权重。

## 评测原则

评测器是确定性的，不让 LLM 当 judge。

当前指标：

```text
evidence_coverage_rate
assertion_calibration_score
overclaim_rate
conflict_resolution_score
advice_grounding_rate
probe_yield_score
llm_boundary_violation_rate
surface_leakage_rate
overall_score
```

其中：

```text
forbidden_assertion_hit
llm_boundary_violation
surface_leakage
```

会把评测状态推到 `blocked`。

## 新增 API

```text
POST /api/v40/evaluation/runs/from-runtime
GET  /api/v40/evaluation/runs

POST /api/v40/training/impact-from-evaluation
GET  /api/v40/training/impact-diffs
```

## 新增仓储

```text
v40_evaluation_runs
v40_training_impact_diffs
```

## Release Gate

`EvaluationRunResult` 可以同步生成 `ReleaseGateResult`：

```text
MetricSummary -> ReleaseGateResult
```

即使 gate 推荐 `approve`，当前也只是记录候选状态：

```text
production_write_allowed=false
```

真正生效必须由后续控制面明确执行。

## TrainingImpactDiff

`TrainingImpactDiff` 用来回答：

```text
这次训练候选影响了哪些主题？
哪些指标变好？
哪些风险仍然存在？
是否建议进入下一轮 release gate？
```

它不是权重文件，也不直接改生产系统。

## 下一阶段

Phase 7 已进入：

1. V40 Admin/Lab read model；
2. Artifact CLI：导入/导出 case、run、impact；
3. Golden case bank seed；
4. Synthetic case runner 进入后续阶段；
5. 多样本聚合 MetricSummary 进入后续阶段；
6. 候选权重版本对象进入后续阶段，仍不自动启用。
