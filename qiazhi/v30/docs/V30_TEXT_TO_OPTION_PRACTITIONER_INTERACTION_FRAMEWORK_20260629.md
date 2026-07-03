# V30 Text-to-Option Practitioner Interaction Framework

更新时间：2026-06-29

## 目的

本文定义一个新的框架级智能层：

```text
文本语义选项化层
Text-to-Option Intelligence
```

核心观察：

- 测算页面的小结、建议、推演文字里经常包含候选项。
- 对话系统的回答文字里也经常包含可选择、可排序、可数字化的内容。
- 这些内容不应只停留在自然语言里，而应被中枢大脑自动抽成可交互、可训练、可验证的结构。
- 命理师模式可以对这些结构进行选择、降权、排序、备注和反馈。
- 用户对话也可以复用这一层，让回答尽量变成点击选项、数字输入或极短输入。

这会成为 V30 的一个重要特点：

```text
系统先自动生成命理推演
-> 自动抽取可选择的判断点和候选项
-> 命理师选择 / 降权 / 排序 / 标注
-> 中枢大脑吸收反馈
-> 下一轮结论、问答和训练样本变得更准
```

## 定位

该层不是新的排盘模块，也不是 UI 小组件。

它是中枢智能大脑旁边的“语义交互层”：

```text
LLM / 规则 / 画像 / 路径 / 对话文本
-> StagePoint
-> TextSemanticUnit
-> OptionSet
-> PractitionerSelection / UserResponse
-> Central Brain Belief Update
-> Training Example
```

它负责把文本中隐藏的结构显性化。

## 为什么需要这一层

目前 V30 已经能生成：

- 页面级 StagePoint。
- 对话问题。
- 结论和建议。
- 用神、忌神、画像、路径、规则、领域建议。

但这些内容大多仍是“读完就过去”的文本。

例如：

```text
用神候选可先看土与火，土负责承接，火负责温煦，但火过旺会加重燥性。
```

这里至少有 5 个可抽取对象：

- 候选集合：土 / 火。
- 选择模式：单选或排序。
- 作用：土 = 承接，火 = 温煦。
- 风险：火过旺会加重燥性。
- 命理师动作：采纳土、采纳火、二者排序、标记待大运复核。

如果不抽取，系统只能显示一段话。

如果抽取，就可以变成：

```text
OptionSet useful_god_candidate
  - 土：承接、稳定、补结构
  - 火：温煦、激活、但有燥性风险
selection_mode: rank_one_or_more
```

这就是智能化交互的入口。

## 核心对象

### TextSemanticUnit

文本语义单元，是从自然语言里抽出的最小结构。

```json
{
  "unit_id": "tsu.useful_god.001",
  "source_type": "stage_point",
  "source_id": "stage.useful_god_arbitration.001",
  "stage_id": "useful_god_arbitration",
  "unit_type": "alternative",
  "text_span": "土与火",
  "normalized_terms": ["土", "火"],
  "bazi_terms": ["用神", "五行", "取用"],
  "macro_domains": [],
  "evidence_refs": ["useful_god.candidate.earth", "useful_god.candidate.fire"],
  "confidence": 0.78,
  "boundary": "text_semantic_unit_is_extracted_from_text_not_new_chart_fact"
}
```

主要类型：

| unit_type | 含义 | 示例 |
| --- | --- | --- |
| `alternative` | 候选项 | 土或火、官印或食伤 |
| `ranked_list` | 排序列表 | 先事业，再财运 |
| `numeric_marker` | 数字化指标 | 置信度 0.81、证据链 3 |
| `action_item` | 行动建议 | 先积累资质、避免冒进 |
| `risk_boundary` | 风险边界 | 火过旺会加重燥性 |
| `question_need` | 需要追问 | 需要确认年份 |
| `domain_focus` | 领域焦点 | 事业、财运、关系 |
| `bazi_claim` | 命理判断片段 | 官杀转印、食伤生财 |

### OptionSet

OptionSet 是可交互选项集合。

```json
{
  "option_set_id": "opt.useful_god.earth_fire.001",
  "source_unit_ids": ["tsu.useful_god.001"],
  "stage_id": "useful_god_arbitration",
  "topic": "useful_god",
  "title": "用神候选取舍",
  "question": "这一步更应采纳哪条取用方向？",
  "selection_mode": "rank_one_or_more",
  "visibility": {
    "user": "hidden",
    "practitioner": "interactive",
    "admin": "diagnostic"
  },
  "options": [
    {
      "option_id": "earth",
      "label": "土",
      "meaning": "承接水势、稳定结构、帮助力量落地",
      "bazi_terms": ["土", "用神", "承接"],
      "evidence_refs": ["useful_god.candidate.earth"],
      "risk_refs": [],
      "default_weight": 0.62
    },
    {
      "option_id": "fire",
      "label": "火",
      "meaning": "温煦命局、激活表达，但需防燥性过重",
      "bazi_terms": ["火", "用神", "温煦"],
      "evidence_refs": ["useful_god.candidate.fire"],
      "risk_refs": ["avoidance.fire_overheat"],
      "default_weight": 0.54
    }
  ],
  "training_tags": [
    "text_option_extraction",
    "practitioner_selection",
    "useful_god_arbitration"
  ],
  "boundary": "option_set_changes_interpretation_weight_not_chart_fact"
}
```

