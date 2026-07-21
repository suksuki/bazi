# DeepBazi / DeepLife Decision Register

Status: active living record
Owner: product strategy and architecture
Last updated: 2026-07-21

## Purpose

重要讨论不能只存在于聊天记录中。本文件记录已经接受、冻结、修订或仍待裁决的产品与架构决定，并链接到完整 Markdown 基线。

```text
Discussion
→ Decision Register entry
→ Detailed design or contract
→ Implementation and audit report
→ Revised / frozen / retired status
```

聊天记录不是运行时权威。正式代码只能依据标记为 `accepted` 或 `frozen` 的合同；`proposed` 内容不得被工程实现偷跑成产品事实。

## Status Vocabulary

| Status | Meaning |
| --- | --- |
| `proposed` | 已记录，仍需讨论或验证 |
| `accepted` | 方向已接受，可以进入受控设计或实现 |
| `frozen` | 当前权威基线，修改必须产生新版本或修订记录 |
| `implemented` | 已实现，但仍需以对应验收边界理解 |
| `revised` | 原决定已被后续决定部分替代 |
| `retired` | 不再具有产品或架构权威 |

## Maintenance Rule

每轮重要讨论结束后至少补充：

```yaml
decision_id:
date:
title:
status:
decision:
why:
hard_boundaries:
supersedes:
affected_documents:
implementation_status:
open_questions:
```

不得静默改写旧决定。方向变化时保留旧条目，并通过 `supersedes` 或 `revised_by` 建立关系。

## Current Decisions

### DR-001 — Mingli First

```yaml
decision_id: DR-001
date: 2026-07-14
title: DeepLife remains a professional Mingli product first
status: frozen
decision: Life OS、长期陪伴和 Abu 体验必须建立在可追溯的专业命理认知之上，不能退化为泛人生教练。
hard_boundaries:
  - 专业命理依据优先于叙事趣味和用户活跃度
  - 依据不足时保留不确定性，不用通用心理话术补空白
affected_documents:
  - product/PRODUCT_CONSTITUTION_V1_1.md
implementation_status: active product authority
```

### DR-002 — LLM Is The Cognitive Reasoner

```yaml
decision_id: DR-002
date: 2026-07-16
title: LLM performs whole-chart comparative reasoning
status: frozen
decision: LLM 是命理认知主体；确定性系统提供命盘事实、知识、工具、上下文编译、案例记忆和同行评审式检查，不再用模板与评分模块替代整盘综合。
hard_boundaries:
  - 命盘事实不能由 LLM 虚构
  - Review 不得把专业认知重新洗成保守模板
  - Mechanism label 不是最终认知中心
affected_documents:
  - V50_MINGLI_COGNITIVE_ARCHITECTURE_V1.md
  - V50_CURRENT_ARCHITECTURE.md
  - V50_RUNTIME_MODULE_AUTHORITY_MAP_V1.md
implementation_status: current cognitive direction
```

### DR-003 — LifeCase Is The Formal Case Authority

```yaml
decision_id: DR-003
date: 2026-07-15
title: Formal cognition and exploratory state are separated
status: frozen
decision: LifeCase 保存正式案例认知；Draft、Probe、反馈、专题选择和沙盒实验不能自动改写命盘事实或正式认知。
affected_documents:
  - product/LIFE_CASE_AND_FORMAL_INSIGHT_V1.md
  - product/FIRST_RUN_STREAMING_AND_ACTIONS_V1.md
implementation_status: implemented and audited
```

### DR-004 — Product Modes Are Projections, Not Engines

```yaml
decision_id: DR-004
date: 2026-07-10
title: One cognition, role-appropriate disclosure
status: frozen
decision: Guest、Member、Practitioner 和 Research 是任务模式与披露深度，不是四套命理引擎；管理员可以测试切换，普通账户只能进入授权角色。
affected_documents:
  - product/ROLE_BASED_DISCLOSURE.md
implementation_status: active product boundary
```

### DR-005 — Abu Theater Control And Performance Are Separate

```yaml
decision_id: DR-005
date: 2026-07-18
title: Control runtime is frozen; performance remains an asset and runtime production line
status: implemented_p0_slice1
decision: Theater Control Runtime 负责节目、隐私、同步和回放；Performance 负责声音、角色、字幕、动作和命理舞台。更多控制代码不能冒充表演完成。
hard_boundaries:
  - 音频是表演唯一主时钟
  - Replay 不重新调用 LLM、Reasoner、TTS 或动作编排
  - 体验层不发明命理认知
affected_documents:
  - product/V50_ABU_LIVING_THEATER_V1.md
  - product/V50_ABU_PERFORMANCE_PROOF_01.md
implementation_status: Performance Proof 01 runtime-side pass; Rive actor blocked
```

### DR-006 — Gemini Is An Offline Abu Motion Factory

```yaml
decision_id: DR-006
date: 2026-07-18
title: Generated video supplies reusable actor shots, not complete runtime performances
status: accepted
decision: Gemini 用于离线生产阿布入场、思考、指向、倾听、情绪和过场素材；Qwen TTS 负责正式声音；Theater Runtime 负责编排。
hard_boundaries:
  - 不在 Live 中临时生成完整节目
  - 不让 Gemini 生成用户私人命理台词和程序化命盘结构
  - 动作素材必须统一画布、比例、锚点、镜头、光照和可衔接中性姿势
affected_documents:
  - product/V50_INTERACTIVE_MINGLI_THEATER_ARCHITECTURE_V1.md
implementation_status: design baseline only
```

### DR-007 — Mingli Visualization Is A Deterministic Cognitive Interface

```yaml
decision_id: DR-007
date: 2026-07-18
title: Four pillars, paths, timing and Xiangfa require a state-driven visualization runtime
status: accepted
decision: 四柱、做功 Graph、路径、时间激活和象法由结构化 VisualSpec 与程序化 Renderer 表达；可视化层只呈现认知结果，不拥有新的命理判断权。
hard_boundaries:
  - 命理工具动画先准确表达结构，再追求生动与氛围
  - Gemini 不生成命理主结构图
  - 未决路径必须保留，不能被视觉隐藏成确定答案
affected_documents:
  - product/V50_INTERACTIVE_MINGLI_THEATER_ARCHITECTURE_V1.md
implementation_status: Topic 01 four-pillar/path renderer implemented; timing and Xiangfa renderers remain unimplemented
```

### DR-008 — Executable Topics Use An Isolated Sandbox

```yaml
decision_id: DR-008
date: 2026-07-18
title: Mingli topics are operable lessons and experiments, not videos with buttons
status: accepted
decision: 用户可以在专题中选择、点亮、消融、切换时序和比较假设，但所有操作进入 MingliSandboxState / TopicExploration，不直接改变真实命盘或 LifeCase。
hard_boundaries:
  - Baseline、Modified 和 Diff 必须同时可追踪
  - 沙盒结果需标记确定性计算、候选假设或待验证解释
  - 写回正式案例必须重新经过 Reasoner 与 Reliability Gate
affected_documents:
  - product/V50_INTERACTIVE_MINGLI_THEATER_ARCHITECTURE_V1.md
implementation_status: Topic 01 single-node structural ablation implemented; broader Lab remains unimplemented
```

