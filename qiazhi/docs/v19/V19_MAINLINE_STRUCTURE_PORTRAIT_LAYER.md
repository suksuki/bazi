# V19 Mainline Structure Portrait Layer

## 目标

在 Rule Graph 和推荐问题之间增加一层确定性的“结构画像层”：

```text
命盘事实
→ 结构标签
→ 数字画像
→ 推荐问题排序
→ 候选判断
→ 回答边界
```

它用于把八字知识库和规则库转成可解释、可排序、可验证的结构信号。它不是断命模型，也不是黑盒训练层。

## 三层模型

### 1. 结构标签

每个标签必须包含：

- `label_id`：稳定 ID
- `family`：所属画像族
- `value`：标签值
- `score`：内部排序分
- `confidence`：证据置信度
- `evidence_refs`：证据来源
- `candidate_statement`：允许对用户表达的候选判断
- `forbidden_outputs`：禁止输出的硬断语

第一批标签族：

- `strength`：日主承载、月令证据、透藏来源
- `useful_god`：用神/忌神候选边界
- `ten_god`：十神活跃度、财官印食伤可见度
- `wealth`：财星可见、财星稳定性、收入结构候选
- `branch`：冲合刑害破、三合三会、墓库
- `time`：大运/流年触发，仅作时间背景
- `pattern`：格局索引、成格/破格候选边界

### 2. 数字画像

画像向量只用于内部排序和候选判断，不直接展示为“分数断语”。

第一批向量：

```json
{
  "strength_capacity": 0.0,
  "useful_god_candidate_confidence": 0.0,
  "wealth_visibility": 0.0,
  "wealth_stability": 0.0,
  "ten_god_activity": 0.0,
  "branch_volatility": 0.0,
  "time_trigger_activity": 0.0,
  "pattern_index_strength": 0.0,
  "evidence_confidence": 0.0
}
```

### 3. 候选判断

只允许输出候选判断：

- 当前更像某类结构候选。
- 当前证据不足，只能保留为候选。
- 当前不支持直接判断用神忌神。

禁止输出：

- 你一定喜木火 / 忌金水。
- 必然发财、破财、应期、灾祸。
- 无证据的格局定论。

## 接入点

### Runtime

新增：

- `v19.structure_portrait.build_structure_portrait`

运行位置：

```text
rule_graph_runtime_context
→ structure_portrait
→ guided_question_context
→ guided_question_answer
```

### 推荐问题

`guided_question_context.question_personalization_context` 读取画像向量：

- `strength_capacity` 接近中间且置信度不足：提高强弱证据问题。
- `useful_god_candidate_confidence` 有候选但不充分：提高用神候选问题。
- `branch_volatility` 高：提高地支关系问题。
- `time_trigger_activity` 高：提高时间层问题。
- `wealth_visibility` 高但 `wealth_stability` 低：提高收入稳定性问题。
- `pattern_index_strength` 高：提高格局结构问题。

### 回答

回答中可以引用画像摘要，但只能作为“结构候选”和“证据来源”，不作为硬断言。

## 验证

回归要求：

- 合成盘之间画像向量不同。
- 合成盘之间首屏推荐问题不同。
- 用神/忌神回答没有证据时输出候选边界。
- 画像不会改写结果卡，不启用规则，不生成预测。
- 用户反馈短期只可影响排序和表达，不可直接修改标签真值。

## 后续插槽

当前只实现确定性画像。未来可接：

- 贝叶斯评分：内部不确定性排序。
- GNN：图路径 embedding / rerank。
- RL：问题排序和对话策略，不参与核心规则真值。
