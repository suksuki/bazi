# V20 知识库、规则、画像、裁决与互动主线完成计划

## 目标

V20 的核心不是展示内部特征，而是完成一条可审查、可训练、可交互的八字测算主线：

```text
八字排盘
-> 当前盘结构事实
-> 知识库命理单元
-> 候选规则定义
-> 当前盘规则命中
-> 裁决与命理师校准
-> 动态命理画像
-> 推荐问题
-> LLM 命理师式对话
-> 反馈与训练脚本
-> 晋升后的规则/参数
```

核心原则：

- 知识库是源头，但知识不是直接结论。
- 规则来自 reviewed 知识库，可由 LLM 辅助抽取，但必须经过验证。
- 画像必须动态生成，围绕当前八字的命理主题，不依赖 518K 静态标签作为真相。
- 推荐问题必须像用户会问的问题，围绕财富、事业、婚恋、健康、流年、大运、格局、用神等测算主题。
- 命理师裁决是系统特色：用结构化选择帮助系统刷新画像、问题和回答，不开放自由输入污染规则。
- 518K 全量库用于覆盖、相似盘、统计先验、聚类和训练素材，不直接决定单盘画像。
- LLM 可以当命理师表达层，但不能创建盘面事实、绕过规则裁决、输出无证据断语。

## 当前完成度判断

### 知识库系统

当前状态：P1 seed 扩充阶段。

- 已有 reviewed seed 单元：强弱、地支、时间层、财富、事业、关系、健康、用神、十神、五行、格局等。
- 已补入根气与月令、十神来源优先级、食伤转财、事业官伤印裁决、关系地支十神裁决、五行偏枯边界等第二批 seed。
- 已有 V19 知识迁移审计和 review queue。
- 缺口：知识单元还偏少，结构字段不足，尚未形成大规模 reviewed 知识资产。

P1 目标：

- 每个知识单元必须逐步补齐规则原子、画像映射、推荐问题映射、回答边界、反例。
- 新知识进入 reviewed 前必须经过 review packet 和 approval preflight。
- 默认不激活为运行时规则。

### 规则系统

当前状态：shadow 候选已落地，正在进入子条件拆分阶段。

- 已有知识到规则提案、规则抽取、LLM 辅助抽取、合成验证入口。
- 已形成 `KnowledgeRuleLibrary`：18 条 reviewed seed 知识均可生成 shadow rule definition。
- 9 个 synthetic case 已按领域覆盖 18 条知识规则，当前没有“缺合成案例”的红灯。
- 当前主要缺口：17 条规则仍然过宽，需要基于 518K 覆盖统计拆子条件、找反例、再交给命理师/管理员审查。
- 最新 DecisionRegistry review artifact 已形成 155 条待审记录，其中 69 条可进入批量审阅候选，86 条需要人工/管理员单独审查。

P2 目标：

- 建立 KnowledgeRuleLibrary：从 reviewed 知识生成可审查规则定义。
- 每条规则包含条件原子、画像输出、问题输出、回答边界、反例和验证状态。
- 合成八字用于验证规则碰撞、边界、反例，不由 518K 直接训练出规则真相。
- `run_knowledge_rule_validation.py --summary` 是当前规则审查入口：它会把每条规则标记为已合成覆盖、缺合成案例、语料支持过宽、下一步需要拆子条件或补反例。
- `run_rule_activation.py --summary` 是激活迭代入口入口：机器先把 active rules 分流为补合成案例、拆子条件、候选 active 权重训练等迭代包；人工只处理迭代包，不逐条翻原始规则。
- `run_rule_subcondition_split.py --progress --write` 会读取 518K 训练产物，为过宽规则生成子条件候选和反例候选。它仍是离线审查材料，不会激活运行时规则。
- `run_decision_registry_review.py --progress --write` 会把迭代包、子条件候选和反例候选整理成 DecisionRegistry review records。它做批量分流和建议动作，但不等同于人工批准，也不激活运行时规则。
- `import_decision_registry_postgres.py --apply` 才会把本地 review records 导入 `v20_decision_registry`，用于后续管理员审查和回溯；导入仍不是运行时晋升。

### 画像系统

当前状态：方向修正完成，深度不足。

- 运行时已改为动态画像，不再把 518K 静态画像当作真相。
- 命理师裁决已能作为结构化校准信号。
- 缺口：画像轴还少，主题化表达还不够，规则裁决和画像映射需要更强。

P3 目标：

