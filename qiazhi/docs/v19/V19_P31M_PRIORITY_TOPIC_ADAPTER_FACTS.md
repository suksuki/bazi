# V19 P31M 高优先专题 Adapter Facts

## 定位

P31M 接在 P31K/P31L 后面，给 22 条 P31E Rule DB candidates 补最小 adapter structured facts 和 synthetic gate marker。

本阶段允许：

- 写入 `condition.structured_facts`。
- 增加 `synthetic_gate_candidate` 标记。
- 运行 adapter contract eval 和 smart gate dry-run。

本阶段不允许：

- engine activation。
- runtime activation。
- 直接改变回答。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31m_priority_topic_adapter_fact_enrichment
```

## 当前结果

- Rule DB candidates：22
- adapter facts updated：22
- eval samples：88
- eval failed：0
- gate selected：22
- gate blocked：0
- engine enabled：0
- runtime mutation：false

## 边界

P31M 只说明这些规则已经具备“进入 adapter synthetic gate 的候选形态”，不说明它们已经可以生产启用：

- structured facts 仍是最小锚点。
- 还未跑信号级正反样本。
- engine 仍保持 disabled。

## 后续

P31N 应该针对这些 adapter facts 生成信号级正反样本，验证是否会误触发或漏触发，再决定是否进入 shadow activation。