### DR-009 — Structural Experiments Have Three Separate Authorities

```yaml
decision_id: DR-009
date: 2026-07-18
title: Visualization, deterministic structure and professional interpretation cannot be collapsed
status: implemented
decision: Topic 01 freezes visual_only, deterministic_structure and reasoning_required as separate authorities. The sandbox may calculate edge/path integrity after one node is removed, but only the professional Reasoner may interpret what that means in life.
hard_boundaries:
  - one sandbox permits one single-node ablation only
  - prediction freezes before ablation
  - Baseline, Modified and Diff remain traceable
  - restore returns to the immutable source snapshot
  - save writes TopicExploration only and never mutates LifeCase
  - clients select the renderer through declared capabilities, not Topic ID-specific code
affected_documents:
  - product/V50_INTERACTIVE_MINGLI_THEATER_ARCHITECTURE_V1.md
  - product/V50_ABU_MINGLI_TOPIC_01_STRUCTURAL_ABLATION.md
implementation_status: machine validated; professional interpretation, TTS and Live are not claimed
```

### DR-010 — Selective Refoundation, Not Greenfield Rewrite

```yaml
decision_id: DR-010
date: 2026-07-18
title: Preserve cognitive and LifeCase authority while rebuilding experience boundaries
status: accepted
decision: V50 不从零重写，也不继续在现有万能文件中叠加体验。冻结 Chart Facts、LLM Cognitive Core、Reliability Gate 和 LifeCase；建立只读 MingliExperienceEnvelope 与统一 Experience Timeline，按纵向切片迁移后再隔离、归档和删除遗留实现。
hard_boundaries:
  - 不复制 V50 成长期独立 V60
  - 不长期双写
  - Experience 不读取完整 LifeCase Repository
  - Visualization / Theater / LifeScript 不拥有命理判断权
  - 旧报告和历史自然语言不自动升级为 Formal Insight
  - 专业盲测 Prompt、理论和模型版本不与体验重构同时修改
  - 未通过删除门禁不得物理删除代码、表、Prompt 或控制组证据
affected_documents:
  - V50_ARCHITECTURE_PURIFICATION_AND_EXPERIENCE_REFOUNDATION_V1.md
implementation_status: P0 authority registries, legacy formal-write blocker, runtime legacy usage trace, read-only MingliExperienceEnvelope API and independent 看见命局 Next shell are machine validated; old default entry remains active pending human experience acceptance
```

### DR-011 — Canvas Compiles Cognition; It Does Not Reason

```yaml
decision_id: DR-011
date: 2026-07-18
title: 操作命局 Temporal Sandbox is the second vertical experience slice
status: frozen
decision: Mingli Interactive Canvas 只消费 Chart、Temporal Snapshot 与 committed LifeCase，经唯一 Canvas Compiler 生成 MingliCanvasSpec 和 CanvasDiffSpec；它负责呈现正式认知与隔离实验状态，不拥有新的命理判断权。
why: 用户需要观察原局、大运和流年之间哪些结构新增、改变或影响主路径，同时必须防止前端自算、实验污染正式案例和视觉效果升级结论确定性。
hard_boundaries:
  - 每个对象必须标记 canonical / committed / derived / hypothetical / presentation 来源
  - 原局四柱 immutable；第一版只允许选择一个大运和一个流年
  - 结构变化使用 introduced / removed / activated / reinforced / weakened / blocked / reopened / unchanged 离散语义，不使用虚假连续强度分数
  - 前端不得自行判断合冲刑害、十神、路径或做功
  - 用户动作必须经过 Sandbox Mutation、重新编译与正式 Diff
  - Abu 只消费当前 CanvasContextPack，不把假设状态表达成命主事实
  - Sandbox 不写 ChartVersion、TemporalSnapshot 或 LifeCase，不自动 promotion
  - 第一版不夹带课堂编辑器、多人 Live、录制或视频导出
refines:
  - DR-007
  - DR-008
  - DR-009
affected_documents:
  - product/V50_MINGLI_INTERACTIVE_CANVAS_TEMPORAL_SANDBOX_V1.md
  - product/V50_INTERACTIVE_MINGLI_THEATER_ARCHITECTURE_V1.md
implementation_status: C0 CLOSED / PASS; C1 read-only six-pillar canvas is machine validated against six real formal LifeCases with desktop/mobile evidence; analyst/product review remains pending and C2 is not automatically authorized
closure_invariant: 一旦对象因角色披露策略被过滤，任何 fallback、补全、默认选择或上下文组装都不得使其重新进入 Spec、Diff 或 CanvasContextPack。
open_questions:
  - 复杂专业 Graph 是否在 C1 后证明需要 React Flow
  - 哪些时间关系可由确定性 Compiler 直接给出语义 Diff，哪些必须保留为 reasoning_required
```

### DR-012 — C1 Renders Formal LifeCase Without Becoming a Second Reasoner

```yaml
decision_id: DR-012
date: 2026-07-18
title: C1 Read-only Six-pillar Canvas enters the real LifeCase experience
status: product_rework_required
decision: 在现有 Experience Shell 中，以只读六柱 Viewer 展示原局、正式大运与正式流年；页面只消费角色过滤后的 MingliCanvasSpec、CanvasDiffSpec 与 CanvasContextPack，不补算关系、路径、变化或认识论状态。
observed_data:
  formal_life_cases_found: 16
  real_cases_rendered: 6
  cases_refused_without_formal_baseline: 10
  c0_c1_targeted_tests: 12_passed
  full_regression: 325_passed
hard_boundaries:
  - 前端不推导 relation、path、Diff 或 epistemic status
  - 被角色过滤的对象不进入响应、客户端状态、DOM 或调试输出
  - 原局四柱 immutable；大运与流年仅来自正式时序计算
  - C1 不调用 LLM，不执行 Sandbox mutation，不写 LifeCase 或其他正式状态
  - 没有唯一 typed graph evidence 的主路径明确不画，不解析自然语言补线
  - 当前正式数据没有 typed temporal path update 时，只显示时间柱 introduced 与主路径 contract-level unchanged
  - C1 通过不等于底层专业命理内容已经通过人工裁决
review_result:
  implementation: complete
  machine_gate: pass
  regression_gate: pass
  product_semantic_review: fail
  production_release: not_approved
  c2_entry: not_approved
resolution:
  - 保留当前 Renderer，重新定位为内部 Mingli Canvas Inspector
  - 用户侧进入 C1 Time Structure Lens 产品重设计
  - 先比较时间故事、路径聚焦、前后对照三套可点击原型
  - 不在当前 Inspector 上继续做单纯 CSS 美化
next_gate: three_prototype_product_and_visual_review
deployment_status: local_only
```

