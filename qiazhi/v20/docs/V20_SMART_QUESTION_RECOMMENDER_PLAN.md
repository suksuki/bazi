# V20 Smart Question Recommender Mainline

## 目标

智能问题不再是固定种子问题列表，而是以当前八字、大运、流年、角色和已问记录为核心上下文的对话式问题推荐系统。

2026-05-20 主线补充：智能问题的第一优先级从“推荐更合适的问题类型”升级为“生成已经绑定当前命主八字的问题”。`QuestionSeed` 和 `QuestionAtom` 只允许作为问题意图来源，不能直接作为最终 UI 问题标题。最终展示问题必须经过 `BaziQuestionAnchor` 绑定，详见 `docs/V20_BAZI_ANCHORED_QUESTION_REFACTOR.md`。

新的问答交互重构执行总纲见 `docs/V20_QA_INTERACTION_REFACTOR_MAINLINE.md`。该文档作为后续代码清理、UI 对齐、LLM 上下文和训练验证的主线任务来源。

2026-05-20 完成：问答交互重构主线已达到 100%。运行时问题已统一生成 `display_title` 和 `question_anchor`；`next_question_plan` 输出 `recommended_questions`；前端不再展示 `template_zh`；`question_agent` 不再生成旧 followup；知识库/decision 的 `question_seeds` 只作为来源信号；LLM prompt 已消费 `selected_question_anchor`。

系统主线：

```text
当前八字 + 大运流年
-> 结构动态主链
-> 规则命中与反证边界
-> 画像轴与八字特征
-> 当前角色
-> 已问问题与点击反馈
-> Next Question Policy
-> 推荐问题 + 追问链 + UI 展示
```

约束：

- 所有问题必须绑定当前八字、大运、流年，不允许脱离命局泛问。
- 所有最终展示问题必须先生成 `BaziQuestionAnchor`，anchor 未绑定时隐藏或降权，不进入普通用户视图。
- 知识库问题只能作为种子或原子来源，不能绕过当前盘锚定直接展示。
- LLM 只负责把已选问题润色成符合角色的自然语言，不负责凭空生成问题事实。
- 已问问题不重复出现，同主题追问需要冷却和深度控制。
- 训练直接优化问题排序、追问策略和角色表达，机器 gate 通过后直接生效。

## 成熟框架借鉴

### Conversational Recommender System

对话式推荐系统强调多轮问题、用户意图建模、偏好 elicitation 和下一步推荐。V20 对应为：

- 用户点击/提问 = interaction signal
- 当前命局结构 = item/context facts
- 下一问 = recommendation action
- 问题链连续性 = session-based recommendation

### Knowledge-based Recommender

八字问题必须由知识库、规则、结构动态和画像提供约束。问题不能只按热度推荐，必须满足：

- 有当前八字证据。
- 有主题知识单元支撑。
- 有角色可读表达。
- 有边界，不直接断具体事件。

### Information Gain

下一问优先选择最能减少不确定性的方向：

- 主链已清楚时，追问承接、阻断、时间触发。
- 主链不清楚时，先问结构主轴。
- 角色意图明确时，优先问该主题下最能区分路径的问题。
- 已问过的问题降权或隐藏。

## 问题原子模型

`QuestionAtom` 是问题系统的基础单元。

```text
atom_id
question_key
domain
topic
stage
role_targets
template_zh
evidence_requirements
context_requirements
followup_targets
cooldown_scope
max_depth
source
```

注意：`template_zh` 只表达问题意图，不再作为最终展示标题。最终标题必须由当前盘的 `BaziQuestionAnchor` 和角色叙事渲染生成。

## 八字问题锚点

新增运行时合同：

```text
BaziQuestionAnchor
```

字段：

```text
context_id
question_key
atom_id
role_key
anchor_status
natal_pillars
day_master
luck_pillar
flow_year_pillar
primary_dynamic_chain
mainline_domain
mainline_label
evidence_refs
portrait_axes
feature_ids
time_binding
why_this_question
missing_requirements
```

只有 `anchor_status == bound` 的问题可以进入普通用户展示。`weak` 问题只允许在命理师或 Admin 观察层出现，`missing_time`、`missing_structure`、`unsupported` 默认隐藏。

新链路：

```text
QuestionSeed / QuestionAtom
-> QuestionIntent
-> BaziQuestionAnchor
-> RoleQuestionNarrative
-> DisplayQuestion
-> LLM SelectedQuestionContext
```

### stage

