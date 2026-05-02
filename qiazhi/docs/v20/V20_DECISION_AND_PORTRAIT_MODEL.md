# V20 裁决链路与画像层模型

## 总目标

V20 的裁决链和画像层不再依赖手工 `if rule_key == ...` 作为主系统。主线采用：

```text
RuleSpec Runtime
-> Defeasible ArgumentNode
-> DecisionState
-> RuleDecision
-> MainlineDecision
-> TopicProjection
-> PortraitProjection
-> DynamicPortrait
-> QuestionCandidate
-> AnswerPlan
```

旧手工逻辑只保留为兼容桥，用于保护当前产品输出和测试稳定性。

## 裁决模型

模型名称：

```text
V20 Bazi Defeasible Decision Model
八字可反证裁决模型
```

核心思想：

```text
事实不是结论。
规则命中不是结论。
规则命中要进入论证节点。
论证节点接受支持、反证、阻断、岁运引动和主题投射。
最终只输出结构状态，不输出命运断语。
```

### 算法组合

```text
RuleSpec Production System
+ Defeasible Argumentation
+ Certainty / Fuzzy Scoring
+ Topic Projection
```

成熟模型参考：

- Production System / Rete：用于大量规则匹配事实。
- Defeasible Reasoning / Argumentation Framework：用于规则成立但可被反证压制。
- Certainty Factor：用于专家系统第一版置信评分。
- Fuzzy Scoring：用于强弱、承载、寒暖、偏枯等非 0/1 判断。

### 决策状态

```text
confirmed        明确成立
candidate        候选成立
weak_candidate   弱候选
mixed            成而不纯
volatile         岁运引动
countered        有反证
blocked          被阻断
requires_review  需要复核
out_of_scope     不进入输出
```

### 评分策略

```text
decision_score =
  rule_match_score
+ status_weight
+ evidence_weight
+ projection_weight
- counter_evidence_penalty
- blocked_penalty
```

评分只用于排序，不代表吉凶。

## 画像模型

模型名称：

```text
V20 Portrait Projection Model
八字画像投射模型
```

画像不是性格标签，而是结构轴：

```text
PortraitAxis = 当前盘在某个命理维度上的结构投影
```

画像层输入：

```text
DecisionState[]
MainlineDecision[]
TopicProjection[]
BaziFeature[]
```

画像层输出：

```text
PortraitProjection
PortraitAxis[]
PortraitItem[]
DynamicPortrait
```

### 画像轴

```text
micro_axis      日主、十神、五行、地支、宫位
decision_axis   强弱、格局、用神、反证、纯杂
macro_axis      财富、事业、关系、感情、健康
time_axis       大运、流年、引动、波动
```

## LLM 位置

LLM 可以解释裁决和画像，但不能生成核心裁决：

```text
BaziFeature + DecisionState + EvidencePack + PortraitProjection
-> LLM Expression Adapter
-> Verifier
-> 用户输出
```

禁止：

```text
LLM 直接判断用神
LLM 直接裁决格局
LLM 覆盖 DecisionState
LLM 绕过 EvidencePack
```

## Phase 1 落地

当前 Phase 1 实现：

```text
RuleSpec Runtime
-> ArgumentNode
-> DecisionState
-> RuleDecisionCandidate
-> MainlineCandidate
-> PortraitProjection
```

保留旧决策链作为兼容桥：

```text
legacy RuleHit / RuleDecision = compatibility bridge
RuleSpec Defeasible Model = primary decision model
```