### DR-013 — Mingli Lab Is a Direct-manipulation Sandbox, Not a Second Reasoner

```yaml
decision_id: DR-013
date: 2026-07-18
title: C2A proves the Mingli Lab tool loop before full C2
status: machine_validated_product_review_pending
decision: 保留 C1 为内部 Inspector；用户产品方向进入 Mingli Lab 命局实验台。第一切片只做历法合法的时柱校勘、流年信号拨盘与做功路径比较，实验状态通过确定性引擎重建，不由前端或 LLM 补算命理语义。
authority:
  formal_chart: canonical facts
  life_case_path: committed reference
  variant_graph: candidate evidence
  user_path: user draft
hard_boundaries:
  - 正式盘与实验副本严格分离，Sandbox 不写 ChartVersion 或 LifeCase
  - 年月日锁定，只扫描与当前日干相容的十二个合法时柱
  - 原 LifeCase 路径只能作为比较基线，不自动转移到变体
  - Graph candidate 不自动 promotion，PathDraft 永远不成为系统结论
  - 流年拨盘没有 typed temporal path effect 时，只显示正式或假设时间信号
  - A/B 槽位只通过显式保存更新，未保存草稿不得覆盖比较基线
  - 路径评价使用保留段、缺失段与离散状态，不使用未校准百分比
  - C2A 不调用 LLM，不部署，不授权完整 C2
observed_data:
  real_anonymized_cases: 1
  legal_hour_variants: 12
  path_outcomes: 1_preserved_1_partial_10_broken
  targeted_tests: 16_passed
  full_regression: 329_passed
  desktop_mobile_browser_validation: passed
implementation_status: C2A prototype COMPLETE / machine PASS
next_gate: analyst_product_review_of_hour_calibration_tool_loop
deployment_status: local_only
```

### DR-014 — One Mingli Semantic World, Three Render Profiles

```yaml
decision_id: DR-014
date: 2026-07-18
title: Mingli Scene Runtime unifies 理, 象 and 时 without creating another Reasoner
status: machine_validated_product_review_pending
decision: C1R composes one already filtered semantic world into Lab, Xiangfa and Theater profiles. The same semantic_ref, selected object, active path, PathDraft and time signal survive profile changes; visual metaphors and scene cues remain disclosed projections of that state.
hard_boundaries:
  - C0 Canvas Compiler remains the sole semantic authority
  - Scene Composer may arrange, focus, bind metaphors and order cues, but may not infer relations or paths
  - the same semantic_ref identifies the same object in all render profiles
  - role-filtered objects cannot reappear in state, DOM, fallback content or debug output
  - Xiangfa bindings carry their own source, author and disclosure level and never become formal facts
  - Theater stops at the first missing segment and may not animate across an unproven bridge
  - PathDraft remains user_draft and never writes LifeCase
  - hypothetical time signals cannot fabricate formal temporal path effects
  - C1R does not authorize production integration, full C2, classroom authoring, Live or export
observed_data:
  real_anonymized_cases: 1
  render_profiles: 3
  partial_path_cues: 4
  targeted_tests: 24_passed
  full_regression: 337_passed
  desktop_mobile_browser_validation: passed
implementation_status: C1R prototype COMPLETE / machine PASS
next_gate: analyst and product review of shared-scene comprehension and authority clarity
deployment_status: local_only
```

### DR-015 — Six Pillars Are the Graph and the Only Primary Operation Surface

```yaml
decision_id: DR-015
date: 2026-07-18
title: C2A-R replaces the console-shaped C2A surface with Mingli OneCanvas
status: machine_validated_product_review_pending
decision: C2A 的确定性功能证据继续保留，但其多面板产品形态判定失败。C2A-R 将年、月、日、时、大运、流年六个固定 semantic slot 与十二个唯一干支节点定义为唯一 Graph；改柱、选时间、系统路径、PathDraft、播放与 A/B 比较均直接发生在同一节点空间。
authority:
  legal_calendar_candidates: existing_birth_calendar_engine
  chart_relations_and_graph: existing_deterministic_graph_pipeline
  luck_recalculation: existing_personal_timing_material
  formal_path: committed_life_case
  experiment_path: graph_candidate
  user_path: path_draft
  renderer: no_semantic_authority
hard_boundaries:
  - 正式盘柱值 immutable；实验盘只选择预编译的历法合法候选
  - 前端不得计算历法、十神、关系、Graph、路径或大运
  - 六柱十二节点只存在一份；不得复制到 Path Studio 或比较页面
  - 约束镜片和解释按需出现，不建立永久 Inspector、候选行或流年拨盘
  - 日柱变化必须携带合法联动时柱；大运必须明确返回已重算有变化或无变化
  - 系统路径、Graph candidate 与 PathDraft 使用不同认识论状态且不得 promotion
  - A/B 只在同一空间残影或擦除，不复制两张命盘
  - 不使用未校准能量百分比
  - 无 LLM、无 TTS、无正式状态写入、无生产部署
observed_data:
  anonymized_real_cases: 1
  legal_candidates: 12_hour_5_day_5_month_5_year
  primary_nodes_per_variant: 12
  prototype_tests: 8_passed
  focused_canvas_regression: 32_passed
  full_regression: 345_passed
  desktop_mobile_browser_validation: passed
implementation_status: C2A-R prototype COMPLETE / machine PASS
next_gate: analyst_product_review_of_continuous_A_to_I_task
full_c2_status: blocked
deployment_status: local_only
```

### DR-016 — Li, Xiang and Time Are Three States of OneCanvas

```yaml
decision_id: DR-016
date: 2026-07-18
title: One Mingli world is edited in Li, seen through Xiang and played through Time
status: machine_validated_product_review_pending
decision: C1R 作为 Shared Semantic Projection Proof 技术 Spike 结项，其独立三页面产品形态不继续扩展。理是 OneCanvas 语义骨架，象是同一节点与路径的连续视觉映射，时是同一场景上的确定性 Cue 播放；三者不得复制节点、路径或页面。
hard_boundaries:
  - 六柱十二节点是唯一主要对象，理象转换不改变 semantic_ref
  - 象法映射携带来源与披露说明，不产生新命理事实
  - 演时只引用现有节点与关系，遇缺失关系立即停止
  - 暂停、改柱、重编译、继续均保持实验、选择、PathDraft 与时间位置
  - 系统路径与用户 PathDraft 同图但认识论状态不同
  - 不增加第二 Graph、第二页面、Path Studio、永久 Inspector 或流年拨盘
  - 无 LLM、无 TTS、无正式状态写入、无生产部署
observed_data:
  anonymized_real_cases: 1
  primary_canvas_count: 1
  primary_nodes: 12
  focused_canvas_regression: 40_passed
  full_regression: 353_passed
  desktop_mobile_browser_validation: passed
implementation_status: OneCanvas three-state prototype COMPLETE / machine PASS
next_gate: analyst_product_review_of_single_continuous_task
full_c2_status: blocked
deployment_status: local_only
```

