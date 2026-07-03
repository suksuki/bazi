# V30 Dialogue Brain Implementation Tasks

Updated: 2026-06-27

## 当前执行原则

本轮开始正式重构智能对话系统，顺序固定为：

```text
先清理旧入口
-> 再建立 current_dialogue_turn 唯一出口
-> 再把旧 recommender / graph / hidden factor 收编
-> 最后做训练与可视化增强
```

不能一边保留旧问题池，一边叠新大脑。否则系统会继续出现多个地方都能决定问题的混乱状态。

## 本轮任务状态

### T1 清理旧前端残留

状态：已完成第一批。

已清理：

```text
frontend/app.js
- remove unused stageDialogueProjection()
- remove unused renderQuestion()
- remove focusedQuestionForStage()
- remove stageScopedQuestions()
- remove stageQuestionTopicHints()

frontend/styles.css
- remove unused .question-dock
```

效果：

```text
前端不再根据 questions[] + topic hints 自行挑问题。
```

### T2 后端唯一对话出口

状态：已完成第一版。

新增字段：

```text
reading_surface.current_dialogue_turn
```

结构：

```json
{
  "version": "v30.current_dialogue_turn.v1",
  "action": "ask",
  "stage_id": "domain_synthesis",
  "stage_display": "领域建议",
  "question": {},
  "why_now": "...",
  "target_claim_ids": [],
  "target_claim_count": 4,
  "visual_hint": {},
  "ui_policy": {
    "max_visible_questions": 1,
    "question_source": "current_dialogue_turn",
    "show_engine_diagnostics": false
  }
}
```

旧字段仍保留：

```text
reading_surface.next_question
questions[]
question_dialogue_graph.next_question_id
```

但它们现在是兼容层，不再是客户 UI 的主出口。

### T3 前端切换到 current_dialogue_turn

状态：已完成第一版。

当前规则：

```text
renderStageInteractionSlot()
-> currentDialogueTurnForStage()
-> renderFocusedQuestionPanel()
```

前端只渲染：

```text
surface.current_dialogue_turn.question
```

不再做：

```text
从 questions[] 里按 topic 匹配
从 rows[0] 兜底挑问题
根据 stage topic hints 自己选题
```

### T4 轻量可视化巧思

状态：已完成接口与第一版 UI。

设计目标：

用户每次看到问题时，不只是看到一个按钮，而是看到“为什么问、问完会让哪个建议更清楚”。

新增：

```text
current_dialogue_turn.visual_hint
answer_panel.visual_hint
```

当前可视化形态：

```text
advice_compass
- 主题 chips：事业 / 领域建议 / 只问一个关键点
- 细进度线：信息增益、输入成本
- guidance：回答后会把建议收束到哪个方向

hidden_signal_probe
- 用于隐藏属性校准
- 强调只作为线索，不改命盘事实
```

产品边界：

```text
可视化只帮助理解当前对话目的。
不展示 raw score、policy weight、schema、内部诊断。
不把可视化做成复杂 dashboard。
```

### T5 收编旧 recommender / graph

状态：已完成第一版。

已经落地：

```text
v30/questions/recommender.py
- 每个推荐问题增加 candidate_source = question_recommender_candidate
- 每个推荐问题增加 decision_owner = dialogue_brain
- boundary 明确 recommender 只输出候选，不选择客户当前问题

v30/questions/dag.py
- QuestionDialogueGraph 增加 decision_owner = dialogue_brain
- QuestionDialogueGraph 增加 customer_decision_field = reading_surface.current_dialogue_turn
- boundary 明确 graph 是 memory/relation graph，不是客户决策者

v30/brain/reading_engine.py
- central_reading_state 增加 dialogue_decision_owner
- central_reading_state 增加 customer_decision_field
- central_reading_state 增加 candidate_sources
- central_reading_state 增加 current_turn_seed
- training_signal.targets 增加 dialogue_turn_policy
```

当前边界：

```text
recommender 负责候选。
question_dialogue_graph 负责关系和历史记忆。
central_reading_state.current_turn_seed 负责把当前问题绑定到大脑判断。
reading_surface.current_dialogue_turn 负责客户 UI 唯一出口。
```

