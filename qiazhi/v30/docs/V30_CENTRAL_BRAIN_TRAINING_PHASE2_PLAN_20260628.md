# V30 中枢智能大脑训练第二阶段计划

更新时间：2026-06-28

## 定位

第一阶段已经完成训练系统的工程闭环：

- Admin 可启动训练。
- 后台 job 有进度、历史、失败步骤和 diff。
- 策略可以验证后自动生效。
- M3 / 518K 已进入 Orchestrator。
- 训练结果已经有业务质量对比。

第二阶段的目标不是继续堆脚本，而是让训练后真正改善中枢智能大脑：

```text
真实反馈 / 合成验证 / 518K 分布证据
-> BrainTrainingExample
-> 策略优化算法
-> 候选策略
-> 合成回放验证
-> 518K sample / shard 验证
-> 自动生效
-> 质量 diff 观察是否变聪明
```

一句话：训练系统从“能跑”升级为“能学习、能验证、能比较、能回滚”。

## 核心原则

### 训练什么

可训练对象：

- `claim_score` 权重：哪些断语更可靠。
- `next_action_policy` 权重：什么时候下结论，什么时候追问。
- `question_selection_policy`：问哪个问题信息增益最高。
- `hidden_attribute_probe_policy`：隐藏属性如何低成本校准。
- `final_synthesis_policy`：最终结论如何排序、收束和表达。
- `advice_actionability_policy`：建议如何更具体、更可执行。
- `template_risk_penalty`：如何惩罚空话、套话、车轱辘话。
- `overclaim_risk_penalty`：如何避免没有证据的硬断。

不可训练对象：

- 四柱、六柱、日主、月令。
- 历法、真太阳时、大运、流年换算。
- 规则命中事实。
- 未经用户确认的隐藏属性事实。
- LLM 生成的命盘事实。

边界：

```text
phase2_training_optimizes_central_brain_policy_not_chart_facts
```

## 第二阶段架构

```text
Runtime Reading Trace
  -> BrainTrainingExample Builder
  -> Training Dataset Store
  -> Policy Optimizer
  -> Candidate Policy Pack
  -> Synthetic Replay Gate
  -> 518K Distribution Gate
  -> Auto Apply
  -> Quality Diff / Rollback
```

### 1. BrainTrainingExample

第二阶段的训练样本是第一等对象，不再只从 synthetic result 临时抽 training signal。

标准结构：

```json
{
  "version": "v30.brain_training_example.v1",
  "example_id": "...",
  "source": "runtime_feedback | synthetic_replay | 518k_validation | admin_label",
  "stage_id": "path_reasoning",
  "input": {
    "evidence_graph_snapshot": {},
    "belief_state": {},
    "candidate_claims": [],
    "candidate_questions": [],
    "user_goal": "career"
  },
  "decision": {
    "selected_action": "ask_stage_question",
    "selected_claim_ids": [],
    "selected_question_id": ""
  },
  "outcome": {
    "user_answered": true,
    "answer_type": "choice",
    "claim_delta": {},
    "followup_useful": true
  },
  "labels": {
    "claim_correctness": 0.0,
    "question_information_gain": 0.0,
    "advice_actionability": 0.0,
    "template_risk": 0.0,
    "overclaim_risk": 0.0,
    "user_cost": 0.0
  },
  "safety": {
    "chart_fact_mutation_allowed": false,
    "llm_fact_injection_detected": false
  }
}
```

### 2. Dataset Store

训练样本需要可重复、可回放、可追踪。

存储层分三类：

- `raw_examples`：原始样本，包含 trace、反馈、标签。
- `training_splits`：训练集、验证集、回放集。
- `policy_runs`：每次优化输入、输出、指标和 promoted artifact。

最小实现先使用 runtime JSONL，后续进入 Postgres。

建议路径：

```text
.runtime/training/brain_examples/*.jsonl
.runtime/training/brain_splits/*.json
.runtime/training/brain_policy_runs/*.json
```

### 3. Policy Optimizer

第二阶段先不用黑盒大模型训练，先做可解释的在线策略优化。

初始算法：

```text
weighted_signal_aggregation
+ clipped_delta_update
+ regression_guard
+ risk_penalty
+ validation_gate
```

核心思想：

