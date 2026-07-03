# V30 Stage Intelligence LLM Brain Framework

更新时间：2026-06-29

## 目的

本文沉淀 2026-06-29 两轮讨论后的新共识：

- 每个测算页面都有自己的“食材加工”职责。
- 中枢智能大脑是大厨，负责判断、取舍、边界、证据和最终采用。
- LLM 是中枢授权的表达与推演助手，负责组织语言、把证据关系讲顺、生成候选判断点。
- LLM 输出不能直接成为页面结论，必须回到中枢大脑清洗、验收、排序和沉淀。
- 页面最终不再只有一段 `conclusion/advice`，而是结构化 `StagePoint` 列表。

目标是把页面小结升级为：

```text
LLM 推演候选
-> 中枢大脑验收
-> 结构化 StagePoint
-> 页面要点列表
-> 边栏工作记忆
-> 命理师可勾选
-> 训练与验证样本
```

这条主线的关键词是：

```text
stage-local
evidence-bound
point-based
customer-readable
sidebar-ready
trainer-ready
```

## 核心定位

### 中枢大脑

中枢大脑负责：

- 决定本页是否需要 LLM。
- 决定本页允许讨论的范围。
- 选择要喂给 LLM 的上下文。
- 检查 LLM 是否跑题、发散或新增事实。
- 把 LLM 候选推演拆成结构化判断点。
- 给每个判断点打分、排序、降权或拒绝。
- 决定哪些点展示到页面，哪些点进入边栏。
- 生成训练信号和验证样本。

中枢大脑不应该把模板文案当成结论，也不应该把 LLM 的漂亮话直接采用。

### LLM

LLM 负责：

- 组织语言。
- 把命理证据讲成通俗但不低幼的表达。
- 把规则、画像、路径、用神、时运之间的关系讲顺。
- 生成候选 `StagePoint`。
- 生成客户可见的公开推演线。

LLM 不负责：

- 修改排盘事实。
- 直接定最终结论。
- 跨页面生成完整报告。
- 把候选判断说成确定人生事实。
- 用模板格式替代推演。

### 页面

页面负责：

- 只展示当前页面的核心要点。
- 用列表、图标、小标签等方式呈现结构化判断点。
- 不展示工程字段、模型状态、内部 id。
- 不把边栏和页面变成两份重复报告。

### 边栏

边栏负责：

- 沉淀高价值短标签。
- 逐步展示当前命盘的工作记忆。
- 给后续页面和最终报告提供可见上下文。
- 为命理师选择、复核和勾选预留入口。

## StagePoint 数据模型

新增核心契约：

```json
{
  "point_id": "stage.rule_matching.001",
  "stage_id": "rule_matching",
  "kind": "verdict",
  "text": "官印相生不是单纯压力，而是压力能转成资质、平台或专业背书。",
  "short_label": "官印相生：压力转资质",
  "bazi_terms": ["官印相生", "官杀", "印星"],
  "macro_domains": ["career"],
  "evidence_refs": ["matched_rule.official_seal", "path.official_to_resource"],
  "counter_refs": ["timing.missing_luck_context"],
  "scope": "stage_local",
  "confidence": 0.78,
  "actionability": 0.72,
  "display_priority": 0.86,
  "sidebar_visible": true,
  "selectable": true,
  "selected_default": true,
  "source": "central_brain_reviewed_llm",
  "training_tags": [
    "stage_point_quality",
    "evidence_binding",
    "sidebar_memory_priority"
  ],
  "boundary": "stage_point_is_user_facing_judgment_not_chart_fact"
}
```

### kind 类型

| kind | 含义 | 页面标记 | 用途 |
| --- | --- | --- | --- |
| `verdict` | 本页核心判断 | 断 | 页面第一优先级 |
| `evidence` | 关键证据 | 证 | 展示为什么这么断 |
| `mechanism` | 命理机制 | 机 | 解释十神、五行、路径如何作用 |
| `advice` | 取舍建议 | 策 | 告诉用户怎么用这个判断 |
| `risk` | 风险边界 | 戒 | 防止过度断言 |
| `question` | 必要追问 | 问 | 只有高信息增益时才出现 |

### 页面使用原则

每页默认展示：

- 1 条 `verdict`
- 1 条 `advice`
- 可选 1 条 `mechanism` 或 `risk`

不建议每页展示超过 5 条，否则会变成报告页。

## LLM 输出契约

页面级 LLM 不再只返回 `text / derived_conclusion / derived_advice`。新契约是：

