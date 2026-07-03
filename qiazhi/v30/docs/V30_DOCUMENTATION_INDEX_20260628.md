# V30 文档索引与合并边界

更新时间：2026-06-30

## 当前状态

本轮审计后，`docs/` 下仍保留多份 V30 文档。文档不是全部废弃，而是混合了四类内容：

- 当前主线架构
- 已完成阶段记录
- 专项设计草案
- 历史计划和 review

后续阅读和维护应先看本索引，不再从文件名猜测状态。

## Canonical 主文档

### 中枢智能大脑与测算引擎

优先阅读：

- `V30_MAINLINE_STATUS_20260628.md`
- `V30_DECISION_CENTERED_ARCHITECTURE_20260629.md`
- `V30_MAINLINE_COMPLETION_AND_NEXT_PLAN_20260629.md`
- `V30_CHATGPT_HANDOFF_PRODUCTION_ORCHESTRATOR_AUDIT_20260629.md`
- `V30_PRODUCTION_ORCHESTRATOR_DCA13_DCA14_PLAN_20260629.md`
- `V30_SIGNAL_BASED_DECISION_CANDIDATE_DCA15_PLAN_20260629.md`
- `V30_CONFLICT_RESOLVER_DCA15_ENHANCEMENT_PLAN_20260629.md`
- `V30_DCA16_DECISION_WORKBENCH_UI_CLOSEOUT_20260629.md`
- `V30_DCA17_DECISION_WORKBENCH_QUALITY_AUDIT_20260629.md`
- `V30_DIALOGUE_CHAIN_ARCHITECTURE_20260629.md`
- `V30_A_TO_E_MAINLINE_EXECUTION_20260629.md`
- `V30_STAGE_INTELLIGENCE_LLM_BRAIN_FRAMEWORK_20260629.md`
- `V30_TEXT_TO_OPTION_PRACTITIONER_INTERACTION_FRAMEWORK_20260629.md`
- `V30_PROBABILISTIC_BRANCH_REASONING_FRAMEWORK_20260629.md`
- `V30_ADMIN_CONTROL_PLANE_MAINLINE_20260630.md`
- `V30_SURFACE_ORCHESTRATOR_MAINLINE_20260630.md`
- `V30_OUTPUT_RUNTIME_PRODUCT_PROJECTION_MAINLINE_20260630.md`
- `V30_MULTI_ENGINE_ARCHITECTURE_20260630.md`
- `V30_ZIWEI_DOMAIN_LENS_ENGINE_PLAN_20260630.md`
- `V30_CENTRAL_BRAIN_V2_MAINLINE.md`
- `V30_CENTRAL_BRAIN_READING_ENGINE_FRAMEWORK_20260627.md`
- `V30_STAGE_PROMPT_CONTEXT_DESIGN_20260628.md`
- `V30_UNIFIED_INTERACTION_BRAIN_PLAN.md`
- `V30_EXPRESSION_AND_CENTRAL_BRAIN_FRAMEWORK.md`
- `V30_BAZI_LLM_CONTEXT_AND_PROMPT_MAINLINE.md`

用途：

