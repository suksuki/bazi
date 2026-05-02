# V20 Bazi Feature Graph Model

## 1. Direction

V20 mainline is no longer centered on "rules, portraits, and question recommendation" as separate systems. The core is:

```text
Find the real Bazi features first.
```

Everything downstream must be driven by discovered Bazi features:

```text
Bazi knowledge base
-> Bazi feature discovery
-> structural decision state
-> topic projection
-> portrait
-> question recommendation
-> interaction
-> evidence-based answer
```

The adopted modeling direction is:

```text
Symbolic Expert System
+ Bazi Knowledge Graph
+ Defeasible Reasoning
+ Certainty Factor
+ Traceable Explanation
```

In Chinese:

```text
符号专家系统
+ 八字知识图谱
+ 可反证裁决
+ 置信因子
+ 可追踪解释链
```

This matches Bazi measurement because Bazi is not label classification, and it is not a simple rule-hit system. A practitioner-style measurement follows:

```text
事实成立
-> 机制成立
-> 反证检查
-> 强弱权衡
-> 岁运引动
-> 主题投射
-> 边界表达
```

## 2. Feature Spine vs Feature Graph

These two concepts must remain separate.

```text
Feature Graph = internal reasoning model
Feature Spine = product mainline contract
```

The internal model may contain graph-like reasoning structures, but UI, question recommendation, answer generation, and user-facing layers must not directly consume internal graph/debug objects.

The product-facing contract is:

```text
BaziFeature[]
QuestionCandidate[]
EvidencePack
AnswerPlan
```

Correct relationship:

```text
ChartFacts
-> FactGraph / lightweight fact objects
-> RulePath / MechanismPath
-> FeatureGraph / lightweight feature objects
-> BaziFeature[]
-> QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
```

## 3. Required Projection Layer

The model must include a projection layer.

Codex's earlier four-layer model was:

```text
FactGraph
-> FeatureGraph
-> MechanismGraph
-> DecisionGraph
```

V20 requires a fifth layer:

```text
TopicProjection
```

Full target chain:

```text
FactGraph
-> FeatureGraph
-> MechanismGraph
-> DecisionGraph
-> TopicProjection
-> BaziFeature[]
-> QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
```

Reason: the user does not ask for internal rule hits. The user asks about:

```text
事业
财富
关系
感情
健康
性格/行为模式
大运流年
下一步应该问什么
```

Without `TopicProjection`, the system can discover internal features but cannot reliably transform them into measurement topics.

## 4. Decision State Is Not Fate Conclusion

`DecisionGraph` must not output deterministic fate conclusions. It outputs structural states.

Required states:

```text
confirmed        明确成立
candidate        候选成立
weak_candidate   弱候选
blocked          被阻断
countered        有明显反证
mixed            成而不纯
volatile         岁运引动后波动
requires_review  需要命理师复核
out_of_scope     当前证据不足，不输出
```

Example:

```text
有财星
```

must not directly become:

```text
财运好
```

It must pass through:

```text
财星存在
-> 来源：天干/地支/藏干
-> 是否有根
-> 是否透出
-> 是否受冲合刑害
-> 日主是否能承载
-> 是否有食伤生财
-> 是否有比劫夺财
-> 是否被官杀/印星改写机制
-> 岁运是否引动
-> 投射为财富主题下的材料、机会、承接、波动、风险
```

## 5. Phase 1 Scope

Do not build a heavy graph platform in Phase 1.

Phase 1 should use lightweight typed objects:

```text
FactNode
EvidenceAtom
RulePath
MechanismPath
CounterEvidence
DecisionState
BaziFeature
TraceNode
```

Phase 1 runnable chain:

```text
ChartFacts
-> CoreInference
-> EvidenceAtom[]
-> RulePath[]
-> MechanismPath[]
-> DecisionState[]
-> BaziFeature[]
-> QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
-> deterministic answer
```

The internal model may be called graph-oriented, but implementation should stay simple until the mainline is stable. Property Graph, graph index, embedding, and learning-to-rank are later steps.

## 6. Priority

V20 must not become a knowledge management system. Knowledge exists to drive measurement.

Implementation priority:

```text
P0: ChartFacts / calendar accuracy
P0: core Bazi fact extraction
P0: ten-god / hidden-stem / branch-relation / strength evidence
P0: RulePath -> BaziFeature
P0: BaziFeature -> user-understandable question / evidence / answer
P1: Knowledge Graph
P1: full Defeasible Reasoning
P2: Certainty Factor calibration
P3: learning / embedding / learning-to-rank
```

Main actor:

```text
八字测算主线
```

Not:

```text
知识管理系统
```

## 7. LLM Position

LLM is allowed as expression and interaction support, not as core fate arbitration.

LLM can do:

```text
用户意图理解
问题归类
追问生成
AnswerPlan 自然语言表达
多语言改写
用户反馈摘要
命理师风格解释
复杂证据链可读化
```

LLM must not do:

```text
生成 ChartFacts
判断用神忌神
直接裁决格局成败
直接判断财运好坏
覆盖 DecisionGraph
修改 RuleGraph
绕过 EvidencePack
```

Allowed position:

```text
BaziFeature[]
+ EvidencePack
+ AnswerPlan
-> LLM Expression Adapter
-> Verifier
-> user output
```

## 8. Final Mainline

V20 should move from:

```text
知识库
-> 特征发现
-> 规则裁决
-> 画像
-> 推荐问题
```

to:

```text
八字事实
-> 命理机制链
-> 反证裁决
-> 主题投射
-> 用户问题
-> 证据化回答
```

This is the architectural turn that separates V20 from V19.

