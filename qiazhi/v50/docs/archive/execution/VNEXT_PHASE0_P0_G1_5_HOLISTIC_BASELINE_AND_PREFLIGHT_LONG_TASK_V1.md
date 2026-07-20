# VNext Phase 0 P0-G1.5 Holistic Baseline and Formal Preflight Long Task v1

Status: `approved for machine-side execution`

## 1. Purpose

本轮修正 Phase 0 正式实验的能力变量，不修改命理算法，也不提前运行十张密封盘。

核心变化：

```text
Historical V30
= 条件性历史对照
= 有真实不可变资产才加入
= 不再阻塞 P0-G2

Holistic Synthesis Baseline
= 可信事实
+ 冻结的命理综合方法论
+ 少量不含具体命盘答案的推理范式
+ 统一输出合同
+ 同一核心模型
```

本轮要回答的不是“V30 还原得像不像”，而是：

> 在没有 VNext 工具编排、Challenge Pack 和 Epistemic Review 的情况下，仅允许同一强模型基于准确事实进行整体命理综合，能产生多少专业价值？

## 2. Analyst Feedback Accepted

以下判断正式采纳：

1. 仓库中的 `v30_runtime` 不是历史自由综合 Agent，不得作为 Formal Lane 冒充 Historical V30。
2. Historical V30 改为可选研究项；真实代码、模型、Prompt、上下文和不可变输出不足时，状态为 `unavailable`。
3. 六条正式 Lane 冻结为：

```text
Lane A  Direct Same Model
Lane B  Direct Frontier
Lane C  Current Production V50
Lane D  Fact-only LLM
Lane E  Holistic Synthesis Baseline
Lane F  VNext Cognitive Slice
```

4. Formal Run 只保留四类硬门禁：

```text
Expert Reference Freeze
Frontier Policy Freeze
Six Lane Policy Freeze
Clean Code Snapshot + FormalRunLock
```

5. 正式运行前最后一次预检只能使用 Development Set 或 Model Policy Selection Set。
6. P0-G2 只生成不可变实验材料，专业胜负由 P0-G3 Expert Blind Adjudication 决定。

## 3. Additional Architecture Review

Holistic Synthesis 与 Fact-only 的边界必须严格可审计，否则两条 Lane 会退化成“两个措辞略有不同的 Prompt”。

### Fact-only LLM

允许：

- 四柱与性别；
- 确定性命盘事实；
- 中性结构关系；
- 统一输出合同。

禁止：

- 命理综合步骤；
- 高质量推理范式；
- Graph / Path 排名；
- 预设假设；
- Challenge Pack；
- Review。

### Holistic Synthesis Baseline

在 Fact-only 基础上只增加：

- 冻结的整体观察顺序；
- 多假设比较原则；
- 做功、体用、旺衰、调候与象法的冲突处理原则；
- 条件性用忌原则；
- 领域因果推演原则；
- 少量不携带具体命盘答案的抽象推理范式。

仍然禁止：

- 旧 Graph v1 / Path v1 / Role v1 排名；
- 旧 Mechanism 结论；
- 现实经历与 Probe 答案；
- VNext Challenge Pack；
- VNext Epistemic Review；
- 人工预设主假设。

## 4. Long Task Scope

### Lane A - Governance Correction

- 替换 Formal Lane 中的 `v30_runtime`；
- 将 Historical V30 记录为 optional research baseline；
- 删除 `representative_v30_baseline_not_frozen` 硬阻塞；
- 将晋级门槛的 V30 对比改为 Holistic Synthesis 对比；
- 保留 Historical V30 的历史说明，不伪造复现能力。

### Lane B - Executable Baseline

- 新增冻结的 Holistic Synthesis Policy；
- Runner 使用同一核心模型运行 Holistic Lane；
- Holistic 上下文只能读取可信事实、中性关系和冻结方法论；
- FormalRunLock 绑定该 Policy、依赖、事实引擎、Prompt、Context 与 Retry Policy 的哈希。

### Lane C - Non-sealed Preflight

- 先执行离线 plan check；
- 再在 Development Set 上执行非密封 live preflight；
- 在 Frontier 尚未冻结时，只运行其余五条可运行 Lane；
- Direct Frontier 保留为显式 blocker，不得用本地模型冒充；
- 检查 schema、checkpoint/resume、盲码、原始输出 hash、失败分类和成本统计。

### Lane D - Audit and Analyst Handoff

- 生成 `MASTER_AUDIT_REPORT`；
- 生成 `ANALYST_REVIEW_PACKET`；
- 清楚区分 Observed Data、Interpretation、Recommendation；
- 不宣布专业胜者；
- 不自动进入 P0-G2。

## 5. Execution Loop

```text
Contract correction
-> targeted tests
-> offline six-lane plan
-> non-sealed five-lane live preflight
-> classify failures
-> repair harness-only defects if needed
-> rerun targeted preflight
-> full regression
-> audit packet
-> stop for analyst review
```

允许修复：

- Lane 路由错误；
- schema / checkpoint / hash / blind-code 实现错误；
- 报告或失败分类错误；
- Holistic Policy 泄漏被禁止上下文的问题。

禁止修复：

- 根据输出质量调命理 Prompt；
- 修改 Graph、Path、Mechanism、Brain 或生产命理算法；
- 放宽 verifier 让失败变绿；
- 查看或运行十张 Sealed Formal Charts；
- 修改 Expert Reference 内容；
- 选择或宣传专业胜者。

## 6. Acceptance Criteria

1. Formal Lane 恰好为批准的六条，且不包含 `v30_runtime`。
2. Historical V30 明确为 `required_for_formal_run: false`。
3. FormalRunLock blockers 不再包含代表性 V30。
4. Holistic 与 Fact-only 的可见输入差异可由配置和测试证明。
5. Holistic 不读取旧工具排名、Challenge Pack、Review 或现实经历。
6. Direct Same Model、Fact-only、Holistic 与 VNext 使用同一核心模型 Policy。
7. FormalRunLock 绑定方法论、依赖、事实引擎和失败策略哈希。
8. 离线六路计划可生成，非密封五路 live preflight 可复跑。
9. Sealed Formal output count 保持为 `0`。
10. 最终报告明确剩余人类/外部门禁，并停止等待分析师决定。

## 7. Boundary Status

```yaml
training_performed: false
weights_modified: false
production_runtime_rules_modified: false
brain_logic_modified: false
mingli_algorithm_modified: false
theory_modified: false
ui_modified: false
expert_reference_modified: false
reality_evidence_opened: false
sealed_formal_charts_executed: false
formal_outputs_generated: false
professional_winner_claimed: false
historical_v30_fabricated: false
```

## 8. Expected Stop State

本轮结束后，合理状态仍可能是：

```yaml
status: partial
machine_side_g1_5: passed
ready_for_formal_run: false
remaining_blockers:
  - round1_expert_reference_not_human_frozen
  - true_frontier_policy_not_frozen
  - v50_code_snapshot_not_committed
```

`partial` 在这里不是失败，而是没有越过人类专家、外部模型选择和代码冻结的权限边界。