### PractitionerSelection

命理师操作结果。

```json
{
  "selection_id": "sel.opt.useful_god.001",
  "option_set_id": "opt.useful_god.earth_fire.001",
  "actor_role": "practitioner",
  "action": "rank",
  "selected_option_ids": ["earth", "fire"],
  "ranked_option_ids": ["earth", "fire"],
  "rejected_option_ids": [],
  "note": "土优先，火只能作为阶段激活条件，不能直接定为主用。",
  "confidence": 0.82,
  "effect_targets": [
    "belief_state.useful_god_candidate_weight",
    "stage_point.display_priority",
    "final_synthesis.evidence_order",
    "training_signal.practitioner_selection_alignment"
  ],
  "forbidden_effect_targets": [
    "four_pillars",
    "calendar_conversion",
    "birth_time",
    "raw_rule_truth"
  ],
  "boundary": "practitioner_selection_updates_belief_and_weight_not_chart_facts"
}
```

## 抽取算法

### 1. Source Collection

输入来源：

- `StagePoint.text`
- `StagePoint.short_label`
- LLM `public_derivation`
- 对话回答文本
- 最终报告草稿
- 用神候选说明
- 规则匹配说明
- 画像、特征、路径、领域建议

不直接抽取：

- 原始 runtime。
- 数据库内部对象。
- 未投影的 diagnostic trace。
- 模型自检文字。

### 2. Text Segmentation

把文本切成可分析片段：

- 句号、分号、顿号、逗号分段。
- 项目符号、数字序号、冒号后结构。
- “A 或 B”“A / B”“先 A 再 B”“一是 / 二是”等模式。
- 五行、十神、宫位、领域词的命理词典命中。

### 3. Ontology Mapping

把自然语言映射到 V30 术语体系：

```text
五行：木、火、土、金、水
十神：比劫、食伤、财星、官杀、印星
结构：旺衰、格局、做功、流通、合冲刑害
领域：财富、事业、感情、亲情、健康、时运
操作：采纳、降权、待问、排序、排除、复核
```

### 4. Candidate Grouping

把语义单元组合成 OptionSet：

| 文本形态 | OptionSet 类型 |
| --- | --- |
| “A 或 B” | `single_choice` 或 `rank_one_or_more` |
| “先 A，再 B” | `ranked_choice` |
| “重点看 A/B/C” | `multi_select` |
| “置信度 0.81” | `numeric_marker` |
| “需要确认年份” | `short_input` 或 `year_input` |
| “避免 A，优先 B” | `action_risk_pair` |

### 5. Central Brain Gate

中枢大脑必须裁决：

- 是否属于当前阶段。
- 是否绑定证据。
- 是否有交互价值。
- 是否会引导用户或命理师改写命盘事实。
- 是否只是普通文本，不值得做成选项。

评分建议：

```text
option_value_score =
  evidence_binding * 0.24
  + ambiguity_reduction * 0.20
  + practitioner_actionability * 0.18
  + downstream_impact * 0.16
  + bazi_specificity * 0.12
  + user_cost_saving * 0.10
  - fact_mutation_risk * 0.30
  - ui_noise_risk * 0.18
```

只有超过阈值才生成 OptionSet。

这点非常重要：不是所有文字都要变成选项。

## 和 StagePoint 的关系

StagePoint 是页面判断点。

OptionSet 是从 StagePoint 或其他文本里抽出来的交互结构。

推荐关系：

```json
{
  "stage_point_id": "stage.path_reasoning.002",
  "semantic_units": ["tsu.path.001", "tsu.path.002"],
  "option_sets": ["opt.path.domain_focus.001"]
}
```

StagePoint 继续负责：

- 用户可读判断。
- 证据绑定。
- 页面展示。
- 边栏记忆。

OptionSet 负责：

- 命理师选择。
- 对话点击。
- 排序和反馈。
- 训练样本。

不要把 StagePoint 做得太重。OptionSet 应该作为独立层扩展。

## 和对话系统的关系

当前对话系统已经收束为：

