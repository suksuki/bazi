# V20 Self-Evolution Backend Loop

V20 的下一阶段不是继续手工堆规则，而是把知识库、规则、八字特征、裁决链、画像、问题推荐和命理师对话纳入同一个后台自进化闭环。

核心原则：

```text
知识库给来源
规则系统给可执行候选
合成八字给边界验证
影子评估给离线对比
DecisionRegistry 给晋级裁决
运行时只消费已通过的稳定版本
```

LLM 可以参与候选生成、表达优化、反例总结和多语言改写，但不能直接生成八字事实、裁决用神格局、绕过证据包输出结论，或者直接修改线上运行时。

## 当前状态

V20 已经具备后台训练闭环的主要零件：

- `v20/scripts/run_training_iteration.py`
- `v20.learning.training_iteration.run_training_iteration`
- `v20.validation.rule_synthetic`
- `v20.learning.rule_activation`
- `v20.learning.rule_subcondition_split`
- `v20.learning.rule_replay_eval`
- `v20.learning.decision_registry_review`
- `v20.learning.practitioner_calibration_training`
- `v20.learning.dynamic_decision_training`
- `v20.corpus.full_precompute`

一次轻量 dry-run 当前通过：

```text
dynamic_decision_training       pass
practitioner_calibration        ready
rule_synthetic_training         ready
knowledge_rule_review_overlay   ready
rule_subcondition_split         ready
rule_replay_eval                ready
decision_registry_review        ready
corpus_preview                  ready
decision_training_plan          ready
```

当前链条的性质是：

```text
offline script only
local artifact only
no untraced runtime override
no user-facing training surface
```

这是正确的。下一步要补的不是再造一套规则系统，而是把这些专项报告升级成统一的 `EvolutionRun`。

## 目标链路

```text
KnowledgeBase
-> ActiveGeneration
-> SyntheticCaseGeneration
-> RuntimeReplay
-> Feature/Rule/Portrait/Dialog Evaluation
-> ShadowComparison
-> DecisionRegistry
-> Versioned Artifact Package
-> Scoped Runtime Promotion
```

产品主链仍然保持：

```text
ChartFacts
-> CoreInference
-> EvidenceAtom[]
-> RulePath[]
-> MechanismPath[]
-> DecisionState[]
-> TopicProjection
-> BaziFeature[]
-> QuestionActive[]
-> EvidencePack
-> AnswerPlan
-> LLM Expression Adapter
```

自进化系统只优化这个链条中的候选和参数，不允许黑箱模型替代裁决层。

## EvolutionRun

建议新增统一对象：

```text
EvolutionRun
```

字段：

```text
run_id
started_at
source_versions
knowledge_snapshot
rule_catalog_snapshot
synthetic_suite_snapshot
corpus_snapshot
active_packages
eval_reports
active_replay_reports
decision_registry_records
promotion_recommendations
blocked_reasons
next_synthetic_case_requests
```

输出目录：

```text
v20/.runtime/local/training/evolution/<run_id>/manifest.json
v20/.runtime/local/training/evolution/latest.json
```

这个 manifest 是后续后台自学习、自调优、管理员 review 和版本晋级的唯一入口。

## 候选生成

### 规则候选

来源：

- 知识库目录和条目
- 现有 `RuleSpec`
- 规则 synthetic 失败项
- 子条件拆分报告
- corpus feature co-occurrence
- LLM draft，但只能生成候选

输出：

```text
RuleActive
EvidenceAtomActive[]
CounterEvidenceActive[]
SyntheticCaseRequest[]
```

晋级条件：

```text
contract validation
synthetic positive case
synthetic negative case
counterexample case
replay eval
DecisionRegistry approval
```

### 画像候选

来源：

- `DecisionState`
- `TopicProjection`
- `PortraitAxis`
- 用户问题意图
- 命理师回答校准报告

输出：

```text
PortraitAxisActive
PortraitToneActive
TopicProjectionActive
```

评价：

```text
是否来自当前盘证据
是否能回连规则裁决
是否避免宿命化表达
是否支持多语言表达
是否能服务财富、事业、感情、健康、关系等主题
```

### 八字特征候选

来源：

- `ChartFacts`
- 十神、藏干、强弱、合冲刑害、岁运引动
- 规则命中与反证压制
- feature coverage gap

输出：

