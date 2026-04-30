# V19 P31L 高优先专题 Adapter Readiness

## 定位

P31L 接在 P31K 后面，对 22 条 Rule DB candidates 做 engine adapter readiness dry-run。

本阶段只做：

- 运行 smart gate dry-run。
- 输出候选规则为何不能 engine enable。
- 明确下一步 adapter 补齐项。

本阶段不做：

- engine activation。
- runtime activation。
- 回答链路变更。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31l_priority_topic_adapter_readiness
```

## 当前结果

- Rule DB candidates：22
- ready candidates：0
- selected：0
- blocked：22
- engine enabled：0
- runtime mutation：false

## 当前主要 blocker

- `missing_structured_facts`：P31E 条件模型还没有转成 Rule DB adapter 可匹配的 structured facts。
- `missing_synthetic_gate_candidate`：候选规则还没有通过 adapter 级正反样本和合成回归。

## 后续

P31M 应该补 P31E/P31K 候选的 adapter facts 和样本生成器，而不是直接打开 engine。
