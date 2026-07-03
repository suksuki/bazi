# V30 当前主线状态

更新时间：2026-06-30

## 当前判断

V30 已经不再是单纯补齐八字基础模块的阶段。排盘、规则、画像、特征、路径、领域解读、LLM thinking、智能对话、训练校准和验证闸门都已经进入同一条产品主线。

当前主线不是继续堆功能，而是把这些模块统一到“中枢智能大脑驱动的八字测算系统”：

```text
出生资料
-> 六柱排盘与事实层
-> 规则 / 画像 / 特征 / 路径
-> 中枢智能大脑
-> Decision Engine 裁决
-> LLM 最终表达
-> 结论与建议
-> 必要时智能追问
-> 训练样本与验证闭环
```

## 当前主线锚点

最新主线任务已经收束到：

```text
Decision-Centered Architecture over CBI-V2
```

Canonical 文档：

```text
docs/V30_CENTRAL_BRAIN_V2_MAINLINE.md
docs/V30_DECISION_CENTERED_ARCHITECTURE_20260629.md
docs/V30_MAINLINE_COMPLETION_AND_NEXT_PLAN_20260629.md
docs/V30_CHATGPT_HANDOFF_PRODUCTION_ORCHESTRATOR_AUDIT_20260629.md
docs/V30_PRODUCTION_ORCHESTRATOR_DCA13_DCA14_PLAN_20260629.md
docs/V30_SIGNAL_BASED_DECISION_CANDIDATE_DCA15_PLAN_20260629.md
docs/V30_CONFLICT_RESOLVER_DCA15_ENHANCEMENT_PLAN_20260629.md
docs/V30_DCA16_DECISION_WORKBENCH_UI_CLOSEOUT_20260629.md
docs/V30_DCA17_DECISION_WORKBENCH_QUALITY_AUDIT_20260629.md
docs/V30_DIALOGUE_CHAIN_ARCHITECTURE_20260629.md
docs/V30_A_TO_E_MAINLINE_EXECUTION_20260629.md
docs/V30_STAGE_INTELLIGENCE_LLM_BRAIN_FRAMEWORK_20260629.md
docs/V30_TEXT_TO_OPTION_PRACTITIONER_INTERACTION_FRAMEWORK_20260629.md
docs/V30_ADMIN_CONTROL_PLANE_MAINLINE_20260630.md
docs/V30_SURFACE_ORCHESTRATOR_MAINLINE_20260630.md
docs/V30_OUTPUT_RUNTIME_PRODUCT_PROJECTION_MAINLINE_20260630.md
```

当前判断：