```text
BaziFeatureActive
FeatureStateActive
FeatureTraceActive
```

评价：

```text
是否能解释来源
是否能被反证削弱
是否能映射到主题投射
是否能生成问题候选
是否能进入 EvidencePack
```

### 智能问题候选

来源：

- `BaziFeature[]`
- `QuestionIntent`
- `InteractionSession`
- 画像轴
- 用户当前问题

输出：

```text
QuestionActive
FollowupQuestionActive
ClarificationQuestionActive
```

评价：

```text
是否贴合当前盘
是否贴合用户问题
是否能引出有效反馈
是否避免泛泛而谈
是否有证据锚点
```

### 对话候选

来源：

- `AnswerPlan`
- `EvidencePack`
- LLM role prompt profile
- locale
- 用户反馈摘要

输出：

```text
PractitionerAnswerActive
RewriteActive
MultilingualVariant
SafetyReview
```

评价：

```text
白话程度
命理师口吻
证据一致性
多语言准确性
禁止绝对断语
禁止绕过裁决链
```

## 算法选择

P0 可立即落地：

- symbolic expert system
- defeasible reasoning
- certainty factor
- active learning for synthetic gaps
- feature co-occurrence mining
- replay evaluation
- learning-to-rank for question order
- Bayesian-style confidence calibration

P1 可增强：

- embedding retrieval for similar chart/rule/knowledge recall
- clustering for coverage gaps and counterexamples
- weak supervision for active_item grouping
- pairwise ranking for question and answer-plan preference

P2 暂缓：

- GNN rule graph embedding
- reinforcement learning dialog policy
- neural conclusion generation

暂缓原因不是这些模型没价值，而是 V20 目前最重要的是主链稳定、证据可追踪、候选可回滚。

## 合成八字验证

合成八字不是拿来学习“命运真值”，而是拿来验证结构碰撞：

```text
positive case
negative case
counterexample case
time-trigger case
mixed-state case
blocked-state case
out-of-scope case
```

每个规则、画像、特征和问题候选都应该能回答：

```text
它在哪些盘成立？
在哪些盘不成立？
在哪些盘成而不纯？
在哪些盘被反证压制？
大运流年引动后是否只输出波动状态？
是否会产生宿命化或医疗/财务绝对断语？
```

## 晋级状态

建议统一候选状态：

```text
draft
contract_validated
synthetic_ready
active_ready
needs_human_review
approved_for_active_package
approved_for_runtime_replaytime
approved_for_scoped_runtime
rejected
blocked
```

运行时只允许消费：

```text
approved_for_scoped_runtime
```

## 下一步实施

P0 先做三件事：

1. 新增 `v20.learning.self_evolution`，把现有训练迭代报告汇总为 `EvolutionRun`。
2. 新增 `v20/scripts/run_self_evolution.py`，支持 dry-run、write、status。
3. 在 manifest 中输出下一轮候选：
   - `rule_active_item_requests`
   - `portrait_active_item_requests`
   - `feature_active_item_requests`
   - `question_active_item_requests`
   - `synthetic_case_requests`

P0.5 把候选请求转成候选包：

```text
EvolutionRun
-> ActiveRequest[]
-> ActivePackage
-> validation_plan
-> DecisionRegistry review input
```

当前入口：

```text
v20.learning.active_generation.build_active_package
v20/scripts/run_active_generation.py
```

候选包只作为后台 artifact，不允许直接进入 runtime。

P1 再做：

1. 从失败项和覆盖缺口自动生成合成八字 case request。
2. 从知识库条目自动生成规则候选包。
3. 从画像和回答校准报告生成画像表达候选。
4. 从用户问题和当前盘特征生成问题排序候选。

P2 最后做：

1. 后台 admin artifact dashboard。
2. runtime replay A/B 对比。
3. DecisionRegistry 审批写入。
4. scoped runtime activation。

## 禁止事项

```text
不能让 LLM 直接改规则库
不能让 corpus 共现直接变成命理真值
不能让 synthetic pass 直接上线
不能让对话模型覆盖裁决链
不能把用户 UI 做成训练入口
不能输出无证据的发财、破财、疾病、必然、一生等绝对结论
```

V20 的自进化目标不是制造一个会胡乱自改的系统，而是制造一个能不断提出候选、验证候选、解释候选、回滚候选的命理测算系统。