```json
{
  "public_derivation": [
    "亥月水气重，庚金在此处先看泄秀与流通。",
    "若盘内木财能承接水势，财路更像输出之后的结果。"
  ],
  "candidate_points": [
    {
      "kind": "verdict",
      "text": "庚日主生亥月，重点不在急断旺弱，而在水金木能否形成流通。",
      "short_label": "庚金亥月：先看流通",
      "bazi_terms": ["庚金", "亥月", "五行流通"],
      "evidence_refs": ["chart.month_branch", "element_distribution"]
    },
    {
      "kind": "advice",
      "text": "后面要优先看食伤、财星和印星之间谁能承接力量，不要只看单一强弱。",
      "short_label": "先看食伤财印承接",
      "bazi_terms": ["食伤", "财星", "印星"]
    }
  ],
  "uncertainty": [
    "时柱或大运缺口会影响最终取用优先级。"
  ]
}
```

兼容期可以保留旧字段：

```text
text
derived_conclusion
derived_advice
public_thinking_lines
```

但中枢最终必须把它们转成 `StagePoint`，页面和边栏不再直接消费旧字段。

## Prompt 设计

每个页面的 prompt 必须由三部分组成：

```text
stage_scope
context_pack
output_contract
```

### stage_scope

定义本页只允许说什么。

示例：

```text
stage_id: rule_matching
allowed:
  - 命中的规则族
  - 规则在此命盘中的作用
  - 哪些规则进入下一页验证
forbidden:
  - 最终人生判断
  - 未命中规则
  - 具体年份事件
  - 完整报告
```

### context_pack

只喂本页必需素材：

| 页面 | context_pack |
| --- | --- |
| `chart_build` | chart facts, day master, month branch, strength entry |
| `rule_matching` | matched rules, rule signals, useful-god hints, counter evidence |
| `feature_extraction` | feature evidence, ten-god visibility, element distribution |
| `portrait_projection` | portraits, supporting features, domain tendency |
| `path_reasoning` | paths, force flow, domain landing, blockers |
| `structure_reasoning` | strength, structure, ranked decisions, counter evidence |
| `useful_god_arbitration` | useful-god candidates, avoidance risks, cross checks |
| `timing_layers` | luck/flow activation, timing gaps, original paths |
| `domain_synthesis` | domain claims, paths, portraits, practical readings |
| `final_report` | accepted StagePoints, selected claims, user feedback, final blueprint |

禁止直接喂：

- 完整 runtime。
- 数据库原始对象。
- 内部 id 作为用户可见依据。
- 未确认的隐藏属性事实。

### output_contract

必须要求：

- 返回 JSON。
- 至少 2 条 `candidate_points`。
- 第一条优先是 `verdict`。
- 必须包含 `short_label`，用于边栏。
- 每条点必须绑定本页 evidence 或 bazi terms。
- 禁止固定前缀 `结论：`、`建议：`、`依据：`。
- 禁止模板句式和工程语言。

## 中枢大脑采用算法

LLM 返回后，中枢执行 `StagePointAdoptionPipeline`。

### 1. Scope Gate

过滤非本页内容。

```text
stage_scope_score =
  allowed_anchor_hit
- forbidden_topic_hit
- cross_stage_leak
```

拒绝：

- 规则页讲最终事业/财富报告。
- 画像页讲具体年份事件。
- 时运页创造未给出的年份事实。
- 用神页输出“某五行永久为忌”。

### 2. Evidence Binding

检查每条点是否有证据绑定。

```text
evidence_binding_score =
  evidence_ref_hit * 0.45
+ bazi_term_hit * 0.25
+ module_anchor_hit * 0.20
- unsupported_claim_penalty * 0.30
```

没有证据但语言漂亮的点，要么降权，要么进入 `discarded_noise`。

### 3. Information Extraction

中枢从 LLM 文本里提取有效信息：

- 命理术语。
- 机制关系。
- 现实领域映射。
- 风险边界。
- 可执行建议。

无效信息：

- “综合来看”
- “当前阶段”
- “需要进一步分析”
- “可作为参考”
- “后续继续观察”
- 自检式英文或模型过程话。

### 4. Point Scoring

```text
point_score =
  stage_scope_score * 0.22
+ evidence_binding_score * 0.22
+ bazi_specificity * 0.16
+ mechanism_clarity * 0.14
+ customer_value * 0.14
+ actionability * 0.10
- template_risk * 0.16
- overclaim_risk * 0.18
```

排序规则：

