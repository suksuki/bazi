# V19 P46 Rule Graph Orchestrator

## 目标

P46 将知识库和规则链接入测算系统的路径选择层。

这一步采用图结构思想，而不是引入重型 GNN/RL：

- 八字结构被转换为图节点和边。
- 用户问题被转换为意图。
- 规则候选按命盘图和问题意图召回。
- 路径使用确定性评分和仲裁。
- 回答前执行审计，不允许预测文本或运行层越权。

## 实时链路

```text
chart + time_context
→ chart rule graph
→ question intent
→ candidate rule retrieval
→ path scoring
→ arbitration
→ answer pre-audit
→ guided question / answer context
```

## 图结构

当前图节点包括：

- 四柱位置。
- 天干。
- 地支。
- 藏干。
- 五行。
- 十神标签。
- 地支关系。
- 大运 / 流年时间层。

当前图边包括：

- `has_stem`
- `has_branch`
- `contains_hidden_stem`
- `maps_to_ten_god`
- `emits_feature`
- `has_time_stem`
- `has_time_branch`

## 路径选择

路径选择使用确定性评分：

- 问题意图匹配。
- 规则专题 lane 匹配。
- 规则 domain 匹配。
- 命盘图 feature 匹配。
- 风险等级。
- canary 状态。

仲裁规则：

- 本命结构优先于时间层。
- 显性层优先于藏干背景层。
- R2 仍只进入 shadow scoring。
- canary 只允许内部结构信号。
- 不输出领域预测。

## GNN/RL 插槽

P46 预留但不启用：

- GNN：未来用于 path embedding 或 rerank。
- RL：未来用于问题排序、对话策略，不用于核心规则真假判断。

## 当前接入点

- `build_guided_question_context`：加入 `rule_graph_context`，并把 selected paths 转成动态问题信号。
- `build_guided_question_answer`：加入 `rule_graph_context` 和 `rule_graph_answer_audit`，作为回答前审计上下文。

## 边界

- 不启用生产规则 engine。
- 不改变用户回答的结论。
- 不输出预测词。
- 不输出内部 debug 字段。
- 只做 chart-specific path selection。
