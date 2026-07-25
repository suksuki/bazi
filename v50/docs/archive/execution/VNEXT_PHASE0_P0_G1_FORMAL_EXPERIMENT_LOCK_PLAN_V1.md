# VNext Phase 0 P0-G1 Formal Experiment Lock Plan v1

Status: `P0-G1.5 machine policy corrected; human, frontier and code snapshot freeze pending`

## Accurate Naming

本阶段只证明实验基础设施、Lane 因果边界与机器门禁可用。它没有证明 VNext 已恢复专业命理能力，也没有产生专业胜者。

```yaml
phase0_harness: usable
p0_g1_5_machine_policy: passed
ready_for_formal_run: false
professional_winner: null
```

## Isolated Evaluation Sets

```text
Development Set (2)
  只用于 harness 和预检。

Model Policy Selection Set (5)
  只用于冻结 Direct Frontier 完整 Policy。

Sealed Formal Evaluation Set (10)
  只在 FormalRunLock frozen 后运行。
```

三套清单必须互斥。任何已用于调试、Prompt、Context 或模型选择的盘不得回到 Formal Set。

## Six Formal Lanes

1. `Direct Same Model`：同一核心模型，只看四柱、性别和普通专业任务。
2. `Direct Frontier`：独立冻结的强通用模型，模拟用户直接询问。
3. `Current Production V50`：原样冻结当前工具锚定链。
4. `Fact-only LLM`：可信事实与中性关系，无命理综合协议和旧工具排名。
5. `Holistic Synthesis Baseline`：Fact-only 加冻结的整体命理综合协议，无 VNext 工具、Challenge Pack 和 Review。
6. `VNext Cognitive Slice`：独立第一眼、工具挑战、相关知识、假设比较和认识论 Review。

`Direct Same Model`、`Fact-only LLM`、`Holistic Synthesis Baseline` 与 `VNext Cognitive Slice` 使用同一核心模型 Policy。

## Historical V30

```yaml
historical_v30:
  required_for_formal_run: false
  status: unavailable
  use: excluded
```

仓库现存 `v30_runtime` 只可作为代码考古或 retrospective reference。除非找回真实历史代码、模型、Prompt、上下文、参数、输入和不可变输出，否则不得称为 Historical V30，也不得阻塞 P0-G2。

## Expert Reference Space

专家冻结的是可接受认知空间，不是唯一标准文章：

```text
must_notice
acceptable_primary_hypotheses
strongest_alternatives
critical_relations
plausible_work_paths
conditional_useful_roles
conditional_harmful_roles
required_domain_distinctions
unsupported_claims
unresolved_disagreements
```

Round 1 不得包含现实经历。LLM 可以排版，不能代替人类专家填写。

## FormalRunLock

正式运行前必须冻结并绑定：

```text
git commit and clean V50 snapshot
benchmark manifest hash
expert reference hash
reality evidence hash
six-lane policy hash
holistic synthesis policy hash
frontier policy hash
prompt hashes
context policy hashes
model policy hashes
dependency lock hash
fact engine version
chart fact hashes
retry and mechanical repair policy
Go / No-Go gates
```

任何绑定资产变化都会使 Lock 失效。正式运行不得挑选三次中的最佳输出。

## Four Hard Gates

```text
round1_expert_reference_not_human_frozen
true_frontier_policy_not_frozen
lane_policy_not_frozen_for_formal_run
v50_code_snapshot_not_committed
```

如果 Lane Policy 已冻结，第三项自然消失。Historical V30 不属于硬门禁。

## Final Non-sealed Preflight

最后预检只能使用 Development Set 或 Model Policy Selection Set，并检查：

- 六 Lane 调用与失败分类；
- Schema 解析；
- checkpoint / resume；
- 盲码和 operator map 隔离；
- 原始输出 hash；
- 成本、延迟和速率；
- Lockfile fail-closed。

不得使用十张 Sealed Formal Charts 调试。

## Formal Discipline

- 全部 180 份输出不可变保留；
- 事实幻觉进入认知失败，不能重跑洗掉；
- 超时和供应商错误按冻结策略重试，仍失败进入可靠性统计；
- 不展示 best-of-three；
- 不在正式运行中改 Prompt、Context、模型参数或 Review Policy；
- P0-G2 不宣布胜者，P0-G3 才进行专家盲审裁决。

## Frozen Promotion Gates

- VNext 确定性事实冲突为 0；所有失败进入分母。
- 至少 8/10 盘专业优于 Current V50。
- 相对 Holistic Synthesis 至少 8/10 不弱，至少 5/10 明确更好。
- 至少 6/10 专业优于 Direct Frontier，至少 7/10 有 DeepBazi 独特增量。
- 三次运行不得无理由反转主假设、主做功或条件性用忌。
- 每盘必须有专属重心、主做功、排除项、2-3 条先验预测和鉴别性 Probe。

这些是架构晋级门禁，不是统计学证明。

## Boundary Status

```yaml
training_performed: false
weights_modified: false
production_runtime_rules_modified: false
brain_logic_modified: false
mingli_algorithm_modified: false
theory_modified: false
ui_modified: false
formal_outputs_generated: false
expert_gold_fabricated: false
historical_v30_fabricated: false
professional_winner_claimed: false
```
