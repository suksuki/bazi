# V30 Evaluation & Training Spine 主线设计

更新时间：2026-06-30

## 主线定位

V30 当前已经有 Signal Registry、Multi-Engine Runtime、Golden Case、EngineTrainingExample、Replay Queue、Practitioner Label 和 Reality Probe Diff。下一步不是继续加命理模块，也不是马上强化 LLM，而是建立真正的评测脊柱：

```text
命盘输入
-> 模块信号
-> DecisionVerdict
-> Advice
-> Probe
-> 用户/命理师反馈
-> 训练影响
-> 回归验证
```

一句话：

```text
Signal Registry 是管道。
Evaluation Contract 是尺子。
Golden Case 是标准答案。
Training Impact 是训练有效性的证明。
```

## 当前缺口

Phase 1/2 已经可以评分和生成训练资产，但仍然偏训练侧。系统还需要一个独立的 Evaluation Contract，回答：

- Verdict 是否合理？
- assertion_level 是否用对？
- Advice 是否绑定 Verdict 和 evidence？
- Probe 是否命中关键不确定性？
- LLM/表达是否越界？
- 训练后到底改变了什么？

## 第一阶段范围

本轮新增 `v30.evaluation`，只做 sidecar evaluation：

- 不改变用户结果。
- 不改变 DecisionVerdict。
- 不写 production pointer。
- 不让 LLM 当唯一评测裁判。
- 只基于结构化 runtime、SignalRegistry、MultiEngine 和 TrainingExample 评估。

## 目录

```text
v30/evaluation/
  contracts.py
  case_bank.py
  verdict_evaluator.py
  advice_evaluator.py
  probe_evaluator.py
  training_impact.py
  metrics.py
  regression_runner.py
```

## 核心合约

### EvaluationCaseSpec

比 `MingliGoldenCase` 更完整，包含：

- expected_signals
- expected_verdicts
- expected_advice
- expected_probes
- allowed_assertions
- forbidden_assertions
- known_reality
- expert_notes

它是“标准试卷”，训练和验证都必须围绕它。

### VerdictEvalResult

评估：

- evidence_coverage_rate
- overclaim_rate
- assertion_calibration_score
- conflict_resolution_score
- forbidden_assertion_hits

### AdviceEvalResult

评估：

- advice_grounding_rate
- actionability_score
- assertion_boundary_score
- ungrounded_advice

### ProbeEvalResult

评估：

- probe_binding_rate
- probe_yield_score
- answer_signal_count
- requires_followup

### TrainingImpactDiff

评估：

- 训练前后质量变化
- evidence / advice / overclaim / probe 指标变化
- 改变是否映射到 trainable targets
- 是否禁止 production pointer

## 任务计划

- `ETS-1`：新增 Evaluation Spine 文档。
- `ETS-2`：新增 evaluation contracts。
- `ETS-3`：新增 case bank，把现有 MingliGoldenCase 升级为 EvaluationCaseSpec。
- `ETS-4`：新增 Verdict / Advice / Probe evaluator。
- `ETS-5`：新增 TrainingImpactDiff 和 MetricSummary。
- `ETS-6`：新增 regression runner。
- `ETS-7`：专项测试和文档索引更新。

本轮执行 `ETS-1` 到 `ETS-7`。

## 第二阶段执行更新

本轮继续把 Evaluation Spine 接入 Admin 与训练编排器，完成 `ETS-8` 到 `ETS-11`：

- `ETS-8`：新增 `/api/v30/admin/evaluation/training-spine` 只读质量门入口。
- `ETS-9`：Training Orchestrator 新增 `evaluation_spine_quality_gate` 计划。
- `ETS-10`：隔离 worker `scripts/run_admin_training_worker.py` 支持该计划，Admin 后台任务可显示进度、结果和失败案例。
- `ETS-11`：新增命令行入口 `scripts/run_evaluation_training_spine.py`，用于本地/服务器专项评测。
- `ETS-12`：Admin 训练页接入“测算质量门”摘要卡、推荐计划下拉和中文化质量 diff 指标。

当前质量门输出：

```text
EvaluationCaseSpec
-> VerdictEval
-> AdviceEval
-> ProbeEval
-> MetricSummary
-> Admin Quality Gate
-> Training Orchestrator quality diff
```

当前边界：

- Admin 可运行和观察，不自动改生产策略。
- Training Orchestrator 可记录质量指标，不自动写 runtime pointer。
- `quality_metrics` 已纳入 `evaluation_overall_score`、`evaluation_evidence_coverage_rate`、`evaluation_advice_grounding_rate`、`evaluation_probe_yield_score`、`evaluation_overclaim_rate`。
- 后续训练候选必须先过这个 gate，才能进入更高风险的 pointer promotion 审核。

验证：

```text
python scripts/run_evaluation_training_spine.py
v30.evaluation_training_spine_runner.v1: passed (6/6 cases) score=0.974 overclaim=0.0
```

## 后续阶段

- 接 Admin UI 的进一步视觉简化和历史趋势图。
- 接训练前后 diff 的真实策略候选对比。
- 接 90-100 个命理师高质量 golden cases。
- 接 518K shard 分布观察。
- 接真实 Reality-Labeled Case。
