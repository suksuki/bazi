# V19 P66 Mainline P0 Application

P66 执行 P65 审计提出的两个 P0 主线修复：

```text
Rule Graph 选路 → 回答证据绑定 → 用户可见领域结构回答
```

## 已完成

### 1. 领域结构回答面

新增并接通三个安全回答类型：

- `career_structure`
- `relationship_structure`
- `health_structure`

这些回答只说明结构路径和阅读边界，不输出事业成败、关系结果、身体结论、时间应期或预测断语。

### 2. Rule Graph 证据绑定

`build_guided_question_answer` 现在会把当前回答路径中 Rule Graph 选中的知识合并进 `applied_knowledge`。这些知识只作为 evidence pack 和回答组织依据：

- 不启用运行时规则。
- 不改变命盘结果。
- 不输出内部 rule id。
- 不把候选规则当作断语。

## 验收结果

P65 审计当前状态：

- `answer_kind_gap_count = 0`
- `route_selected_not_applied_row_count = 0`
- `p0_action_count = 0`
- `runtime_mutation = false`

剩余主线任务降为 P1：

- R3/R4 安全 wrapper 分专题处理。
- Rule Graph 代表问题覆盖率继续提升。

## 回归

- `test_p65_mainline_completion_audit_locks_core_chain_before_new_frameworks`
- `test_guided_question_p10_review.py`
- 完整 `v19/tests`
