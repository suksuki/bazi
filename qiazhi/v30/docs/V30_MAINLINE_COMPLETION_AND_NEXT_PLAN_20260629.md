# V30 主线完成度与下一阶段计划

更新时间：2026-06-29

## 当前结论

V30 当前已经从“八字功能堆叠”进入“中枢智能大脑驱动的测算系统”阶段。

2026-06-29 A-E 执行更新：

- Phase A-E 已完成主线骨架落地，详见 `V30_A_TO_E_MAINLINE_EXECUTION_20260629.md`。
- TOI / SPI / CBI 已并入当前主线，不再作为旁支任务管理。
- 命理师选择、Admin 中枢回放、专项 synthetic、prompt profile audit 和前端投影已具备可运行闭环。
- 尚未完成的是：选择持久化、final synthesis 深度采用、真实 LLM profile 对比、训练 orchestrator 指标正式接入。

当前主线整体判断：

```text
工程主线完成度：约 93%
智能体验完成度：约 81%
产品可打磨完成度：约 69%
```

2026-06-29 下一阶段主线已启动：

```text
Central Feedback Overlay
```

目标不是再做一个页面功能，而是把用户回答、命理师选择、Text-to-Option 分支选择统一投影成中枢可训练的权重层：

```text
用户回答 / 命理师选择
-> Central Feedback Overlay
-> Claim Score Delta
-> Dialogue Next Question
-> Final Synthesis
-> Training Signal
```

硬边界：

- 反馈只改 belief、claim ranking、next question priority 和 final synthesis ordering。
- 反馈不改四柱、历法、原始规则命中、时运计算、命盘事实。
- 命理师的“采纳/降权/待问”是中枢权重输入，不是直接改结论文本。

2026-06-29 架构级主线升级：

```text
Decision-Centered Architecture
```

这次升级解决一个核心问题：步骤页每次调用 LLM 生成长文，会把规则、画像、特征、路径、用神和时运素材污染成二手文本，导致后续判断又长又脏。

新口径：

```text
步骤页产素材
-> Central Feedback Overlay 给权重
-> Decision Engine 生成 Verdict
-> LLM 只做最终表达和必要对话
```

硬边界：

- 步骤页默认不再调用 LLM 生成长篇小结。
- LLM 没有最终命理断语权。
- 训练权重没有最终命理断语权。
- 规则、画像、路径、用神候选都只是素材，不能单独成为最终结论。
- 最终可给用户展示的断语必须来自 `Verdict`，并带 assertion level、证据、反证、允许断语和禁止断语。

执行状态：

- `DCA-2` Decision Contract 已完成基础落地。
- `DCA-3` 素材归一化已完成第一版，现阶段从 `diagnosis.claims + claim_scores` 生成 Candidate，后续继续拆细规则、画像、路径、用神和时运来源。
- `DCA-4` Decision Engine V1 已接入 central reading state 和 final synthesis。
- `DCA-5` LLM Expression Boundary 已接入 Bazi LLM context pack 与 prompt contract。
- `DCA-6` 13 步压缩已完成基础落地：后端新增 7 个 `journey_steps`，前端导航优先使用 7 阶段，旧 `steps` 保留为细粒度素材池。
- `DCA-7` 命理师分支校准已完成基础落地：Decision Verdict 分支能生成 practitioner-only OptionSet。
- `DCA-8` 边栏工作记忆已完成基础落地：边栏新增 Decision Verdict 记忆，并随 7 阶段映射到细粒度素材逐步释放。
- `DCA-9` 智能对话重接入已完成基础落地：当旧推荐问题缺席时，Decision Verdict `next_question_slots` 会补位为当前对话问题。
- `DCA-10` 轻量合成验证已完成基础落地：新增 DCA validation gate，覆盖 Decision Engine、Verdict、LLM expression boundary、7 阶段压缩、边栏、命理师分支和对话补位。
- `DCA-11` Verdict 反馈与 Admin 训练联动已完成基础落地：Decision Engine 输出 feedback recalculation summary，并暴露 admin training projection。
- `DCA-12` Verdict 反馈质量 diff 与 UI 投影已基础启动：`reading_surface.decision_feedback` 已按角色隔离投影反馈重算摘要。

