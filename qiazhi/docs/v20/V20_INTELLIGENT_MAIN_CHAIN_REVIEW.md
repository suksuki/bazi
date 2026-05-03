# V20 智能主链审计与清理

## 当前主链

V20 现在固定为一条测算主线：

```text
ChartFacts
-> KnowledgeUnit
-> KnowledgeRuleDefinition
-> RuleRuntimeReport
-> BaziFeatureContext
-> DomainDecisionReport
-> TopicProjection / PortraitProjection
-> QuestionAgent
-> EvidencePack
-> AnswerPlan
-> DeterministicAnswer
-> Optional LLM Practitioner Adapter
-> ArbitrationLoop
-> TrainingIteration
```

这条链路的职责边界是：

- `KnowledgeUnit`：命理知识来源，给理论、边界、hook 和规则原子。
- `KnowledgeRuleDefinition`：把知识转成可运行规则，不再卡在候选态。
- `RuleRuntimeReport`：让单个八字碰撞全部规则并记录命中、弱命中、阻断和证据。
- `BaziFeatureContext`：特征元数据层，是后续画像、问题、回答、训练的计算总线。
- `DomainDecisionReport`：裁决层，输出结构性决策，不直接输出命运断语。
- `TopicProjection / PortraitProjection`：画像层，只做命理师视角的标签化和主题投射，不复用规则标题。
- `QuestionAgent`：根据画像、特征、已回答问题和当前问题刷新下一批智能问题。
- `EvidencePack / AnswerPlan`：把可解释证据整理成回答计划。
- `LLM Practitioner Adapter`：只负责命理师口吻、多语言和白话表达，不生成事实、不裁决规则。
- `ArbitrationLoop`：把 mixed、countered、requires_review 等冲突快照送入命理师校准、反例权重和 replay eval。
- `TrainingIteration`：后台自学习闭环，优化权重、排序、覆盖和问题策略。

## 本轮清理

已经从产品主链清掉：

- V19 档案迁移前端入口。
- V19 档案迁移后端 API。
- V19 档案迁移脚本。
- 决策层中的旧桥接命名，改为 `core_seed_decision_status`。

保留：

- V19 auth session 导入。它只用于本地账号/Admin 过渡，不进入测算主链。
- V19/legacy 文档审计。它只作为资料来源，不进入运行时。
- `knowledge.migration`。它是知识资料审计工具，不是档案/用户主链。

## 主链健康检查

新增统一审计脚本：

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi
python3.12 v20/scripts/run_main_chain_review.py
```

它会一次检查：

- 知识库单元数量和领域覆盖。
- 知识规则库定义、规则原子、画像输出、问题输出。
- 规则库验证是否通过。
- 一个样例八字是否能生成 FeatureContext、裁决、画像、问题、AnswerPlan 和回答。
- 推荐问题是否数量不足或标题过于雷同。
- mixed/countered/requires_review 是否被整理成仲裁学习样本。

需要连同学习闭环一起 dry-run 时：

```bash
python3.12 v20/scripts/run_main_chain_review.py --include-training --progress
```

这个命令不写数据库、不改规则、不改用户档案。

## 后台学习闭环

日常快速迭代：

```bash
python3.12 v20/scripts/run_training_iteration.py --progress
```

默认动态裁决抽样 12 个 case，规则迭代抽样 120 条，且不跑重型 replay eval 与 rule/portrait/question batch，保证主链路审计可以快速反馈。需要长跑时：

```bash
python3.12 v20/scripts/run_training_iteration.py --progress --dynamic-limit 0 --rule-iteration-limit 0 --include-replay-eval --include-rule-batch
```

写本地 artifact：

```bash
python3.12 v20/scripts/run_training_iteration.py --write --progress
```

自进化清单：

```bash
python3.12 v20/scripts/run_self_evolution.py --write --progress
```

规则冲突与反证仲裁：

```bash
python3.12 v20/scripts/run_arbitration_loop.py --progress
python3.12 v20/scripts/run_arbitration_loop.py --write --progress
```

518K 只作为离线覆盖、相似盘、权重和排序素材：

```bash
python3.12 v20/scripts/run_full_precompute.py --run-id v20_full_518k_mainline --limit 518400 --status-every 500 --progress
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --progress --no-sqlite
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_mainline --training
```

## 继续加强方向

下一步只沿主链增强：

1. 让 `KnowledgeUnit` 覆盖更多盲派、做功、格局、岁运、应用主题。
2. 让 `KnowledgeRuleDefinition` 全量进入 active runtime。
3. 让 `BaziFeatureContext` 承载更多 blockers、amplifiers、activation_sources。
4. 让画像只消费 TopicProjection，不再像规则列表。
5. 让 QuestionAgent 根据已回答问题、画像主轴和 FeatureContext 动态换问题。
6. 让训练脚本只优化排序、权重、覆盖和置信，不直接改事实或命运结论。
7. 让 `ArbitrationLoop` 把规则打架、反证压制和低置信复核变成稳定的学习样本。