- 现有中枢大脑已经有 orchestrator、reading engine、dialogue planner、final synthesis、LLM thinking 审核和训练信号。
- 下一步不是继续补页面细节，而是把中枢升级为 Evidence Graph + Belief State + Value-of-Information Dialogue + LLM Candidate + Brain Judge + Training / Validation Loop。
- 页面级 LLM 小结已升级为 `StagePoint` 框架：LLM 生成候选推演与候选要点，中枢大脑做 scope gate、证据绑定、质量评分、清洗采用，再沉淀到页面和边栏。
- Text-to-Option 已进入主线执行：从测算文本和对话文本里自动抽取候选、列表、数字、取舍和追问需求，生成 `TextSemanticUnit / OptionSet / PractitionerSelection`。
- 2026-06-29 补充：中枢表达策略从“去掉不确定词”升级为 Evidence-Bound Branch；允许候选、分支、概率和待复核，但必须绑定八字证据、反证、置信度和复核条件。
- 2026-06-29 补充：分支候选进入角色化投影。普通用户只读，优先看到主分支或最高概率分支；命理师与 admin 可看到可选择、可降权、可待问的 `OptionSet`，选择结果只更新中枢权重和训练信号，不改命盘事实。
- 2026-06-29 补充：Central Feedback Overlay 已启动落地，把用户回答与命理师选择统一投影成中枢权重层；当前已能影响 claim score、下一问 topic 优先级和 final synthesis 反馈摘要。
- 2026-06-29 补充：主线升级为 Decision-Centered Architecture。步骤页不再默认生成 LLM 长文解释，而是沉淀干净素材、分支、证据、反证和待校准项；Central Feedback Overlay 只提供权重，最终可输出断语必须由 Decision Engine 生成 `Verdict` 后，再交给 LLM 做最终表达。
- 2026-06-29 补充：现有 13 步测算流程将压缩为 7 个高层阶段：资料与排盘校准、结构十神与用神候选、规则画像特征素材、做功路径时运与领域触发、分支冲突与命理师校准、Decision Engine 裁决、最终断语建议与智能对话。
- 2026-06-29 执行更新：`DCA-2` 到 `DCA-11` 已完成基础落地。新增 Decision Contract、Decision Engine V1、Decision Verdict 输出、final synthesis Verdict 优先消费、LLM context `decision_verdicts` section、prompt boundary gate、7 阶段 journey navigation、命理师 Verdict 分支 OptionSet、边栏 Decision Verdict 记忆、Verdict slot 对话补位、DCA 轻量合成验证入口和 Decision feedback recalculation summary。
- 2026-06-29 执行更新：`DCA-12` 已基础启动，`reading_surface.decision_feedback` 已能按角色投影 feedback recalculation summary；普通用户只见校准摘要，命理师/Admin 可见 affected verdict、candidate 和 admin training projection。
- 2026-06-29 交接审计更新：新增 `V30_CHATGPT_HANDOFF_PRODUCTION_ORCHESTRATOR_AUDIT_20260629.md`，把 ChatGPT 对 Production Orchestrator 的建议落到 V30 当前真实 runtime：模块产出映射、断语来源、LLM 表达边界、训练/验证影响路径和 DCA-13 到 DCA-18 下一阶段任务已经文档化。
- 2026-06-29 本轮执行更新：新增 `V30_PRODUCTION_ORCHESTRATOR_DCA13_DCA14_PLAN_20260629.md`，DCA-13 Module Audit 和 DCA-14 Signal Registry V1 已完成最小落地。新增 `v30.production` 旁路层、runtime production sidecar、`/api/v30/readings/{reading_id}/production-audit` 只读接口和专项测试；当前 smoke 可生成 279 条 signal、8 个 module audit，Decision Verdict 仍保持 9 条，现有裁决和 Final Synthesis 未被替换。
- 2026-06-29 DCA-15 执行更新：`V30_SIGNAL_BASED_DECISION_CANDIDATE_DCA15_PLAN_20260629.md` 已更新执行结果。Signal-aware DecisionCandidate Builder 兼容模式已完成，`DecisionCandidate` 现在绑定 `source_signal_ids / signal_source_summary / candidate_builder`，`DecisionEngineResult` 输出 `candidate_builder_summary`，`CentralReadingState` 输出 `decision_signal_registry`。当前 smoke：Decision Verdict 仍为 9 条，decision-facing registry 为 239 条 signal，claims_with_direct_signal_count 为 80，score mutation 关闭；专项组合测试 11 passed。
- 2026-06-29 DCA-15 增强执行更新：新增 `V30_CONFLICT_RESOLVER_DCA15_ENHANCEMENT_PLAN_20260629.md`。`ConflictResolver` 已从 `DecisionEngine` 内部抽离为 `v30.brain.conflict_resolver`，输出 `conflict_resolver_summary / conflict_resolver_audit`；`DecisionEngineResult`、`DecisionVerdict.trace` 和 `CentralReadingState` 已接入审计摘要。当前仍保持 compatibility：不改 score、不改 Verdict，runtime smoke 的 Decision Verdict 仍为 9 条；专项组合测试 14 passed。
- 2026-06-29 DCA-16 执行更新：新增 `V30_DCA16_DECISION_WORKBENCH_UI_CLOSEOUT_20260629.md`。`reading_surface.decision_workbench` 已成为页面消费的稳定入口，7 阶段页面已接入分支冲突卡、Verdict 裁决卡和最终收束卡；`journey_branch_calibration` 可生成命理师可操作 option hints；普通用户不暴露训练信号，命理师/Admin 可见校准和训练投影。当前 smoke：7 个 journey steps、4 个 branch option sets、9 条 Verdict、13 个 conflict、52 个 practitioner option sets；专项组合测试 24 passed。
- 2026-06-29 DCA-17 执行更新：新增 `V30_DCA17_DECISION_WORKBENCH_QUALITY_AUDIT_20260629.md`。新增只读质量审计 `v30.decision_workbench_quality_audit.v1` 和 `/api/v30/admin/readings/{reading_id}/decision-workbench-quality`，Admin 测算记录页展示质量分、7 阶段、Verdict、冲突、分支选项、命理师选项和关键检查；审计确认步骤页不默认调用 LLM 长文、智能对话独立挂载、普通用户不泄漏训练信号、命理师/Admin 可见校准投影。当前专项组合测试 18 passed。
- 2026-06-29 对话稳定性修复：第 4/7 阶段连续点击多个智能追问会造成多个 `/answer` 并发写同一 runtime，前端 pending 和后端 accepted answer 可能错位。已新增前端 single-flight guard、全局问答按钮禁用、LLM 响应 question_id 校验，以及后端 per-reading answer serialization；专项组合测试 6 passed。
- 2026-06-29 Dialogue Chain 主线设计：新增 `V30_DIALOGUE_CHAIN_ARCHITECTURE_20260629.md`。明确 7 阶段测算页只负责测算产出与一个轻量追问入口，完整八字对话必须升级为独立 `DialogueSession`，支持系统种子问题、用户自然语言种子问题、命理师种子和训练种子；对话链必须 answer-first、无限延展、可训练、可验证，并通过独立 `问八字` surface 展示。
- 2026-06-29 Dialogue Chain 执行更新：新增 `V30_DIALOGUE_CHAIN_EXECUTION_PLAN_20260629.md` 并完成最小闭环。新增 `v30.dialogue_chain` 契约、seed router、orchestrator、JSON store、独立 `/dialogue-seeds` 与 `/dialogues` API，前端新增独立 `问八字` 面板；用户可从 `我今年财运如何？` 等种子或自由输入启动连续问答，每轮 answer-first 后生成下一问和快捷选项。专项测试 `tests/unit/test_dialogue_chain_mainline.py` 3 passed；对话追加 turn 不修改 chart facts，不进入 7 阶段导航。
- Phase A-E 已完成主线骨架：命理师模式可以采纳、优先、降权、排除、待问和备注；选择结果进入中枢 belief delta / StagePoint overlay / final synthesis priority 线索；Admin 可回放 StagePoint、OptionSet、Brain Judge、Prompt Profile 和 PractitionerSelection。
- 当前主线完成度更新：工程主线约 98%，智能体验约 90%，产品可打磨约 80%；下一阶段优先做 Dialogue Chain 的 LLM 表达增强、Postgres/Admin 回放、真实案例对话 replay、518K 分布观察和 UI 细节打磨。
- 2026-06-30 紫微 Domain Lens 主线启动：新增 `V30_ZIWEI_DOMAIN_LENS_ENGINE_PLAN_20260630.md`。紫微不作为第二主引擎，不独立下结论；V1 仅做事实层、辅助信号、Probe 触发候选、命理师/admin 旁路观察和训练冲突样本，`ziwei_decision_weight` 固定为 0。
- 2026-06-30 Multi-Engine 主线启动：新增 `V30_MULTI_ENGINE_ARCHITECTURE_20260630.md` 和 `v30.engines` 薄抽象层。BaziEngine 包装现有 runtime，ZiweiEngine 接紫微 Domain Lens，RealityProbeEngine 包装现实校准；EngineManager 只做旁路审计和 SignalRegistry 汇总，不改变 DecisionVerdict、FinalSynthesis 或页面输出。
- 2026-06-30 命理测试与训练闭环 Phase 1 启动：新增 `V30_MINGLI_TEST_TRAINING_LOOP_PHASE1_20260630.md`。第一阶段把 Golden Case、Multi-Engine Training Example、ReadingQualityScore 和 MingliTrainingQualityGate 接成闭环，用于评价真实命理输出质量、训练样本质量和是否可进入下一轮 synthetic replay。
- 2026-06-30 命理测试与训练闭环 Phase 2 启动：新增 `V30_MINGLI_TEST_TRAINING_LOOP_PHASE2_20260630.md`。第二阶段把失败案例 Replay Queue、命理师标注投影、紫微 Golden Cases 和 Reality Probe / Verdict Diff 接成训练资产，仍不写 production pointer、不改 DecisionVerdict。
- 2026-06-30 Evaluation & Training Spine 启动：新增 `V30_EVALUATION_TRAINING_SPINE_20260630.md` 和 `v30.evaluation`。EvaluationCaseSpec 成为比 MingliGoldenCase 更强的评测合约，Verdict/Advice/Probe/TrainingImpact 各自独立评估；当前只做 sidecar evaluation，不改变用户结果、不写 production pointer。
- 2026-06-30 Evaluation Spine Admin 接入更新：新增 `/api/v30/admin/evaluation/training-spine` 只读质量门、`evaluation_spine_quality_gate` Training Orchestrator 计划、隔离 worker 支持、`scripts/run_evaluation_training_spine.py` 命令行入口，以及 Admin 训练页“测算质量门”摘要卡。当前专项实跑 `6/6 cases passed`，`average_overall_score=0.974`，`overclaim_rate=0.0`；该质量门进入 Admin 训练编排和 quality diff，但仍不写 production pointer。
- 2026-06-30 Admin Control Plane 主线启动：新增 `V30_ADMIN_CONTROL_PLANE_MAINLINE_20260630.md`、`v30.admin` contracts/RBAC/manifest 和 `/api/admin/v30/*` 第一批控制面入口。Admin 被正式定义为 Runtime Trace、Module Audit、Evaluation、Training、Validation、Config/Release 六个工作台组成的控制面；旧 `/api/v30/admin/*` 暂保留兼容，新开发优先走 `/api/admin/v30/*`。
- 2026-06-30 Admin Frontend 物理拆分启动：新增 `admin_frontend/index.html`、`v30.api.admin_frontend_app` 和 `scripts/run_admin_console.py`。Admin Console 可独立运行在 `http://127.0.0.1:9031/admin`，通过 proxy 调用 `9030` Runtime/Admin API；用户测算 UI 继续保留在 `9030`。
- 2026-06-30 Surface Orchestrator 主线完成到 `SO-12`：新增并更新 `V30_SURFACE_ORCHESTRATOR_MAINLINE_20260630.md`。用户测算面正式拆为 `ReadingSurface / CalibrationSurface / ConversationSurface / ThinkingSurface`；核心原则是报告先出、Probe 只在高价值时出现、连续对话必须用户主动进入、Thinking 只在请求时展示。`current_dialogue_turn` 已降级为诊断兼容字段；中枢 trace 改为 `reading_surface.conversation_surface` + `surface_decision_fields`，旧入口记录为 `legacy_customer_decision_field`。普通用户 `/view` 和 `/answer` 响应不直接暴露 `current_dialogue_turn / next_question / options`，诊断角色仍可在 `legacy_dialogue_surface.payload` 查看。新增 `v30.surface_output_pipeline.v1`，明确 SignalRegistry -> DecisionContract -> Verdict -> Advice -> Explanation -> DialogueRefinement 产出链路；本轮专项 `33 passed`。
- 2026-06-30 LLM 产品策略修正：`V30_LLM_SYNC_MODE` 代码默认从 `fast` 改为 `blocking`，用户可见命理回答默认等待 Gemma/Ollama 表达并通过中枢验收；`fast` 只保留为测试、离线验证和显式性能模式。LLM 不参与命盘事实、排盘、规则裁决或 Verdict 决策，但必须参与最终表达、智能对话回答和请求式 Thinking。`/api/v30/ui/capabilities` 已更新为 `blocking_llm_expression_default_fast_mode_explicit_only`；live LLM smoke 已确认 `gemma4:latest` 可用，约 4.46 秒返回。
- 2026-06-30 分支校准页产品化清理：`journey_branch_calibration` 不再把 `keep_both_branches... / ask_only_if_value... / downgrade_assertion...` 等工程策略 key 投影到页面；分支冲突按领域和关键问题去重，命理师 OptionSet 去重，按钮从全量调参动作收敛为当前选项相关操作。前端资源版本更新为 `20260630-branch-ui-clean`。
- 2026-06-30 Output Runtime Product Projection 主线启动：新增 `V30_OUTPUT_RUNTIME_PRODUCT_PROJECTION_MAINLINE_20260630.md`。本轮把 ChatGPT 定稿的 ProductProjection / Product Cards / LeakageGuard 落到 V30 runtime，先不重写 Decision Engine、不让 LLM 做裁决；`reading_surface.decision_workbench` 将兼容旧字段，同时新增产品投影、BranchCard 去重、人话化命理师动作和用户侧工程语言泄漏扫描。
- CBI-V2 之后，所有页面结论、智能追问、隐藏属性校准、最终报告都要能落到同一条中枢决策 trace。