- 定义中枢大脑如何调度排盘、规则、画像、特征、路径、LLM thinking、结论建议。
- 定义 Decision-Centered Architecture：步骤页只沉淀干净素材和分支候选，Central Feedback Overlay 只提供权重，最终断语只能由 Decision Engine 裁决，LLM 只负责最终表达、必要解释、对话措辞和边界复核。
- 定义当前主线完成度、模块完成百分比、主要缺口和下一阶段 Phase A-E 任务计划。
- 记录 Production Orchestrator / Signal Registry 交接审计：当前 runtime 链路、模块到产出的映射、断语来源、LLM 边界、训练验证影响路径和 DCA-13 到 DCA-18 下一阶段任务。
- 定义 DCA-13 / DCA-14 第一阶段执行计划：旁路 Signal Registry、SignalUsageAudit、ModuleAudit 和 production audit debug 出口；明确本阶段不替换 Decision Engine、不改变 Verdict 和 FinalSynthesis。
- 定义 DCA-15 signal-aware DecisionCandidate Builder：兼容模式先把 DiagnosisClaim / Path / Portrait / Rule / RankedDecision signals 绑定到 DecisionCandidate，不改分数、不改 Verdict，为后续 signal-based 裁决增强做准备。
- 定义 DCA-15 ConflictResolver 增强阶段：把近似分支、反证、校准需求从 `DecisionEngine` 内部抽成独立 resolver 和 audit，不改 score、不改 Verdict，为命理师校准、Admin 回放和训练验证提供结构化产出。
- 定义 DCA-16 Decision Workbench 与页面流程收口：把 Verdict、ConflictResolver audit、命理师校准和 7 阶段页面投影接到 `reading_surface.decision_workbench` 与前端 UI，普通用户清爽可读，命理师可校准，训练信号按角色隔离。
- 定义 DCA-17 Decision Workbench 质量审计：把 7 阶段、Verdict、冲突、命理师选项、角色隔离和智能对话入口纳入只读 admin 质量 diff，确认产出链路真的进入用户结果。
- 定义 Dialogue Chain Architecture：把智能八字对话从 7 阶段页面附属追问升级为独立 `DialogueSession`，支持系统种子、用户自然语言种子、命理师种子、无限问题链、answer-first 策略、训练和验证闭环。
- 定义 Dialogue Chain Execution：记录 `v30.dialogue_chain` 契约、seed router、orchestrator、store、API、前端 `问八字` 面板和专项测试执行结果。
- 记录 Phase A-E 的执行结果：TOI/SPI/CBI 进入命理师校准、中枢权重、Admin 回放、synthetic 验证和 UI 投影闭环。
- 定义 `StagePoint` 页面智能判断点框架，让 LLM 候选推演经中枢验收后，变成页面列表、边栏记忆、命理师可选项和训练样本。
- 定义 Text-to-Option 文本语义选项化框架，把测算文本和对话文本里的候选、列表、数字、取舍自动抽成 `OptionSet`，用于命理师选择、用户点击式回答和训练反馈。
- 定义 Evidence-Bound Branch / Probabilistic Reasoning 框架：允许候选、分支、概率和待复核，但必须绑定证据、反证、置信度和复核条件。
- 定义分支候选的角色化投影：普通用户只读并优先看到主分支，命理师和 admin 可交互选择、降权、待问和备注，反馈进入中枢权重与训练闭环。
- 定义 Admin Console / Control Plane：Admin 不是用户测算 UI 的隐藏页面，而是 Runtime Trace、Module Audit、Evaluation、Training、Validation、Config/Release 六个工作台组成的控制面；第一阶段启用独立 `/api/admin/v30/*` namespace、Admin contracts、RBAC、Versioned Config 和 Job 边界；当前 Admin 前台已独立为 `v30.api.admin_frontend_app`，默认端口 `9031`，并已拆出 `admin_frontend/app.js` 与 `admin_frontend/styles.css`。主系统前端只保留 guest/user/practitioner，不承载 Admin Shell、后台入口或训练/验证/配置 UI。
- 定义 Surface Orchestrator：用户测算 UI 分为 ReadingSurface、CalibrationSurface、ConversationSurface 和 ThinkingSurface；测算步骤不再直接消费 `current_dialogue_turn`，Probe 必须从 `calibration_surface` 来，连续智能问答必须从 `conversation_surface` 主动进入，Thinking 只做请求式过程查看；`v30.surface_output_pipeline.v1` 约束 SignalRegistry -> DecisionContract -> Verdict -> Advice -> Explanation -> DialogueRefinement 的用户侧产出链路。
- 定义 Output Runtime Product Projection：把内部 Verdict、ConflictResolver audit、Probe 和 Advice 先转成用户/命理师产品卡片，再进入 LLM 表达和页面投影；`LeakageGuard` 阻断工程策略 key、训练字段、debug 文案和 raw runtime status 进入用户侧。
- 定义 Multi-Engine Architecture：所有命理能力都以 Engine 形式接入；Engine 只能产出 facts/features/signals/probe candidates，中枢只生成 EnginePlan 和调度，DecisionEngine 是唯一 Verdict 生成者。
- 定义紫微 Domain Lens：紫微不是第二主引擎，不生成独立报告；V1 只落事实层、36 条领域信号、Probe 映射和 Signal Registry 旁路观察，决策权重固定为 0。
- 定义中枢大脑 V2 的 Evidence Graph、Belief State、Value-of-Information 对话策略、LLM Candidate + Brain Judge、Final Synthesis Blueprint、Brain Judge/Blueprint 质量策略候选和训练验证闭环。
- 约束所有小结和问答必须绑定八字证据，而不是模板化表达。
- 约束测算步骤从“每步 LLM 长文解释”改为“素材页 + 裁决页 + 表达页”：13 个细碎步骤将压缩为 7 个高层阶段，每阶段默认不调用 LLM 生成长文，避免污染规则、画像、路径、用神和时运素材。
- 定义页面级 `stage_prompt_profile`，让规则、画像、路径、结构、领域和报告使用不同提示词与上下文契约。
- 硬性约束：测算步骤和智能对话是两个独立 surface；步骤页只能显示 `calibration_surface` 给出的高价值校准卡，连续对话必须进入 `conversation_surface`，不能通过 `current_dialogue_turn` 或 `question_followup` 伪步骤混入导航。