解释：

- 工程主线完成度较高：排盘、规则、画像、特征、路径、中枢、LLM thinking、StagePoint、Text-to-Option、训练和验证骨架都已经接入。
- 智能体验仍未完全成熟：真实 LLM 输出质量、命理师交互、Admin 回放、专项 synthetic tier、长期训练闭环仍需要继续做。
- 产品可打磨完成度较低一些：UI 已明显收敛，但命理师模式、OptionSet 交互、Admin 观察台和真实测算体验仍需要产品化。

## 当前系统主线

当前系统主线已经固定为：

```text
出生资料
-> 六柱排盘与事实层
-> 规则 / 画像 / 特征 / 路径 / 用神取舍
-> 中枢智能大脑
-> 素材候选归一化
-> Text-to-Option / 分支选项化
-> 用户对话 / 命理师选择
-> 中枢 belief update
-> Decision Engine Verdict
-> LLM Expression
-> 训练样本与验证闭环
```

这条主线的核心不是“生成一段八字报告”，而是：

```text
可解释
可交互
可训练
可验证
可由命理师校准
```

## 完成度总表

| 模块 | 完成度 | 当前状态 | 下一步 |
| --- | ---: | --- | --- |
| 八字事实层 | 90% | 六柱、日主、十神、五行、时运上下文已可用 | 继续补边界 case 和真实数据回放 |
| 规则/画像/特征/路径 | 82% | 已作为中枢食材进入页面和诊断 | 提升领域质量和证据密度 |
| 用神忌神取舍 | 72% | 已进入独立阶段和边栏记忆 | 补专项验证和命理师选择 |
| 中枢智能大脑 V2 | 81% | Evidence Graph、Belief、VOI、Brain Judge、Final Synthesis、Decision Verdict、反馈重算摘要和训练样本已接入 | 强化 belief update 与真实反馈学习 |
| Decision Engine 裁决层 | 54% | Decision Contract、Verdict、断语等级、allowed/forbidden assertions、final synthesis、DCA 验证和反馈重算摘要已完成基础落地 | 拆细素材来源、补冲突算法和命理师校准闭环 |
| 页面级 LLM thinking | 70% | LLM 输出进入中枢清洗，硬边界拦截、软质量清洗已落地 | 继续优化 prompt profile 和 live LLM 质量 |
| LLM Expression Boundary | 52% | `decision_verdicts` section、prompt boundary gate、final synthesis expression contract 和 DCA 验证已落地 | 接入 live LLM 输出 verifier 和页面表达打磨 |
| StagePoint 框架 | 72% | `SPI-1` 到 `SPI-5` 已完成基础落地 | 做命理师选择、synthetic tier、Admin 回放 |
| Text-to-Option 框架 | 68% | `TOI-1` 到 `TOI-5` 已完成基础落地 | 做命理师 UI、专项验证、Admin 抽取观察 |
| 智能对话系统 | 70% | `current_dialogue_turn` 聚焦单一问题，`response_option_set` 已接入 | 让回答真正触发 belief update 与下一问优化 |
| 隐藏属性校准 | 62% | 有结构化问题和训练/审核边界 | 接入 TOI 和命理师选择闭环 |
| 训练系统 | 77% | Auto training、orchestrator、diff、Phase2 gate 和 Decision feedback training projection 已接入 | 让 TOI/SPI 与 Verdict feedback 进入训练指标 |
| 合成验证/518K | 73% | 主体验证可运行，518K sample/shard/readiness 已跑通过，DCA 轻量验证已接入 | 增加 StagePoint/OptionSet 专项 tier 与 518K 分布观察 |
| Admin 管理页 | 62% | 训练、进度、LLM、只读审核已可用 | 做候选/采纳/丢弃回放视图 |
| 用户 UI | 66% | 流程已简化，边栏、页面结论和 decision feedback 投影开始收敛 | 清理残余复杂区，增强 Step/Option 体验 |
| 13 步测算流程压缩 | 62% | 后端 `journey_steps`、前端 7 阶段导航和 DCA 验证已基础落地，旧细步保留为素材池 | 打磨每个阶段的 UI 素材卡、边栏联动和对话重算 |
| 边栏工作记忆 | 62% | 命盘、规则、特征、画像、路径、结构、用神、时运、领域和 Verdict 记忆已基础投影 | 增加点击证据展开和命理师校准入口 |
| 命理师模式 | 28% | 角色和数据契约已有，真正交互 UI 未做 | 下一阶段重点 |
| Decision 分支命理师校准 | 52% | Verdict 分支已生成 practitioner-only OptionSet，并进入 feedback recalculation summary 与角色化投影 | 让选择结果触发 Admin 回放聚合和质量 diff |

