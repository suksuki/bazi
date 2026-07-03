# V30 训练后直接生效与 Admin 联动主线

更新时间：2026-06-28

## 目标

V30 进入高迭代训练模式：训练不是只生成报告，而是在验证通过后直接更新 runtime policy pointer，让下一次测算自动使用新策略。

主线目标：

- 训练后直接生效。
- 生效前必须通过验证闸门。
- Admin 必须明确展示 active policy、previous policy、rollback pointer、训练信号和验证结果。
- 训练永远不能改排盘、历法、四柱、十神等事实层。

## 当前链路

```text
Admin 训练按钮
-> POST /api/v30/admin/training/run
-> run_auto_apply_training()
-> synthetic all 抽训练信号
-> 生成 policy candidates
-> promotion validation
-> 写 PolicyArtifact
-> 更新 RuntimePointer
-> 新 runtime 自动读取 active policy
```

默认训练族：

- `structure_policy`
- `mainline_policy`
- `question_policy`
- `rule_policy`

当前中枢大脑训练信号：

- `v30.training_signal.central_brain_judge_quality`
- `v30.training_signal.central_brain_synthesis_blueprint_quality`

当前中枢策略挂载点：

```text
question_policy.weights.central_brain_synthesis_policy
```

## Admin 展示要求

训练页必须说清楚：

- 这是“训练并自动生效”，不是 dry-run。
- `promoted_count / candidate_count`。
- 每个 family 的 active policy。
- 每个 family 的 previous policy。
- 每个 family 的 rollback target。
- 本次训练信号总数。
- Brain Judge / Blueprint 训练信号是否出现。
- 验证模式：`strict` 或 `smoke`。
- 命盘事实层是否允许被训练修改：必须为 false。

## 安全边界

允许训练：

- 结构权重
- 问题排序
- 追问策略
- 最终综合质量
- 证据绑定权重
- 建议行动性
- 模板风险惩罚
- 过度断言惩罚
- 风险边界清晰度

禁止训练：

- 排盘事实
- 历法换算
- 四柱、六柱、日主
- 十神基础映射
- 大运流年事实
- 原始规则命中事实

## 下一步任务

1. 后端训练结果增加 `policy_application` 和 `training_signal_summary`。
2. Admin 训练页改为“训练并自动生效”。
3. Admin 最近训练结果展示 active/previous/rollback。
4. Admin 展示中枢训练信号覆盖情况。
5. 补测试确认训练结果对象与 UI 文案一致。

## 启动方式

### 1. 合成验证

```bash
python3 scripts/run_synthetic_validation.py --tier all
```

用途：

- 检查所有 synthetic case。
- 产出训练信号来源。
- 不写 runtime pointer。

### 2. 518K 验证

```bash
python3 scripts/run_518k_validation.py --mode sample --limit 8
python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

用途：

- `sample`：快速分布验证。
- `shard`：指定分片验证。
- `readiness_matrix`：检查 518K 验证链路是否完整。

### 3. 自动训练并生效

```bash
python3 scripts/run_auto_training.py \
  --training-run-id <run-id> \
  --promotion-validation-mode strict
```

用途：

- 抽取 synthetic training signals。
- 生成 `structure_policy`、`mainline_policy`、`question_policy`、`rule_policy` 候选。
- 对每个候选跑 promotion validation。
- 验证通过后直接写 runtime pointer。
- 新测算自动使用 active policy。

### 4. Admin 后台百分比任务

Admin 页面中的 “M3、训练合成、518K 后台验证” 使用后台 job：

```bash
python3 scripts/run_m3_background_training_job.py \
  --job-file <runtime-job-json> \
  --job-id <job-id> \
  --sample-limit 8 \
  --include-shard \
  --include-readiness-matrix
```

该 job 会写：

- `current_step`
- `completed_steps`
- `total_steps`
- `progress_percent`
- `results`

Admin 训练页读取这些字段展示百分比进度。

普通 CLI 脚本当前是结束态输出，不显示实时百分比。

## 2026-06-28 实跑结果

运行环境：

```bash
PATH=/tmp/qiazhi-v30-venv/bin:$PATH
```

结果：

```text
synthetic all: passed 127/127
518K sample: eligible, cases=8
518K shard: eligible, shard=7, cases=16
518K readiness matrix: passed 7/7
auto-training strict: applied, promoted 4/4
training_signal_count: 36
synthetic_signal_case_count: 127
```

生效 policy：

```text
structure_policy = structure_policy.cbi-v2-q8-real-run.structure_policy
mainline_policy  = mainline_policy.cbi-v2-q8-real-run.mainline_policy
question_policy  = question_policy.cbi-v2-q8-real-run.question_policy
rule_policy      = rule_policy.cbi-v2-q8-real-run.rule_policy
```

中枢训练信号：

```text
v30.training_signal.central_brain_judge_quality
v30.training_signal.central_brain_synthesis_blueprint_quality
```

边界：

```text
chart_fact_mutation_allowed = false
rollback_available = true
```