### 智能对话、训练与验证

优先阅读：

- `V30_DIALOGUE_TRAINING_PIPELINE_20260628.md`
- `V30_MINGLI_TEST_TRAINING_LOOP_PHASE1_20260630.md`
- `V30_MINGLI_TEST_TRAINING_LOOP_PHASE2_20260630.md`
- `V30_EVALUATION_TRAINING_SPINE_20260630.md`
- `V30_TRAINING_ARCHITECTURE.md`
- `V30_AUTO_APPLY_TRAINING_ADMIN_MAINLINE.md`
- `V30_TRAINING_LOOP_V2_ADMIN_CONSOLE.md`
- `V30_TRAINING_ORCHESTRATOR_V1.md`
- `V30_QUESTION_INTELLIGENCE.md`
- `V30_DIALOGUE_SYSTEM_CLEANUP_AUDIT_20260627.md`

用途：

- 定义智能问题如何产生、校准、训练、候选、验证、复核。
- 定义命理测试与训练闭环 Phase 1：Golden Case、Multi-Engine Training Example、ReadingQualityScore 和 MingliTrainingQualityGate，用于评价真实测算质量而不是只看模块是否能跑。
- 定义命理测试与训练闭环 Phase 2：失败案例 Replay Queue、命理师标注投影、紫微 Golden Cases 和 Reality Probe / Verdict Diff，把评分结果转成可迭代训练资产。
- 定义 Evaluation & Training Spine：EvaluationCaseSpec、ExpectedVerdict、VerdictEval、AdviceEval、ProbeEval、MetricSummary 和 TrainingImpactDiff，把“测得好不好”从训练样本里抽成独立评测合约；当前已接入 `/api/v30/admin/evaluation/training-spine`、Training Orchestrator `evaluation_spine_quality_gate` 和 `scripts/run_evaluation_training_spine.py`。
- 明确 DTC-1 到 DTC-8 已合并为一条训练验证管线。
- 定义训练后直接生效、runtime pointer、rollback 和 Admin 训练页展示边界。
- 定义 Admin 启动训练、后台 job、百分比进度、验证后自动生效和训练边界。
- 定义 Training Orchestrator V1 的计划层、统一 job/history/status 和后续 M3/518K 接入方向。
- DTC-9 显式执行 runner 暂作为支持任务；当前主线优先推进中枢 StagePoint、训练样本、验证回放和 Admin 观察闭环。

### 八字事实层、规则层、画像层

优先阅读：

- `V30_INTEGRATED_BAZI_MODEL_PIPELINE.md`
- `V30_CORE_BAZI_EIGHT_MODULE_PLAN.md`
- `V30_KNOWLEDGE_RULE_PORTRAIT_PLAN.md`
- `V30_STRUCTURE_DYNAMICS.md`
- `V30_RULE_KNOWLEDGE_DYNAMICS_REVIEW.md`

用途：

- 定义排盘、十神、旺衰、格局、规则、动态路径、画像、特征等基础模块。
- 这些模块是中枢大脑推演的“食材”，不能被智能对话替代。

### 合成验证与 518k 验证

优先阅读：

- `V30_SYNTHETIC_VALIDATION.md`
- `V30_SYNTHETIC_CANONICAL_BAZI_CALIBRATION_PLAN.md`
- `V30_518K_VALIDATION_PLAN.md`
- `V30_TEST_ARCHITECTURE.md`

用途：

- 定义可训练、可合成验证、可回归测试的质量闭环。
- 所有策略晋级都必须经过验证，不允许直接靠页面观感上线。

### 产品体验与 UI

优先阅读：

- `V30_UI_CORE_READING_PRODUCTIZATION_PLAN.md`
- `V30_UI_PRODUCT_DESIGN_PLAN.md`
- `V30_BAZI_INTERACTION_SYSTEM.md`
- `V30_QUESTION_INTERACTION_SIMPLIFICATION_20260627.md`