| stage | 作用 |
| --- | --- |
| entry | 入口问题，适合游客和普通用户 |
| focus | 主题聚焦，事业/财运/婚恋/健康 |
| structure | 结构追问，主链、承接、阻断 |
| timing | 大运流年触发 |
| review | 命理师复核 |
| observe | 管理员观测 |
| advice | 行动边界和现实选择 |
| closure | 收束问题 |

### topic

第一批专题：

- `career_structure`
- `wealth_channel`
- `relationship_pattern`
- `timing_trigger`
- `structure_dynamics`
- `portrait_axis`
- `useful_god`
- `health_balance`
- `practitioner_review`
- `admin_observe`

## 角色问题风格

### 游客 guest

原则：少术语、低压力、能入口。

例：

- 这盘事业上更适合稳定发展，还是靠能力输出打开机会？
- 近几年更该先看工作变化、财运机会，还是关系状态？
- 这个八字最值得先看的主线是什么？

### 普通用户 user

原则：生活化、可追问、能落到现实选择。

例：

- 这盘事业压力，是来自规则约束、竞争，还是自己表达方式？
- 财运更像稳定收入、项目机会，还是合作分账带来的波动？
- 当前大运流年，会先牵动事业、财运还是关系？

### 命理师 analyst/practitioner

原则：保留专业术语，强调证据、边界、反证。

例：

- 当前结构主链是食神制杀，印星承接是否足以闭合到日主？
- 财生官杀路径成立时，是否有比劫或印星改写承接？
- 当前大运流年触发的是原局主链，还是形成新的阻断边？

### 管理员 admin

原则：看系统链路，不做咨询表达。

例：

- 这个问题由哪些结构动态、规则命中和画像轴触发？
- 已问问题 suppression 是否正确生效？
- 下一问排序中，角色权重、主链连续性和时间层权重分别是多少？

## Next Question Policy

第一版为可解释确定性 scorer。

```text
score =
  bazi_context_match
+ structure_chain_relevance
+ role_fit
+ previous_question_continuity
+ timing_relevance
+ information_gain
+ click_feedback_weight
- answered_question_penalty
- repeated_topic_penalty
- evidence_gap_penalty
- max_depth_penalty
```

### 关键规则

- `answered_question_penalty`：同 `question_id` 或 `question_key` 已问过则隐藏。
- `previous_question_continuity`：下一问必须和上一问同 domain、同 topic 或合法 DAG 边相连。
- `structure_chain_relevance`：问题 domain 必须能回到结构动态主链、规则或画像轴。
- `timing_relevance`：有大运/流年时，timing 问题升权；无时间层时不强行推荐。
- `max_depth_penalty`：同 topic 连续追问到上限后转入 advice 或 closure。

## 问题 DAG

默认路径：

```text
guest: entry -> focus -> advice -> closure
user: entry -> focus -> structure -> timing -> advice -> closure
analyst: structure -> review -> timing -> closure
admin: observe -> review -> closure
```

主题内追问示例：

```text
career.entry
-> career.focus.pressure_source
-> career.structure.output_authority_resource
-> timing.trigger
-> advice.work_choice_boundary
```

结构动态追问示例：

```text
structure.primary_chain
-> structure.chain_closed_or_blocked
-> structure.carrier_node
-> timing.chain_trigger
-> advice.reality_boundary
```

## 已问管理

运行时已经有 `answered_question_ids` 和 `answered_question_keys`，下一阶段扩展为 `QuestionSessionState`：

```text
answered_question_ids
answered_question_keys
answered_topics
last_question_id
last_domain
last_stage
topic_depth
suppressed_questions
cooldown_scopes
```

作用：

- 已问问题不再显示。
- 同主题重复问题降权。
- 合法追问优先显示在前 3 个。
- 用户跳过的问题降低同类问题权重。
- 用户点击的问题进入 role question click ledger，训练问题排序。

## 训练闭环

### 合成验证

为不同八字结构生成 synthetic cases：

- 食神制杀：事业压力、表达、印星承接。
- 食伤生财：收入渠道、承接、比劫分财。
- 财生官杀：责任、职位、资源承接。
- 官印/杀印相生：规则压力、学习资格、保护机制。
- 比劫承身/印星承身：承载、支持、资源来源。
- 岁运冲合：当前大运流年触发哪个主题。

每个 case 要验证：

- 推荐问题贴合主链。
- 下一问和上一问相连。
- 已问问题不重复。
- 角色语气正确。
- UI 不显示工程术语。

### 真实反馈

使用现有 ledger：

