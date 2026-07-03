# V30 中枢智能测算引擎主线任务

Updated: 2026-06-27

## 当前目标

把 V30 从“分页面展示材料”推进到“中枢智能读盘”。

当前已经有六柱排盘、规则、画像、特征、做功路径、时运、智能问答等材料。下一阶段的重点是让中枢智能大脑决定：

- 当前页面是否应该直接给结论。
- 当前页面是否应该插入一个有价值的追问。
- 用户回答后，哪些候选断语、路径、画像应该升权或降权。
- 最终报告如何从候选断语池合成，而不是简单拼接各模块。

## 主线阶段

### CBRE-1 Central Reading State

状态：已完成第一版。

输出：

- `v30.central_reading_state.v1`
- `v30.central_claim_score.v1`
- `v30.central_reading_action.v1`

能力：

- 读取 real_bazi_diagnosis claims、paths、portraits。
- 读取 question recommendations 和 question dialogue graph。
- 产出候选断语评分。
- 产出下一动作：`conclude_stage` / `ask_stage_question` / `continue_next_stage`。
- 产出训练信号和禁止训练边界。

### CBRE-2 Stage Question Opportunity

状态：已完成第一版。

目标：

- 把 `central_reading_state.next_question` 映射到具体分页面。
- 每个 thinking step 可携带 `stage_question_opportunity`。
- 前端只在中枢认为有价值的页面显示问答卡。
- 智能问答不再作为最后的伪页面出现；`question_followup` 已从运行态 steps 删除，它只能以 `current_dialogue_turn` 挂载在中枢认为有价值的测算页面。

验收：

- `thinking_payload.central_reading_state.version == v30.central_reading_state.v1`
- 至少一个 step 可带 `stage_question_opportunity`。
- 该机会包含 `step_id`、`question_id`、`target_claim_ids`。
- 用户页面不展示工程语言。

本轮实现：

- `build_central_reading_state()` 为追问机会增加 `step_id` 和 `display_mode`。
- `build_thinking_projection()` 输出 `central_reading_state`。
- 对应分页面 step 挂载 `stage_question_opportunity` 和 `next_action`。
- 前端不再只在最后的追问页显示智能问答；任意分页面只要中枢给出机会，就可显示结构化追问。
- `tests/test_v30_scaffold.py` 已覆盖 thinking payload 和 step-level opportunity。

验证：

```text
node --check qiazhi/v30/frontend/app.js
python -m compileall v30
pytest tests/test_v30_scaffold.py -q
67 passed
```

### CBRE-2.5 Question Interaction Simplification

状态：本轮执行。

目标：

- 把智能问答从复杂表单和问题池改为阶段交互槽。
- 用户点击问题或选项后直接生成回答。
- 回答后刷新下一组推荐问题或进入下一步。
- 隐藏属性/明珠暗投线索只允许极简结构化输入：状态选择、年份数字、跳过。
- 前端不展示历史工程语言、约束说明、候选统计和多余文本框。

验收：

- 每个页面只出现一个简洁追问区域，且每次最多聚焦一个问题。
- 页面推演未完成时不展示智能问题或测算反馈。
- 普通问题以按钮动作提交。
- 隐藏属性反馈映射到 `structured_payload`，但 UI 不暴露复杂字段。
- 用户回答后显示 `answer_panel`，并使用打字机效果。
- deferred 回答等待 LLM 推演，不把规则兜底作为最终结论展示。
- 中枢智能大脑继续负责调权和下一问，不由前端模板决定。

本轮实现：

- 新增 `V30_QUESTION_INTERACTION_SIMPLIFICATION_20260627.md`。
- 废弃 `renderQuestionUxPanel()`，新增 `renderStageInteractionSlot()`。
- 每个阶段最多展示一个聚焦问题，不再一次性展示候选问题池。
- 聚焦问题只接受中枢当前机会，前端不自行从候选池挑第二问。
- `StageInteractionSlot` 只在本页推演完成后显示。
- `answer_panel` 必须有 `question_stage_id` 才能进入对应阶段页。
- 阶段 LLM 自动增强增加单次尝试、长超时和失败终态，避免乱点后无限推演。
- 普通问题以选项按钮直接提交。
- 隐藏属性/明珠暗投线索改为状态标签 + 年份数字 + 跳过动作。
- 提交后在阶段页显示 `answer_panel`。
- LLM deferred 时显示等待/未完成，不打出规则兜底答案。
- 移除旧问答 UI 的历史链路、约束下拉、补充文本框和候选队列。
- 智能对话从阶段 summary LLM 门控里拆出，固定走 dialogue brain：不请求阶段小结、不显示阶段推演失败、不阻塞下一条追问，也不投影成导航步骤。

### CBRE-2.8 DialoguePlanner

状态：已完成第一版。

目标：

- 把“问不问、问哪个、挂在哪一页、是否继续/收束”从 `reading_engine` 和 presentation 中拆出来。
- 让 recommender 只给候选，QuestionDialogueGraph 只给记忆关系。
- 让中枢大脑拥有一个可训练、可回放、可观测的对话策略层。