## 当前主线任务

### 1. 清理旧系统残留

目标：

- 不保留旧模板式对话。
- 不保留幽灵式问题区。
- 不让工程状态文案出现在用户测算页。
- 前端只显示当前页面需要的一个问题。

状态：

- DTC-1 到 DTC-8 文档已合并。
- 历史计划文档已归档。
- 运行缓存已清理。
- 前端步骤页改为只消费 `CalibrationSurface` 中的高价值校准卡；连续智能问答进入独立 `ConversationSurface`。

### 2. 强化中枢智能大脑

目标：

- 步骤页只产出当前阶段的结构化素材、候选、分支、证据、反证和待校准项。
- 最终结论和建议必须由 Decision Engine 的 `Verdict` 生成，再交给 LLM 做用户可读表达。
- 结论优先，建议明确，但保留有证据的分支、概率和待复核边界。
- LLM thinking 过程服务最终表达、必要解释和对话，不再默认污染每一步素材。

状态：

- 中枢测算引擎框架已形成。
- LLM thinking 与页面小结已接入。
- 页面级提示词与上下文重构设计已文档化：`V30_STAGE_PROMPT_CONTEXT_DESIGN_20260628.md`。
- DCA 主线已经文档化：`V30_DECISION_CENTERED_ARCHITECTURE_20260629.md`。
- `DCA-2` 到 `DCA-11` 已完成基础落地：final synthesis、LLM context、prompt contract、7 阶段 journey navigation、命理师分支 OptionSet、边栏 Verdict 记忆、Decision slot 对话、轻量合成验证和反馈重算摘要已切到 `DecisionInputBundle -> Verdict -> LLM Expression` 主链。
- 下一步是把反馈重算摘要进一步接入 Admin 质量 diff、真实案例反馈和命理师 UI 回放。