- 画像轴围绕命理测算主题：日主承载力、格局复核、十神角色、财星结构、事业结构、婚恋互动、健康边界、流年大运牵动、用神候选。
- 画像只展示当前盘真正命中的主题，不展示内部技术碎片。
- 画像要支持温度、置信度、命理师待裁决状态。

### 裁决系统

当前状态：有雏形。

- 已支持命理师结构化按钮选择。
- 选择后会刷新推荐问题。
- 缺口：裁决项数量少，尚未覆盖强弱、格局、伤官见官、财星承载、用神方向、流年牵动等主线。

P4 目标：

- 每个关键规则都要声明是否需要裁决、裁决选项、裁决后影响的画像和问题。
- 训练脚本收集命理师选择，用于参数校准和规则晋升建议。
- UI 只放必要裁决，训练和大批量学习放后台脚本。

### 推荐问题系统

当前状态：可用方向对了，但仍需扩充。

- 问题已经从动态画像和裁决主线生成。
- 缺口：问题库少、领域细化不足、个性化仍偏弱。

P5 目标：

- 每条规则和画像轴绑定 2-5 个真实用户会问的问题。
- 根据用户输入领域、当前盘命中规则、命理师裁决、时间层动态排序。
- 禁止向用户展示内部术语堆叠式问题。

### 对话系统

当前状态：LLM practitioner 路径已接入，但上下文质量仍取决于前面几个系统。

- LLM 已能在证据包和边界内生成回答。
- 缺口：答案还依赖少量规则材料，命理师风格需要更多高质量规则和画像素材支撑。

P6 目标：

- LLM 输入只包含当前盘事实、规则命中、画像主题、知识依据、边界和用户问题。
- LLM 输出经过安全拦截，不能生成无证据断语。
- 回答风格更像命理师：先讲结构，再讲推理，再讲可继续追问的方向。

## 后台训练与脚本体系

所有重训练、批量抽取、全量预计算、规则验证都放脚本或 admin 只读面板，不放普通用户 UI。

优先脚本：

- 知识库 review packet 生成与导入审计。
- LLM 辅助知识规则抽取。
- 合成八字规则碰撞验证。
- 画像轴批量验证。
- 命理师裁决学习聚合。
- 518K 结构覆盖基线、相似盘索引、聚类、规则支持统计。
- shadow 规则子条件拆分与反例候选生成。
- DecisionRegistry review 台账生成，把候选规则、子条件、反例和 active 权重候选变成可批量裁决对象。

518K 结构覆盖基线的角色：

- 建覆盖分布：哪些盘型、十神、五行、地支互动常见或稀缺。
- 建相似盘检索：给单盘分析提供参考样本。
- 建训练素材：为画像排序、问题排序、规则参数提供离线校准材料。
- 不直接生成单盘最终画像真相。

## 近期批次

## 维度化与命主隐藏设置

V20 的知识库、规则、画像、推荐问题和回答必须共享同一套维度坐标：

- 微观结构维度：日主、十神、五行、地支。
- 裁决路径维度：强弱、格局、用神、候选路径。
- 时间触发维度：大运、流年、流月和原局互动。
- 宏观主题维度：财富、事业、关系、健康边界。

知识库里的“藏干、墓库、暗合、隐性牵制”属于结构隐藏属性，是命局材料。

P64 里的隐藏因子属于命主级隐藏出厂设置，是个体校准参数。它解释为什么同一结构先验在不同命主身上有不同兑现方式：

- `action_efficiency`：行动效率。
- `resource_support`：资源支持。
- `opportunity_access`：机会可达性。
- `risk_tolerance`：风险承受。
- `stress_recovery_capacity`：压力恢复能力。

放大因子是变化响应倍率：

- `baseline_amplifier`：基础兑现放大因子。
- `timing_sensitivity`：时间引动敏感度。
- `wealth_amplifier`：财富兑现放大因子。
- `career_amplifier`：事业兑现放大因子。
- `relationship_sensitivity`：关系事件敏感度。

这些参数只允许通过用户事件账本、命理师校准和合成用户校准评估进入后台学习。它们只影响路径重排、问题优先级和后续询问，不修改规则真值，不直接生成用户可见结论。

校验方式采用反向人生节点选择题：

- 让用户选择关键变化出现的大致年龄段，而不是输入自由年份叙述。
- 让用户从固定结果中选择变化类型，例如收入上升、收入下降、平台变化、责任变化、关系重心变化、恢复较快、恢复较慢。
- 让用户选择强度和置信度，用于形成事件观测权重。
- 所有答案进入 `latent_event_calibration_ledger`，只生成 `factor_update_signals`。

