# V30 智能问答极简交互重构

Updated: 2026-06-27

## 背景

当前中枢智能读盘框架方向正确，但智能问答 UI 仍带着历史实现痕迹：会话摘要、当前问题、补充文本、结构化下拉、已知线索、历史回合和候选队列同时展示，用户看到的是一套复杂表单，而不是一次自然的测算互动。

这会削弱 V30 的核心体验：用户只关心结论、建议，以及必要时补一个关键背景。

## 重构目标

智能问答改成推荐问题流：

1. 中枢智能大脑决定当前页面是否需要追问。
2. 前端只展示一组推荐问题。
3. 用户点击问题或选项后，系统生成回答。
4. 回答完成后，中枢刷新下一组推荐问题或进入下一步。
5. 回答以打字机方式出现，保留“正在推演”的体验。

页面不再展示工程语言、历史链路、候选统计、约束字段说明。

## 交互模型

```text
CentralReadingState
-> stage_question_opportunity
-> StageInteractionSlot
-> one focused question
-> user click / minimal structured input
-> interaction brain
-> answer panel
-> refreshed CentralReadingState
```

前端不负责推理，只负责把用户动作稳定映射成结构化反馈。中枢负责解释、调权、追问和下一步。

2026-06-27 追加重构：

- 问答区不再渲染问题池。
- 每个分析阶段只允许一个 `StageInteractionSlot`。
- 每个 `StageInteractionSlot` 最多展示一个聚焦问题。
- 聚焦问题只来自中枢当前 `stage_question_opportunity` 或智能问答步骤的 `next_question`。
- 前端不从候选问题池自行挑第二个问题。
- 推演未完成时不展示智能问题和测算反馈。
- 回答必须归属到 `question_stage_id` 才能在对应阶段展示；旧回答不允许靠问题 id 猜测归属。
- 已回答的问题不会在同一阶段继续作为当前问题重复出现。
- 客户视图过滤 `诊断口径`、`结构化明细`、证据计数等内部诊断语言。
- 阶段 LLM 推演同一 reading/stage 只自动尝试一次；超时、失败或无 final summary 都进入失败态，不再无限显示推演中。
- 智能对话是独立 dialogue surface，不是独立页面，也不是阶段小结页；它不触发阶段 summary LLM，也不被阶段推演失败挡住。
- `question_followup` 已从运行态 thinking steps、后端投影和前端导航删除；任何新实现不得重新引入这个伪步骤。
- 旧的 `renderQuestionUxPanel` / `stage-question-shell` 模型已废弃。

## 2026-06-29 硬性设计边界

测算步骤页面和智能对话必须彻底解耦：

- 测算步骤只负责当前阶段的八字推演、小结、建议和必要的命理师校准。
- 智能对话只负责当前 `current_dialogue_turn`，可以出现在任意测算页面，但不能成为第 N 步。
- 智能对话不能由前端看见候选问题后自行展示；必须由中枢大脑选择 `ask_stage_question`，并且问题和当前页面 stage 有明确相关性。
- 用户点击问题、选择选项或提交隐藏属性线索后，页面必须留在原测算步骤。
- 对话回答只刷新 answer panel、下一轮 question、belief state 和 training trace。
- 页面导航不得因为对话回答而跳转、刷新、前进或后退。
- 对话 pending 状态不得展示规则兜底草稿；只展示“等待大模型推演”。
- 如果没有可用 LLM，明确告诉用户模型不可用，不用模板答案补位。

## 普通问题

普通问题只保留按钮式选择：

- 有选项时：展示 2-4 个可点击选项。
- 无选项时：展示一个“生成回答”动作。
- 点击后直接提交 `selected_option`。
- 不展示自由文本输入框。
- 不展示历史回合和会话统计。

## 隐藏属性 / 明珠暗投线索

隐藏属性不能再让用户填写复杂表单。用户只需要：

- 选择一个反复状态标签。
- 可选填一个明显年份数字。
- 点击提交线索。
- 或者点击“不确定 / 先按中性看 / 暂不回答”。

前端映射：

```json
{
  "state_tags": ["career_pressure"],
  "years": [2024],
  "recurrence": "repeated",
  "intensity": "medium",
  "confidence": "approximate"
}
```

说明：

- `recurrence` 默认按 `repeated`，因为这个功能关注的是反复出现的隐藏线索。
- `intensity` 和 `confidence` 使用保守默认值，只作为中枢调权信号。
- 用户跳过时不更新隐藏属性，只让中枢降低追问强度或换一个问题。
- 用户反馈不改写命盘事实，只更新 hidden factor state、claim score 和 question policy。

## 验收

- 每个出现追问的页面只显示一个极简问题区域。
- 问题区域主体是推荐问题按钮，不是多段表单。
- 隐藏属性输入只包含状态选择、年份数字、提交和跳过动作。
- 用户点击后必须能看到回答面板。
- 回答面板继续使用打字机显示。
- 如果回答处于 LLM deferred 状态，前端显示等待 LLM 推演，不把规则兜底当成最终结论。
- 后端结构化约束继续生效。
- 不新增模板式回答，不绕过中枢智能大脑。

## 本轮实现

- 废弃 `renderQuestionUxPanel()`，改为 `renderStageInteractionSlot()`。
- `renderStageInteractionSlot()` 统一决定当前阶段是否展示回答和单个聚焦追问。
- 为隐藏属性新增极简结构化输入。
- 普通问题改成点击选项直接提交。
- 提交后在当前阶段展示 `answer_panel`。
- deferred 回答会等待 LLM 增强；增强失败时明确提示，不展示规则兜底结论。
- 保留 `structured_payload` 与后端校验，但隐藏复杂字段。
- 智能对话 summary policy 固定由 dialogue brain 管理，不进入页面小结 LLM；页面只挂载当前回答和下一条聚焦追问。
