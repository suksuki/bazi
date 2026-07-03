# V30 Stage Prompt And Context Design

日期：2026-06-28

## 背景

V30 的页面级推演已经从一次性全盘分析，拆成排盘、规则、特征、画像、做功路径、结构、时运、领域、报告等阶段。

当前问题不是“LLM 是否调用”，而是：

- 不同页面使用同一套通用 prompt，导致模型容易泛化、自检、重复工程语言。
- 页面上下文虽然被模块化，但缺少明确的场景任务契约。
- 中枢智能大脑审核了 LLM 输出，但还没有把“本页应该问什么、只允许答什么”沉淀成可训练结构。
- Gemma4 thinking 模式会增加等待时间，因此每次调用必须足够有价值，不能让模型漫游。

原则：

- 需要 LLM 的页面就等待真实 LLM，不使用 fallback 冒充推演。
- Prompt 必须按页面场景设计，不再所有页面共用一段大而全说明。
- LLM 只做本页推演候选，中枢大脑负责最终结论和建议。
- 上下文必须可追踪、可训练、可合成验证。

## 总体架构

```text
thinking step
-> summary_policy
-> stage_prompt_profile
-> stage_context_pack
-> Gemma4 thinking LLM
-> derivation JSON
-> central_brain_review
-> final_decision
-> UI typewriter display
```

核心分工：

| 层 | 职责 |
| --- | --- |
| `summary_policy` | 判断本页是否需要 LLM，是否显示小结，是否进入智能追问 |
| `stage_prompt_profile` | 定义本页 LLM 任务、必须命名的锚点、禁止跑题范围、回答形状 |
| `stage_context_pack` | 只提供本页需要的模块上下文，不倾倒完整 runtime |
| `Gemma4 thinking` | 产出本页推演候选，不做最终裁决 |
| `central_brain_review` | 清洗、验收、拒绝或收束 LLM 结果 |
| `final_decision` | 页面最终展示的结论、建议、依据、边界 |

## 页面分类

### 不调用 LLM 的页面

这些页面以事实、材料、证据整理为主，使用中枢规则小结即可：

| 页面 | 原因 |
| --- | --- |
| `chart_build` 排盘 | 四柱、日主、月令、时运入口是确定性事实，不需要 LLM |
| `knowledge_library` 知识库 | 装载规则边界，不应让 LLM 泛泛解释 |
| `feature_extraction` 特征抽取 | 证据整理页，先保留结构化特征 |
| 智能追问 dialogue surface | 由 dialogue brain 管，不走页面小结 LLM；不进入测算步骤导航 |

### 调用 LLM 的页面

这些页面需要推演表达和中枢审核：

| 页面 | Prompt Profile | 目标 |
| --- | --- | --- |
| `rule_matching` | `matched_rule_interpretation` | 解释命中规则、作用、下一步验证 |
| `portrait_projection` | `portrait_tendency_synthesis` | 把规则和特征合成画像倾向 |
| `path_reasoning` | `force_flow_path_derivation` | 解释力量流向、做功机制、领域落点 |
| `structure_reasoning` | `structure_decision_review` | 审定旺衰、格局、用神、反证边界 |
| `timing_layers` | `luck_flow_activation` | 解释大运流年如何激活原局路径 |
| `domain_synthesis` | `practical_domain_advice` | 转成用户关心的现实领域建议 |
| `final_report` | `final_stage_synthesis` | 收束所有已完成阶段，不新增事实 |

## Stage Prompt Profile

每个 profile 必须包含：

```text
profile_id
scene
task
must_name
avoid
answer_shape
trainable
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `profile_id` | 稳定版本号，用于训练、回放、审计 |
| `scene` | 页面场景，不同场景使用不同 prompt 任务 |
| `task` | 本页 LLM 只需要完成的任务 |
| `must_name` | 输出必须命名的本页锚点 |
| `avoid` | 本页禁止回答的内容 |
| `answer_shape` | 期望的推演形状 |
| `trainable` | 是否进入训练信号 |

### 规则匹配

```text
profile_id: v30.stage_prompt.rule_matching.v1
scene: matched_rule_interpretation
task: 解释本页命中的规则族、规则在此命盘中的作用，以及哪些规则需要进入下一页验证。
must_name:
  - matched_rule_family
  - rule_effect_in_chart
  - next_verification_target
avoid:
  - 不写最终人生判断
  - 不泛泛解释规则库
  - 不把未命中的规则写成结论
answer_shape:
  规则命中 -> 命盘作用 -> 验证方向 -> 行动提醒
```

### 画像投射

```text
profile_id: v30.stage_prompt.portrait_projection.v1
scene: portrait_tendency_synthesis
task: 把本页画像倾向讲清楚：画像是什么、由哪些规则或特征支撑、对用户意味着什么。
must_name:
  - portrait_tendency
  - supporting_feature_or_rule
  - user_facing_implication
