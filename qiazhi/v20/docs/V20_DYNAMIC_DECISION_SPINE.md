# V20 Dynamic Decision Spine

V20 的主线重新定义为八字测算系统，而不是特征展示系统。

## 核心判断

之前的问题不在 UI，也不在 LLM，而在 runtime 把 `BaziFeature`、518K 预计算画像、规则候选和知识语义索引直接投影成画像与推荐问题。这样得到的是技术材料集合，不是命理师会使用的动态画像。

新的主线是：

```text
八字排盘
-> ChartFacts
-> 知识库规则 / 程序化规则
-> RuleHit
-> RuleDecision
-> DefeasibleDecisionModel
-> PortraitProjection / TopicProjection
-> FeatureStateModel
-> QuestionIntentModel
-> InteractionSession
-> QuestionCandidate
-> LLM practitioner answer
```

## 模块职责

- `knowledge`: 产生和维护结构化命理知识，不直接给用户画像结论。
- `rule`: 从知识库、程序模板、LLM 草案中生成离线规则草案，进入合成验证和晋升门槛。
- `decision`: 在当前八字上做规则命中、可反证裁决、主次排序和主题投射。
- `portrait_projection`: 只来自当前盘的 `DecisionState + MainlineDecision + TopicProjection`，不来自 518K 静态画像。
- `questions`: 从问题意图模型和主题投射生成用户可问的问题。
- `llm`: 使用裁决状态、主题投射画像和证据包，以命理师角色解释，不产生核心事实或规则真值。
- `corpus/learning`: 离线训练和覆盖验证，只由脚本或 admin 管理，不进入用户测算主链。

## 当前主线修正原则

用户测算页面只应该暴露命理师可读的动态裁决素材。`RuleDecision` 的 `label`、`portrait_tags`、`question_seeds` 必须优先表达命理关系，而不是内部工程标签。

核心规则输出要求：

- 伤官见官如果见印星缓冲，必须显示为“伤官见官见印缓冲”，并把问题导向“是否被印星缓冲”。
- 财星可见但日主承接不足时，必须显示“财星可见但日主承接需扶助”，并把问题导向“先看能不能承接”。
- 食伤生财必须同时保留食伤与财星两侧证据，不能只因证据排序暴露单边材料。
- 印星缓冲只作为事业压力的候选路径，不直接写成事业结果。

## 训练目标

不训练 LLM 本体。V20 训练自己的命理大脑：

1. 知识库训练：知识条目的权重、领域映射、规则映射、证据模板质量。
2. 规则库训练：规则条件权重、支持因子、削弱因子、冲突因子、触发因子。
3. 画像库训练：画像标签与规则裁决的映射、误导标签降权、推荐问题模板排序。
4. 裁决逻辑训练：规则是否成立、成立程度、主线/辅助、化解、是否需要时间层触发。

当前后台脚本入口：

```bash
./v20/scripts/run_dynamic_decision_training.py --progress
./v20/scripts/run_dynamic_decision_training.py --write --progress
./v20/scripts/run_dynamic_decision_training.py --status
./v20/scripts/run_question_ranking_training.py --progress
./v20/scripts/run_question_ranking_training.py --write --progress
./v20/scripts/run_question_ranking_training.py --status
./v20/scripts/run_practitioner_calibration_training.py --progress
./v20/scripts/run_practitioner_calibration_training.py --write --progress
./v20/scripts/import_calibration_postgres.py --ledger practitioner_calibration_ledger
./v20/scripts/run_training_iteration.py --write --progress
```

`run_training_iteration.py` 在 P1~P3 中会串起：
1) dynamic_decision_training（生成动态裁决和画像问题链路）
2) practitioner_calibration_training（命理师结构化选择信号）
3) question_ranking_training（基于决策-问题命中序列反推问题优先级）
4) rule_synthetic_training（规则覆盖/反例/子条件候选）
5) rule_portrait_batch（画像映射）

这个脚本专门检查：一个当前八字是否能从 `RuleDecision` 动态生成可用画像、用户会问的推荐问题、命理师可校准的结构化选项，以及后续可训练的裁决参数提案。它不写 Postgres，不修改规则真值，默认只输出 dry-run 报告。

`run_training_iteration.py` 是更上层的迭代入口，会串起动态裁决训练、规则合成验证、规则/画像批量验证和训练计划汇总。大计算量的 518K 全量预计算不自动跑，必须手动调用：