```text
reading_surface.current_dialogue_turn
```

Text-to-Option 层可以让对话问题更简单：

```json
{
  "question": "这一步更应先确认哪个现实背景？",
  "response_option_set": {
    "selection_mode": "single_choice",
    "options": [
      {"label": "事业压力", "value": "career_pressure"},
      {"label": "财务波动", "value": "wealth_volatility"},
      {"label": "关系反复", "value": "relationship_repetition"}
    ]
  }
}
```

用户只需要点选。

隐藏属性对话尤其适合：

- 年份输入。
- 强度滑杆。
- 重复状态选择。
- 关系/事业/财务/健康事件类型选择。

回答后进入：

```text
UserResponse
-> TextSemanticUnit / OptionSelection
-> Belief State delta
-> Hidden Factor state
-> 下一轮 current_dialogue_turn
```

## 命理师模式

命理师模式不是显示更多废话，而是显示可操作的结构。

### 可见内容

- 当前页面 StagePoints。
- 每条 StagePoint 抽出的 OptionSet。
- 候选项证据。
- 反证和风险。
- 中枢默认排序。
- 命理师选择状态。

### 可执行操作

| 操作 | 含义 | 影响 |
| --- | --- | --- |
| 采纳 | 认为该候选成立 | 提升解释权重 |
| 降权 | 认为证据不足或表达过重 | 降低 display priority |
| 排序 | 多个候选排序 | 影响 final synthesis 顺序 |
| 待问 | 需要用户补背景 | 生成高 VOI 追问 |
| 排除 | 明确不采用 | 进入反例训练 |
| 备注 | 增加命理师判断理由 | 进入训练样本，不直接给用户 |

命理师操作只能影响：

- belief posterior。
- StagePoint 权重。
- OptionSet 置信度。
- 最终报告排序。
- 对话下一问。
- 训练样本标签。

绝不能影响：

- 四柱。
- 六柱。
- 大运流年事实。
- 出生时间。
- 原始规则是否存在。

## 用户模式

用户模式只显示必要选项。

原则：

- 不展示“命理师审核”字样。
- 不展示太多选项。
- 每次只让用户回答一个高价值问题。
- 优先点击，其次数字，最后短文本。
- 用户选择只作为背景线索，不改命盘事实。

## LLM 的角色

LLM 可以参与两件事：

1. 在生成 StagePoint 时，同时提供 `option_hints`。
2. 在文本已经生成后，辅助抽取 `TextSemanticUnit`。

但最终 OptionSet 必须由中枢大脑裁决。

推荐 LLM 输出扩展：

```json
{
  "candidate_points": [
    {
      "kind": "verdict",
      "text": "用神候选先看土与火，土重承接，火重温煦。",
      "short_label": "用神候选：土火取舍",
      "option_hints": [
        {
          "type": "alternative",
          "topic": "useful_god",
          "labels": ["土", "火"],
          "selection_mode": "rank_one_or_more"
        }
      ]
    }
  ]
}
```

中枢可以采用，也可以丢弃。

## 训练闭环

每次抽取和选择都形成训练样本：

```text
source_text
extracted_units
generated_option_sets
default_selection
practitioner_selection
user_response
downstream_result_quality
```

训练目标：

- 哪些文本值得抽成选项。
- 哪些候选项经常被命理师采纳。
- 哪些候选项经常被降权。
- 哪些用户选项能最大减少不确定性。
- 哪些 OptionSet 造成 UI 噪音。
- 哪些抽取会误改事实边界。

训练信号：

```text
v30.training_signal.text_option_extraction_quality
v30.training_signal.practitioner_selection_alignment
v30.training_signal.dialogue_option_information_gain
v30.training_signal.option_ui_noise_penalty
```

## 合成验证

需要新增 synthetic tier：

```text
text_to_option_extraction
```

验证用例：

1. 用神候选文本能抽出五行候选。
2. 规则匹配文本能抽出命中规则列表。
3. 路径文本能抽出做功路径和领域落点。
4. 对话回答文本能抽出用户选择。
5. 数字化文本能抽出 numeric marker。
6. 工程语言和模型自检不得进入 OptionSet。
7. 命理师选择不得修改命盘事实。
8. 用户选项每次只出现一个当前问题。

## UI 设计原则

### 用户页面

- 只展示当前需要回答的一个 OptionSet。
- 点击式优先。
- 不显示抽取诊断。
- 不显示候选项过多的复杂结构。

### 命理师页面

- 每个 StagePoint 下可展开 OptionSet。
- 默认只显示中枢推荐的高价值选项。
- 支持采纳、降权、排序、待问、排除、备注。
- 选项旁显示证据和风险短标签。

### Admin 页面