### T6 拆出 DialoguePlanner

状态：已完成第一版。

新增模块：

```text
v30/brain/dialogue_planner.py
```

核心输出：

```text
v30.dialogue_plan.v1
v30.dialogue_planner.v1
```

职责：

```text
输入：
- claim_scores
- recommendations
- question_dialogue_graph memory
- interaction_state

输出：
- action
- current_question_id
- current_question
- next_action
- stage_question_opportunities
- current_turn_seed
- decision_features
- training_signal
```

第一版算法特征：

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

重要边界：

```text
QuestionDialogueGraph 仍可作为 memory input。
recommend_questions() 仍可作为 candidate input。
但客户侧当前问题只认 dialogue_plan.current_question_id -> reading_surface.current_dialogue_turn。
```

### T7 回归测试

状态：待完整执行。

已增加断言：

```text
tests/unit/test_presentation_projection.py
- current_dialogue_turn exists
- question matches next_question compatibility field
- max_visible_questions == 1
- target_claim_ids non-empty
- visual_hint exists

tests/test_v30_scaffold.py
- HTTP/API view exposes current_dialogue_turn
- answer refresh updates current_dialogue_turn
- answer_panel carries visual_hint
- recommender question is marked as legacy candidate source
- question_dialogue_graph is marked as memory/relation graph
- central_reading_state exposes current_turn_seed and dialogue_turn_policy
- central_reading_state exposes dialogue_plan
- customer next question matches dialogue_plan.current_question_id
```

### T8 反馈权重更新

状态：已完成第一版。

新增模块：

```text
v30/brain/feedback_weight_updater.py
```

核心输出：

```text
v30.feedback_weight_update.v1
v30.feedback_weight_updater.v1
```

职责：

```text
输入：
- diagnosis claims
- question_outcomes

输出：
- claim_alignment_signals
- support / contradiction / net_alignment
- training_signal
```

接入位置：

```text
central_reading_state.feedback_weight_update
central_claim_score.components.feedback_alignment
central_claim_score.components.feedback_contradiction
central_claim_score.feedback_signal
```

边界：

```text
用户回答只调权。
不改四柱、六柱、日主、月令、历法。
不改 base diagnosis claim text。
```

### T9 最终结论与建议合成

状态：已完成第一版。

新增模块：

```text
v30/brain/final_synthesis.py
```

核心输出：

```text
v30.final_synthesis.v1
v30.final_synthesis_engine.v1
```

职责：

```text
输入：
- central claim_scores
- diagnosis claims / paths / portraits
- practical_reading_context
- feedback_weight_update

输出：
- conclusion
- advice
- evidence_chain
- customer_summary
- quality_contract
- training_signal
```

产品规则：

```text
结论和建议必须优先。
证据链服务于结论，不展示内部原始 trace。
LLM 只能表达增强，不能新增命盘事实和最终裁决。
```

接入位置：

```text
central_reading_state.final_synthesis
reading_surface.reading_summary.primary_message
reading_surface.final_synthesis
thinking.steps[final_report]
```

### T10 中枢智能合成验证

状态：已完成第一版。

新增模块：

```text
v30/validation/central_reading_synthetic_validation.py
```

核心输出：

```text
v30.central_reading_synthetic_validation.v1
```

验证项：

```text
central_reading_claim_selection
stage_question_policy
feedback_weight_update
same_bazi_divergent_feedback
final_synthesis_quality
```

产品意义：

```text
证明中枢不是模板拼接。
证明用户回答会调权，但不改命盘事实。
证明最终结论和建议有结构化质量门槛。
证明这套链路可以进入后续训练和合成回放。
```

## 下一阶段任务

### DBR-CLEAN-2 降级 questions[]

状态：已完成客户 UI 与 projection contract 第一版，继续保留兼容字段。

目标：

```text
客户 UI 不消费 questions[]。
questions[] 只作为兼容字段或 admin/practitioner diagnostics。
```

后续处理：

- `client_model.py` 中保留 `questions[]`。
- projection contract 明确 `questions[]` fallback-only。
- 前端继续不读取 `questions[]` 做选题。
- `projection_contract.dialogue_entry_policy.customer_primary_entry = reading_surface.current_dialogue_turn`。
- `projection_contract.customer_surface_contract.questions_array_fallback_only = true`。

