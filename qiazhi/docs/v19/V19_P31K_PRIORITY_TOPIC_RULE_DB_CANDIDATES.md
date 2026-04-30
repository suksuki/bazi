# V19 P31K 高优先专题 Rule DB Candidates

## 定位

P31K 接在 P31J 后面，把 P31I rule version 中的 22 条规则写入 Rule DB 候选记录。

本阶段允许：

- 创建 Rule DB candidate records。
- 保留 proposal/version/release 来源。
- 标记为 engine adapter candidate。

本阶段不允许：

- engine activation。
- runtime activation。
- 直接改变回答。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31k_priority_topic_rule_db_candidates
```

## 当前结果

- versioned proposals：22
- Rule DB candidates：22
- imported：22
- blocked：0
- engine enabled：0
- runtime mutation：false

## 为什么暂不启用

P31E/P31I 的规则来自条件模型和审核链路，但还没有完成 Rule DB adapter 的 `structured_facts` 匹配器。因此 P31K 只落候选记录，不进入结构信号引擎。

## 后续

P31L 可以基于这些候选补 adapter facts、自动正反样本和合成回归门禁，再决定是否 shadow enable。