本轮实现：

- 新增 `v30/brain/dialogue_planner.py`。
- 新增 `v30.dialogue_plan.v1`。
- `central_reading_state.dialogue_plan` 成为对话策略主出口。
- `central_reading_state.next_action`、`stage_question_opportunities`、`current_turn_seed` 均由 `dialogue_plan` 派生。
- presentation 优先读取 `central_reading_state.dialogue_plan.current_question_id`，graph 只做兼容兜底。

第一版可训练特征：

```text
top_claim_score
top_claim_requires_question
requires_question_count
candidate_question_count
current_question_score
answered_count
user_cost
overask_penalty
necessity_score
invalid_retry_active
```

训练目标：

```text
dialogue_action_policy
question_selection_policy
overask_penalty_weight
user_cost_weight
stage_question_policy
```

边界：

- Planner 不生成命盘事实。
- Planner 不修改四柱、六柱、历法、日主、月令。
- Planner 只选择当前对话动作和当前客户问题。
- 用户回答进入后续权重更新，不直接成为命盘事实。

### CBRE-2.9 Semantic Ontology And Dialogue Training Trace

状态：已完成第一版。

目标：

- 把十神、宏观相、关键词、问题槽、训练权重槽统一成中枢语义坐标。
- 让每个候选问题、每条候选断语、每次对话动作都能被训练系统消费。
- 明确训练只更新策略和权重，不更新命盘事实。

本轮实现：

- 新增 `v30/semantics/ontology.py`。
- 新增 `v30/semantics/domain_mapping.py`。
- 新增 `v30/brain/dialogue_training.py`。
- `recommend_questions().semantic_projection` 标注每个问题的宏观领域、十神驱动和问题槽。
- `central_reading_state.claim_scores[].semantic_projection` 标注每条候选断语的语义驱动。
- `dialogue_plan.semantic_trace` 汇总本轮候选、当前问题和训练槽。
- `central_reading_state.dialogue_training_trace` 输出可训练动作、特征、反馈标签和 blocked targets。
- `projection_contract.dialogue_entry_policy` 明确 `questions[]` 是兼容字段，客户主入口为 `current_dialogue_turn`。

验证：

- `central_reading_synthetic_validation.semantic_ontology_mapping`
- `central_reading_synthetic_validation.dialogue_training_trace`
- `tests/unit/test_presentation_projection.py`
- `tests/test_v30_scaffold.py`

### CBRE-3 Feedback Weight Update

状态：已完成第一版。

目标：

- 用户回答分页面问题后，不修改命盘事实。
- 更新 claim/path/portrait 的 alignment signal。
- 刷新 `central_reading_state.claim_scores`。
- 刷新下一问和下一页建议。

验收：

- 同一八字、不同结构化回答会改变 claim score 排序。
- 四柱、六柱、日主、月令不变。
- 训练信号只进入 question policy / claim score / path alignment。

本轮实现：

- 新增 `v30/brain/feedback_weight_updater.py`。
- 新增 `v30.feedback_weight_update.v1`。
- 用户回答会生成 `claim_alignment_signals`。
- 每条 claim score 增加 `feedback_signal`。
- claim scoring 增加 `feedback_alignment` 与 `feedback_contradiction` 组件。
- `central_reading_state.feedback_weight_update` 进入 trace / admin diagnostics / thinking payload。

第一版算法：

```text
question_outcomes
-> domain / selected_option / structured_payload 匹配
-> support / contradiction / net_alignment
-> claim score components
-> DialoguePlanner 重新选择下一问
```

边界：

- `chart_fact_mutation_allowed = false`
- 不修改四柱、六柱、日主、月令、历法。
- 不改写 base diagnosis claim text。
- 只影响排序、追问必要性、后续 synthesis 权重。

### CBRE-4 Final Synthesis Engine

状态：已完成第一版。

目标：

- 最终报告不拼接模块。
- 从 top claims、strongest path、portrait alignment、domain priority、timing status 合成结论和建议。
- LLM 只做推演表达，中枢负责最终裁决。

验收：

- 最终输出以结论和建议为主。
- 能说明主路径、核心画像、关键风险、行动建议。
- 不出现工程字段、内部 id、模板话。

本轮实现：

- 新增 `v30/brain/final_synthesis.py`。
- 新增 `v30.final_synthesis.v1`。
- `central_reading_state.final_synthesis` 成为最终结论和建议的结构化来源。
- `reading_surface.reading_summary.primary_message` 优先读取 final synthesis。
- `reading_surface.final_synthesis` 暴露客户可读结论、建议、证据链和质量契约。
- `thinking.final_report` 读取 final synthesis 的结论、建议和证据链。

第一版算法：

```text
claim_scores
-> top diagnosis claims
-> path labels / portrait statements
-> practical domain priority
-> feedback_weight_update
-> conclusion / advice / evidence_chain
```