## 已完成主线

### 1. CBI-V2 中枢智能大脑基础闭环

状态：已完成基础落地。

已完成：

- Evidence Graph 进入中枢。
- Belief State 与 claim posterior 已接入。
- Value-of-Information 控制追问。
- Brain Decision Trace 统一记录下一步动作。
- BrainTrainingExample 已形成标准样本。
- Brain Judge 接入 LLM derivation 与 final synthesis。
- Final Synthesis Blueprint 先生成断语、证据、建议和风险边界，再投影给用户。
- 训练信号进入 auto training 和 orchestrator。

剩余：

- 更强的真实反馈学习。
- 更细的 belief update。
- 对命理师选择的权重学习。

### 2. StagePoint 页面智能判断点

状态：`SPI-1` 到 `SPI-5` 已完成基础落地。

已完成：

- `v30.stage_point_set.v1`
- `v30.stage_point.v1`
- LLM `candidate_points`
- 中枢采用与清洗
- 页面列表展示
- 边栏 source 追踪
- StagePoint 进入 LLM context

剩余：

- `SPI-6` 命理师可选模式。
- `SPI-7` StagePoint synthetic tier 与 518K 分布观察。
- `SPI-8` Admin candidate/selected/discarded 回放。

### 3. Text-to-Option 文本语义选项化

状态：`TOI-1` 到 `TOI-5` 已完成基础落地。

已完成：

- `v30.text_semantic_unit.v1`
- `v30.option_set.v1`
- `v30.text_option_projection.v1`
- `v30.practitioner_selection.v1`
- StagePoint 文本抽取候选、列表、数字、行动、风险、追问需求。
- OptionSet Gate 按证据、歧义减少、命理师可操作性、UI 噪音和事实风险评分。
- `current_dialogue_turn.response_option_set` 已接入。
- 前端优先使用 `response_option_set.options`。

剩余：

- 命理师 UI 交互。
- 用户选项反馈进入 belief update 的更完整闭环。
- OptionSet synthetic tier。
- Admin 抽取回放和训练指标。

### 4. 智能对话简化

状态：已完成主结构，仍需智能化深化。

已完成：

- 前端不再批量堆问题。
- 只渲染 `current_dialogue_turn`。
- 用户回答以选项、数字、短文本为主。
- 隐藏属性校准已结构化。
- `response_option_set` 已使对话选项标准化。

剩余：

- 用户选择如何改变 belief posterior。
- 回答后下一问的质量优化。
- 隐藏属性和 TOI 的完整闭环。

### 5. 训练与验证

状态：主骨架已完成，专项智能指标待补。

已完成：

- Auto training。
- Training Orchestrator。
- 训练历史、diff、失败步骤重跑。
- Phase2 policy optimizer。
- Synthetic replay gate。
- 518K distribution gate。
- Admin 可启动和查看进度。

剩余：

- StagePoint quality synthetic tier。
- Text-to-Option extraction synthetic tier。
- Practitioner selection alignment 指标。
- Option UI noise penalty 指标。

## 当前主要缺口

### 1. 命理师模式还没有真正产品化

已有：

- `role_key=practitioner`
- StagePoint `selectable`
- OptionSet `visibility.practitioner=interactive`
- PractitionerSelection 契约

缺：

- 页面上可采纳、降权、排序、待问、排除、备注。
- 命理师选择后回写中枢 belief。
- 命理师选择成为训练标签。

### 2. Admin 观察台还不够像“中枢大脑工作台”

已有：

