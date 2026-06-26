# V20 角色感知中枢设计

更新时间：2026-05-12

## 目标

V20 的中枢大脑只生成一套确定性事实、规则命中、知识对齐和主线判断；不同角色不重新改写底层判断，而是在中枢输出之后生成不同的画像、问题和可见内容。

```text
ChartInput
-> ChartFacts
-> CoreInference / FeatureLayer / DecisionReport / BrainState
-> RoleViewModel
-> RoleRuntimeView
```

核心原则：

- 命盘事实统一：四柱、十神、关系、强弱、岁运事实不因角色变化。
- 中枢判断统一：主线、候选路径、知识对齐和策略状态不因角色变化。
- 视图投影分层：guest、user、analyst、admin 看到不同画像深度、问题表达和字段范围。
- 角色层可迭代：角色画像和问题策略可以单独版本化、测试和学习，不污染 core/decision。

## 当前问题

旧实现里，所有角色基本共享一套问题和画像：

- 游客会看到过多技术链条，入口理解成本高。
- 普通用户需要可行动问题，但经常拿到命理师复核问题。
- 命理师需要证据边界和候选路径，但不能被普通用户表达方式限制。
- 管理员需要系统观测信息，而不是用户咨询体验。

因此需要把“角色体验”建成中枢后的独立投影层。

## 模块边界

建议新增 `role_view/` 包，承接角色视图能力：

```text
role_view/
  model.py       RoleViewModel/RoleProfile 的稳定数据结构
  policy.py      不同角色的画像深度、问题数量、表达风格
  projection.py  从 runtime result 生成角色画像和问题
```

现有模块职责保持：

| 模块 | 职责 |
| --- | --- |
| `core/` | 确定性命盘事实，不感知角色。 |
| `features/` | 结构特征发现，不感知角色。 |
| `decision/` | 候选判断、主线、规则路径，不感知页面角色。 |
| `orchestrator/` | 中枢整合、策略、记忆和学习信号。 |
| `role_view/` | 按角色生成画像和问题视图。 |
| `access/` | 权限裁剪、字段投影、敏感信息隐藏。 |
| `answer/` | 后续根据 RoleViewModel 生成不同表达。 |

## RoleViewModel

```text
RoleViewModel
- version
- role_key
- portrait_profile
- question_profile
- explanation_profile
- visibility_profile
- runtime_mutation
- guardrails
```

### portrait_profile

同一份 `decision_report.portrait_projection.axes`，按角色降维：

| 角色 | depth | 画像目标 |
| --- | --- | --- |
| guest | `entry_overview` | 2 个以内入门画像，只解释大方向。 |
| user | `guided_summary` | 4 个以内用户画像，可带置信度。 |
| analyst | `technical_review` | 8 个以内复核画像，保留证据边界。 |
| lab | `experiment_observation` | 实验观察画像。 |
| admin | `full_observation` | 完整观测画像。 |

### question_profile

同一批候选问题，按角色改写标题、限制数量、设置策略标签：

| 角色 | style | 问题目标 |
| --- | --- | --- |
| guest | `starter_questions` | 入口问题，避免术语。 |
| user | `guided_questions` | 咨询问题，强调可理解和可行动。 |
| analyst | `review_questions` | 复核问题，强调证据和边界。 |
| lab | `observation_questions` | 实验观察问题。 |
| admin | `full_observation_questions` | 系统观测问题。 |

### explanation_profile

回答层后续需要读取这个 profile：

| 角色 | 表达方式 |
| --- | --- |
| guest | 生活化、短句、少术语。 |
| user | 人话解释命理依据，给出选择重点。 |
| analyst | 展示结构、候选、分歧和复核点。 |
| admin | 展示系统状态、耗时、缓存、降级和策略版本。 |

### visibility_profile

权限层继续由 `access/roles.py` 和 `access/projection.py` 执行，但 `RoleViewModel` 会声明本角色的可见性意图：

| 角色 | 可见性 |
| --- | --- |
| guest | `public_entry` |
| user | `public_guided` |
| analyst | `technical_review` |
| lab | `experiment_observation` |
| admin | `system_observation` |

## 角色互动模型

角色差异不只是“显示不同问题”，而是不同角色进入不同互动流程。统一原则是：

```text
同一套八字事实和中枢判断
-> 不同角色视图
-> 不同问题链阶段
-> 不同结构化选择
-> 不同学习信号
```

用户交互应保持简单、明确、可直接选择，避免开放式发散。自由文本可以作为补充，但不作为核心训练信号。

