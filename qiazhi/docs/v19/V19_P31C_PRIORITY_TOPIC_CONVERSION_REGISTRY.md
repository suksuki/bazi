# V19 P31C 高优先专题转换注册表

## 定位

P31C 不再补目录，而是把“部分”状态的高优先知识推进到可测试的新框架：

- 条件模型
- 正反样本
- 干扰样本
- 回归门禁
- 不启用运行时规则

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.build_p31c_priority_topic_conversion_registry
v19.synthetic_validation.priority_topic_conversion.run_p31c_priority_topic_regression
```

## 当前批量结果

- P0/P1 partial 项：155
- 已接入 P28-P30 链路的十神机制案例：24
- P31C 新增条件模型：28
- P31C eval 样本：112
- 运行时激活：0

## 新增条件模型分布

| lane | 数量 |
|---|---:|
| regular_pattern | 10 |
| pattern_quality | 4 |
| time_activation | 7 |
| wealth_domain_bridge | 2 |
| career_domain_bridge | 4 |
| palace_domain_bridge | 1 |

## 样本规则

每个模型固定生成 4 类样本：

- positive：核心路径满足
- negative：关键条件轴缺失
- distractor_time：时间层干扰，不改写本命
- distractor_hidden：藏干或背景层干扰，不升为主机制

## 通过标准

- 每个模型 4 个样本齐全。
- 正例必须输出 expected signal。
- 非正例必须把当前模型放入 forbidden signals。
- 非正例至少一个条件轴 blocked。
- 禁止文本合同必须包含发财、破财、疾病、应期等高风险词。
- runtime 激活数必须为 0。

## 后续

P31D 可以基于 P31C 注册表继续做：

- 格局正格与格局质量专题解释器。
- 时间引动专题解释器。
- 财富/事业领域承接解释器。
- P31C 样本导出为统一 eval dataset。