### DR-017 — Key Product Components Advance Through Reviewed Refinement Slices

```yaml
decision_id: DR-017
date: 2026-07-18
title: DeepBazi key components are discussed, contracted and refined one slice at a time
status: process_frozen_onecanvas_r1_machine_pass
decision: 所有关键产品部件先讨论真实任务与认知权威，再形成 Markdown 合同；实现只覆盖已授权的单一纵向切片。机器通过、产品通过与生产授权保持为三个独立门禁。OneCanvas 方向通过，下一阶段进入精修而非推翻，但 R1 至 R6 不得同时开工。
governing_docs:
  - docs/product/KEY_COMPONENT_REFINEMENT_PROTOCOL_V1.md
  - docs/product/V50_ONECANVAS_REFINEMENT_SPEC_V1.md
onecanvas_refinement_order:
  - R1_authority_and_constrained_selection
  - R2_guided_path_construction
  - R3_root_reveal_local_structure
  - R4_temporal_activation_and_path_flow
  - R5_discrete_path_assessment
  - R6_visual_and_multi_terminal_refinement
hard_boundaries:
  - 理、象、时仍是同一 OneCanvas 的语义、表现与播放状态，不恢复为三个页面
  - 大运只由确定性引擎推导，用户只能切换观察，不能手工编辑
  - 前端不得计算合法干支、大运、通根、透干、关系、路径或时间引动
  - 路径评估使用可追溯的离散状态，不使用未校准能量百分比
  - 每一精修切片开始前必须冻结用户任务、权威、缺失数据行为和产品 Gate
  - 本次只冻结协议与规格，不修改 UI、Runtime、Reasoner、LifeCase 或命理算法
next_gate: analyst_and_first_time_user_product_review_of_onecanvas_R1
full_c2_status: blocked
deployment_status: no_change
```

### DR-018 — OneCanvas R1 Begins with Calendar Authority and Component Discipline

```yaml
decision_id: DR-018
date: 2026-07-18
title: OneCanvas R1 implements authority and constrained selection only
status: implemented_machine_pass_product_pending
decision: R1 仅实现正式盘保护、历法合法实验候选、完整联动预览、大运派生重算三态和公历年份流年观察。组件化从 R1 开始，但只作为稳定语义对象、交互职责和视觉图层的实现纪律，不另起框架迁移或设计系统项目。
governing_docs:
  - docs/product/V50_ONECANVAS_R1_IMPLEMENTATION_DESIGN.md
  - docs/product/V50_ONECANVAS_VISUAL_COMPONENT_CONTRACT_V1.md
authority:
  formal_chart: immutable_chart_version
  experiment: sandbox_variant_only
  candidate_source: precompiled_calendar_constraint_solver
  luck_sequence: deterministic_derived_result
  observed_annual: gregorian_year_with_derived_ganzhi
hard_boundaries:
  - R1 只支持 calendar_valid，不支持 structural_free
  - UI 提交 PillarEditIntent，不能孤立替换一个干支字符
  - 完整四柱、联动差异和重算状态必须在确认前预览
  - 多候选不得静默提交
  - 大运不可编辑；改变、无变化、无法计算必须明确区分
  - 组件只消费 ViewModel 并发出 UI Intent，不直接修改 Spec
  - 不迁移 React，不重写 Experience Shell，不提前开发 R2-R6
next_gate: R1_analyst_and_human_product_review
verification:
  focused_tests: 50_passed
  full_regression: 363_passed
  desktop_and_mobile_browser_review: pass
  browser_console_errors_or_warnings: 0
implementation_status: R1 COMPLETE / machine PASS / product PENDING
full_c2_status: blocked
production_deployment: blocked
```

### DR-019 — Pillar Selection Is Closed and Path Completion Is Explicit

```yaml
decision_id: DR-019
date: 2026-07-18
title: OneCanvas pillar editing uses closed legal choices and existing path drafts have explicit completion
status: implemented_machine_pass_product_review_pending
decision: 四柱实验候选不再通过自由文本查找，而由 Calendar Constraint Solver 返回的完整候选下拉选择；现有单条 PathDraft 支持连续点选，并可通过重复点击终点、完成按钮、Enter 或 Escape 明确结束。
hard_boundaries:
  - 下拉变化只预览，完整候选仍需显式确认
  - 浏览器不能拼装或推断合法命盘
  - 画线优化不增加关系推理、路径推荐或专业评估
  - PathDraft 仍只写本地 Sandbox，不写 LifeCase
  - 本决定不授权完整 R2 或生产部署
affected_documents:
  - docs/product/V50_ONECANVAS_SELECTION_AND_PATH_FINISHING_PATCH_V1.md
implementation_status: local implementation complete; 364-test regression and desktop/mobile browser tasks PASS
next_gate: analyst_and_first_time_user_product_review
```

### DR-020 — Year and Day Are the Only Independent Natal Choice Axes

```yaml
decision_id: DR-020
date: 2026-07-18
title: OneCanvas uses the 60 Jiazi cycle with explicit pillar dependencies
status: superseded
superseded_by: DR-021
supersedes:
  - DR-018 nearby-date candidate model
  - DR-019 five-option candidate presentation
decision: OneCanvas 不再把年月日时做成四个附近日期编辑轴。年柱与日柱各自从完整六十甲子中选择；月柱由年干按五虎遁联动，时柱由日干按五鼠遁联动；流年独立观察；大运在命局结构完成后由系统派生且不可手选。
governing_document: docs/archive/product/V50_ONECANVAS_PILLAR_DEPENDENCY_MODEL_V1.md
authority:
  year: independent_60_jiazi_choice
  month: linked_from_year_stem
  day: independent_60_jiazi_choice
  hour: linked_from_day_stem
  annual: independent_calendar_observation
  luck: final_deterministic_derivation
hard_boundaries:
  - 结构实验不伪装成真实公历生日反查
  - 月柱和时柱没有独立编辑入口
  - 前端不得实现六十甲子、五虎遁、五鼠遁或大运算法
  - 下拉选择只预览，确认后才更新本地 Sandbox
  - 正式 ChartVersion 与 LifeCase 不写入
  - 本决定不授权多轴浏览器拼装、完整 R2 或生产部署
implementation_status: 120_candidates_compiled / 54_focused_tests_passed / 367_full_tests_passed / desktop_mobile_browser_passed
next_gate: analyst_and_first_time_user_product_review
```

> **Superseded by DR-021.** DR-020 incorrectly made month and hour
> non-editable linked results instead of dependent selections with 12 legal
> candidates.

### DR-021 — OneCanvas Uses Cascading Pillar Selection and Split DaYun Authority

