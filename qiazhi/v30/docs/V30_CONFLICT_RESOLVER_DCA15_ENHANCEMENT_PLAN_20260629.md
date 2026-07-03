# V30 DCA-15 ConflictResolver 增强阶段执行计划

更新时间：2026-06-29

## 阶段定位

DCA-15 第一段已经完成 `Signal Registry -> DecisionCandidate` 的兼容绑定。当前阶段继续推进 DCA-15，但仍保持兼容模式：

```text
DecisionCandidate
-> ConflictResolver
-> DecisionConflict / conflict audit
-> DecisionVerdict
```

本阶段只把冲突解释、反证、近似分支和待校准问题抽成独立模块，不改分数、不改 Verdict 数量、不让 Signal Registry 直接替代 Decision Engine。

## 为什么要做

旧逻辑里，冲突判断直接藏在 `DecisionEngine` 内部：

- 哪些候选形成冲突，不容易独立审计。
- 为什么出现下一问，不容易训练和验证。
- 反证、近似分支、命理师校准项没有自己的产出层。
- Signal Registry 已经绑定到 candidate，但 ConflictResolver 还没有消费这些信号摘要。

这会导致中枢大脑看起来“能下结论”，但解释不了“为什么保留这个分支、为什么要问这个问题、为什么不能更强断言”。

## 本阶段原则

1. `ConflictResolver` 是产出编排层，不是命盘事实层。
2. `ConflictResolver` 可以读取 `DecisionCandidate.source_signal_ids` 和 `signal_source_summary`，但不能改 candidate score。
3. `ConflictResolver` 输出 `DecisionConflict` 和审计摘要，给 Decision Engine、对话策略、Admin 回放和训练验证使用。
4. 本阶段不改变 `DecisionVerdict` 的数量、排序和 assertion level。
5. 本阶段不让 LLM 参与冲突裁决。

## 新增模块

```text
v30.brain.conflict_resolver
```

职责：

- 按 domain 汇总候选。
- 识别近似概率分支。
- 识别需要校准的候选。
- 识别主分支反证。
- 生成 `DecisionConflict`。
- 生成 `conflict_resolver_summary`。
- 生成 `conflict_resolver_audit`。

## 输出契约

### conflict_resolver_summary

```text
version
mode
candidate_count
conflict_count
domain_count
conflict_type_counts
signal_bound_candidate_count
candidate_signal_count
domains_with_conflicts
score_mutation_allowed
verdict_mutation_allowed
boundary
```

### conflict_resolver_audit

每个 domain 一条审计记录：

```text
version
domain
candidate_count
top_candidate_id
top_confidence
runner_up_candidate_id
runner_up_confidence
confidence_gap
signal_bound_candidate_count
top_source_signal_count
source_type_counts
conflict_types
resolution_policy
needed_question
score_mutation_allowed
boundary
```

## 接入点

### DecisionEngine

`build_decision_result` 改为：

```text
DecisionCandidate Builder
-> ConflictResolver
-> DecisionVerdict
```

`DecisionEngineResult` 增补：

- `conflict_resolver_summary`
- `conflict_resolver_audit`

### CentralReadingState

中枢状态增补：

- `conflict_resolver_summary`
- `conflict_resolver_audit`

后续 UI/Admin 可以直接读取它们，而不是再解析 debug 文本。

## 验收标准

1. 旧分支冲突用例仍然产生 `mixed` Verdict。
2. DCA-15 signal-bound candidate 用例的 Verdict 不变。
3. `DecisionEngineResult.conflict_resolver_summary.score_mutation_allowed` 为 `False`。
4. `DecisionEngineResult.conflict_resolver_summary.verdict_mutation_allowed` 为 `False`。
5. Runtime smoke 的 `DecisionVerdict` 数量保持 9。
6. `CentralReadingState` 能看到 conflict resolver 摘要和 domain audit。

## 执行结果

执行状态：已完成 DCA-15 ConflictResolver 增强阶段基础落地。

完成内容：

- 新增 `v30.brain.conflict_resolver`。
- 新增 `DECISION_CONFLICT_RESOLVER_VERSION = v30.decision_conflict_resolver.v1`。
- `DecisionEngine` 改为先调用独立 `resolve_decision_conflicts`，再生成 `DecisionVerdict`。
- `DecisionEngineResult` 增补 `conflict_resolver_summary / conflict_resolver_audit`。
- `DecisionVerdict.trace` 增补当前 domain 的 `conflict_resolver` audit。
- `CentralReadingState` 顶层输出 `conflict_resolver_summary / conflict_resolver_audit`。
- `v30.brain.__init__` 导出 `resolve_decision_conflicts` 和版本号。

当前边界：

- `score_mutation_allowed = False`
- `verdict_mutation_allowed = False`
- `llm_text_as_fact_used = False`
- 仍由 `DecisionVerdict` 作为用户侧断语来源。

验证结果：

```text
../.venv312/bin/python -m py_compile v30/brain/conflict_resolver.py v30/brain/decision_engine.py v30/brain/contracts.py v30/brain/reading_engine.py v30/brain/__init__.py tests/unit/test_decision_conflict_resolver.py
../.venv312/bin/pytest tests/unit/test_decision_conflict_resolver.py tests/unit/test_signal_based_decision_candidate_builder.py tests/unit/test_decision_centered_architecture.py tests/unit/test_production_signal_registry.py -q

14 passed in 0.49s
```

Smoke 结果：

```text
DecisionVerdict count 保持 9。
conflict_resolver_summary 已进入 central_reading_state。
conflict_resolver_audit 已进入 central_reading_state。
```

## 后续阶段

DCA-16 再进入 signal-based 权重增强和训练验证闭环：

```text
ConflictResolver audit
-> practitioner feedback
-> training examples
-> validation replay
-> candidate/conflict policy weight update
```

在 DCA-16 之前，ConflictResolver 只做解释和审计，不直接改变命理裁决。