训练目标：

```text
claim_selection_for_final_synthesis
domain_priority_weight
advice_actionability_weight
feedback_to_synthesis_weight
evidence_chain_ordering
```

边界：

- 不从 LLM 生成新断语。
- 不改写 base diagnosis claim text。
- 不改四柱、六柱、日主、月令、历法。
- LLM 以后只能做表达增强，不能负责最终裁决。

### CBRE-4.5 Stage LLM Policy And Central Brain Review

状态：已完成第一版。

目标：

- 不是每个页面都调用 LLM。
- 每页小结只聚焦本页内容，不跨页泛化。
- LLM 只产出阶段推演候选，最终结论和建议由中枢智能大脑审核定稿。

页面策略：

| 页面 | LLM 策略 | 原因 |
| --- | --- | --- |
| 排盘 `chart_build` | 不需要 | 事实页， deterministic summary 足够 |
| 知识库 `knowledge_library` | 不需要 | 装载边界页，不应消费 token 做泛泛解释 |
| 规则匹配 `rule_matching` | 自动 | 需要解释命中规则、规则作用和下一步验证 |
| 特征抽取 `feature_extraction` | 不需要 | 证据整理页，先保留结构化特征 |
| 画像 `portrait_projection` | 自动 | 需要把规则和特征合成为用户可理解倾向 |
| 做功路径 `path_reasoning` | 自动 | 需要解释力量流向、路径机制和领域落点 |
| 结构判断 `structure_reasoning` | 自动 | 旺衰、格局、用神取向需要中枢审定 |
| 时运 `timing_layers` | 条件自动 | 大运和流年齐全时才推演阶段激活 |
| 领域合成 `domain_synthesis` | 自动 | 直接面向用户现实问题和行动建议 |
| 智能追问 dialogue surface | 跳过 | 由 dialogue brain 管，不走页面小结 LLM，不进入步骤导航 |
| 最终报告 `final_report` | 自动 | 收束已完成阶段，不新增事实 |

中枢审核规则：

- LLM prompt 必须遵守 `summary_policy.signals.focus_scope`，只处理本页内容。
- LLM 输出必须包含 `text`, `public_thinking_lines`, `derived_conclusion`, `derived_advice`, `used_evidence`, `uncertainty`。
- 中枢审核后统一形成 `结论 / 建议 / 依据`，再进入页面展示。
- 规则、画像、路径、结构、领域页必须带本页锚点；缺锚点时记录 coverage notes，用于训练。
- fallback 不能冒充 LLM 推演；不需要 LLM 的页面直接保留中枢规则小结。

训练目标：

```text
stage_local_llm_need_and_central_brain_summary_quality
llm_enhancement_stage_gate
stage_focus_scope_weight
central_brain_review_threshold
stage_anchor_coverage
```

### CBRE-5 Synthetic Validation

状态：已完成第一版。

目标：

新增合成验证层：

- `central_reading_claim_selection`
- `stage_question_policy`
- `feedback_weight_update`
- `same_bazi_divergent_feedback`
- `final_synthesis_quality`

验收：

- 缺时运时追问时运，不强断流年。
- 画像冲突时追问现实反馈，不直接定性。
- 同一八字不同反馈改变权重，但不改变命盘事实。
- LLM 不得新增未授权断语。

本轮实现：

- 新增 `v30/validation/central_reading_synthetic_validation.py`。
- 新增 `v30.central_reading_synthetic_validation.v1`。
- 新增 `tests/unit/test_central_reading_synthetic_validation.py`。

第一版验证项：

```text
central_reading_claim_selection
stage_question_policy
feedback_weight_update
same_bazi_divergent_feedback
final_synthesis_quality
```

验证内容：

- `central_reading_state` 必须有 claim scores、top claims 和 ready final synthesis。
- `dialogue_plan` 必须是客户当前问题的策略出口。
- `feedback_weight_update` 必须产生 active alignment signal，且 blocked_targets 包含 chart_facts。
- 同一八字的事业反馈与关系反馈会产生不同 positive claim ids，但 chart_context 完全一致。
- final synthesis 必须 `结论：` 开头，`建议：` 开头，不能把边界废话混入主结论。

运行命令：

```text
pytest tests/unit/test_central_reading_synthetic_validation.py -q
```

## 本轮交付

本轮已完成 CBRE-2：

```text
central_reading_state
-> stage_question_opportunities
-> thinking step
-> frontend stage question panel
-> tests
```

后续已追加完成：

```text
CBRE-2.8 DialoguePlanner
CBRE-3 Feedback Weight Update
CBRE-4 Final Synthesis Engine
CBRE-5 Synthetic Validation
```

## 边界

- 中枢智能大脑只协调，不改写命盘事实。
- LLM 不生成候选断语，只生成推演表达候选。
- 用户回答只调权，不直接创建事实。
- 训练只训练权重和策略，不训练四柱、历法、命盘事实。
