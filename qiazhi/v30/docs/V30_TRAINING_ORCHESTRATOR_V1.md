# V30 Training Orchestrator V1

更新时间：2026-06-28

## 目标

Training Orchestrator V1 是训练系统的总调度层。它不重写 auto-training、M3、518K 或对话校准，而是把它们收束成可管理的训练计划。

核心目标：

- Admin 只需要选择训练计划，而不是理解每个脚本。
- 每个训练计划都有 steps、progress、history、result、lineage、rollback 边界。
- 可执行计划先从中枢自动训练和 M3 / 518K sample 验证开始，后续逐步接入 518K full run、对话回放、失败重跑和训练结果对比。
- 训练调度只优化策略参数、问题策略、综合质量、规则/结构权重，不修改命盘事实。

## V1 计划

### `central_brain_auto_apply`

用途：

- 训练中枢智能大脑相关策略。
- 生成并验证 `structure_policy`、`mainline_policy`、`question_policy`、`rule_policy` 候选。
- 验证通过后自动写 runtime pointer。

步骤：

```text
preflight_lineage
auto_apply_training
post_training_lineage
history_snapshot
```

### `quick_validation_only`

用途：

- 只跑轻量训练管线验证。
- 不提升 runtime pointer。

步骤：

```text
training_pipeline_synthetic
lineage_snapshot
```

### `m3_518k_validation`

用途：

- 验证知识库、规则、画像、路径和训练管线是否可用。
- 运行 518K sample，并可选 shard 与 readiness matrix。
- 不提升 runtime pointer，只作为训练和验证证据。

步骤：

```text
m3_snapshot
m3_synthetic
training_pipeline
518k_sample
optional: 518k_shard
optional: 518k_readiness_matrix
```

默认参数：

```text
sample_limit = 8
shard_id = 7
shard_limit = 16
full_518k = not_default
```

## Job 模型

```text
job_id
plan_id
status: queued / running / completed / failed
current_step
progress_percent
completed_steps / total_steps
step_results
training_run
lineage_summary
history_snapshot
quality_metrics
diff_summary
failed_steps
failures
```

任务落盘：

```text
.runtime/training/orchestrator_jobs/<job_id>.json
```

## API

```text
GET  /api/v30/admin/training/orchestrator/plans
POST /api/v30/admin/training/orchestrator/run
GET  /api/v30/admin/training/orchestrator/status
GET  /api/v30/admin/training/orchestrator/history
GET  /api/v30/admin/training/orchestrator/diff
POST /api/v30/admin/training/orchestrator/rerun-failed
```

## Diff 与失败重跑

Diff 比较同一 plan 的当前 job 与上一轮 job，只读取摘要指标：

```text
passed_step_count
failed_step_count
case_count
eligible_518k_count
promoted_count
```

同时比较中枢智能大脑的业务质量指标：

```text
final_synthesis_quality_score
brain_judge_accepted_rate
advice_actionability
decision_focus_coverage
action_step_coverage
risk_boundary_coverage
evidence_chain_coverage
interaction_loop_strength
high_value_question_strength
expression_quality_strength
template_risk
overclaim_risk
m3_step_pass_rate
m3_518k_eligible_rate
validation_case_count
```

`quality_diff_rows` 会给出 `current / previous / delta / judgement`。结论质量、建议可执行性、焦点覆盖、证据链覆盖、交互质量、问题质量、验证通过率等指标越高越好；`template_risk` 与 `overclaim_risk` 越低越好。

Diff 不重新训练、不改 pointer、不改命盘事实。

失败步骤重跑只在 job 存在 failed steps 时开放。V1 支持：

```text
quick_validation_only: training_pipeline_synthetic / lineage_snapshot
m3_518k_validation: m3_snapshot / m3_synthetic / training_pipeline / 518k_sample / 518k_shard / 518k_readiness_matrix
```

`central_brain_auto_apply` 暂不做步骤级重跑，因为策略提升是一个需要整体一致性的闭环；失败时应重新运行完整计划。

## 与现有训练系统关系

```text
Admin
-> Training Orchestrator
   -> auto-training
   -> M3 / 518K background validation
   -> dialogue replay / calibration
   -> lineage / rollback / history
```

V1 已接入 `central_brain_auto_apply`、`quick_validation_only` 和 `m3_518k_validation`。原 M3 / 518K 后台任务入口继续保留，用作底层任务和长任务兜底；Orchestrator 负责统一计划、进度、历史和结果摘要。

## 边界

允许：

- 启动训练计划。
- 查看进度和历史。
- 查看训练结果 diff。
- 重跑失败步骤。
- 读取 policy lineage。
- 自动提升通过验证的 runtime pointer。
- 回滚 runtime pointer。

禁止：

- 修改出生资料。
- 修改四柱排盘。
- 修改历法和大运流年事实。
- 把 LLM 输出当作命盘事实写入。
- 跳过验证直接提升策略。

## 下一步

- 增加 central_brain_auto_apply 的安全整体 retry。
- 增加 full 518K 的断点续跑和长任务 progress。
- 将 orchestrator job 写入 Postgres。
- 用真实用户反馈生成 BrainTrainingExample，并进入计划输入。