- 训练进度。
- LLM 配置。
- 训练历史。
- 隐藏属性只读审核。

缺：

- StagePoint candidate/selected/discarded 回放。
- OptionSet extracted/discarded 回放。
- Brain Judge 分数和失败原因可视化。
- Prompt profile 效果对比。

### 3. LLM 真实输出质量仍需要专项打磨

已有：

- LLM thinking 接入。
- candidate_points 契约。
- 中枢硬边界和软清洗。

缺：

- 真实 Gemma thinking 的 profile 对比。
- 不同页面 prompt 的质量分布。
- 慢请求、超长输出、自检语句的专项处理。

### 4. 用户 UI 还没有完全体现智能交互优势

已有：

- 逐步页面。
- 边栏记忆。
- StagePoint 列表。
- 单问题对话。

缺：

- OptionSet 交互视觉。
- 页面和边栏之间的联动。
- 命理师模式与用户模式的清晰切换。

## 下一阶段主线计划

### Phase DCA：Decision-Centered 测算主链

优先级：最高。

目标：把 V30 从“每页 LLM 解释”重构为“素材沉淀、裁决引擎断语、LLM 最终表达”的主链。

任务：

1. `DCA-2` 建立 Decision Contract：`DecisionInputBundle / Candidate / Conflict / Verdict / DecisionTrace`。状态：基础完成。
2. `DCA-3` 建立素材归一化管线：规则、画像、特征、路径、用神、时运统一转为候选。状态：第一版完成，后续拆细素材来源。
3. `DCA-4` 建立 Decision Engine V1：证据评分、路径连贯、冲突处理、分支概率、断语等级门控。状态：基础完成。
4. `DCA-5` 建立 LLM Expression Boundary：LLM 只消费 Verdict，输出必须通过 boundary verifier。状态：基础完成。
5. `DCA-6` 把 13 步流程压缩为 7 个高层阶段，步骤页默认不再输出 LLM 长文小结。状态：基础完成。
6. `DCA-7` 命理师分支校准：Decision Verdict 分支生成 practitioner-only OptionSet。状态：基础完成。
7. `DCA-8` 边栏工作记忆同步：显示事实、候选、分支、用神、路径和 Verdict 摘要，不显示长文。状态：基础完成。
8. `DCA-9` 智能对话重接入：只由 `next_question_slots` 和 VOI 策略触发，回答后重算相关 Verdict。状态：基础完成。
9. `DCA-10` 合成验证：新增轻量 DCA gate，覆盖 Verdict、LLM boundary、7 阶段、边栏、命理师分支和对话补位。状态：基础完成。
10. `DCA-11` Verdict 反馈与 Admin 训练联动：用户回答、命理师选择和真实案例反馈触发相关 Verdict 重算摘要。状态：基础完成。
11. `DCA-12` Verdict 反馈质量 diff 与 UI 投影：把 feedback recalculation summary 接入 Admin 回放、命理师 UI 和真实案例验证。状态：基础启动。

验收：

- 不调用 LLM 也能完成素材阶段。
- LLM 长文不能回写污染素材。
- 最终给用户看的结论和建议全部来自 Verdict。
- 普通用户看到简洁结论和必要分支。
- 命理师能看到候选分支并做校准。
- 智能对话不进入步骤导航，不自问自答，不幽灵出现。

### Phase A：命理师交互闭环

目标：让 V30 真正具备“命理师可校准”的产品特色。

任务：

1. `TOI-6A` 命理师页面显示 OptionSet。
2. `TOI-6B` 支持采纳、降权、排序、待问、排除、备注。
3. `TOI-6C` 命理师选择生成 `PractitionerSelection`。
4. `TOI-6D` 选择结果写入中枢 belief delta，不改命盘事实。
5. `TOI-6E` 选择结果进入 final synthesis 排序。

验收：

- practitioner 可操作。
- user 页面不显示命理师控件。
- 操作不会改变四柱、大运、流年和原始规则。
- 选择后最终建议顺序会改变。

### Phase B：Admin 中枢观察台

目标：让系统能解释“为什么这么断、为什么这么问、为什么没采用”。

任务：