```yaml
decision_id: DR-021
status: accepted_for_implementation_review
date: 2026-07-19
scope: OneCanvas pillar selection and DaYun derivation
decision:
  year: independent_60_jiazi
  month: dependent_12_candidates_from_year
  day: independent_60_jiazi
  hour: dependent_12_candidates_from_day
  annual: independent_observation
  dayun: derived_last_never_editable
  dayun_sequence: derivable_from_year_month_gender
  dayun_exact_timing: requires_verified_real_datetime
supersedes: DR-020
governing_document: docs/product/V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md
production_deployment: false
```

### DR-022 — Architecture Consolidation Precedes Relation Atlas Implementation

```yaml
decision_id: DR-022
date: 2026-07-19
title: V50 uses selective consolidation rather than a rewrite or continued prototype accumulation
status: accepted_read_only_audit_complete
decision: V50 保留已验证的事实引擎、LLM 认知主链、LifeCase、Canvas 合同和 OneCanvas R1；不从零重写，也不继续让原型平行生长。R1 真人产品审阅继续进行，但 RA1 之前必须通过 Architecture Consolidation Gate。
governing_documents:
  - docs/CURRENT_ARCHITECTURE.md
  - docs/CURRENT_PRODUCT_BASELINE.md
  - docs/CURRENT_IMPLEMENTATION_ROADMAP.md
  - docs/V50_ARCHITECTURE_CONSOLIDATION_AUDIT_V1.md
audit_findings:
  - Graph v1 relation 以 neutral_relation 进入 World，并被默认映射为 production，存在绕过独立第一眼隔离的权威缺陷
  - production OneCanvas adapter 依赖 scripts 下的 fixture builder 内部函数
  - C0/C1 MingliCanvasSpec 与 R1 OneCanvas fixture 是两套并行场景合同
  - 时运与大运推导存在多个实现位置
  - LifeCase 正式路径依赖重建 Graph v1 后的间接匹配，缺少稳定版本化 provenance
  - legacy L5 shell 仍服务公开根路由
preserved_assets:
  - deterministic_chart_and_calendar_facts
  - llm_mingli_reasoner
  - reliability_and_epistemic_review_boundaries
  - life_case_and_revision_ledger
  - c0_canvas_contract_and_disclosure_fixtures
  - onecanvas_r1_as_only_user_product_candidate
frozen_prototype_identities:
  C0: contract_fixture
  C1: internal_inspector
  C1R: shared_semantic_projection_proof
  old_C2A: functional_fixture
  C2AR_R1: only_user_product_candidate
hard_boundaries:
  - 不进行全系统重写或 React 迁移
  - 不因审计直接删除旧模块或历史数据
  - 不在 Renderer 内补命理语义
  - 不让 production 继续长期依赖 scripts
  - 不静默重写历史 LifeCase
  - 不在 Consolidation Gate 前启动 RA1
  - 不将机器回归通过解释为产品、专业或生产通过
next_authorized_work:
  - complete_R1_unguided_human_product_review
  - prove_and_close_experimental_graph_authority_leak
  - extract_canonical_chart_calendar_and_dayun_temporal_services
  - freeze_scene_compiler_adapter_and_typed_relation_path_provenance
verification:
  experience_typescript_typecheck: pass
  focused_architecture_canvas_onecanvas_tests: 40_passed
  full_regression: 376_passed
  architecture_purification_audit: pass
  markdown_link_check: pass
runtime_code_modified: false
architecture_consolidation_gate: NOT_PASSED
RA1_status: BLOCKED
production_deployment: BLOCKED
```

### DR-023 — Deep Cleanup Uses Retention Classes and Responsibility-led Splits

```yaml
decision_id: DR-023
date: 2026-07-19
title: V50 cleans duplicate authority now and splits active large files only at stable gates
status: first_consolidation_slice_implemented_machine_pass
decision: 深度清理不以删除数量或文件行数为目标。重复命理权威、反向依赖、缓存和无引用样本立即清理；旧产品运行面按使用证据退休；技术证明和历史文档归档；专业报告与素材母版保留；活跃大文件沿职责与权威边界分阶段切割。
governing_documents:
  - docs/V50_DEEP_CLEANUP_AND_LARGE_FILE_GOVERNANCE_V1.md
  - config/artifact_retention_v1.json
implemented:
  - Graph v1 关系改为 experimental_tool_observation，未知 authority 不再默认 production
  - fixture builder 从 scripts 移入 product application，保留薄 CLI 兼容入口
  - 新建 canonical pillar_cycle 与 dayun deterministic services
  - production -> scripts import 加入永久架构门禁
  - 旧执行、架构、产品建议与完成技术证明移入 docs/archive
  - 删除缓存、编译残留和四张无引用 Abu sample frames
  - OneCanvas 生成 fixture 由约 4.90 MB 压缩为约 2.94 MB
large_file_policy:
  review_threshold_lines: 800
  mandatory_plan_threshold_lines: 1500
  legacy_l5: retire_not_split
  onecanvas_controller: split_after_R1_human_behavior_freeze
  canvas_compiler: split_before_scene_contract_convergence
  reasoner: split_after_professional_baseline_lock
  agent_api: split_in_next_application_consolidation_slice
  life_case_service: split_after_typed_provenance_contract
hard_boundaries:
  - 不删除盲测、专业裁决、验收或声线证据
  - 不删除仍被引用的 Abu 动画、母版和过渡锚点
  - 不借清理启动 Relation Core V2 或 Path Core V2
  - 不借大文件拆分改变 Reasoner、LifeCase 或 OneCanvas 产品行为
  - 不进行 React 或全站重写
verification:
  focused_regression: 103_passed
  full_regression: 376_passed
  experience_typescript_typecheck: pass
  architecture_purification_audit: pass
  runtime_authority_audit: pass
production_deployment: false
```

### DR-024 — Architecture Audit v2 Adds Global Chart Constraints and Versioned Core Migration