### DBR-CLEAN-3 收编 QuestionDialogueGraph

状态：已完成第一版边界标记，后续要继续移除旧决策依赖。

目标：

```text
QuestionDialogueGraph 只做 memory/relation graph。
不再作为客户 next question 决策者。
```

迁移：

```text
graph.next_question_id -> compatibility
DialogueBrainState.current_dialogue_turn -> customer decision
```

### DBR-CLEAN-4 收编 recommender

状态：已完成第一版候选源标记，并已拆出 DialoguePlanner 第一版。

目标：

```text
recommend_questions() 只产出 candidate questions。
DialoguePlanner 才能决定当前问题。
```

需要新增：

```text
candidate_source
decision_owner
question_score_components
```

已新增：

```text
candidate_source
decision_owner
dialogue_plan.decision_features
dialogue_plan.training_signal
```

### DBR-SEM-1 命理语义本体

状态：已完成第一版。

目标：

把十神、宏观相、六亲、健康五行、关键词和权重矩阵落到代码。

已新增模块：

```text
v30/semantics/ontology.py
v30/semantics/domain_mapping.py
```

已接入：

```text
recommend_questions().semantic_projection
recommend_questions().question_score_components.semantic_weight_slot
central_reading_state.semantic_ontology
central_reading_state.claim_scores[].semantic_projection
dialogue_plan.semantic_trace
reading_surface.current_dialogue_turn.semantic_focus
```

当前覆盖：

- 十神：比肩、劫财、食神、伤官、正财、偏财、正官、七杀、正印、偏印。
- 宏观相：事业、财富、感情、亲情、身体健康、时机、隐藏属性。
- 健康五行关键词：木、火、土、金、水。
- 训练槽：`ten_god_to_macro_domain_weight`、`macro_domain_question_slot_weight`、`semantic_driver_claim_weight`、`hidden_factor_probe_slot_weight`。

验证：

- `central_reading_synthetic_validation.semantic_ontology_mapping`
- `tests/unit/test_presentation_projection.py`
- `tests/test_v30_scaffold.py`

### DBR-TRAIN-1 对话训练 Trace

状态：已完成第一版。

新增模块：

```text
v30/brain/dialogue_training.py
```

已接入：

```text
central_reading_state.dialogue_training_trace
```

训练内容：

- 当前对话动作：ask / conclude / continue。
- 当前问题和宏观领域。
- 语义训练槽。
- necessity、user_cost、overask_penalty、question_score 等决策特征。
- 用户反馈标签：positive_claim_ids / contradicted_claim_ids。

训练边界：

- 可训练：对话动作策略、问题选择策略、语义问题权重、隐藏属性探针权重、回答质量策略。
- 不可训练：四柱事实、历法换算、排盘事实、未确认隐藏属性事实。

验证：

- `central_reading_synthetic_validation.dialogue_training_trace`

### DBR-VIS-2 结果驱动可视化

状态：已完成第一版。

当前 visual hint 已经从 final synthesis 结构化结果生成：

```text
central_reading_state.final_synthesis.visual_hint
reading_surface.final_synthesis.visual_hint
frontend final-synthesis-visual
```

视觉类型：

```text
career_path_card
- 稳定承接 / 转型突破 / 职责上升

wealth_risk_meter
- 主动争取 / 保守积累 / 合作分配风险

relationship_pattern_loop
- 拉扯点 / 边界点 / 改善建议

hidden_signal_map
- 领域 / 年份 / 重复性 / 代价
```

要求：

- 每次只展示一个小视觉元素。
- 不占主信息流。
- 视觉元素必须来自中枢结构化结果，不从 LLM 文本硬猜。
- 不显示内部评分和工程字段。

当前字段：

```text
kind
title
chips
markers
guidance
boundary
```

当前 marker：

```text
结论强度
证据覆盖
反馈校准
```

## 本轮验证命令

```text
node --check frontend/app.js
python -m compileall v30/presentation/client_model.py
pytest tests/unit/test_presentation_projection.py -q
pytest tests/test_v30_scaffold.py -q
```