1. `SPI-8A` StagePoint candidate/selected/discarded 回放。
2. `TOI-7A` OptionSet extracted/discarded 回放。
3. `CBI-OBS-A` Brain Judge 质量分数展示。
4. `CBI-OBS-B` Prompt profile 与 LLM 调用质量统计。
5. `CBI-OBS-C` PractitionerSelection 分布统计。

验收：

- Admin 能定位每条结论来源。
- Admin 能看到抽取失败原因。
- 不泄露模型密钥和用户隐私。

### Phase C：专项合成验证

目标：把 StagePoint 和 OptionSet 从“有功能”变成“可验证智能能力”。

任务：

1. `SPI-7A` StagePoint synthetic tier。
2. `TOI-7B` Text-to-Option synthetic tier。
3. `TOI-7C` Practitioner selection alignment synthetic tier。
4. `HF-TOI-A` 隐藏属性 OptionSet synthetic tier。
5. `VAL-518K-A` 518K sample 增加 StagePoint/OptionSet 分布观察。

验收：

- StagePoint 不模板化。
- OptionSet 不抽工程语言。
- 用户每次最多一个当前问题。
- 命理师选择不会改命盘事实。

### Phase D：LLM Prompt Profile 实测优化

目标：让真实 LLM 输出更像命理推演，而不是空泛总结。

任务：

1. `LLM-PROFILE-A` 每个 stage profile 建立质量样例。
2. `LLM-PROFILE-B` live LLM smoke 记录 latency、candidate count、hard failure。
3. `LLM-PROFILE-C` 对比不同 prompt profile 的 StagePoint 质量。
4. `LLM-PROFILE-D` 清理自检语句、模板句式和跨页发散。

验收：

- 每页都有 stage-local 结论。
- 规则页能说清命中规则。
- 用神页能说清取舍和反证。
- 路径页能说清做功机制。
- 领域页能给明确建议。

### Phase E：用户体验收束

目标：让普通用户看到的是结论、建议和必要选择，不看到工程语言。

任务：

1. `UI-STAGE-A` 页面 StagePoint 视觉继续收敛。
2. `UI-OPTION-A` 用户 OptionSet 视觉设计。
3. `UI-SIDEBAR-A` 边栏与当前阶段联动。
4. `UI-MOBILE-A` 手机端 OptionSet 和边栏简化。
5. `UI-COPY-A` 清理所有工程状态文案。

验收：

- 用户页面没有内部 id。
- 没有模板化“结论：建议：”。
- 每页聚焦当前主题。
- 手机端不拥挤。

## 优先级排序

第一优先级：

```text
TOI-6 命理师模式 UI
SPI-8 / TOI-7 Admin 回放
TOI-7 synthetic tier
```

第二优先级：

```text
LLM Prompt Profile 实测优化
用户 OptionSet 视觉体验
隐藏属性 TOI 闭环
```

第三优先级：

```text
518K 分布观察增强
更多训练策略自动生效
大规模发布 readiness
```

## 验证基线

当前可作为下一阶段回归基线：

```text
全量单元测试：654 passed
TOI / thinking / presentation 相关：31 passed
scaffold 相关：18 passed
py_compile passed
node --check frontend/app.js passed
git diff --check passed
```

## 当前暂停项

以下暂不作为主线第一优先级：

- 大规模 UI 视觉重做。
- 外部发布 readiness。
- full 518K 默认长跑。
- 外部 agent 框架迁移。
- 复杂多用户权限体系扩展。

原因：

- 当前最有价值的差异化能力是中枢智能、命理师校准、文本选项化和训练验证闭环。
- 先把这个闭环打穿，再继续做大规模产品化和发布。

## 下一步建议

下一步直接进入：

```text
Phase A：命理师交互闭环
```

推荐任务顺序：

1. 做命理师模式的 OptionSet 面板。
2. 增加 `PractitionerSelection` API。
3. 让选择影响 belief delta 和 final synthesis 排序。
4. 增加 Admin 回放视图。
5. 补 TOI synthetic tier。

这条路径最符合当前系统的核心优势：让 V30 不只是自动测算，而是能让命理师参与、校准、训练、验证的智能八字系统。
