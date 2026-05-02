# V20 八字特征、智能问题与交互系统模型

## 总目标

这一层承接前面的知识库、RuleSpec、裁决链和画像层：

```text
BaziFeature
-> FeatureState
-> DecisionState
-> PortraitAxis
-> QuestionIntent
-> QuestionCandidate
-> InteractionSignal
-> AnswerPlan
```

核心原则：

```text
特征不是结论。
问题不是文案列表。
交互不是即时改规则。
```

## FeatureState Model

模型名称：

```text
V20 Feature State Fusion Model
八字特征状态融合模型
```

输入：

```text
BaziFeature[]
DecisionState[]
MainlineDecision[]
PortraitAxis[]
ArgumentNode[]
```

输出：

```text
FeatureState[]
PriorityFeature[]
EvidenceGapFeature[]
```

特征状态：

```text
active
available
requires_review
evidence_gap
blocked_or_countered
```

优先级评分：

```text
feature_priority =
  feature_confidence
+ decision_score
+ mainline_score
+ portrait_axis_score
+ argument_score
```

## QuestionIntent Model

模型名称：

```text
V20 Question Intent Model
智能问题意图模型
```

输入：

```text
MainlineDecision
PortraitAxis
FeatureState
DecisionState
```

输出：

```text
QuestionIntent[]
QuestionBinding[]
SelectedQuestionIntent
```

问题意图类型：

```text
confirm_structure       确认结构
explore_candidate       展开候选
collect_evidence        补证据
resolve_mixed_state     裁决纯杂
inspect_timing_trigger  查看岁运引动
ask_practitioner_review 命理师复核
explain_boundary        解释边界
```

## InteractionSession Model

模型名称：

```text
V20 Interaction Signal Fusion Model
交互信号融合模型
```

输入：

```text
SelectedQuestion
QuestionIntent
PractitionerSelection
LatentEventAnswer
DecisionReport
```

输出：

```text
InteractionSignal[]
NextAction[]
```

交互信号只允许：

```text
rerank questions
refresh evidence pack
record calibration signal
prepare review proposal
```

禁止：

```text
直接改 ChartFacts
直接改 RuleSpec
直接改 DecisionState
直接生成命运断语
```

## 智能算法选择

Phase 1 使用成熟、可解释的混合模型：

```text
Feature State Fusion
+ Utility-based Question Ranking
+ Intent Classification by Decision State
+ Session Signal Fusion
+ Validation-gated Calibration
```

后续可扩展：

```text
Learning-to-rank
Bayesian calibration
Bandit exploration for follow-up questions
Embedding recall for knowledge context
```

这些学习模型只能调排序、召回和置信权重，不能绕过 EvidencePack 或 RuleSpec 裁决。
