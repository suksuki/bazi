# V19 P31D 高优先专题智能门禁干跑

## 定位

P31D 接在 P31C 后面，用智能门禁干跑加速专题规则转化。

它只做筛选和审计：

- 低风险模型进入 shadow proposal-ready。
- 高风险模型继续阻断。
- 不启用运行时规则。
- 不输出领域预测。

## 入口

```text
v19.synthetic_validation.priority_topic_conversion.run_p31d_priority_topic_smart_gate
```

## 当前结果

- 模型数：28
- shadow proposal-ready：22
- blocked：6
- runtime 激活：0

## 通过门槛

- P31C regression 必须 pass。
- 模型风险等级只能是 R1/R2。
- 每个模型必须有完整 eval 样本。
- `activation_allowed` 必须为 false。
- 禁止输出必须包含 fortune。

## 当前阻断项

R3 继续阻断：

- 成格 / 破格
- 救应
- 清浊 / 混杂
- 相神
- 事业 / 职业结构
- 格局事业承接

这些不是失败，而是正确的安全门禁：它们需要更细解释器和安全审阅。
