# V30 Sidebar Memory And Useful-God Mainline

## 目标

把左侧边栏从“档案与导航”升级为“八字测算工作记忆”。

用户每走完一步，边栏逐步沉淀本盘最重要的判断关键词：规则、特征、画像、路径、结构、用神忌神、时运和领域建议。边栏不自己解析页面文字，而是消费后端正式契约 `thinking_projection.sidebar_memory`。

同时把“用神/忌神”从结构页里的混合概念提升为独立模型组件：

- 用神不是固定五行断语，而是当前最优取用策略。
- 忌神不是永久凶神，而是当前最容易破坏平衡或路径的忌避风险。
- 两者必须绑定强弱、十神、规则、路径、反证和时运条件。

2026-06-29 补充：

- 边栏工作记忆的主要来源升级为 `StagePoint`。
- 页面级 LLM 不直接写边栏；LLM 只生成候选点，中枢大脑验收后把 selected `StagePoint.short_label` 写入边栏记忆。
- 边栏显示的是高价值短标签，不显示页面完整小结。
- 命理师可选模式后续应优先操作 `StagePoint`，而不是操作页面自然语言段落。

## 现状

已有能力：

- `xuanming_model.useful_god_model`
- 算法：`multi_strategy_useful_god_candidate_v1`
- `core_bazi_reading.ranked_decisions.useful_god`
- LLM stage context 已在规则页和结构页局部带入 `useful_god_model`

缺口：

- 前台没有独立“用神忌神与取舍”步骤。
- 边栏没有逐步沉淀关键判断。
- `useful_god_model` 只表达候选策略，忌避风险没有结构化输出。
- 中枢大脑和 LLM prompt 没有统一的“工作记忆”输入。

## 契约设计

新增：

```text
thinking_projection.sidebar_memory
```

结构：

```json
{
  "version": "v30.sidebar_memory.v1",
  "reading_id": "...",
  "items": [
    {
      "memory_id": "useful_god.primary",
      "kind": "useful_god",
      "stage_id": "useful_god_arbitration",
      "label": "用神取向",
      "value": "泄秀生财",
      "detail": "食伤与财星承接当前过旺之气，仍需路径和时运落地。",
      "chips": ["食伤", "财星", "路径承接"],
      "evidence": ["日主偏旺", "食伤生财路径成立"],
      "counter_evidence": ["财星路径不能直接等同收入结果"],
      "confidence_band": "medium",
      "visibility_stage": "useful_god_arbitration",
      "source_point_id": "stage.useful_god_arbitration.001"
    }
  ],
  "training_signal": {
    "trainable": true,
    "targets": [
      "sidebar_memory_priority",
      "useful_god_strategy_weight",
      "avoidance_risk_weight",
      "stage_visibility_weight"
    ]
  }
}
```

前端规则：

- 只显示已经走到的步骤对应记忆。
- 不提前展示后续阶段结论。
- 边栏信息必须是关键词和短句，不重复页面完整小结。
- 边栏优先使用 `StagePoint.short_label`，再使用 `chips` 和 `confidence_band`。
- 同一阶段同类短标签要合并，避免边栏变成第二报告页。
- 点击档案或步骤仍然保持简洁，不把边栏变成第二报告页。

## 用神忌神模型

扩展：

```text
xuanming_model.useful_god_model.avoidance_model
```

输入：

- `strength_model`
- `ten_god_model`
- `structure_model`
- `path_model`
- `ranked_decisions.useful_god`
- 规则命中与反证

输出：

- `primary_label`：用神取向
- `primary_elements`：候选五行
- `primary_families`：候选十神族
- `avoidance_model.primary_risks`：忌避风险
- `avoidance_model.risk_keywords`：边栏关键词
- `cross_checks`：强弱、十神、结构反证、路径数量

边界：

- 禁止输出“唯一用神已定”。
- 禁止输出“某五行永久为忌”。
- 禁止把财官食伤等直接翻译成财富、职位、婚姻结果。
- 训练只调整策略权重、风险权重和显示优先级，不改排盘事实。

## 步骤设计

新增前台步骤：

```text
useful_god_arbitration
标题：用神忌神与取舍
位置：结构、十神判断之后；大运流年之前
```

本页回答：

- 当前优先取用策略是什么。
- 为什么这个策略比其他候选更优先。
- 当前最需要避开的忌避风险是什么。
- 哪些反证会让这个用神取向降权。

LLM 任务：

```text
用神取向 -> 忌避风险 -> 取舍依据 -> 行动边界
```

## 训练与验证

训练目标：

- `useful_god_strategy_weight`
- `avoidance_risk_weight`
- `counterevidence_penalty`
- `timing_activation_weight`
- `sidebar_memory_priority`
- `stage_visibility_weight`

验证项：

- `sidebar_memory_contract`
- `useful_god_avoidance_boundary`
- `useful_god_stage_context`
- `no_fixed_useful_god_verdict`
- `no_fixed_unfavorable_element_verdict`
- `progressive_sidebar_visibility`

## 执行计划

1. 后端新增 `sidebar_memory` 契约。
2. `useful_god_model` 增加 `avoidance_model` 和训练信号。
3. 新增 `useful_god_arbitration` thinking step。
4. LLM stage context 接入新步骤 prompt profile。
5. 前端边栏渲染逐步工作记忆。
6. 测试覆盖契约、步骤、LLM context 和 UI 静态残留。
