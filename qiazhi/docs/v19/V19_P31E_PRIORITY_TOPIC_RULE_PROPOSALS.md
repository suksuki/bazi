# V19 P31E 高优先专题规则提案生成

## 定位

P31E 接在 P31D 后面，把 shadow proposal-ready 的专题模型批量转成 Bazi rule proposals。

本阶段只做：

- 创建 rule proposal。
- 运行 schema validation。
- 停在 `validation_ready`。

本阶段不做：

- 审批。
- 版本发布。
- Rule DB engine activation。
- 运行时回答变更。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31e_priority_topic_rule_proposal_generation
```

## 当前结果

- P31D shadow-ready 模型：22
- 创建 rule proposals：22
- validation-ready：22
- validation-failed：0
- runtime 激活：0

## proposal domain 分布

| domain | 数量 |
|---|---:|
| structural_relation | 13 |
| time_structure | 7 |
| income_stability | 2 |

## lane 分布

| lane | 数量 |
|---|---:|
| regular_pattern | 10 |
| time_activation | 7 |
| wealth_domain_bridge | 2 |
| career_domain_bridge | 2 |
| palace_domain_bridge | 1 |

## 边界

这些 proposal 仍然只是结构信号候选：

- 格局只输出候选，不确认成格、贵贱、职业或财富结果。
- 时间引动只输出触发层，不输出事件和应期。
- 财富/事业承接只输出问题语境，不输出收入、职位或成败。

## 后续

P31F 可以把 validation-ready proposal 自动组成 review packet，进入审批前置包；仍不自动批准。