- `role_question_click_ledger`
- `orchestrator_memory_ledger`
- `question_source_record`

训练目标：

- 问题排序权重。
- 角色问题风格。
- 追问深度。
- seed question 保留/降权。

## UI 对齐

前台：

- 只显示自然语言问题。
- 显示 3-6 个推荐问题。
- 问题按“先看什么、继续追问、看时间、看建议”分组。
- 已问问题从列表中消失。

管理员：

- 显示 question atom、topic、stage、role targets。
- 显示推荐分数拆解。
- 显示上游问题、下游追问。
- 显示 suppression 原因。
- 显示训练来源和 pointer 状态。

## P0-P3 任务计划

### P0 文档和契约

- 新增智能问题推荐系统设计文档。
- 明确 `QuestionAtom`、`QuestionSessionState` 和 `NextQuestionPolicy`。
- 把主线计划和 UI 计划并入现有文档。

### P1 问题原子库

- 建立第一版角色化常见问题原子库。
- 覆盖游客、普通用户、命理师、管理员。
- 覆盖事业、财运、婚恋、大运流年、结构动态、画像、用神、健康。
- 保留来源说明，但不复制网页原文。

### P2 下一问策略

- 不再在现有 `question_agent` 上继续叠加旧 followup 模板；保留 suppression 能力，下一问生成迁移到 `QuestionAtom + QuestionDAG + BaziQuestionAnchor`。
- 已问问题 suppression 保持硬规则。
- 同 topic 追问使用 DAG 边和 depth。
- 输出 machine-readable scoring report。

### P3 UI 和训练对齐

- 前台问题区显示角色化问题和追问组。
- Admin 显示问题原子、推荐理由、已问管理和训练状态。
- 新增 synthetic question recommender 验证。
- 训练通过后直接写 question runtime pointer。

### P4 旧问答出口清理

- `QuestionCandidate.title` 降级为内部兼容字段，不再作为最终用户问题文本。
- `QUESTION_LABELS`、seed `template_zh`、knowledge `question_seeds` 只作为意图来源。
- 移除或旁路 `question_agent` 的旧 followup 生成和旧标题 humanize。
- 前端不再读取 `recommended_atoms[].template_zh` 展示下一问。
- LLM 不再只依赖 `selected_question.title`，必须消费 `selected_question_anchor`。

## 当前完成度

```text
QuestionCandidate 基础候选: 已有
question_seed_registry: 已有，需扩为 QuestionAtom
question_dag: 已有，需补 topic/depth/edge
question_agent answered suppression: 已有，仅保留 suppression，旧 followup 生成需清理
role_question_click ledger: 已有
question ranking pointer: 已有
UI role question profile: 已有，需补推荐原因和追问组
```

## 2026-05-19 推进记录