```text
verdict > mechanism > evidence > advice > risk > question
```

但如果 `risk` 分数高于 0.82，可以提前展示，防止误断。

### 5. Brain Judge

Brain Judge 不直接拦截所有低分内容，只负责：

- 给出质量分。
- 标记模板风险。
- 标记过度断言。
- 标记证据不足。
- 产出训练信号。

硬拦截只用于：

- 内部 id 泄露。
- 角色/权限泄露。
- 新增命盘事实。
- 高风险绝对断语。
- 空文本或模型不可达。

### 6. Final StagePoint Selection

```text
selected_points =
  top verdict
+ top advice
+ optional mechanism/risk
```

边栏选择：

```text
sidebar_points =
  points where sidebar_visible=true
  and display_priority >= threshold
  and short_label not duplicate
```

命理师勾选选择：

```text
selectable_points =
  evidence_bound
  and not hard_boundary_risk
  and kind in verdict/mechanism/advice/risk
```

## 边栏联动

`StagePoint` 是边栏工作记忆的主要来源。

边栏显示字段：

```json
{
  "memory_id": "stage.rule_matching.001",
  "kind": "rule",
  "label": "规则命中",
  "value": "官印相生：压力转资质",
  "chips": ["官印", "资质", "平台"],
  "stage_id": "rule_matching",
  "confidence_band": "high",
  "source_point_id": "stage.rule_matching.001"
}
```

边栏规则：

- 只显示已经走到的页面。
- 显示短标签，不显示完整段落。
- 同类重复点合并。
- 点选后可以回到对应页面。
- 后续命理师模式可以勾选、取消、标记为“采用/降权/待问”。

## 命理师可选模式

为以后专业命理师使用，`StagePoint` 预留：

```text
selectable
selected_default
operator_state
operator_note
```

状态：

- `accepted`
- `rejected`
- `needs_question`
- `watch_only`

命理师操作只影响：

- final synthesis 权重。
- 报告选择。
- 训练标签。

不能影响：

- 排盘事实。
- 规则原始命中。
- 大运流年计算。

## 和 Text-to-Option 的关系

2026-06-29 新增 `V30_TEXT_TO_OPTION_PRACTITIONER_INTERACTION_FRAMEWORK_20260629.md`。

两者分工：

- `StagePoint` 负责承载页面级判断点，回答“这一页到底断什么、依据什么、建议什么”。
- `Text-to-Option` 负责从 StagePoint 和对话文本里抽出候选、列表、数字、取舍和追问需求，回答“哪些内容可以让命理师或用户选择、排序、降权、补充”。

推荐链路：

```text
StagePoint.text
-> TextSemanticUnit
-> OptionSet
-> PractitionerSelection / UserResponse
-> Central Brain Belief Update
-> Training Example
```

因此不要把 StagePoint 做成复杂表单。StagePoint 保持可读判断，OptionSet 作为独立交互层扩展。

## 训练与验证

### 训练信号

新增训练信号：

```text
v30.training_signal.stage_point_quality
```

字段：

```text
stage_id
prompt_profile_id
candidate_point_count
selected_point_count
discarded_noise_count
stage_scope_score
evidence_binding_score
template_risk
overclaim_risk
sidebar_promotion_count
operator_selection_delta
user_action_after_display
```

### 合成验证

新增 synthetic tier 检查：

- 每页至少有 1 条 stage-local verdict。
- 每条展示点必须有证据或命理术语。
- 规则页不能输出最终人生断语。
- 画像页不能输出必然事件。
- 用神页不能输出永久忌神。
- 领域页必须给现实建议。
- 边栏只显示短标签。
- UI 不显示工程字段。

### 518K 验证

518K 只检查分布稳定性：

- stage_point_count 分布不能异常膨胀。
- sidebar_memory_count 不能过多。
- template_risk 平均值不能上升。
- overclaim_risk 不能上升。
- LLM unavailable 不能被规则 summary 冒充。

## 任务计划

### SPI-0 文档与边界冻结

状态：本文。

交付：

- 新 canonical 文档。
- 更新文档索引。
- 更新主线状态。

### SPI-1 StagePoint 契约

状态：已完成基础落地。

目标：

- 新增 `StagePoint` / `StagePointSet` 契约。
- 兼容旧 `final_decision` 字段。
- 页面和边栏后续只消费 `StagePoint`。

验收：

- 单测覆盖 schema、kind、source、boundary。
- 旧 reading 不崩。

### SPI-2 LLM 输出契约升级

