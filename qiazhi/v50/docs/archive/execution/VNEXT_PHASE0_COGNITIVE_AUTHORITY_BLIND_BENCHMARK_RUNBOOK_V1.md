# VNext Phase 0 Cognitive Authority Blind Benchmark Runbook v1

Status: `harness usable; P0-G1 lock pending`

## Question

VNext 是否真的比 Current V50、Holistic Synthesis Baseline 和直接问同一模型更像一个专业命理认知系统？DeepBazi 的准确事实、整体综合协议、上下文、工具挑战、知识和 Review 分别增加了什么？

## Six Lanes

| Lane | Input / behavior | Answers |
| --- | --- | --- |
| `direct_same_model` | 四柱 + 普通高质量命理任务；与 VNext 使用同一模型 | 系统相对同模型裸问增加了什么 |
| `direct_frontier` | 四柱 + 同一任务；独立配置 Frontier Model | 真实用户直接问最强模型能做到什么 |
| `current_v50` | Graph/Path/Role/Sensitivity 作为 tool-anchored first look 的历史重放 | 当前/旧 V50 工具锚定链的表现与风险 |
| `fact_only_deepbazi` | 准确事实 + 中性关系 + 统一输出合同；无命理综合协议、无旧工具排名、无现实经历 | 准确事实本身的增量 |
| `holistic_synthesis` | 准确事实 + 冻结的整体命理综合协议；无旧工具排名、Challenge Pack 和 Review | 整体综合原则本身的增量 |
| `vnext` | 独立第一眼 + 挑战包 + 相关知识 + 比较推理 + Review | 新认知链的额外价值 |

`direct_frontier` 不得用“新模型名称”自动获得生产资格。`qwen3.6:27b` 只标记为 `Local Open Stress Baseline`；真正的 Frontier Policy 未配置时，正式 Gate 保持 `pending`。

Historical V30 只在真实代码、模型、Prompt、上下文、参数、输入和不可变输出可共同复现时作为可选历史对照加入。它不属于六条 Formal Lane，也不阻塞 P0-G2。

## Isolated Evaluation Sets

清单拆为：

```text
data/validation/phase0/vnext_phase0_development_set_v1.json
data/validation/phase0/vnext_phase0_model_policy_selection_set_v1.json
data/validation/phase0/vnext_phase0_sealed_formal_manifest_v1.json
```

三套清单互斥。两张已用于 Dry Run 的盘属于 Development Set；正式十盘不得用于 Prompt、Context、预算或模型政策选择。

分类目标：

- 3 anchor candidates；
- 3 contrastive candidates；
- 2 ambiguous candidates；
- 2 ordinary / negative-control candidates。

正式十盘来自 synthetic taxonomy，只能用于架构晋级盲测和人工参考冻结。它们不是现实 Golden Cases。专家参考与现实证据分别保存在独立 Round 1 / Round 2 文件中。

## Unified Output

六 Lane 全部产出 `CognitiveBenchmarkReading`：

```text
independent_first_look
chart_center_of_gravity
primary_hypothesis
strongest_alternative
why_primary_over_alternative
main_work_path
secondary_or_blocked_paths
critical_nodes
pivot_candidates
bridge_or_support_candidates
body_function_relation
conditional_useful_roles
conditional_harmful_roles
stable_portrait
hidden_attribute_candidates
career_reasoning
wealth_reasoning
prior_predictions
falsifiers
discriminating_probe
known_uncertainties
evidence_refs
```

自由长文、缺字段摘要或不同 Lane 不同题目不能进入正式对比。

## Two Rounds

### Round 1 - Prior Reading

允许：出生信息、命盘事实、当前 Lane 明确允许的命理上下文。

禁止：现实职业、性格自述、财富状态、重大经历、用户既有反馈、expected contract 和专家答案。

### Round 2 - Controlled Feedback

只使用专家预先冻结的现实信息或 Probe 答案。检查：

- 局部判断是否正确修正；
- 未受影响认知是否保留；
- 是否考虑替代假设；
- 是否承认错配；
- 是否强行圆回原结论。

