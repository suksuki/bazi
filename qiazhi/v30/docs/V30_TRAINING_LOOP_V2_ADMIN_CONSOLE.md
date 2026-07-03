# V30 Training Loop V2 与 Admin 控制台

更新时间：2026-06-28

## 目标

V30 的训练不再是零散脚本，而是一条可在 Admin 管理、可重复执行、可看到进度、验证通过后直接生效的训练闭环。

核心原则：

- Admin 可以启动训练任务，并看到百分比进度、当前阶段、完成状态和策略生效摘要。
- 训练可以反复运行，每次生成新的 policy candidate。
- 验证通过后直接更新 runtime policy pointer。
- 训练只能优化中枢智能大脑、对话策略、规则权重、结构权重和综合质量参数。
- 训练不能修改排盘、历法、大运流年、四柱、固定命盘事实。

## 当前任务模型

Admin 自动训练任务使用统一 job 结构：

```text
job_id
status: queued / running / completed / failed
progress_percent
current_step
completed_steps / total_steps
progress_events
training_run
policy_application
training_signal_summary
active_policy_versions
```

后台接口：

```text
POST /api/v30/admin/training/auto-apply/run
GET  /api/v30/admin/training/auto-apply/status
GET  /api/v30/admin/training/auto-apply/history
GET  /api/v30/admin/policies/lineage/summary
POST /api/v30/admin/policies/rollback
```

任务文件落盘：

```text
.runtime/training/auto_apply_jobs/<job_id>.json
```

## 百分比语义

百分比来自训练核心函数，而不是前端猜测：

```text
1%   started
20%  synthetic_signal_source_ready
35%  training_signals_extracted
50%  candidates_generated
50-90% per-family validation and promotion
95%  active_policy_versions_loaded
100% completed
```

这样 Admin、CLI、未来调度器看到的是同一条训练生命周期。

## 训练闭环

当前 auto-training 主链路：

```text
synthetic all
-> extract_training_signals
-> generate policy candidates
-> validate each candidate
-> promote valid runtime pointers
-> expose rollback target
-> runtime consumes active policy versions
```

覆盖策略族：

- `structure_policy`
- `mainline_policy`
- `question_policy`
- `rule_policy`

## Admin 页面联动

Admin 训练页现在分为两类任务：

- 自动生效训练：用于中枢智能大脑和策略参数训练，完成后可直接影响 runtime。
- M3 / 518K 后台验证：用于知识、规则、画像、路径和真实大样本验证，不直接提升 policy pointer。

页面只展示必要信息：

- 启动任务
- 刷新进度
- 当前阶段
- 百分比进度条
- 最近进度事件
- 最近训练历史
- 当前 active / previous / rollback policy pointer
- 完成后的策略生效摘要

不展示大 JSON、不展示候选内部 payload、不展示工程噪音。

## 回滚语义

Admin rollback 只做一件事：

```text
当前 active pointer -> previous rollback pointer
当前 active pointer -> 写入新的 rollback target
```

它不重新训练、不重新生成候选、不修改命盘事实、不改用户档案。

回滚后的 runtime 会读取新的 active policy pointer，因此后续测算会回到上一版策略参数。

## 训练边界

允许训练：

- 中枢综合质量
- Brain Judge / Blueprint 权重
- 对话问题选择策略
- 隐藏属性反推策略
- 规则权重
- 结构路径权重
- 领域建议排序和表达质量

禁止训练：

- 出生资料
- 四柱排盘
- 历法转换
- 大运流年事实
- 固定命盘事实
- 用户原始档案数据

## 下一步

Training Loop V2 后续应继续统一：

- 全量 518K 训练任务的后台 job 化。
- 训练进度写入 Postgres，便于多用户 admin 查看。
- Admin 提供失败重跑、训练结果对比和全量 518K 任务编排。
- 用合成验证和真实样本验证结果自动调整训练参数。
- 将训练样本、验证结果和线上反馈合成 BrainTrainingExample，形成可持续优化的中枢智能系统。
