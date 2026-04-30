# V19 P81 标签画像本体与互动校准

## 目标

将结构画像从“粗标签展示”升级为主链画像引擎：

```text
命盘事实
→ 标签本体
→ 规则图知识路径支持
→ 证据评分
→ 内部贝叶斯式置信度
→ 画像标签
→ 推荐提问 / 回答证据 / 互动校准
```

旧的粗标签生成链路不再作为主逻辑保留。底层 facts 和 vectors 只作为画像编译器输入。

## 标签本体字段

每个标签必须包含：

- `label_id`
- `family`
- `required_evidence`
- `source_layers`
- `confidence_rule`
- `question_hooks`
- `answer_kinds`
- `answer_boundary`
- `topic_lanes`
- `domains`
- `vector_key`
- `prior`
- `user_calibration_hooks`
- `analyst_confirmation_hooks`

## 评分模型

当前采用确定性评分，不引入 GNN/RL：

```text
compiled_score =
  vector_score * 0.52
+ evidence_score * 0.18
+ rule_graph_support * 0.22
+ prior * 0.08
- penalty
```

`posterior_confidence` 是内部贝叶斯式置信度，用于排序和提问，不向用户输出概率断言。

## 知识路径支持

Rule Graph 选中的知识路径会进入每个标签：

- `knowledge_evidence_ids`
- `rule_evidence_ids`
- `score_breakdown.rule_graph_support`

这些证据只提高标签置信度和问题相关性，不直接激活规则，也不改写结论。

## 互动校准

画像需要通过用户和命理师逐步变清晰。

普通用户侧：

- 询问事件阶段、状态变化、收入稳定性、时间节点感受。
- 用于校准画像置信度和推荐问题顺序。
- 不直接修改规则库。

命理师侧：

- 确认标签是否满足证据门槛。
- 确认是否有同层作用路径。
- 确认时间层是否被误用为本命结构。
- 作为 audit 信号进入后续合成验证。

## 边界

- 用户反馈只校准画像和问题路径。
- 命理师确认是审核信号，不是自动规则变更。
- 规则变更必须经过知识库、规则图和合成数据验证。
- 不输出硬喜忌、吉凶、应期、财富或健康断语。

## 验收

- 每个合成盘都必须产生 ontology compiled labels。
- 每个标签必须有 `question_hooks` 和 `answer_boundary`。
- 每个合成盘必须有 user hooks 和 analyst hooks。
- 每个合成盘必须绑定至少一条 Rule Graph knowledge path。
- 合成回归不能出现 forbidden text。