```yaml
decision_id: DR-024
date: 2026-07-19
title: V50 retains selective consolidation and adds target-chart, provenance, and dual-run prerequisites
status: accepted_read_only_audit_complete
decision: V50 继续采用选择性、版本化、可回退的架构收敛，不从零重写。旧审计中的 Graph 第一眼权威泄漏已关闭；新审计确认 R1 的局部级联编辑不能保证到达目标四柱，正式入口的 supplied pillar 校验过弱，Scene、正式路径 provenance 与前后端合同仍需收敛。RA1 前必须先完成 Chart Constraint Solver、权威校验、Temporal 去重、Scene 适配和 Legacy/V2 双跑设计。
governing_document: docs/V50_ARCHITECTURE_CONSOLIDATION_AUDIT_V2.md
supersedes_current_audit_reference: docs/V50_ARCHITECTURE_CONSOLIDATION_AUDIT_V1.md
does_not_rewrite_history: true
closed_since_v1:
  - Graph/Path/Role 进入 World 时已明确为 experimental_tool_observation
  - independent first look 已排除实验观察
  - unknown WorldFact authority 已改为直接失败
new_blocking_findings:
  - 本地 year->month、day->hour 破坏性级联具有操作顺序依赖，不能保证目标四柱可达
  - Birth Calendar 对 supplied pillars 仅检查两个字符，缺少 Jiazi、依赖和历法一致性校验
  - production structural service 仍依赖 fixture builder 私有 projection 函数
  - OneCanvas 重复 DaYun direction 逻辑
  - LifeCase 正式路径仍可能因未来 Graph 重建和匹配变化而消失
required_rebuilds:
  - global_chart_constraint_solver
  - relation_core_v2
  - path_core_v2
required_convergence:
  - chart_calendar_and_dayun_temporal_authority
  - canonical_scene_compiler_and_adapters
  - typed_formal_path_provenance
  - pydantic_json_schema_to_generated_typescript
hard_boundaries:
  - 不修改本轮运行代码或产品行为
  - 不借审计启动 RA1、完整 C2 或生产部署
  - 不进行全系统重写、React 迁移或无门禁大文件切割
  - 不静默改写历史 LifeCase
  - 不让前端承担历法、关系、路径或大运判断
architecture_consolidation_gate: NOT_PASSED
R1_human_product_gate: PENDING
RA1_status: BLOCKED
production_deployment: BLOCKED
```

### DR-025 — R1 Uses Locked Pillar Composition and a Simple Gregorian Annual Selector

```yaml
decision_id: DR-025
date: 2026-07-19
title: OneCanvas edits target intent without destructive local cascades
status: design_frozen_implementation_pending
decision:
  year_pillar: first chosen stem or branch is temporarily locked; choose the legal counterpart; then unlock
  month_pillar: choose one complete pillar from 12 candidates derived from the resolved year stem
  day_pillar: first chosen stem or branch is temporarily locked; choose the legal counterpart; then unlock
  hour_pillar: choose one complete pillar from 12 candidates derived from the resolved day stem
  annual_observation: one Gregorian-year dropdown; select once; close immediately; derive annual Jiazi
  target_state: PillarTargetDraft separate from the last compiled Sandbox snapshot
  compile: server-owned global Chart Constraint Solver returns zero, one, or many complete variants
  dayun: derived only; structural sequence and exact active period remain distinct
  year_semantics: sexagenary cycle anchor and actual Gregorian birth-year candidate remain distinct
governing_document: docs/product/V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md
supersedes_behavior:
  - destructive_local_year_to_month_cascade
  - destructive_local_day_to_hour_cascade
  - structural_annual_jiazi_selector_in_R1
interaction_boundaries:
  - 年柱与日柱的锁只存在于一次未完成的组柱手势
  - 月柱与时柱不拆开编辑天干地支
  - 流年没有锁、确认、弹窗、提示或独立干支输入
  - 唯一合法求解结果所见即所得，多候选才要求显式选择
  - 任何草稿或实验均不写入 ChartVersion 或 LifeCase
R1_v1_human_protocol: PAUSED
R1_v5_implementation: COMPLETE_MACHINE_PASS
production_deployment: BLOCKED
```

### DR-027 — OneCanvas Uses an Automatic First-operation Anchor Session

```yaml
decision_id: DR-027
date: 2026-07-19
title: 年柱与日柱以首个实际操作自动建立锚点，不再要求用户管理编辑状态
status: implemented_machine_verified_human_gate_pending
decision:
  reveal: hover_or_focus_only
  session_start: first_previous_or_next_operation
  anchor: first_operated_component
  counterpart: constrained_by_server_owned_legal_catalog
  visible_state: always_complete_legal_jiazi
  compile: every_step_submits_a_complete_target_to_server_solver
  session_end:
    - pointer_leaves_pillar
    - focus_leaves_pillar
    - touch_selects_another_pillar_or_outside
    - escape
  retained_result: latest_successfully_compiled_sandbox_snapshot
removed_controls:
  - explicit_edit_button
  - explicit_finish_button
  - manual_lock_switch
  - partial_invalid_chart
authority:
  frontend_may: consume_catalog_and_prepare_complete_target
  frontend_may_not: invent_jiazi_validate_calendar_or_commit_formal_state
  server: final_target_compile_authority
supersedes_interaction_portion_of: DR-025
governing_document: docs/product/V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md
verification:
  focused_tests: 44_passed
  full_regression: 381_passed
  desktop_visual_check_1440x1000: PASS
  mobile_visual_check_390x844: PASS
  horizontal_overflow: false
production_deployment: BLOCKED_PENDING_HUMAN_PRODUCT_GATE
```

### DR-026 — Abu Says Mingli S0 Is a Brand Production Prototype, Not a Second Cognitive System

```yaml
decision_id: DR-026
date: 2026-07-19
title: 阿布说命 S0 以同一场景连接品牌、OneCanvas、Xiangfa 与 Theater
status: analyst_g1_pass_with_conditions_s0_g2_internal_authorized
decision: >-
  下一项 Theater 相关提案不是完整剧场系统，而是 45–48 秒品牌级开场小剧场
  S0。S0 只消费匿名批准的命理场景，以 OneCanvas 表达理、Xiangfa 表达同一
  结构的象、Editorial Timeline 表达时间；三者不各自理解命局。S0 不新增命理
  判断，不修改正式状态，不代表 OneCanvas、Xiangfa、Abu 声线或 Theater 已
  通过产品和生产门禁。
governing_document: docs/product/V50_ABU_SAYS_MINGLI_S0_OPENING_THEATER_AND_XIANGFA_SYNC_V1.md
brand_thesis:
  main_slogan: 看见命局，也看见自己。
  supporting_line: 读懂人生剧本，做出更清醒的选择。
  life_script: 命局是人生剧本的底稿，不是写死的结局
  abu_role: 与用户站在同一侧的命理向导和人生剧本阅读伙伴
single_source:
  - approved_anonymous_teaching_fixture
  - canonical_scene_state
  - versioned_semantic_path_and_temporal_refs
authorized_now:
  - s0_g1_anonymous_fixture_candidates
  - s0_g1_source_manifest_draft
  - frozen_narration_subtitles_and_forbidden_claims
authorized_only_after_g1_lock:
  - static_storyboard
  - internal_non_production_animatic
blocked_now:
  - silent_system_fixture_selection
  - storyboard_before_fixture_lock
  - animatic_before_fixture_lock
  - final_film_production
  - public_release
  - production_route_integration
  - new_mingli_reasoning
  - xiangfa_writeback
  - use_of_private_user_case_data
next_gate:
  owner: product_brand_and_professional_review
  requires:
    - static_storyboard_bound_to_final_manifest
    - internal_low_fidelity_animatic
    - eric_internal_audition_only
    - 16_9_and_9_16_composition_proof
    - s0_g2_human_review_before_xiangfa
analyst_g1_decision:
  decision: SELECT
  selected_fixture_id: s0-fixture-candidate-a
  professional_content_approved: true
  confidence: medium
  source_mode: approved_anonymous_teaching_fixture
  s0_g2_authorized: true
  s0_g3_authorized: false
g1_decision_history_lock: reports/abu-says-mingli-s0/g1/S0_G1_ANALYST_DECISION_LOCK_V2.json
g1_decision_lock: reports/abu-says-mingli-s0/g1/S0_G1_CANDIDATE_A_PROFESSIONAL_DECISION_LOCK_V1.json
g1_review_packet: reports/abu-says-mingli-s0/g1/S0_G1_CANDIDATE_A_PROFESSIONAL_REVIEW_PACK.md
g1_final_manifest: reports/abu-says-mingli-s0/g1/s0_source_manifest_final_v1.json
g1_final_hash_lock: reports/abu-says-mingli-s0/g1/S0_G1_FINAL_MANIFEST_LOCK.sha256
does_not_change_current_roadmap: true
production_deployment: false
```