- 显示抽取质量。
- 显示 discarded units。
- 显示命理师选择分布。
- 显示训练信号和失败原因。

## 主线任务

### TOI-0 文档与主线接入

状态：当前文档完成。

目标：

- 建立 Text-to-Option canonical 设计。
- 接入主线状态和文档索引。

### TOI-1 契约层

状态：已完成基础落地。

目标：

- 新增 `TextSemanticUnit`。
- 新增 `OptionSet`。
- 新增 `PractitionerSelection`。
- 明确 role visibility 和 forbidden effect targets。

验收：

- 单测覆盖 schema。
- 用户角色不看到 diagnostic。
- 选择不允许改命盘事实。

### TOI-2 抽取器

状态：已完成基础落地。

目标：

- deterministic pattern extractor。
- bazi ontology mapper。
- numeric/list/alternative extractor。
- LLM `option_hints` 兼容入口。

验收：

- 用神、规则、路径、领域、对话文本都有基础抽取。
- 工程字段不进入抽取结果。

### TOI-3 中枢 OptionSet Gate

状态：已完成基础落地。

目标：

- 计算 option_value_score。
- 按角色决定是否展示。
- 过滤低价值 UI 噪音。

验收：

- 用户每次最多 1 个 OptionSet。
- 命理师可见多个高价值 OptionSet。
- Admin 可见 discarded reason。

### TOI-4 StagePoint 接入

状态：已完成基础落地。

目标：

- StagePoint 关联 semantic_units 和 option_sets。
- 页面最终展示仍以 StagePoint 为主。
- OptionSet 只作为交互层。

验收：

- 旧 StagePoint 不崩。
- 没有 OptionSet 时页面不变。

### TOI-5 对话系统接入

状态：已完成基础落地。

目标：

- `current_dialogue_turn` 支持 `response_option_set`。
- 隐藏属性对话使用 structured option。
- 用户选择进入 belief update。

验收：

- 用户点击后不刷新步骤页。
- 回答后生成下一轮当前问题。
- 用户回答不改命盘事实。

### TOI-6 命理师模式 UI

状态：未开始，保留下一阶段。

目标：

- 展示可选择判断点。
- 支持采纳、降权、排序、待问、排除、备注。
- 不污染普通用户页面。

验收：

- practitioner role 可操作。
- user role 只看到必要对话选项。

### TOI-7 训练与合成验证

状态：已完成基础训练信号，专项 synthetic tier 待后续补强。

目标：

- 新增训练信号。
- 新增 synthetic tier。
- Admin 可观察选择分布与抽取失败。

验收：

- synthetic tier 通过。
- 训练样本可记录 default vs practitioner selection 差异。

## 当前结论

该层应作为 V30 下一条智能主线之一。

它的价值不在于“把文字变按钮”，而在于：

- 让系统知道自己说的话里面有哪些候选和取舍。
- 让命理师可以用结构化方式校准中枢大脑。
- 让用户对话更简单。
- 让每次交互都变成训练样本。
- 让 V30 从“生成文本的系统”升级为“能理解、拆解、选择、学习文本结论的系统”。

## 2026-06-29 实施记录

已落地：

- 新增 `v30.brain.text_options`。
- 新增版本契约：`v30.text_semantic_unit.v1`、`v30.option_set.v1`、`v30.text_option_projection.v1`、`v30.practitioner_selection.v1`。
- 支持从 StagePoint 文本抽取五行/十神/领域候选、先后排序、数字化标记、行动建议、风险边界和待补背景。
- 新增 OptionSet Gate，按证据绑定、歧义减少、命理师可操作性、下游影响、UI 噪音和事实风险评分。
- StagePointSet 自动附加 `text_option_projection / semantic_units / option_sets`。
- 每条 StagePoint 附加 `semantic_unit_ids / option_set_ids / practitioner_selectable`。
- LLM `candidate_points` 可保留 `option_hints`，但 OptionSet 仍由中枢抽取和裁决。
- `current_dialogue_turn` 接入 `response_option_set`，用户仍只看到一个问题，但选项变成标准 OptionSet。
- 前端 `compactQuestionOptions` 优先消费 `response_option_set.options`，旧 `question.options` 继续兼容。
- `ThinkingStageContext` 暴露轻量 option summary，避免把命理师选择状态喂给 LLM。

验证：

```text
tests/unit/test_text_to_option_interaction.py passed
tests/unit/test_sidebar_memory_useful_god.py passed
tests/unit/test_presentation_projection.py passed
py_compile passed
node --check frontend/app.js passed
```

仍待后续：

- TOI-6 命理师模式 UI。
- TOI-7 专项 synthetic tier、518K 分布观察和 Admin 抽取回放。