用途：

- 定义一步一步测算、页面结论和建议、必要时智能追问、可视化反馈。
- 交互原则是简洁、聚焦、结论优先。
- `V30_BAZI_INTERACTION_SYSTEM.md` 记录“测算步骤 vs 对话 surface”硬边界，后续 UI 和中枢设计必须优先遵守。

### 部署、运行、发布

优先阅读：

- `V30_DEPLOYMENT.md`
- `V30_RUNTIME_POINTERS.md`
- `archive/V30_CONTROLLED_RELEASE_READINESS_PLAN.md`
- `archive/V30_POST_SEAL_RELEASE_HARDENING_PLAN.md`

用途：

- 定义本地、服务器、数据库、LLM、发布和运行状态。

## 已归档阶段计划

以下文档已经从根目录移入 `archive/`。它们仍保留历史证据价值，但不再作为当前开发入口：

- `archive/V30_BRAIN_TRAINING_SYNTHETIC_COMPLETION_MAINLINE.md`
- `archive/V30_MULTI_USER_TERMINAL_LOCALE_PRODUCTIZATION_MAINLINE.md`
- `archive/V30_CONTROLLED_RELEASE_READINESS_PLAN.md`
- `archive/V30_POST_SEAL_RELEASE_HARDENING_PLAN.md`
- `archive/V30_M1_M2_BAZI_CALCULATION_FACT_LAYER_COMPLETION_PLAN.md`
- `archive/V30_M3_CORE_KNOWLEDGE_STRUCTURE_COMPLETION_PLAN.md`
- `archive/V30_M4_TEN_GOD_ENERGY_MODEL_COMPLETION_PLAN.md`
- `archive/V30_M5_RANKED_DECISION_COMPLETION_PLAN.md`
- `archive/V30_M6_PRACTICAL_READING_OUTPUT_COMPLETION_PLAN.md`
- `archive/V30_M7_REAL_CASE_CALIBRATION_COMPLETION_PLAN.md`
- `archive/V30_M8_USER_PRESENTATION_API_PROJECTION_COMPLETION_PLAN.md`

## 下一轮可合并文档

以下文档建议进入第二轮合并，不建议继续作为主线入口维护：

- `archive/V30_CURRENT_MAINLINE_TASKS_20260610.md`
- `archive/V30_MAINLINE_COMPLETION_PLAN.md`
- `archive/V30_MASTER_MAINLINE_PLAN.md`
- `archive/V30_NEAR_TERM_EXECUTION_PLAN.md`
- `archive/V30_POST_SEAL_MAINLINE_TASK_PLAN.md`
- `archive/V30_CORE_MODULE_FINAL_COMPLETION_MAINLINE.md`
- `archive/V30_MAIN_MODULE_COMPLETION_REVIEW.md`

合并目标：

- 只保留一个 `V30_MAINLINE_STATUS_20260628.md`
- 历史计划转入 archive
- 当前任务只保留正在推进的主线和阻断项

## 暂不删除的文档

以下文档虽然有阶段性特征，但仍包含领域建模依据，暂不删除：

- `V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md`
- `V30_HIDDEN_FACTORS_AND_DIALOGUE_DISCOVERY.md`
- `V30_LATENT_BAZI_ATTRIBUTES_SYSTEM_PLAN.md`
- `V30_LATENT_BAZI_PROFILE_REFACTOR_PLAN.md`
- `V30_THINKING_LLM_PROMPT_FRAMEWORK_20260626.md`
- `V30_XUANMING_CORE_MODEL_DESIGN_20260626.md`
- `V30_XUANMING_REASONING_ENGINE_TASKS_20260626.md`

原因：

- 隐藏属性、thinking、玄明中枢建模仍是当前产品体验和算法框架的重要来源。
- 需要等 DTC-9 和智能对话闭环稳定后，再抽象成更少的 canonical 文档。

## 文档维护规则

- 新主线只写入 canonical 文档，不再新增散落的日期任务文档。
- 阶段性记录必须写明是否可执行、是否已执行、是否只读。
- 涉及策略训练、验证、发布的文档必须明确禁止自动上线边界。
- UI 文档必须从用户体验出发，不保留工程状态文案作为产品说明。
- 任何废弃文档进入 archive 前，先确认没有唯一的领域知识或验证结论。