第一版后端入口：

- `GET /api/v20/learning/latent-event-calibration`
- `POST /api/v20/latent-event/calibration/analyze`
- `POST /api/v20/latent-event/calibration/record`

当前运行时对接：

- `MeasureRequest.latent_event_answers` 接收受控选择题结果。
- `recommend_decision_questions(...)` 会把命主校准答案转成当前会话的问题排序镜头。
- 这些问题只用于追问和路径复核，不把人生节点反写为规则真值。
- 测算页档案模式提供命主校准面板；训练和统计仍放在脚本层。
- 本地 `latent_event_calibration_ledger` 可通过 `v20/scripts/import_calibration_postgres.py --ledger latent_event_calibration_ledger` 导入 Postgres。

### P0b：知识规则桥已进入 runtime

当前主链已经形成第一版闭环：

```text
KnowledgeUnit
→ KnowledgeRuleDefinition
→ DecisionKnowledgeRuleBridge
→ RuleDecision.knowledge_rule_refs
→ PortraitProjection / QuestionIntent / QuestionCandidate / AnswerPlan / LLM practitioner prompt
```

验收状态：

- 每条 runtime decision 可以挂接 0-N 条知识规则引用。
- 知识规则引用包含 source knowledge、condition atoms、portrait labels、question outputs、answer guidance keys、boundary。
- 推荐问题可以从知识规则 question outputs 衍生候选。
- 回答计划可以把知识规则 portrait labels 转成用户可读的“复核重点”。
- LLM 命理师提示词接收 compact knowledge rules，但不得激活规则。
- Runtime 只使用 lightweight bridge，不实时调用 synthetic validation。
- `GET /api/v20/knowledge/rule-review-overlay` 提供后台只读 overlay，汇总 synthetic、corpus、promotion gate 状态。

仍需继续：

- 把 rule review overlay 写入 ArtifactRegistry/Postgres，并允许 runtime 读取锁定版本。
- 把 DecisionRegistry review 结果用于 shadow weight，而不是只做报告。
- 建立知识规则版本锁定和 Postgres artifact registry 记录。

### P1：知识库结构补强

验收标准：

- KnowledgeUnit 支持 rule_atoms、portrait_mappings、question_mappings、answer_guidance、counterexamples。
- 默认 seed 至少有核心主题的结构化映射示例。
- 新增只读规则库报表和验证端点。

### P2：规则库落地

验收标准：

- 每条 reviewed 知识能生成一个 shadow KnowledgeRuleDefinition。
- 每条规则声明条件、画像输出、问题输出、边界、验证状态。
- 所有规则默认 runtime_allowed=false。

### P3：合成验证深化

验收标准：

- 伤官见官、财星承载、日主强弱、用神候选、地支冲合、流年大运牵动、事业投影、关系投影、健康边界至少各有 synthetic case。
- 验证报告能指出规则过宽、缺子条件、冲突、反例缺失。

### P3b：规则子条件拆分

验收标准：

- 过宽规则能从 518K 统计产物中生成 `all_of_feature_ids` 子条件候选。
- 每条过宽规则配套若干 counterexample cluster 候选。
- 子条件只进入 review packet，不自动变成 runtime rule。

### P3c：裁决台账批处理

验收标准：

- 子条件、反例和 active 权重候选都有稳定 `decision_id` 和 `subject_id`。
- 系统能区分可批量审阅候选和必须人工单独审查候选。
- DecisionRegistry review 只生成审查台账，不直接写运行时规则、不直接晋升。

### P4：动态画像和问题质量提升

验收标准：

- UI 画像只显示用户能理解的命理主题。
- 推荐问题来自当前盘真正命中的规则和画像轴。
- 命理师裁决后立即刷新画像权重、推荐问题和回答上下文。

### P5：LLM 命理师回答增强

验收标准：

- LLM 回答明显基于当前盘规则命中，而不是泛泛而谈。
- 回答不输出固定吉凶、具体时间断言或无证据预测。
- 回答能自然引导用户继续问一个合理命理问题。

## 不再继续的旧路

- 不再把 Feature Spine 本身当成用户画像。
- 不再把 518K 静态预计算标签当成单盘画像真相。
- 不再展示内部技术标签式推荐问题。
- 不再让 LLM 单独决定命理事实。
- 不再把训练功能塞进普通测算 UI。