avoid:
  - 不把画像说成必然事件
  - 不脱离本页画像扩展到完整报告
  - 不重复工程流程
answer_shape:
  画像倾向 -> 支撑证据 -> 现实表现 -> 提醒
```

### 做功路径

```text
profile_id: v30.stage_prompt.path_reasoning.v1
scene: force_flow_path_derivation
task: 解释本页做功路径：力量从哪里来、通过什么机制流动、落到哪些领域。
must_name:
  - primary_path_mechanism
  - force_flow_direction
  - domain_landing
avoid:
  - 不重写规则页
  - 不写完整领域报告
  - 不只说强弱而不说力量流向
answer_shape:
  路径机制 -> 力量流向 -> 领域落点 -> 建议
```

### 结构判断

```text
profile_id: v30.stage_prompt.structure_reasoning.v1
scene: structure_decision_review
task: 审定本页结构主线：旺衰、格局、用神取向和反证边界如何共同决定主线。
must_name:
  - structure_mainline
  - useful_god_boundary
  - counterevidence_or_confidence
avoid:
  - 不只给性格描述
  - 不跳到具体年份事件
  - 不新增命盘事实
answer_shape:
  结构主线 -> 取舍依据 -> 边界反证 -> 用神/行动方向
```

### 时运层

```text
profile_id: v30.stage_prompt.timing_layers.v1
scene: luck_flow_activation
task: 解释本页时运：大运和流年如何激活原局路径，哪些结论必须等待时间资料。
must_name:
  - luck_pillar_or_gap
  - flow_year_or_gap
  - activated_original_path
avoid:
  - 不凭空创造年份事件
  - 不离开原局路径单断流年
  - 不把时运缺口写成确定结论
answer_shape:
  时运入口 -> 激活路径 -> 阶段主题 -> 边界
```

### 领域合成

```text
profile_id: v30.stage_prompt.domain_synthesis.v1
scene: practical_domain_advice
task: 把本页领域合成转成用户能执行的结论：哪个领域最重要、证据来自哪里、怎么做。
must_name:
  - priority_domain
  - supporting_path_or_structure
  - concrete_action_advice
avoid:
  - 不平均铺开所有领域
  - 不写空泛安慰
  - 不脱离规则路径证据
answer_shape:
  优先领域 -> 证据链 -> 结论 -> 行动建议
```

### 最终报告

```text
profile_id: v30.stage_prompt.final_report.v1
scene: final_stage_synthesis
task: 收束已完成阶段，给出最终结论、核心建议和证据边界；不得新增事实。
must_name:
  - final_conclusion
  - core_advice
  - evidence_boundary
avoid:
  - 不新增命盘事实
  - 不重复所有页面
  - 不把未验证信息说成定论
answer_shape:
  最终结论 -> 核心建议 -> 关键依据 -> 边界