| 角色 | 互动目标 | 主交互形式 | 学习信号 |
| --- | --- | --- | --- |
| guest | 快速进入主题，理解系统能看什么。 | 3 个以内入口问题 + 简短选择。 | 点击、停留、是否注册/进入档案。 |
| user | 围绕当前盘做主题探索。 | 主题选择、继续追问、答案偏好选择。 | 点击、跳过、继续追问、答案方向选择。 |
| analyst | 复核系统判断并校准主线。 | 认可、降权、切换主线、标记证据不足。 | 结构化校准、裁决选择、复核结论。 |
| admin | 观测系统质量和策略状态。 | 策略查看、回放、测试、回滚/激活。 | 策略观测、fallback、耗时、版本切换事件。 |

交互影响范围必须分层：

```text
当前会话：影响本轮问题排序、回答侧重点、LLM prompt 上下文。
用户偏好：影响下次推荐的主题、表达长度、术语密度。
群体经验：影响问题模板排序、角色画像表达和候选策略。
核心模型：不能被用户点击直接修改，只能经过合成验证、回放和版本激活。
```

禁止把用户偏好误当成命理真值。用户喜欢问财运，只说明交互偏好，不说明财星一定是本盘主线。

## 问题链 DAG

当前推荐问题已经具备角色排序、点击记录和已回答记忆，但仍偏“问题列表”。下一阶段要升级为问题链 DAG：

```text
entry
-> focus
-> structure
-> timing
-> advice
-> closure
```

问题不是孤立推荐，而是角色化问题图中的下一步节点。每个节点必须声明：

```text
question_id
role_target
stage
domain
title
choice_options
next_question_rules
answer_mode
learning_signal
visibility
```

### DAG 阶段

| stage | 目标 | 适用角色 |
| --- | --- | --- |
| `entry` | 快速确定用户想看哪一块。 | guest/user |
| `focus` | 聚焦事业、财运、关系、时间等主题。 | guest/user |
| `structure` | 将主题绑定到当前八字结构。 | user/analyst |
| `timing` | 判断大运、流年、流月是否引动。 | user/analyst |
| `review` | 复核证据边界、候选主线和冲突。 | analyst/admin |
| `observe` | 观察策略、耗时、fallback、学习状态。 | lab/admin |
| `advice` | 输出可理解建议和下一步选择。 | guest/user |
| `closure` | 收束本轮，推荐继续方向或保存档案。 | guest/user |

### 示例

普通用户：

```text
Q1 entry：你最想先看哪一块？
[事业] [财运] [感情] [近两年变化]

Q2 focus：事业里你更关心什么？
[稳定发展] [换方向] [升职压力] [合作关系]

Q3 structure：系统结合当前八字判断事业主题。
[看原因] [看时间] [看建议] [换一个主题]
```

命理师：

```text
Q1 review：当前主线是否接受？
[认可] [降权] [切换主线] [证据不足]

Q2 review：冲突点按哪条路径处理？
[印星缓冲] [财星通关] [比劫承接] [待复核]
```

管理员：

```text
Q1 observe：本次推荐问题来自哪里？
[角色策略] [seed registry] [runtime pointer] [fallback]

Q2 observe：是否需要看候选版本影响？
[查看 replay] [查看点击学习] [测试角色视图] [回滚 baseline]
```

## 交互学习边界

交互信号分为四类：

| signal | 来源 | 可影响 | 不可影响 |
| --- | --- | --- | --- |
| `preference_signal` | 用户主题选择、答案偏好。 | 表达方式、问题排序、会话重点。 | 核心规则、命盘事实。 |
| `interaction_signal` | 点击、跳过、追问、停留。 | 问题模板排序、角色问题分组。 | 单盘主线真值。 |
| `calibration_signal` | 命理师结构化选择。 | 候选策略、参数建议、回放材料。 | 直接在线改规则。 |
| `validation_signal` | 合成数据、回放、批量验证。 | 策略版本晋升、权重候选。 | 未经版本化的直接修改。 |

策略原则：

- 普通用户交互只影响体验和经验层，不直接影响模型。
- 命理师校准可以进入候选策略，但必须经过回放。
- 合成数据验证是规则、画像、问题生成和互动策略升级的主门槛。
- runtime 只能读取已激活 pointer，不直接消费原始训练报告。

## 实施计划

### P1：角色视图模块化

- 新增 `role_view/` 包。
- 将画像深度、问题风格、数量限制从 `access/projection.py` 迁出。
- `access/projection.py` 只负责权限字段、公开字段清洗和返回 runtime view。
- 补测试验证 guest/user/analyst/admin 问题和画像不同。

### P2：角色化回答

- role view 投影层读取 `RoleViewModel.explanation_profile`。
- guest 答案压缩成入口解释。
- user 答案强调“怎么看、怎么选”。
- analyst 答案保留复核依据。
- admin 答案展示系统观测。

### P3：角色化交互