```bash
./v20/scripts/run_full_precompute.py --progress --limit 518400 --status-every 1000
```

全量预计算之后，Postgres 是权威存储。构建覆盖统计和训练素材时可以跳过本地 SQLite cache：

```bash
./v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k --progress --no-sqlite
./v20/scripts/import_corpus_postgres.py --run-id v20_full_518k --apply
```

SQLite 只允许作为一次性本地相似检索 cache，用于没有连 Postgres 时的 fallback，不是 V20 数据库主线。

## 命理师校准

命理师校准是 V20 的产品特色，但必须是结构化选择，不使用自由输入框作为核心裁决来源。

示例：

```text
日主强弱：
[偏强] [中和偏强] [中和] [中和偏弱] [偏弱] [待复核]

伤官见官：
[成立] [候选] [被印化] [被财通关] [不成立] [待复核]

格局判断：
[成格] [破格] [候选] [不取格] [待复核]

用神方向：
[扶身] [泄秀] [制杀] [通关] [调候] [待复核]
```

这些选择写入学习系统，用来训练裁决参数，不直接修改运行时规则真值。

对应脚本：

```bash
./v20/scripts/run_practitioner_calibration_training.py --progress
```

它读取 `practitioner_calibration_ledger`，统计每个结构化裁决项的选择分布，生成 `decision_parameters` 的离线训练提案。样本不足时只提示继续收集；样本达到门槛也只成为候选，仍必须通过合成验证和规则/画像批量验证。

本地 ledger 可以通过下面的 dry-run 检查导入计划：

```bash
./v20/scripts/import_calibration_postgres.py --ledger practitioner_calibration_ledger
```

真正写入 Postgres 必须显式加 `--apply`，并配置 `V20_DATABASE_URL`。导入目标是 `v20_feedback_ledger`，用于把本地采集的反馈/校准信号同步到权威存储。

## 518K 结构覆盖基线定位

518K 八字库是离线结构覆盖基线，不是画像真值库，也不是运行时测算主脑。

允许：

- 规则覆盖率
- 相似八字检索
- 规则共现统计
- 合成验证补洞
- 画像排序和问题排序的离线校准材料
- 决策参数离线训练

禁止：

- 直接生成用户画像结论
- 覆盖当前盘动态裁决
- 自动激活规则真值
- 在用户 UI 上展示训练细节

## 维度、隐藏属性与放大因子

V20 的主线不再只用 `domain` 平铺分类，而是使用“维度坐标”贯穿知识库、规则、画像、推荐问题和回答：

- 微观维度：日主、十神、五行、地支等命局内部结构。
- 裁决维度：格局、用神、强弱等需要复核的候选路径。
- 时间维度：大运、流年、流月与原局之间的显式触发背景。
- 宏观维度：财富、事业、关系、健康边界等用户关心的主题投影。

这里必须区分两类“隐藏”：

1. **结构隐藏属性**
   这是命局材料，例如藏干、墓库、暗合、隐性牵制、时间层引动。它们属于当前八字的结构证据，只能说明“有隐藏材料或潜在触发路径”，不能直接解释同八字不同命。

2. **命主隐藏出厂设置**
   这是每个命主独有的个体校准参数。即使八字结构相同，不同命主仍可能因为资源支持、行动效率、机会可达性、风险承受、压力恢复等隐藏设置不同，而出现不同兑现路径。

放大因子是隐藏出厂设置中的一类，表示“变化被放大的倍率”：

- `baseline_amplifier`：基础兑现放大因子。
- `timing_sensitivity`：时间引动敏感度。
- `wealth_amplifier`：财富兑现放大因子。
- `career_amplifier`：事业兑现放大因子。
- `relationship_sensitivity`：关系事件敏感度。

V20 对齐 V19 P64 的边界：

```text
八字结构 = 结构先验
用户事件 = 观测证据
命主隐藏出厂设置 = 个体校准参数
放大因子 = 对变化和触发的个人放大率
校准结果 = 只影响问题排序、路径排序和后续询问优先级
```

允许用途：

- 当前用户的路径重排。
- 推荐问题优先级。
- 内部 posterior calibration。
- 合成用户校准评估。

禁止用途：

- 修改核心命理规则真值。
- 自动启用生产规则。
- 给用户展示“幸运分”“概率分”。
- 健康、寿命、疾病推断。