```

## Context Pack 设计

每个页面只喂本页需要的上下文：

| 页面 | 上下文 |
| --- | --- |
| `rule_matching` | matched_rules, rule_signals, structure/useful_god 子模型 |
| `portrait_projection` | portraits, mainline, path_model |
| `path_reasoning` | structure_graph, diagnosis_paths, path_model, mainline |
| `structure_reasoning` | ranked_decisions, structure_model, useful_god_model |
| `timing_layers` | luck_flow_context, timing_model, mainline |
| `domain_synthesis` | domain_readings, claims, paths, portraits |
| `final_report` | answer_result, final synthesis, accepted stage summaries |

禁止：

- 不喂完整 runtime。
- 不喂原始数据库对象。
- 不喂内部 id 作为用户可见依据。
- 不让 LLM 创造四柱、流年、隐藏属性确认或用户事实。

## 输出契约

2026-06-29 起，页面级 LLM 输出升级为 `StagePoint` 候选契约。旧字段仍可作为兼容输入，但页面、边栏、训练和命理师可选项最终都应消费 `StagePoint`。

实现状态：

- `thinking_step_summary` prompt 已要求返回 `candidate_points`。
- `ThinkingStageContext` 已暴露 `stage_points / stage_point_set`，让后续 LLM 可以看到本页已形成的判断点。
- 中枢 review 已把 LLM candidate 清洗为 `StagePoint`，并把旧字段作为兼容来源。
- 页面展示已优先消费 selected StagePoints。

正式契约：

```json
{
  "public_derivation": ["...", "..."],
  "candidate_points": [
    {
      "kind": "verdict",
      "text": "...",
      "short_label": "...",
      "bazi_terms": ["..."],
      "macro_domains": ["..."],
      "evidence_refs": ["..."]
    },
    {
      "kind": "advice",
      "text": "...",
      "short_label": "...",
      "bazi_terms": ["..."],
      "evidence_refs": ["..."]
    }
  ],
  "uncertainty": ["..."]
}
```

兼容期旧字段：

```json
{
  "text": "...",
  "public_thinking_lines": ["...", "..."],
  "derived_conclusion": "...",
  "derived_advice": "...",
  "used_evidence": ["..."],
  "uncertainty": ["..."]
}
```

要求：

- `candidate_points` 至少包含 1 条 `verdict` 和 1 条 `advice`。
- 每条 `candidate_points` 必须聚焦本页，不得跨页写完整报告。
- 每条点必须有 `short_label`，用于边栏工作记忆。
- 每条点必须绑定本页证据、命理术语或模块锚点。
- `public_derivation` 是客户可见推演线，不是隐藏 chain-of-thought。
- `uncertainty` 只记录本页边界，不做模棱两可的废话。
- 禁止固定前缀 `结论：`、`建议：`、`依据：`。
- 禁止工程语言、内部 id、JSON key、模型状态和自检语句进入用户可见字段。
- 旧字段 `text / derived_conclusion / derived_advice / public_thinking_lines` 只作为中枢转换为 `StagePoint` 的兼容来源。

## 中枢大脑审核

中枢审核要做四件事：

1. 检查 schema 是否完整。
2. 检查是否命中 `must_name` 锚点。
3. 检查是否违反 `avoid` 禁区。
4. 把 LLM 推演收束成：

```text
StagePoint.verdict
StagePoint.mechanism / evidence
StagePoint.advice
StagePoint.risk / boundary
```

拒绝条件：

- 没有结论或建议。
- 出现内部 id、JSON key、工程字段。
- 生成未给出的四柱、年份、用户历史、隐藏属性确认。
- 跨页写完整报告。
- 空泛模板化表达。

## 无 LLM 行为

需要 LLM 的页面，没有模型时：

- 不 fallback。
- 不展示规则小结冒充推演。
- 标记 `llm_unavailable`。
- 告诉用户：本页需要大模型推演，但当前没有连接到可用模型。

不需要 LLM 的页面：

- 可以使用中枢规则小结。
- 但不得显示为 LLM 推演结果。

## LLM 返回后的采用规则

页面级 LLM 输出进入中枢大脑后，采用“硬边界拦截、软质量清洗”的规则：

- LLM 成功返回非空文本时，默认进入中枢大脑清洗和定稿。
- 中枢大脑只拦截硬错误：内部标识泄露、角色可见性泄露、事实边界破坏、高风险绝对断语。
- Brain Judge 继续评分并产出训练信号，但低分、模板味、证据表达不完整不再直接阻塞页面。
- 软质量问题由中枢大脑补齐本页锚点、结论、建议和公开推演线，并记录 `adoption_mode=central_brain_cleaned_llm_derivation`。
- API 只有在模型不可达、执行开关关闭、调用失败或空文本时才标记 `llm_unavailable`。

这条规则的产品含义：

- 页面不会因为“LLM 有内容但中枢不采用”而卡住。
- 用户看到的是 LLM 推演经过中枢大脑定稿后的结论和建议。
- 中枢大脑不替代 LLM，而是负责事实边界、证据锚点和最终表达。

## 训练信号

每次页面级 LLM 调用应输出训练信号：

```text
stage_prompt_profile_id
stage_scene
stage_id
accepted/rejected/unavailable
schema_failures
anchor_coverage
avoid_violations
latency_ms
thinking_trace_chars
central_brain_review_status
user_action_after_result
```

训练目标：

- 哪个页面需要 LLM。
- 哪个 profile 更容易产出具体结论。
- 哪些上下文字段最有用。
- 哪些场景容易空泛。
- 哪些 prompt 会导致模型长时间自检。

## 验收标准

规则页：

- 必须说清命中规则是什么。
- 必须说明规则在命盘中的作用。
- 不得写最终人生断语。

路径页：

- 必须说清做功机制。
- 必须说清力量流向。
- 必须说清领域落点。

结构页：

- 必须说清结构主线。
- 必须说明用神/取舍边界。
- 必须保留反证或置信边界。

领域页：

- 必须优先给用户结论和建议。
- 必须能回扣路径、规则或结构。
- 不得平均铺开所有领域。

最终报告：

- 必须先给结论和建议。
- 必须引用已完成阶段。
- 不得新增命盘事实。

## 后续任务

1. 将 `stage_prompt_profile` 写入 `ThinkingStageContext`。
2. Prompt 编译器读取 profile 生成场景化 task。
3. 中枢审核记录 profile、锚点覆盖和禁区违规。
4. 测试覆盖每个 profile 的 context shape。
5. 增加 live LLM smoke，记录不同 profile 的耗时和输出质量。