- 问题交互组件按角色读取 `RoleViewModel.question_profile`。
- guest 只显示 starter questions 和入口提示。
- user 显示 guided questions 和追问入口。
- analyst 显示复核队列。
- admin 显示运行观测问题。
- 点击问题时写入 append-only 学习信号，后续用于角色问题排序和分组策略调优。

### P4：角色策略版本化和学习

- 给 role view policy 增加版本号。
- 记录不同角色的问题点击、追问、反馈。
- 用学习结果调优画像轴排序、问题标题和数量。
- 先生成只读聚合报告，再进入候选策略版本，不直接在线改写策略。
- 候选策略必须经过回放比较，才能考虑进入 runtime pointer。

### P8：问题链 DAG

- 将推荐问题升级为 `QuestionNode`，包含 stage、choice options、next rules 和 learning signal。
- guest/user 默认使用 entry -> focus -> advice 的短链。
- analyst 使用 structure -> review -> timing 的复核链。
- admin/lab 使用 observe 链查看策略来源、fallback 和 replay 影响。
- UI 上优先展示选择按钮，不把 DAG 内部标签暴露给普通用户。
- 点击选择只改会话状态和问题链游标，不改核心命盘事实。

### P8.5：问题审核互动

- 命理师/admin 可以对推荐问题和问题链节点做结构化审核。
- 审核动作包括通过、改写、降权、合并、删除、角色不匹配、主线不匹配、术语过重、重复、发散。
- 审核信号写入 append-only ledger。
- 审核结果只生成问题策略候选，不直接修改 runtime 问题。
- 候选策略必须经过合成案例和回放，才能进入 runtime pointer。

### P9：交互信号与训练分层

- 建立 `preference_signal`、`interaction_signal`、`calibration_signal`、`validation_signal` 的统一 schema。
- 用户点击和选择进入 append-only ledger。
- 训练脚本聚合信号，生成问题链候选策略。
- 候选策略必须通过合成案例和静态回放，才能进入 runtime pointer。
- 文档和测试必须明确：用户行为不直接改变核心模型。

## 不做什么

- 不让角色改变四柱事实。
- 不让前端决定可见字段。
- 不把角色逻辑塞进 core/decision。
- 不为每个角色复制一套运行时推理链。
- 不把用户点击当成规则真值。
- 不让开放式文本直接训练核心模型。

## 当前进度

- 已确定架构：统一中枢结果，角色视图投影。
- 已完成 P1：新增 `role_view/` 模块并从 access 层拆出画像/问题策略。
- 已启动 P2：`role_answer_profile` 已接入非流式角色 runtime view，答案正文开始按角色表达。
- 已启动 P3：前端智能问题区已读取 `question_profile`，展示角色化问题提示和数量限制。
- P3 进展：命理师/实验室/管理员问题区已按结构复核、证据边界、主题候选、系统观测进行分组。
- P3 进展：问题点击已写入 `role_question_click_ledger`，作为 P4 自学习的数据入口。
- 已启动 P4：`role_question_click_ledger` 已有只读聚合报告和 `/api/v20/learning/role-question-click` 入口。
- P4 进展：role view policy 候选版本已生成，入口为 `/api/v20/learning/role-view-policy-candidates`。
- P4 进展：role view policy replay 已生成，入口为 `/api/v20/learning/role-view-policy-replay`。
- P4 进展：管理员/实验室观测页已接入“角色策略学习”只读面板，可查看点击样本、候选策略、回放状态和 runtime gate。
- 已启动 P5：`question_seed_registry` 已作为冷启动候选源接入问题生成，只在匹配当前八字 domain/time 信号且通过 alignment 后进入候选池。
- P5 进展：seed 来源已进入角色问题点击信号和训练报告，可按角色统计 seed question fit，但仍不保存标题或用户原文。
- P5 进展：seed 点击统计已转换为 `seed_fit_policy` 候选，并纳入 role view policy replay。
- P5 进展：管理员/实验室观测页已展示 seed-fit 候选数量、top seed 和 seed replay 影响数。
- P2 收口：SSE 流式答案完成事件已接入 `role_answer_profile`，最终答案会回到角色表达口径。
- P6 启动：role view runtime pointer 已有只读 preflight 版本，暴露 candidate、replay、blocking gate，但不启用 runtime。
- P6 进展：管理员/实验室观测页已展示 role view pointer 的 active/candidate/gate 状态。
- P6 进展：role view replay 已增加 impact summary，按 policy key、角色和预期影响汇总候选变化。
- P5 进展：seed registry 已扩展到 20 条，覆盖财富、事业、关系、时间、强弱、用神、地支、十神、五行、格局和健康。
- P7 完成：role view runtime pointer 已从只读 preflight 升级为 fast-iteration 指针；候选 replay ready 后会自动应用到角色问题展示排序。
- 主线完成：`/api/v20/role-view/completion` 已提供 100% completion manifest，用于审计 P1-P7 工程闭环。