- 好样本提高对应策略权重。
- 坏样本降低对应策略权重。
- 权重变化必须有上限，避免一次训练把系统带偏。
- 风险指标升高时，不能 promotion。
- 训练产物必须可 diff、可回滚。

候选权重示例：

```text
claim_score.support_strength
claim_score.evidence_diversity
claim_score.graph_path_coherence
claim_score.feedback_alignment
claim_score.actionability
claim_score.counter_evidence_penalty
claim_score.missing_context_penalty
claim_score.overclaim_penalty

next_action.information_gain
next_action.claim_impact
next_action.hidden_attribute_gain
next_action.user_cost_penalty
next_action.overask_penalty

final_synthesis.evidence_binding
final_synthesis.conclusion_strength
final_synthesis.advice_actionability
final_synthesis.template_risk_penalty
final_synthesis.overclaim_risk_penalty
```

### 4. Validation Gate

训练后不能只看测试通过，还要看智能质量有没有提升。

Promotion 必须满足：

- synthetic replay 不退步。
- 关键业务质量 diff 不退步。
- `template_risk` 不升高。
- `overclaim_risk` 不升高。
- 518K sample / shard 不退步。
- chart facts mutation 永远为 false。

关键指标：

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
template_risk
overclaim_risk
m3_step_pass_rate
m3_518k_eligible_rate
```

### 5. Admin 联动

Admin 训练页面第二阶段要增加四件事：

- 训练样本数量：真实反馈、合成、518K、人工标注分别多少。
- 当前训练 split：train / validation / replay。
- 策略优化结果：哪些权重升了、哪些降了、为什么。
- 生效前后质量趋势：本轮、上一轮、最近 7 轮。

启动方式：

```text
Training Orchestrator
-> central_brain_phase2_training
```

计划步骤：

```text
collect_brain_examples
build_training_splits
optimize_policy_candidate
synthetic_replay_gate
518k_distribution_gate
auto_apply_policy
quality_diff_snapshot
```

## 任务计划

### PH2-1：BrainTrainingExample 契约与 Builder

目标：

- 定义 `BrainTrainingExample` schema。
- 从 `CentralReadingState`、`BrainDecisionTrace`、用户问答结果生成样本。
- 样本必须包含 evidence、decision、outcome、labels、safety。

验收：

- 单测覆盖样本字段完整性。
- 单测覆盖 LLM 不得注入 chart facts。
- markdown 更新训练样本字段说明。

状态：已完成。

落地内容：

- `BrainTrainingExample` 升级为 `v30.brain_training_example.v1`。
- 新增 `BrainTrainingInputSnapshot`、`BrainTrainingLabels`、`BrainTrainingSafety`。
- 新增 `v30.training.brain_training_examples.build_brain_training_example`。
- `CentralReadingState` 继续输出 `brain_training_example`，但内部改为走标准 Builder。
- 明确拒绝 chart fact mutation、LLM fact injection、production policy write。

### PH2-2：Training Dataset Store

目标：

- 支持 JSONL 写入与读取。
- 支持按 source、stage、domain、quality bucket 过滤。
- 生成 train / validation / replay split。

验收：

- 可重复读取同一批样本。
- split 带固定 seed。
- Admin/API 可读取样本摘要。

状态：已完成。

已完成：

- 新增 `BrainTrainingExampleStore`。
- 支持 JSONL append/read。
- 支持 raw split 摘要：样本数、source 分布、stage 分布、回答数、有用追问数。
- 固定 seed 的 train / validation / replay split。
- 按 source、stage、domain、quality bucket 过滤。
- Admin/API 样本摘要。

### PH2-3：Policy Optimizer V1

目标：

- 根据样本标签优化中枢策略权重。
- 采用 clipped delta，单轮变化可控。
- 输出 candidate policy artifact。

验收：

- 好样本提升对应权重。
- 坏样本提高风险惩罚。
- 没有足够样本时不 promotion。
- chart fact 权重不存在。

状态：已完成。

落地内容：

- 新增 `v30.brain.policy_optimizer.optimize_central_brain_policy`。
- 采用 weighted signal aggregation + clipped delta。
- 输出候选权重、weight deltas、训练指标、promotion signal 和 blocked reasons。
- 当模板风险、过度断言风险或 claim correctness 不达标时阻止 promotion。
- Admin API 新增 `/admin/training/brain-examples/optimize`，从 split 样本生成候选策略。

### PH2-4：Synthetic Replay Gate

目标：

- 训练后回放关键合成场景。
- 对比训练前后质量指标。
- 失败则阻止自动生效。

验收：

- 覆盖事业、财运、关系、健康、隐藏属性、缺信息、用户跳过。
- 每次最多一个问题。
- 没有证据时不硬断。

状态：已完成。

落地内容：

- 新增 `v30.validation.central_brain_phase2_replay_gate`。
- Gate 输入为 Policy Optimizer 候选策略和 replay split 样本。
- Gate 会运行中枢 synthetic validation，并检查 replay 样本数量、claim correctness、template risk、overclaim risk、chart fact immutability。
- Admin API 新增 `/admin/training/brain-examples/replay-gate`，从 train split 生成候选，再用 replay split 做门禁。
- Admin 训练页展示 `Synthetic Replay Gate` 状态、检查通过数和失败项。

### PH2-5：518K Distribution Gate

目标：

- 让 518K sample / shard 成为训练 promotion 的分布验证。
- 不要求 full 518K 每轮都跑，但 sample 和 shard 必须可配置。

验收：

- Admin 可选择 sample_limit、shard_id、shard_limit。
- Orchestrator quality diff 包含 518K 质量指标。
- 失败时不自动生效。

状态：已完成。

落地内容：

- 新增 `v30.validation.central_brain_phase2_distribution_gate`。
- Gate 输入为 synthetic replay gate 结果、518K sample 结果和可选 518K shard 结果。
- 检查 sample promotion signal、case count、failure clusters、可选 shard 和 chart fact immutability。
- Admin API 新增 `/admin/training/brain-examples/distribution-gate`，会用 train split 生成候选策略、用 replay split 做 synthetic replay gate，并用候选策略作为 518K policy override 运行 sample / 可选 shard。
- full 518K 仍不作为默认门禁，`full_518k_required=false`。

### PH2-6：Admin Phase2 Console

目标：

- Admin 页面展示样本数量、训练 split、策略变化、质量趋势。
- 可启动 `central_brain_phase2_training`。
- 可查看本轮为什么 promotion 或 blocked。

验收：

- 页面不暴露内部噪音。
- 用户只看训练是否变聪明、是否安全、是否已生效。
- 支持历史查看和 rollback。

状态：已完成主闭环。

落地内容：

- Training Orchestrator 新增 `central_brain_phase2_training` 计划。
- 计划步骤：
  - `brain_example_summary`
  - `build_training_splits`
  - `optimize_policy_candidate`
  - `synthetic_replay_gate`
  - `518k_distribution_gate`
- Admin 训练页可从训练总调度启动该计划。
- Orchestrator job 会展示 progress、step results、phase2 result、replay gate 和 distribution gate。
- 该计划只验证候选策略，不写 runtime pointer；后续 auto apply / pointer promotion 仍需单独门禁。

剩余增强：

- 展示最近 N 轮趋势曲线。
- 把真实用户反馈自动沉淀为 `BrainTrainingExample`。
- 通过最终 auto apply gate 后自动提升 runtime pointer。

## 第一轮执行顺序

本阶段先完成最小可用闭环：

1. PH2-1 `BrainTrainingExample` 契约与 Builder。
2. PH2-2 JSONL Dataset Store。
3. PH2-3 Policy Optimizer V1。
4. PH2-4 Synthetic Replay Gate。
5. 接入 Orchestrator 新计划 `central_brain_phase2_training`。
6. Admin 展示样本摘要、策略 diff、质量 diff。

暂不做：

- full 518K 长任务断点续跑。
- 大规模 Postgres 样本仓库。
- 黑盒模型 fine-tune。
- 人工标注工作台。

## 完成度口径

第二阶段完成度按下面标准判断：

```text
20%：样本契约和采集完成
40%：样本存储与 split 完成
60%：策略优化器完成
75%：synthetic replay gate 完成
85%：Orchestrator / Admin 接入完成
95%：518K sample / shard promotion gate 稳定
100%：真实反馈进入训练闭环并可观察质量趋势
```

## 当前状态

```text
phase: CBI-V2 Phase 2
status: in_progress
completion: 95%
next_task: runtime feedback -> BrainTrainingExample 自动沉淀与最终 auto-apply gate
canonical_doc: docs/V30_CENTRAL_BRAIN_TRAINING_PHASE2_PLAN_20260628.md
```
