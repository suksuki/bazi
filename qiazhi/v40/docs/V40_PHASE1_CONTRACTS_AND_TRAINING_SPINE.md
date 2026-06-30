# V40 Phase 1: Contracts And Training Spine

更新时间：2026-06-30

## 目标

本阶段开始 V40 迁移和重构，但不迁移 V30 runtime 实现。目标是先建立 V40 自己的契约层、训练验证脊柱和 V30 DTO migration 边界。

## 特别注意

1. V40 runtime 不能直接 import `v30.*`。
2. V40 不能读写 V30 database、Redis key、runtime file。
3. V30 成熟模块只允许通过 plain JSON / DTO export 进入 V40。
4. V40 第一阶段不重写八字算法。
5. V40 先做 evaluation-first：没有评测合约，就不训练；没有 release gate，就不发布。
6. CentralBrain 只做调度、反馈归因、训练路由和质量门，不做 Verdict。
7. DecisionEngine 是唯一 Verdict 生成者。
8. LLM 只做表达、对话和 Thinking，不做裁决。

## 本阶段新增模块

```text
v40/contracts/base.py
v40/contracts/signal.py
v40/contracts/engine.py
v40/contracts/decision.py
v40/contracts/output.py
v40/contracts/evaluation.py
v40/contracts/training.py
v40/contracts/runtime.py
v40/migration/v30_export.py
v40/evaluation/release_gate.py
v40/training/attribution.py
```

## Contract Map

| 层 | 契约 |
| --- | --- |
| Base | `RoleKey`, `Topic`, `AssertionLevel`, `EngineKey`, `SurfaceKey`, `V40Model` |
| Signal | `RuntimeSignal`, `SignalRegistrySnapshot` |
| Engine | `EnginePlan`, `EngineRunRequest`, `EngineRunResult`, `MultiEngineRunResult` |
| Decision | `DecisionInputBundle`, `BranchCandidate`, `DecisionVerdict`, `AdvicePlan`, `ProbeCandidate` |
| Output | `ProductVerdictCard`, `BranchCard`, `ProductAdviceCard`, `LLMExpressionTask`, `LLMExpressionResult`, `AcceptanceResult`, `ProductProjectionBundle`, `SurfaceBundle` |
| Evaluation | `EvaluationCaseSpec`, `GoldenCase`, `MetricSummary`, `ReleaseGateResult`, `EvaluationRunResult` |
| Training | `TrainingLabelEvent`, `TrainingExampleV2`, `TrainingImpactDiff`, `LocalOverlay`, `GlobalWeightVersion` |
| Runtime | `RuntimeRequest`, `RuntimeResult` |
| Migration | `V30ExportEnvelope`, `V30ToV40MigrationPlan` |

## 已写入模型校验的边界

- `RuntimeSignal` 不能改 chart facts，不能拥有 decision authority。
- `EnginePlan` 必须包含 BaziEngine；CentralBrain 不能拥有 Verdict authority。
- `EnginePlanItem` 和 `EngineRunResult` 中 ZiweiEngine V1 的 `decision_weight` 必须为 0。
- `DecisionInputBundle` 不能用 LLM 输出作为 V40 alpha 的裁决输入。
- `DecisionVerdict` 不能由 LLM 或 CentralBrain 授权，强断语必须有 evidence refs。
- `AdvicePlan` 必须绑定 Verdict，不能超过 Verdict 边界。
- `ProbeCandidate` 只有信息增益超过用户成本时才能 `ask_now`。
- `LLMExpressionTask` / `LLMExpressionResult` 不能改变 Verdict，不能创建 chart facts。
- `AcceptanceResult` 只有无泄漏、无过度断言、无事实/裁决漂移时才能 accepted。
- `EvaluationCaseSpec` 必须包含 expected verdict 和 forbidden assertion。
- `TrainingLabelEvent` 不能训练 chart facts。
- `TrainingExampleV2` 不允许直接全局更新。
- `TrainingImpactDiff` 不能直接写 production。
- `ReleaseGateResult` 只有全部 gate 通过且无 regression 时才能 approve。
- `V30ExportEnvelope` 拒绝 raw V30 runtime path、database ref 和 redis key。

## 下一步

1. 增加 V40 migration fixture：把 V30 导出的 plain JSON 转为 V40 `RuntimeSignal`。
2. 增加最小 Shadow Compare：同一 fixture 比较 V30 DTO 和 V40 contract projection。
3. 增加 V40 Postgres schema：`v40_runtime_records / v40_evaluation_cases / v40_training_label_events / v40_release_gates`。
4. 增加最小 `/api/v40/health` 和 `/api/v40/contracts`，只暴露 V40 边界和 contract map。
