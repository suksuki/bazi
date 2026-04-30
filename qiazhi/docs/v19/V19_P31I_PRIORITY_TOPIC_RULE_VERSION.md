# V19 P31I 高优先专题 Rule Version

## 定位

P31I 接在 P31H 后面，把已经受控 approved 的 P31E rule proposals 汇总成 Bazi rule version record。

本阶段允许：

- 创建 rule version record。
- 把纳入版本的 proposal 状态推进为 `active_record`。

本阶段仍然不允许：

- Rule DB engine activation。
- 运行时回答变更。
- 绕过 P12/P11 合成回归门禁。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31i_priority_topic_rule_version_record
```

## 当前结果

- approved proposals：22
- rule version records：1
- included proposals：22
- rule count：22
- runtime mutation：false

## 范围控制

P31I 只收纳来自 P31E 的 rule proposals：

- `rule_id` 以 `v19.p31e.` 开头。
- evidence source 为 `p31e_priority_topic_rule_proposal_generation`。
- proposal 必须已经是 `approved`。

## 后续

P31J 可以把该 rule version 写入 governance release manifest。运行时激活仍需要独立的 Rule DB gate 和合成回归。