### DR-028 — Abu Actor Pass V1 Closed; Xiangfa Generation V1 Becomes the Next Visual Mainline

```yaml
decision_id: DR-028
date: 2026-07-20
title: 锁定 S0 V1.2，停止重做第一条片子，转入真实 Scene State 驱动的象法生成
status: accepted
decision:
  Abu_Actor_Pass_V1: CLOSED_PASS
  S0_V1_2: ACCEPTED_STAGE_MILESTONE
  S0_V1_3: NOT_AUTHORIZED
  public_release: SEPARATE_GATE
execution_status_superseded_by: DR-031
verified_media_fixes:
  - full_body_safe_crop_on_desktop_mobile_and_portrait
  - real_run_enter_slow_and_stop_sequence
  - native_full_body_turn_raise_paw_and_point_action
  - complete_point_and_face_change_playback_windows
non_blocking_public_backlog:
  - reduce_or_reanchor_Abu_when_mobile_guidance_occludes_lower_pillars
  - decide_whether_full_face_change_is_brand_mainline_or_social_IP_easter_egg
next_mainline:
  name: Xiangfa Generation V1
  flow:
    - approved_real_mingli_scene_state
    - XiangfaSceneSpec
    - bounded_visual_candidates
    - semantic_binding
    - synchronized_OneCanvas_Xiangfa_Theater_projection
  must_not:
    - reopen_S0
    - create_new_mingli_facts
    - promote_image_model_to_reasoning_authority
    - write_formal_case_state
production_deployment: BLOCKED
```

### DR-029 — V50 Lean & Consolidation Becomes the Main Engineering Line

```yaml
decision_id: DR-029
date: 2026-07-20
status: accepted
mainline: V50_Lean_and_Consolidation
scope_now: L0_and_L1_only
product_freeze: true
active_canvas_candidate: apps/product/static/experience/active/onecanvas-r1
isolated_validation: apps/product/static/experience/active/xiangfa-generation-v1
internal_stage_milestone: apps/product/static/experience/internal-tools/abu-says-mingli-s0-v12
archived_proofs: archive/proofs/prototypes
next_slice: L2_Authority_Consolidation_after_L0_L1_closeout
closeout:
  status: COMPLETE_MACHINE_PASS
  repository_bytes: 1558363161_to_445823001
  artifact_bytes: 1310326438_to_197037198
  runtime_prototypes: 11_to_5
  archived_prototypes: 0_to_6
  duplicate_runtime_media_bytes: 309700981_to_0
  full_regression: 413_passed_0_failed
  evidence: reports/v50-lean-consolidation/l0-l1/before_after.json
must_not:
  - change_mingli_behavior
  - change_Runtime_Reasoner_or_LifeCase
  - start_full_C2_or_RA1
  - deploy_production
  - add_parallel_prototypes
```

### DR-030 — L2 Uses One Owner per Chart and Temporal Fact

```yaml
decision_id: DR-030
date: 2026-07-20
status: implemented_machine_verified
title: Global chart constraints and temporal facts have one application owner
owners:
  pillar_facts: birth_calendar + chart_constraints
  chart_target_resolution: solve_chart_constraints
  temporal_and_dayun: CanonicalTemporalService
  onecanvas_projection: presentation_only_adapter
boundaries:
  browser: TargetDraft and display state only
  fixture_builder: consumes public compiler and adapter
  legacy_invalid_research_chart: readable_but_temporal_derivation_rejected
  sandbox_formal_writes: forbidden
verification:
  focused: 67_passed
  full: 434_passed
  authority_audit: PASS
R1_v5_machine_gate: PASS
R1_human_product_gate: READY_PENDING_EXECUTION
R1_human_product_gate_superseded_by: DR-031
RA1: BLOCKED_PENDING_R1_HUMAN_GATE
production_deployment: BLOCKED
```

### DR-031 — R1 v5 Product Dry Run Supersedes the Ready-to-Execute Assumption

```yaml
decision_id: DR-031
date: 2026-07-20
status: accepted
superseded_by: DR-032
supersedes:
  - DR-030.R1_human_product_gate
does_not_reopen:
  - L2_Authority_Consolidation
  - Chart_Constraint_Solver
  - CanonicalTemporalService
finding:
  core_solver_outcomes:
    - no_solution
    - single_solution
    - multiple_solutions
  active_r1_surface:
    request_shape: complete_four_pillar_target
    exposed_outcome: selected_single_variant_only
    missing_product_states:
      - multiple_solution_candidates
      - no_solution_conflicts
      - releasable_constraints
gate_update:
  R1_v5_machine_gate: PASS
  R1_human_product_gate: PREPARATION_BLOCKED
  review_build_frozen: false
  participant_recruitment_authorized: false
verification:
  focused_authority_regression: 36_passed
  full_regression: 435_passed
next_only:
  - expose_existing_solver_zero_many_outcomes_in_R1_application_and_presentation
  - add_no_new_mingli_logic
  - freeze_hash_locked_review_build
  - execute_R1_v5_unguided_human_review
blocked:
  - Relation_Atlas
  - assisted_path
  - Theater
  - Xiangfa_feature_expansion
  - production_deployment
evidence:
  - reports/mingli-onecanvas-r1/review-v5-preparation/R1_V5_PREPARATION_DRY_RUN.md
  - reports/mingli-onecanvas-r1/review-v5-preparation/r1_v5_preparation_dry_run.json
```

### DR-032 — R1 Zero/One/Many Projection Closes the Preparation Blocker