- 已新增 `interaction.question_atoms`，提供 `QuestionAtom`、`QuestionSessionState`、`question_atom_registry_manifest()` 和 `build_next_question_plan()`。
- Runtime 已输出 `next_question_plan`，位置在 `question_mainline_focus` 和 `question_source_ranking_report` 之间，使用最终中枢主线、当前 selected question、已问问题和大运流年状态生成下一问计划。
- `next_question_plan` 已和现有 `QuestionCandidate` 排序合流：只重排已有候选，不凭空生成无证据问题；命中的问题会带上 `next_question_atom_id`、`next_question_topic`、`next_question_stage` 和 `next_question_score_reasons`。
- 角色投影已允许 `next_question_plan` 进入 guest/user/analyst/admin/lab 视图。
- UI 智能问题区已显示“下一问”摘要；普通用户看到自然语言下一步，Admin/命理师额外看到推荐原因、已隐藏数量和每个问题的下一问阶段/专题。
- 测试覆盖已补齐：角色原子问题、已问 suppression、时间层升权、runtime 输出、UI 接线和访问权限。
- 宿主服务已重启验证：`/api/v20/measure/view/user` 能返回 `next_question_plan`，问题列表已带出 `next_question_atom_id`、`next_question_stage`、`next_question_topic` 和 `next_question_score_reasons`。
- 已新增 `validation.next_question_synthetic`：覆盖 guest/user/analyst/admin 的下一问合成验证，检查已问隐藏、时间层升权、角色路径和 top atom 命中。
- `training_iteration` 已纳入 `next_question_synthetic_validation` 阶段；写 artifact 后可由 `question_runtime_pointer` 直接激活为 `next_question_plan_policy`。
- Runtime 已消费 active question pointer 中的 `next_question_plan_policy`，只做 stage/topic boost 和重排，不新增问题、不改八字事实。
- Redis 测算缓存 key 已纳入 active runtime pointer 版本，训练指针生效后不会被旧缓存遮住。
- linux_0_13 已写入并激活下一问训练指针：接口验证出现“训练指针增强阶段排序/专题排序”理由。
- Admin 训练任务已新增“下一问合成验证”，并入智能问答训练专题和中枢问题策略任务图。
- 问题原子库已扩展到健康、关系时机、用神、日主强弱、地支互动、十神显隐和藏干复核等常见专题；新增原子仍绑定现有 `QuestionCandidate` key，不让 UI 推荐系统无法承接的问题。
- 下一问合成验证已从 4 个核心用例扩展到 7 个角色/专题用例，覆盖 health、relationship timing、strength -> useful god。
- Runtime 合流已修正同 `question_key` 多原子的选择逻辑：保留 `next_question_plan` 中排序最高的原子，避免页面理由被低优先级原子覆盖。
- `followup_targets` 已升级为可验证 DAG 约束：合成验证会检查所有目标原子存在；运行时根据上一问激活合法 followup target，并输出 `active_followup_targets` 和 `followup_edges`。
- UI 已展示“当前问题 -> 下一问”的链路摘要，Admin/命理师仍能看到阶段、专题和推荐理由。
- 点击反馈已接入问题原子闭环：前端点击上报会带出 `next_question_atom_id`、`next_question_topic`、`next_question_stage`，后端 ledger 和 `role_question_click_training` 会聚合原子奖励。
- `question_runtime_pointer` 已能消费点击训练产出的 `next_question_feedback_policy`，把真实点击增强/降低合并进 `next_question_plan_policy` 并直接进入 runtime pointer；样本不足时保持 `not_enough_data`，不污染当前策略。
- 问题原子排序已消费 active pointer 中的 `atom_boosts` / `atom_penalties`，命中后会输出“交互反馈增强此问题”或“交互反馈降低此问题”的可观察理由。
- 会话记忆已细化到 `session_memory`：`next_question_plan` 输出已问数量、已问专题、`topic_depth`、上一问 key/domain/stage，排序会对已推进专题降权，减少同一测算内反复问同一层。
- 角色旅程已接入 `role_journey`：guest/user/analyst/admin 分别有不同 stage order；业务阶段会归一到问题原子阶段，例如 `domain_reading -> focus`、`time_context -> timing`、`arbitration -> review`，排序会增强当前角色该走的下一阶段，并避免从 timing/advice 回退到 entry/focus。
- 前端已问记忆修正：点击问题后始终同时记录 `question_id` 和 `question_key`，保证后端 suppression 与 topic depth 都能稳定工作。
- 显式反馈已接入 UI：普通用户/游客可以对当前回答标记“有帮助、继续追问、不感兴趣”，这些信号写入 `role_question_click_ledger` 的 `answer_helpful/followup/skip` 奖励；Admin/命理师保留“通过、降权、改写、删除”的结构化评价。
- `question_runtime_pointer` 已同时消费 `role_question_click_training` 与 `question_review_training`：用户点击/跳过和命理师评价都会合并进 `next_question_plan_policy` 的 atom boost/penalty，并直接写 active pointer。
- linux_0_13 已激活显式反馈策略：当前 active question pointer 为 `v20.question_policy.candidate.f28823dd745f`；真实 review 样本已产生 atom boost/penalty，click atom 样本仍处于 `not_enough_data`，继续收集后会自动合入。
- UI 下一问展示已分层：用户/游客只看到自然语言“下一步”建议；Admin/命理师额外看到 `followup_edges`、atom id、`role_journey`、`session_memory`、策略来源、active pointer 版本和隐藏数量。
- `next_question_plan.policy_trace` 已接入：运行态会输出策略状态、来源、policy id、active pointer source/version，以及 atom/topic/stage boost 计数，方便 Admin 观察训练是否真的生效。
- 最终验收已完成：测试覆盖 QuestionAtom registry、下一问合成验证、runtime pointer、点击反馈、问题评价训练、DAG policy replay、question ranking、Redis cache key、角色访问权限和 UI 接线；线上 linux_0_13 active pointer、用户测算页和运行态 `policy_trace` 均已抽样通过。

当前阶段完成度：**100%**。

下一步：智能问题主线进入稳定迭代阶段。后续不再补主链缺口，而是持续扩容问题原子、合成样本、518K 回放分片、真实反馈样本和角色化叙事质量。