### 3. 重构 Decision-Centered 测算流程

目标：

- 把 13 个细碎测算步骤压缩为 7 个高层阶段。
- 页面从“解释页”改为“素材页”。
- 命理师模式在分支冲突阶段做选择和校准。
- 普通用户只看到主判断、必要分支和最终建议。

状态：

- 已完成架构设计和主线任务拆分。
- 已完成 `DCA-2` 到 `DCA-11` 的基础工程落地。
- 待执行 `DCA-12`：Verdict 反馈质量 diff 与 UI 投影。

### 4. 重构智能对话闭环

目标：

- 推荐问题直接可点击。
- 用户回答尽量是选择、数字或极短输入。
- 回答后生成新的当前问题，而不是一次性显示一堆问题。
- 隐藏属性校准作为智能对话的一部分，不单独暴露复杂表单。

状态：

- 当前前端已改为使用 `calibration_surface` 渲染高价值校准卡，使用 `conversation_surface` 启动连续智能对话；`current_dialogue_turn` 只保留为诊断兼容 payload。
- 后端 DTC 训练链路已形成只读校准、候选、验证、复核、重型验证计划。
- 下一步是让对话只由 Decision Engine 的 `next_question_slots` 和 VOI 策略触发，回答后更新 belief 和相关 Verdict。