```yaml
decision_id: DR-032
date: 2026-07-20
status: implemented_machine_and_browser_verified
supersedes:
  - DR-031.gate_update.R1_human_product_gate
does_not_reopen:
  - L2_Authority_Consolidation
  - Chart_Constraint_Solver
  - CanonicalTemporalService
scope:
  server_projection:
    - preserve_no_solution
    - preserve_single_solution
    - preserve_multiple_solutions
  product_behavior:
    - explicit_complete_variant_selection
    - server_owned_conflict_release
    - cancellation_preserves_current_chart
  browser_mingli_logic_added: false
verification:
  focused_projection_and_authority: 30_passed
  full_regression: 438_passed
  experience_typecheck: PASS
  desktop_browser: PASS
  mobile_390px_browser: PASS
  horizontal_overflow: NONE
  browser_console_errors: NONE
gate_update:
  R1_v5_machine_gate: PASS
  R1_review_build: V6_HASH_LOCKED
  R1_human_product_gate: READY_PENDING_EXECUTION
  participant_recruitment_authorized: true
  RA1: BLOCKED
  production_deployment: BLOCKED
evidence:
  - reports/mingli-onecanvas-r1/review-v6-ready/R1_V6_HUMAN_REVIEW_READY.md
  - reports/mingli-onecanvas-r1/review-v6-ready/r1_v6_review_build.sha256
```

### DR-033 — V50 Consolidation & Slimming Owns the Current Stage

```yaml
decision_id: DR-033
date: 2026-07-20
status: active
stage: V50_Consolidation_and_Slimming
execution_order:
  - V50_Git_Source_Baseline
  - CAG_03_Canonical_Scene
  - CAG_04_Relation_Path_Provenance
  - CAG_05_Schema_Module_Ownership
  - Architecture_Gate
current_task_boundary: Source_Baseline_and_CAG_03_only
validation_principles:
  - self_healing
  - high_velocity_iteration
  - synthetic_validation
validation_principles_create_new_subsystem: false
required_convergence:
  - LifeCase_is_formal_case_authority
  - CanonicalSceneOwner_is_single_scene_owner
  - projections_do_not_own_facts
  - client_cannot_override_formal_chart_facts
  - every_new_module_must_replace_or_remove_existing_complexity
blocked:
  - CAG_04_in_current_task
  - RA1_to_RA3
  - Workspace_production_adoption
  - new_product_UI_animation_or_interaction
  - new_Mingli_algorithm
  - Theater_or_Xiangfa_expansion
  - Self_Healing_platform
R1_V6: immutable_20_file_regression_reference
V40_changes: forbidden
```

### DR-034 — CAG-04 Establishes Stable Relation and Path Assertions

```yaml
decision_id: DR-034
date: 2026-07-21
status: closed_pass
lineage_status: provenance_reconciled_machine_pass
implementation_commits:
  - 1190a873
  - 0225aa1a
source_commits:
  - 42072034
  - c0502ed9
replayed_closeout_commit: efbe9115
authority:
  candidate_observation: Graph_and_Path_v1
  formal_assertion_owner: LifeCase
  projection_owner: CanonicalSceneOwner
contracts:
  - NodeRef
  - RelationKey
  - RelationAssertion
  - PathKey
  - PathAssertion
  - ProvenanceRecord
historical_policy:
  exact_structured_import_only: true
  fuzzy_reconnection: forbidden
  unmatched_history: legacy_unresolved
  committed_history_append_only: true
  graph_candidate_cannot_masquerade_as_formal: true
  dangling_or_non_prior_supersession_rejected: true
removed:
  - Canvas_anonymous_committed_path_id
  - Canvas_relation_text_matching
  - Theater_legacy_path_signature_matching
  - Theater_path_score_tolerance_matching
unchanged:
  - Mingli_relation_semantics
  - Mingli_path_scoring
  - R1_locked_20_files
  - V40
verification:
  focused_relation_path_provenance: 11_passed
  full_regression: 479_passed
  r1_manifest: 20_of_20_ok
next_gate: CAG_05_schema_module_ownership
blocked:
  - RA1_to_RA3
  - production_deployment
```

### DR-035 — RA0 Reclassifies 518K and Opens CAL-01

```yaml
decision_id: DR-035
date: 2026-07-21
status: accepted_pass_with_boundary_finding
source:
  branch: codex/ra0-518k-audit-v1
  commit: 2ac55900fb5885649ba7fca7935e57005070406b
  merge_base: 34cc5b17a86683ed4575d93e15134f0f26bc6687
  previous_controlled_integration_commit: f4c5527c
  controlled_integration_commit: e6cfc76e
  boundary_commit: da0aff4c
legacy_finding:
  v30_518k_identity: Legacy_Validation_Target_Contract
  entity_four_pillar_corpus_found: false
  validation_run_count: 608
  historical_artifacts_retained_as_evidence: true
formal_identity:
  name: Deterministic_Structural_Chart_Universe_Generator
  formula: 60_year_x_12_legal_month_x_60_day_x_12_legal_hour
  record_count: 518400
  unique_chart_keys: 518400
  structurally_valid: 518400
  structurally_invalid: 0
  four_jiazi_realizable: 518400
  universe_sha256: 05c97a1518ff840ef3d4955f92dd0a22de9c4729ef7ff2ec8601efbcb14a454c
retention:
  expanded_universe_in_git: forbidden
  reproducible_gzip_artifact: manifest_and_hash_only
  unseen_in_range_is_structurally_invalid: false
boundary_finding:
  issue: CAL-01_Late-Zi_Five-Rats_Consistency
  formal_policy: lunar_python.sect2.v1
  formal_day_rollover: midnight
  retained_rejected_timestamps: 4019
  formal_algorithm_modified: false
  audit_normalization_may_become_formal: false
  blocks_architecture_gate: true
scope:
  CAG_04_semantics_modified: false
  R1_locked_files_modified: false
  V40_modified: false
  RA1_authorized: false
verification:
  ra0_focused: 10_passed
  v50_full_regression: 477_passed
  r1_manifest: 20_of_20_ok
  v40_commit_diff: zero
evidence:
  - reports/v50-lean-consolidation/ra0-518k-realizability-v1/RA0_518K_CHART_REALIZABILITY_AUDIT_V1.md
  - reports/v50-lean-consolidation/ra0-518k-realizability-v1/ra0_518k_run_manifest_v1.json
  - reports/v50-lean-consolidation/ra0-518k-realizability-v1/ra0_518k_semantic_summary_v1.json
```

## Open Constitutional Conflict

`PRODUCT_CONSTITUTION_V1_1.md` 将“生命小剧场”列为当时阶段不做。后续已分别批准严格受控的 `Abu Performance Proof 01` 与 `Topic 01 Structural Ablation`，但仍未批准全面转向内容剧场或弱化 Mingli First。

```yaml
conflict_id: DC-001
status: pending_constitution_v1_2_review
current_interpretation: Performance Proof 与 Topic 01 是受控垂直切片，不代表旧宪章被静默废止。
required_resolution: Product Constitution v1.2 应明确 Interactive Mingli Theater 与 S0 品牌生产原型在 Mingli First 下的从属地位、批准范围与发布门槛。
```