因此，“同样八字，不同命”的解释入口不是改八字规则，而是：

```text
同一结构先验
→ 不同命主隐藏出厂设置
→ 不同变化放大因子
→ 不同路径排序与追问重点
→ 不同现实兑现解释
```

## 命主校准场景

命主隐藏出厂设置和放大因子不能由八字直接计算。V20 只能通过结构化人生节点观测反推，因此输入必须是选择题，不开放自由文本作为核心校准证据。

第一版校准场景：

- 财富变化：收入、资源或财务压力在哪一段时间最明显变化。
- 事业转换：职业角色、平台或责任在哪一段时间最明显变化。
- 关系重心：关系状态、家庭责任或亲密关系重心在哪一段时间变化。
- 迁移环境：居住地、工作城市或长期环境是否明显变化。
- 压力恢复：压力阶段恢复较快、较慢、反复，或依赖外部支持。
- 行动结果：投入行动后结果较快、较慢、需要多次尝试，或外部帮助关键。

每个场景只允许选择：

- 年份段：`birth_to_12 / 13_to_18 / 19_to_24 / 25_to_30 / 31_to_36 / 37_to_42 / 43_to_48 / 49_to_54 / 55_plus / unknown`
- 结果选项：由场景固定提供，例如 `income_up / income_down / resource_gain / resource_pressure / mixed`
- 强度：`none / mild / clear / strong`
- 置信度：`low / medium / high`

这些答案会进入 `latent_event_calibration_ledger`，生成 `factor_update_signals`。它们仍然只是 posterior calibration 信号：

- 可以校准 `baseline_amplifier`、`timing_sensitivity`、`wealth_amplifier`、`career_amplifier` 等。
- 可以影响后续路径排序和推荐问题。
- 不允许直接改规则真值。
- 不允许生成确定性人生结论。

第一版测算页接入：

- 档案测算页显示 `Latent Factors / 命主校准` 面板。
- 每条场景只能选择年份段、结果、强度、置信度。
- 记录后写入 `latent_event_calibration_ledger`。
- 当前会话把 `latent_event_answers` 作为排序镜头传入 runtime。
- 推荐问题会优先回应刚刚校准的人生节点方向，但核心规则、画像事实和知识库真值不发生运行时修改。

Postgres 处理方式：

- `v20/scripts/import_calibration_postgres.py --ledger latent_event_calibration_ledger` 可把本地校准账本导入 `v20_feedback_ledger`。
- 该导入仍然是 append/upsert ledger，不代表规则晋升。

## UI 边界

用户测算页只展示：

- 六柱/排盘
- 动态裁决画像
- 推荐问题
- 对话回答

训练、规则抽取、语料覆盖、LLM 抽取、批量验证只放在：

- `v20/scripts/*`
- admin 页的 DB/LLM/训练状态视图
- 离线报告和 artifact

## 当前清理方向

- runtime 主链不再使用 `FeatureDiscovery`、旧画像投影、旧规则候选或 518K training prior 来生成推荐问题。
- runtime 主链新增 `DecisionReport`、`DefeasibleDecisionModel`、`PortraitProjection`、`QuestionIntentModel` 和 `InteractionSession`。
- 旧的 feature/portrait intelligence 和保守规则候选模块已退出主链，不再作为用户测算主驱动。
- 用户/命理师 role projection 只暴露主题投射画像、推荐问题、回答与必要证据；训练细节进入脚本或后续 Admin artifact dashboard。

## 知识规则桥

V20 runtime 直接使用 reviewed knowledge 生成的 active rule definition；每条动态裁决必须能回溯到知识来源、规则路径和 EvidencePack。

当前桥接方式：

```text
KnowledgeUnit
→ KnowledgeRuleDefinition(runtime_allowed=false)
→ DecisionKnowledgeRuleBridge
→ RuleDecision.knowledge_rule_refs
→ LLM practitioner prompt / analyst evidence
```

用途：

- 解释每条 runtime decision 背后的知识来源。
- 给 LLM 提供更像命理师的术语、问题、边界和条件原子。
- 给后续 synthetic validation、DecisionRegistry、规则晋升提供稳定对象。

边界：

- `knowledge_rule_refs.runtime_allowed` 永远为 `false`。
- 桥接不激活规则、不改分数、不改画像结论。
- 用户视图不暴露内部 rule atoms；命理师/实验视图可看到用于复核。