没有冻结的 `controlled_feedback` 时，runner 必须标记 `pending`，不能生成假反馈。

## Repetition and Blindness

- 正式批次：每 Lane / 每盘 / 每轮 3 次；
- preflight：Development Set / 6 Lane / 1 次，只验证 harness；Frontier 未冻结时可以先运行其余五 Lane，但必须保留 blocker；
- review packet 只显示随机 blind code；
- Lane、模型和运行顺序映射写入独立 operator map；
- review packet 不含 synthetic label、expected contract、Lane 名称或模型名；
- 三次重复的顺序必须随机化，不能连续暗示同一 Lane。

## Hard Gates

- 不虚构四柱事实；
- 不错十神、不反转生克；
- 不把候选说成确定事实；
- Round 1 不偷用现实经历；
- 重大结论有 evidence ref 或明确标记为模型解释；
- Review 不产生新结论；
- Graph / Path 等实验工具不进入 VNext Independent First Look；
- 所有 lane 共用一个输出合同。

## Human Rubric

每项 0-5：

1. 第一眼重心；
2. 竞争假设真实性；
3. 主做功因果闭合；
4. 关键节点和支撑关系；
5. 条件性用忌；
6. 整盘画像专属性；
7. 事业因果推演；
8. 财富因果推演；
9. 先验预测与 falsifier；
10. 事实可靠性；
11. 跨盘区分度；
12. 专业可用性。

正式结论只允许 `prefer / revise / reject / insufficient`。

## Current Long Task

### Lane A - Authority

- 冻结认知职责；
- 将 Graph v1、Path v1、Role v1、Ablation v1 标成实验性工具观察；
- 将 Mechanism / UnifiedState / Theme 标成 research projection；
- 将 DecisionConfidence 标成 uncalibrated research indicator；
- 更新 authority audit。

### Lane B - Benchmark Harness

- 建统一合同；
- 建十盘清单和 ExpertReference 空合同；
- 建六 Lane adapter；
- checkpoint / resume；
- 随机盲码、review packet 和 operator map 分离；
- 数据、解释、建议分层报告。

### Lane C - Dry Run

- 选择一盘 contrastive candidate 和一盘 ambiguous candidate；
- 每 Lane 运行一次 prior round；
- 检查合同、事实、Lane 泄漏、blind map 和可复跑性；
- dry run 不产生专业胜负结论。

### Lane D - Discovery Archaeology

- 只读盘点 518K、vector、cluster、singularity、energy-break、embedding、Gemini/LLM 分析和异常报告；
- 记录路径、大小、时间、资产族、可复现线索和已知状态；
- 不复制、不删除、不升级理论、不进入生产。

## Exit Decision

本轮只有两种合法状态：

- `harness_ready_for_expert_reference_freeze`；
- `harness_revision_required`。

模型超时、Schema 截断或模型未配置应记录为 `model_policy_failure`，不能伪装成 harness 成功，也不能误归为 benchmark 代码错误。它不阻止专家参考冻结，但会使 `ready_for_formal_run: false`，直到该 Lane 有可用的模型 Policy。

本轮不能输出：

- VNext 已经更专业；
- 新模型可以上线；
- 某个 synthetic label 已被证明；
- 可以训练或 Promotion。

正式 10 x 6 x 3 prior 批次只在 ExpertReference 冻结后运行；Round 2 只在 controlled feedback 冻结后运行。

Formal Run 的四类硬门禁是：Expert Reference Freeze、Frontier Policy Freeze、Six Lane Policy Freeze、Clean Code Snapshot + FormalRunLock。

## Boundary Status

```yaml
training_performed: false
weights_modified: false
production_runtime_rules_modified: false
brain_logic_modified: false
mingli_algorithm_modified: false
theory_modified: false
ui_modified: false
product_mode_modified: false
shadow_policy_promoted: false
expert_gold_fabricated: false
benchmark_harness_only: true
discovery_archaeology_read_only: true
```
