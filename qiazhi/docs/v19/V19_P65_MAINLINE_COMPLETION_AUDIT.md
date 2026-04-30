# V19 P65 Mainline Completion Audit

P65 是一次主线收束审计。目标不是继续铺新框架，而是确认当前最该优先完成的链路：

```text
知识库 → 规则候选 → Rule Graph → 回答证据 → 用户可见回答
```

## 当前结论

审计结果显示：

- 当前知识草稿：436 条。
- P39 可转规则候选：348 条。
- P39 R3/R4 阻塞档案：88 条。
- P61 关系 / 健康 route-only 包装：6 条。
- Rule Graph 当前候选池：354 条。
- 代表问题矩阵：24 行。

最高优先级不是继续扩自学习或交互校准，而是先把主干链路锁住。P65 审计已推动并验收两个 P0 链路修复：

## P0 已完成

### 1. 用户可见回答层的领域边界

deterministic guided answer 已能承接：

- `career_structure`
- `relationship_structure`
- `health_structure`

它们只输出结构边界，不输出事业结果、关系结果、身体结论、寿命或预测断语。

### 2. Rule Graph 选中知识绑定到回答证据层

代表问题中，Rule Graph 选中的知识已经进入 `applied_knowledge` 与 evidence pack。当前 6 类回答面：

- 收入
- 事业
- 关系
- 健康
- 时间
- 元数据

均满足 `rule_graph_selected_knowledge_ids ⊆ applied_knowledge_ids`。

## P1 优先任务

### 1. R3/R4 档案知识安全转化

当前 88 条高风险档案不能直接转规则。它们可以按专题抽取：

- route-only wrapper。
- boundary-only wrapper。
- evidence-only label。

P61 的关系/健康 route wrapper 是模板，后续可以按专题复制。

P69 已按这个模板继续推进：P61 之外剩余 82 条 R3/R4 档案已经降级为安全 wrapper；当前 88 条高风险档案均有安全路径覆盖，仍保持不激活、不改结果、不输出领域断语。

### 2. Rule Graph 覆盖率提升

代表矩阵中仍有大量候选未被选中。这不一定是错误，但说明需要：

- 增加代表问题。
- 增加专题合成样本。
- 调整 deterministic scorer。
- 按十神机制、格局、盲派、时间引动逐组验收。

## P2 暂缓任务

以下功能保留接口，不继续扩：

- P62 静默训练账本。
- P63 静默评估队列。
- P64 交互式命盘校准。
- GNN / RL。

它们是后续扩展位，不是当前主线。

## 入口

- `v19.synthetic_validation.mainline_completion_audit.build_p65_mainline_completion_audit`
- `v19.synthetic_validation.mainline_completion_audit.run_p65_mainline_completion_regression`
- `GET /api/lab/mainline-completion-audit`
- `POST /api/lab/mainline-completion-audit/run`

## 验收

新增回归：

`test_p65_mainline_completion_audit_prioritizes_core_chain_before_new_frameworks`
已更新为：

`test_p65_mainline_completion_audit_locks_core_chain_before_new_frameworks`

要求：

- 候选池包含 P39 + P61。
- 事业 / 关系 / 健康领域回答不再被 fallback 或 unsupported gate 拦截。
- Rule Graph selected knowledge 稳定进入 applied knowledge。
- P0 缺口数为 0，剩余任务只进入 P1/P2。
- runtime / answer / rule activation 全部为 0。