状态：已完成基础落地。

目标：

- Prompt 要求输出 `candidate_points`。
- 保留旧字段兼容。
- LLM 输出禁止模板前缀和工程语言。

验收：

- fake provider output acceptance 覆盖新契约。
- live LLM smoke 记录 point count 和 schema pass。

### SPI-3 中枢 StagePointAdoptionPipeline

状态：已完成基础落地。

目标：

- 实现 scope gate、evidence binding、point scoring、noise discard。
- Brain Judge 只拦硬边界和记录软质量。

验收：

- 规则页跑题点被拒绝。
- 有证据点被采用。
- 模板点被降权或清洗。

### SPI-4 页面展示升级

状态：已完成基础落地。

目标：

- 页面展示 `StagePoint` 列表。
- 图标按 kind 显示。
- 保留打字机但不做大字报。

验收：

- 移动端不溢出。
- 页面不显示 `结论：/建议：` 固定模板。
- 字体和密度符合工具面板。

### SPI-5 边栏工作记忆接入

状态：已完成基础接入。

目标：

- 边栏从 selected StagePoint 生成短标签。
- 点击边栏点可定位阶段。
- 为命理师可选模式预留状态。

验收：

- 边栏不重复页面段落。
- 同类点可合并。
- 手机端仍简洁。

### SPI-6 命理师选择模式预留

状态：未开始，保留后续任务。

目标：

- 后端支持 operator state。
- 前端先只读展示，后续开启编辑。
- 选择结果只影响综合权重和训练标签。

验收：

- 选择不会改命盘事实。
- operator note 不进入用户报告，除非显式采用。

### SPI-7 训练信号与合成验证

状态：已完成基础训练信号，专项 synthetic stage-point tier 待后续补强。

目标：

- 新增 `stage_point_quality` 训练信号。
- synthetic validation 增加 stage-point tier。
- 518K 增加分布观察。

验收：

- synthetic stage-point tier 通过。
- 训练样本可以统计 point 采用率、模板风险、证据绑定率。

### SPI-8 Admin 观察与回放

状态：未开始，保留后续任务。

目标：

- Admin 可以查看每页 candidate/selected/discarded points。
- 显示 prompt profile、scope gate、evidence binding、Brain Judge 分数。
- 用于后续训练和人工审查。

验收：

- Admin 可定位“为什么这条没采用”。
- 不泄露用户隐私和模型密钥。

## 维护规则

- 页面小结相关需求优先查本文。
- `V30_STAGE_PROMPT_CONTEXT_DESIGN_20260628.md` 继续作为 prompt/profile 支撑文档。
- `V30_CENTRAL_BRAIN_V2_MAINLINE.md` 继续作为中枢总架构文档。
- `V30_SIDEBAR_MEMORY_USEFUL_GOD_MAINLINE_20260628.md` 继续作为边栏和用神专项文档。
- 新实现任务使用 `SPI-*` 编号，不再新增散乱任务名。
- 任何新页面小结字段必须说明是否进入 `StagePoint`，否则不进入 UI。

## 2026-06-29 实施记录

已落地：

- 新增 `v30.brain.stage_points`，输出 `v30.stage_point_set.v1` / `v30.stage_point.v1`。
- thinking projection 为每个阶段生成基础 `stage_point_set` 和 `stage_points`。
- LLM thinking prompt 要求 `candidate_points`，兼容旧 `derived_conclusion / derived_advice`。
- 中枢 LLM review 会把 LLM 候选点清洗成 StagePoint，再交给页面最终展示。
- API enhanced step 返回 `stage_point_set / stage_points`，旧 `final_decision` 兼容保留。
- 前端结论与建议改为消费 selected StagePoints，用 `断 / 机 / 证 / 策 / 戒 / 问` 区分类型。
- 边栏记忆项增加 `source_point_id`，后续可追溯到对应阶段判断点。
- Customer surface 去掉 `questions_array_is_fallback_only` 这类工程字段名，避免用户面和验证误判出现 `fallback`。
- Admin 训练页接回隐藏属性只读审核面板，避免训练 closeout 找不到审核入口。

验证：

```text
67 passed, 21 deselected
6 个原全单元失败点已复测通过
py_compile passed
node --check frontend/app.js passed
git diff --check passed
```

仍待后续：

- SPI-6 命理师可选模式。
- SPI-7 专项 stage-point synthetic tier 与 518K 分布观察。
- SPI-8 Admin candidate/selected/discarded StagePoint 回放视图。