### 5. 文档治理

目标：

- 每个主线领域只保留一份 canonical 文档。
- 历史计划进入 archive。
- 新任务只更新当前主线文档，不再新增散落日期文档。

状态：

- 已新增 `V30_DOCUMENTATION_INDEX_20260628.md`。
- 已新增 `V30_ARCHITECTURE_CLEANUP_AUDIT_20260628.md`。
- 已归档 7 份历史计划文档。

## 默认禁止

- 不自动发布策略。
- 不写 production policy pointer。
- 不让 LLM 修改排盘、规则、画像、路径等事实层。
- 不用 fallback 冒充 LLM 推演。
- 不把训练样本直接当成线上策略。
- 不为每个小改动运行 full 518k 或 full synthetic all。

## 下一步

CBI-V2 当前基础闭环已经完成：

```text
Evidence Graph
-> Belief State
-> Value-of-Information Dialogue
-> Brain Decision Trace
-> Brain Training Example
-> Synthetic Validation
-> Product Projection
```

进展：

- CBI-V2-1 中枢决策契约已完成基础落地，新增 V2 决策 trace、belief state、LLM candidate、training example 等契约，并通过目标测试。
- CBI-V2-2 Evidence Graph 第一等输入已完成基础接入，runtime diagnosis payload 输出完整 graph，central reading state 生成 graph snapshot 和 claim graph metrics，并将图支持、图先验、图路径连贯度纳入 claim score。
- CBI-V2-3 Belief State 与 Claim Posterior 已完成基础落地，用户确认/否认会进入 claim posterior delta，反馈只改变 belief，不改命盘事实。
- CBI-V2-4 Value-of-Information 对话策略已完成基础落地，追问动作基于 information gain、claim impact、user cost 和 overask penalty。
- CBI-V2-5 Brain Decision Trace 已完成基础接入，页面下一步动作、claim、question、reason codes 和 feature vector 进入统一 trace。
- CBI-V2-6 BrainTrainingExample 已完成基础接入，每次中枢决策可沉淀为训练样本，且禁止训练事实层和写生产策略。
- CBI-V2-7 central reading synthetic validation 已扩展 `central_brain_v2_decision_loop` 检查，当前中枢组合测试 30 passed。
- CBI-V2-8 老旧脑路径已基础收束，`interaction_brain` 明确作为 structured feedback adapter，不再拥有选问题或下结论权限。
- CBI-V2-9 产品投影已基础接入，`current_dialogue_turn` 优先服从 `brain_decision_trace`，并展示 customer-safe `decision_basis`。
- CBI-V2-Q 中枢智能质量增强已完成第二阶段，新增 Brain Judge，接入 final synthesis、LLM derivation review，并沉淀 `v30.training_signal.central_brain_judge_quality`。
- CBI-V2-Q5 质量评审信号已转为 `question_policy.weights.central_brain_synthesis_policy` 候选策略，runtime `CentralReadingState` 和 `FinalSynthesis` 已消费该策略；策略只调整综合质量、证据绑定、建议行动性、模板风险和过度断言惩罚，不改排盘与规则事实。
- CBI-V2-Q6 最终综合已蓝图化，`final_synthesis.synthesis_blueprint` 先确定主断语、证据抓手、判断焦点、行动步骤和风险边界，再生成结论和建议；客户端只投影安全的 `decision_focus/action_steps/risk_boundary`。
- CBI-V2-Q7 蓝图质量已进入训练闭环，新增 `v30.training_signal.central_brain_synthesis_blueprint_quality`，central reading synthetic validation 增加 `final_synthesis_blueprint_quality` 检查，auto training 会把蓝图覆盖率转入综合策略候选。
- CBI-V2-Q8 训练后直接生效已正规化，auto training 结果新增 `policy_application` 和 `training_signal_summary`，Admin 训练页改为“训练并自动生效”，展示 active/previous/rollback 和 Brain Judge/Blueprint 训练信号。
- CBI-V2-Q9 已开始真实训练与验证实跑：`synthetic all` 127/127 passed，518K sample eligible，518K shard 7 eligible，518K readiness matrix 7/7 passed，`cbi-v2-q8-real-run` strict auto-training promoted 4/4 并写入 runtime pointer。
- CBI-V2-Q10 Training Loop V2 已开始落地，auto-training 支持后台 job、结构化 progress event、Admin 启动/轮询/百分比显示、训练历史、policy lineage summary 和 pointer-only rollback，canonical 文档为 `V30_TRAINING_LOOP_V2_ADMIN_CONSOLE.md`。
- CBI-V2-Q11 Training Orchestrator V1 已开始落地，新增训练计划层、统一 orchestrator job/status/history、`central_brain_auto_apply` 和 `quick_validation_only` 两个计划，Admin 训练页可从总调度启动和查看计划进度，canonical 文档为 `V30_TRAINING_ORCHESTRATOR_V1.md`。
- CBI-V2-Q12 M3 / 518K 验证已纳入 Training Orchestrator，新增 `m3_518k_validation` 计划，覆盖 M3 snapshot、M3 synthetic、training_pipeline、518K sample，并可选 518K shard 与 readiness matrix；该计划不提升 runtime pointer，只作为知识/规则/画像/路径验证证据。
- CBI-V2-Q13 Training Orchestrator 新增训练结果 diff 与失败步骤重跑，`/diff` 可对比同 plan 上一轮摘要指标，`/rerun-failed` 可针对 `quick_validation_only` 与 `m3_518k_validation` 只重跑失败步骤，Admin 训练页展示 diff 并在失败时提供重跑入口。
- CBI-V2-Q14 Training Orchestrator diff 已升级为业务质量对比，新增 `quality_metrics / quality_diff_rows / quality_improvement_count / quality_regression_count`，覆盖最终综合质量、建议可执行性、焦点覆盖、证据链覆盖、智能追问质量、表达质量、模板风险、过度断言风险和 M3/518K 验证质量；Admin 训练页显示“智能质量对比”。
- CBI-V2-PH2 第二阶段训练主线已启动，canonical 文档为 `V30_CENTRAL_BRAIN_TRAINING_PHASE2_PLAN_20260628.md`；目标是把真实反馈、合成验证和 518K 分布证据统一为 `BrainTrainingExample`，再通过策略优化、synthetic replay gate、518K gate、auto apply 和质量 diff 形成“训练后可观察变聪明”的闭环。
- CBI-V2-PH2-1 `BrainTrainingExample` 契约与 Builder 已完成，新增 input snapshot、structured labels、safety gate、标准 builder 与 JSONL store 最小实现；runtime `CentralReadingState` 输出的 `brain_training_example` 已切到标准 Builder，训练样本明确禁止 chart facts、LLM fact injection 和 production policy write。
- CBI-V2-PH2-2 Training Dataset Store 已完成，`BrainTrainingExampleStore` 支持 JSONL append/read/filter、固定 seed 的 train/validation/replay split、split manifest、质量/风险摘要；Admin API 新增 `/admin/training/brain-examples/summary` 与 `/admin/training/brain-examples/split`，训练页展示“中枢训练样本池”。
- CBI-V2-PH2-3 Policy Optimizer V1 已完成，新增 `optimize_central_brain_policy`，从 split 样本聚合 claim correctness、information gain、actionability、template risk、overclaim risk 和 user cost，生成 clipped delta 候选策略；Admin API 新增 `/admin/training/brain-examples/optimize`，风险过高或样本不足时阻止 promotion。
- CBI-V2-PH2-4 Synthetic Replay Gate 已完成，新增 `v30.central_brain_phase2_replay_gate.v1`，用 train split 生成候选策略，再用 replay split 和 central reading synthetic validation 做门禁；Admin API 新增 `/admin/training/brain-examples/replay-gate`，训练页展示 `Synthetic Replay Gate` 状态，门禁仍禁止 chart fact mutation 和 policy pointer write。
- CBI-V2-PH2-5 518K Distribution Gate 已完成，新增 `v30.central_brain_phase2_distribution_gate.v1`，用 replay gate 结果叠加 518K sample / 可选 shard 验证候选策略分布稳定性；Admin API 新增 `/admin/training/brain-examples/distribution-gate`，通过 policy override 验证候选权重，不写 runtime pointer，不默认要求 full 518K。
- CBI-V2-PH2-6 Orchestrator Phase2 计划已完成主闭环，Training Orchestrator 新增 `central_brain_phase2_training`，串联样本摘要、split、Policy Optimizer、Synthetic Replay Gate 和 518K Distribution Gate；该计划可从 Admin 训练总调度启动，输出 `phase2_result / phase2_replay_gate / phase2_distribution_gate`，仍不写 runtime pointer。
- CBI-V2-PH2-7 页面级 LLM 采用规则已收紧为“硬边界拦截、软质量清洗”：LLM 非空文本不再因 Brain Judge 低分被中枢大脑直接丢弃，Brain Judge 只作为训练/质量信号；只有内部标识泄露、角色泄露、事实边界破坏、高风险绝对断语、模型不可达或空文本才会阻断页面结论。
- CBI-V2-PH2-8 边栏工作记忆与用神忌神主线启动，canonical 文档为 `V30_SIDEBAR_MEMORY_USEFUL_GOD_MAINLINE_20260628.md`；目标是新增 `thinking_projection.sidebar_memory`，把规则、特征、画像、路径、结构、用神忌神、时运和领域结论逐步沉淀到边栏，并把用神模型扩展为“取用策略 + 忌避风险 + 反证边界”的可训练、可验证组件。
- CBI-V2-PH2-9 结构页与 LLM 上下文去工程化已完成：结构 `semantic_label`、主链、ranked decision 候选、用神候选理由、侧边栏记忆和通用 Bazi LLM context 均改为 customer-safe 中文投影，避免 `evidence-bound`、`dynamic_structure_review`、`output_or_wealth_release_review` 等内部枚举进入页面或提示词；已对历史 reading `v30-reading-1781329281156` 验证结构页 LLM stream accepted 且无 forbidden hits。
- CBI-V2-PH2-10 Stage Intelligence Point Framework 已完成基础落地，canonical 文档为 `V30_STAGE_INTELLIGENCE_LLM_BRAIN_FRAMEWORK_20260629.md`；`SPI-1` 到 `SPI-5` 已接入 StagePoint 契约、LLM candidate_points 输出、中枢采用管线、页面列表展示和边栏 source 追踪，`SPI-6` 到 `SPI-8` 保留为命理师选择、专项验证和 Admin 回放任务。
- CBI-V2-PH2-11 Text-to-Option Practitioner Interaction Framework 已完成基础落地，canonical 文档为 `V30_TEXT_TO_OPTION_PRACTITIONER_INTERACTION_FRAMEWORK_20260629.md`；`TOI-1` 到 `TOI-5` 已接入 `TextSemanticUnit / OptionSet / PractitionerSelection` 契约、文本抽取器、OptionSet Gate、StagePoint 关联和 `current_dialogue_turn.response_option_set`；`TOI-6` 和 `TOI-7` 保留为命理师 UI、专项 synthetic tier、518K 分布观察和 Admin 抽取回放任务。
- ETS-8 到 ETS-11 已完成：Evaluation & Training Spine 从后端 sidecar 升级为 Admin 可运行质量门，Training Orchestrator 可把 Evaluation 指标纳入训练质量对比，后续策略训练必须用这把尺子证明 Verdict、Advice、Probe 和 overclaim 风险没有退化。
- ACP-1 到 ACP-7 已完成：Admin Control Plane 完成第一阶段逻辑隔离，新增 Control Plane Manifest、RBAC、Versioned Config/Audit 合约、新 `/api/admin/v30` namespace 和 Trace/Evaluation/Training/Validation 第一批入口；物理拆分前先保证边界、权限、Job 和发布审计模型稳定。
- ACP-8 到 ACP-11 已完成：Admin 前台服务已先行物理拆出，默认 9031 端口；`9031/admin` 通过 proxy 调用 `9030` Runtime/Admin API。
- ACP-12 已完成：Admin 前台 JS/CSS 已拆出为 `admin_frontend/app.js` 与 `admin_frontend/styles.css`；主系统前端去 Admin 化，`frontend/app.js`、`frontend/index.html`、`frontend/styles.css` 不再包含 admin 模块、管理入口或后台样式；主系统角色只保留 guest/user/practitioner，admin 账号进入主测算系统时按命理师能力使用。
- SYS-CLEAN-1 已完成：清理主系统前端残留的后台工作台 CSS selector，更新主 UI 与 Admin Console 静态资源版本号为 `20260630-system-cleanup`；`V30_UI_PRODUCT_DESIGN_PLAN.md` 已标记旧 in-product Admin Shell 章节为历史记录，并指向独立 Admin Control Plane 文档。
- 当前主线组合测试 67 passed，BT1/BT2 脚本通过，central reading synthetic validation 9/9 ready；全单元曾检出 6 个 release/RBD/latent 级联失败，已修复并针对失败集合复测 6 passed。

DTC-9 显式执行 runner 暂时降为支持任务。原因是当前主线已经从对话训练执行器，提升为中枢智能大脑 V2 的建模、算法和训练闭环。

近期不再扩散做 UI 细节、大规模发布流程或外部 agent 框架迁移，先把中枢智能大脑的判断能力做扎实。
