# V30 Dialogue System Cleanup Audit

Updated: 2026-06-27 second cleanup pass

## 结论

智能对话系统重构必须先清旧系统边界，再引入 Dialogue Brain。

当前不是没有能力，而是能力分散：

```text
v30/questions/anchor_selector.py
-> v30/questions/recommender.py
-> v30/questions/dag.py
-> v30/brain/reading_engine.py
-> v30/presentation/client_model.py
-> frontend/app.js
-> v30/interaction_brain.py
-> v30/hidden_factor/*
```

这些模块都在不同程度上参与“问什么、何时问、展示什么、用户回答如何更新状态”。这导致旧逻辑很容易残留在新 UI 中，出现问题池、幽灵追问、阶段和问答混杂、隐藏属性表单化等问题。

## 审计范围

本轮审计文件：

```text
v30/questions/anchor_selector.py
v30/questions/recommender.py
v30/questions/dag.py
v30/interaction_brain.py
v30/interaction_constraints.py
v30/brain/reading_engine.py
v30/hidden_factor/question_strategy.py
v30/presentation/client_model.py
frontend/app.js
frontend/styles.css
```

## 当前职责图

### 1. Anchor Selector

文件：

```text
v30/questions/anchor_selector.py
```

当前职责：

- 生成固定 anchors。
- 包括 career、wealth、relationship、timing、decision 五类用户问题。
- 包括 time context、useful god candidate、hidden factor、practical domain focus 等内部校准问题。

问题：

- 种子问题来源仍是固定 anchor 列表。
- 还没有从 ClaimPool 缺口动态生成问题。
- 宏观相和十神语义没有统一本体支撑。

处理策略：

```text
短期保留，作为 candidate source。
DBR-4 后降级为 fallback seed source。
新种子问题应来自 claim_gap + semantic_driver。
```

### 2. Question Recommender

文件：

```text
v30/questions/recommender.py
```

当前职责：

- 给 anchors 打分。
- 混合处理用户问题、隐藏属性、实用领域、模型信号、训练策略、上下文补全。
- 输出 `questions[]` 排序结果。

问题：

- 职责过重，已经接近“旧对话大脑”。
- 同时处理候选生成、策略评分、训练权重、隐藏属性、实用读盘。
- 和 `CentralReadingState.next_action`、`QuestionDialogueGraph.next_question_id` 存在决策重叠。
- 输出是列表，容易让前端或 presentation 又回到问题池。

处理策略：

```text
短期保留为 candidate scorer。
不再作为客户侧最终决策者。
DBR-6 后由 DialoguePlanner 选择唯一 current_dialogue_turn。
```

已完成第一版边界：

```text
recommend_questions() 输出已增加：
- candidate_source = question_recommender_candidate
- decision_owner = dialogue_brain
- boundary = question_recommender_outputs_candidates_dialogue_brain_selects_customer_turn
- semantic_projection
- question_score_components.semantic_weight_slot
```

### 3. Question Dialogue Graph

文件：

```text
v30/questions/dag.py
```

当前职责：

- 根据 `recommendations` 建图。
- 输出 `next_question_id` 和 `internal_next_question_id`。
- 处理 answered suppression 和 selected topic follow-up。

问题：

- 图谱仍在决定 next question。
- 与 `interaction_state.visible_next_question_id`、`CentralReadingState.next_question` 职责重叠。
- 适合作为关系和记忆图，不适合作为最终决策器。

处理策略：

```text
保留图谱和 answered 状态。
把 next_question_id 降级为 compatibility field。
新决策出口改为 DialogueBrainState.current_dialogue_turn。
```

已完成第一版边界：

```text
QuestionDialogueGraph 已增加：
- decision_owner = dialogue_brain
- customer_decision_field = reading_surface.current_dialogue_turn
- boundary = question_dialogue_graph_is_memory_relation_graph_not_customer_decision_owner
```

### 4. Central Reading Engine

文件：

```text
v30/brain/reading_engine.py
```

当前职责：

- 给 claim 打分。
- 根据 top claim 和 next question 选择 `next_action`。
- 输出 `stage_question_opportunities`。

优点：

- 已经有 claim scoring 雏形。
- 已经明确不改写 chart facts。
- 是 Dialogue Brain 的合适基础。

问题：

- 当前 `next_action` 仍依赖外部 next_question，而不是自己生成 current turn。
- `stage_question_opportunities` 只是把一个问题挂到页面，还不是完整对话回合。
- 没有十神/宏观相语义本体输入。
- 没有 user_cost、ghost_penalty、overask_penalty。

处理策略：

```text
保留并升级为 DialogueBrainState 的核心。
DBR-3 增加 current_dialogue_turn。
DBR-6 接管 ask/conclude/continue 决策。
```

已完成第一版边界：

```text
central_reading_state 已增加：
- dialogue_decision_owner = dialogue_brain
- customer_decision_field = reading_surface.current_dialogue_turn
- candidate_sources = question_recommender / question_dialogue_graph
- dialogue_plan
- current_turn_seed
- semantic_ontology
- dialogue_training_trace
- training_signal.targets += dialogue_turn_policy
```

已完成第一版架构拆分：

```text
v30/brain/dialogue_planner.py
- 输出 v30.dialogue_plan.v1
- 接管 action/current_question/stage_question_opportunities/current_turn_seed
- 暴露 decision_features 和 training_signal
```

### 5. Presentation Client Model

文件：

```text
v30/presentation/client_model.py
```

当前职责：

- 输出 `reading_surface.next_question`。
- 输出 `questions[]`。
- 输出 `dialogue`。
- 区分 customer/admin diagnostics。

问题：

- 客户投影里仍保留 `questions[]` 和 `next_question` 兼容字段。
- `_next_question_from_dialogue_plan()` 仍保留 graph/question list 兼容兜底。
- `questions[]` 不能直接删除，否则会破坏现有 API additive contract。

处理策略：

```text
保留 questions[] 作为兼容字段。
新增 current_dialogue_turn。
客户 UI 迁移到 current_dialogue_turn。
DBR-9 后客户侧不再消费 questions[]。
```

已完成第一版边界：

```text
reading_surface.current_dialogue_turn 已成为客户对话唯一出口。
presentation 优先读取 central_reading_state.dialogue_plan.current_question_id。
stage_id 和 target_claim_ids 优先来自 central_reading_state.current_turn_seed。
questions[] 和 next_question 仍保留为兼容字段。
projection_contract.dialogue_entry_policy 已声明 questions[] 是 fallback/diagnostics。
customer dialogue progress 已移除 candidate_count。
```

### 6. Frontend App

文件：

```text
frontend/app.js
frontend/styles.css
```

当前职责：

- 渲染阶段页。
- `renderStageInteractionSlot()` 显示回答和一个问题。
- `focusedQuestionForStage()` 从 stage opportunity / next_question / questions[] 里选问题。
- `stageScopedQuestions()` 用 topic hints 从问题列表筛选问题。

问题：

- UI 仍然会从 `questions[]` 辅助选题。
- `stageScopedQuestions()` 是前端越权决策残留。
- 隐藏属性 UI 已简化，但仍绑定 `hidden_factor` topic，而不是 current turn schema。
- local question turns 曾作为本地缓存，容易与后端权威状态混淆；2026-06-29 已删除。

已安全清理：

- 删除无调用函数 `stageDialogueProjection()`。
- 删除无调用函数 `renderQuestion()`。
- 删除无引用样式 `.question-dock`。
- 删除前端 `stageScopedQuestions()` / `stageQuestionTopicHints()` / `focusedQuestionForStage()`。
- 前端已切换为只从 `reading_surface.current_dialogue_turn` 渲染当前问题。
- 客户侧不再显示候选问题数量。
- `questions[]` 只作为兼容字段，不作为前端选择来源。
- 删除前端 `localQuestionTurns` / `v30.product.question_turns`，本轮问题标题只使用后端 `answer_panel.question_label`。

处理策略：

```text
短期保持现有 one-question UI。
current_dialogue_turn 已成为前端主入口。
下一步继续把 questions[] 降级为兼容字段。
localQuestionTurns 已移除。
```

### 7. Unified Interaction Brain

文件：

```text
v30/interaction_brain.py
v30/interaction_constraints.py
```

当前职责：

- 校验 structured payload。
- 生成 hidden factor feedback payload。
- 阻止 chart fact mutation。

优点：

- 边界清楚。
- 是 SignalUpdater 的基础。

问题：

- 目前只处理反馈路由，不负责 DialogueBrainState 更新。
- hidden factor payload 仍偏事件/状态，没有后验模型。

处理策略：

```text
保留为 SignalUpdater 的底层输入校验。
DBR-5 后接入 hidden_factor_belief posterior update。
```

### 8. Hidden Factor Strategy

文件：

```text
v30/hidden_factor/question_strategy.py
v30/hidden_factor/state.py
v30/hidden_factor/attributes.py
```

当前职责：

- 判断 hidden attribute 是否需要提问。
- 根据状态、跳过次数、候选领域给出问题提示。
- 维护 persisted hidden factor state。

问题：

- 仍像独立隐藏属性问卷策略。
- 与普通智能问答没有完全统一。
- 问题链不是从当前 claim impact 和 posterior entropy reduction 生成。

处理策略：

```text
保留状态和边界。
把 need_strategy 收编到 DialoguePlanner。
隐藏属性问题只作为 drill_hidden action 出现。
```

## 清理分级

### A. 已完成的安全清理

```text
frontend/app.js
- remove unused stageDialogueProjection()
- remove unused renderQuestion()
- remove focusedQuestionForStage()
- remove stageScopedQuestions()
- remove stageQuestionTopicHints()

frontend/styles.css
- remove unused .question-dock styles
```

验证：

```text
node --check frontend/app.js
```

### B. 下一步可清理，但需要继续迁移调用方

```text
v30/presentation/client_model.py
- _next_question_from_dialogue_plan() 的 graph/question list 兜底
- reading_surface.next_question 兼容字段
- top-level questions[] 客户兼容字段

frontend/app.js
- localQuestionTurns 已从状态源和展示缓存中删除
```

清理条件：

```text
mobile/web/admin projection tests no longer require top-level questions[] for user role
answer submit path can resolve question_id from current_dialogue_turn only
admin/practitioner diagnostics have separate candidate endpoint
```

### B2. 本轮已清理的命名和边界

```text
legacy_question_recommender -> question_recommender_candidate
legacy_candidate_sources -> candidate_sources
_next_question_from_graph() -> _next_question_from_dialogue_plan()
dialogue.progress.candidate_count removed from customer projection
answerQuestionLabel() no longer reads questions[] or reading_surface.next_question
answer API next_question_id now mirrors reading_surface.current_dialogue_turn.question
projection_contract.dialogue_entry_policy.answer_submit_source = reading_surface.current_dialogue_turn.question
```

### C. 不能直接删，必须迁移

```text
v30/questions/recommender.py
v30/questions/dag.py
v30/hidden_factor/question_strategy.py
```

原因：

- 现有 tests 和 runtime 仍依赖。
- 它们提供 candidate source、answered suppression、hidden state guardrails。

迁移目标：

```text
recommender -> candidate scorer
dag -> memory/relation graph
hidden_factor/question_strategy -> drill_hidden candidate provider
```

### D. 保留并强化

```text
v30/brain/reading_engine.py
v30/interaction_constraints.py
v30/interaction_brain.py
v30/hidden_factor/state.py
```

原因：

- 已经有不改写 chart facts 的边界。
- 可直接升级为 Dialogue Brain 的骨架。

## 新旧边界

旧系统出口：

```text
questions[]
reading_surface.next_question
question_dialogue_graph.next_question_id
stage_question_opportunities
```

新系统出口：

```text
dialogue_brain_state.current_dialogue_turn
```

兼容期：

```text
current_dialogue_turn 优先
next_question 兼容
questions[] 仅 admin/diagnostic 或 fallback
```

最终目标：

```text
客户 UI 永远只渲染 current_dialogue_turn。
前端不再从问题池、topic hints、rows[0] 选择问题。
```

## 第一批重构任务

### CLEAN-1 当前模块职责测试

新增测试，锁定客户侧只允许一个当前问题：

```text
view.current_dialogue_turn exists
view.questions[] can exist but frontend/customer projection does not rely on it
current_dialogue_turn.target_claim_ids is non-empty when action=ask
```

### CLEAN-2 current_dialogue_turn 投影

在 `client_model.py` 增加客户安全投影：

```text
current_dialogue_turn
  action
  stage_id
  question
  why_now
  target_claim_ids
  answer_constraints
  ui_policy
```

### CLEAN-3 前端切换到单一回合

前端优先渲染：

```text
reading_surface.current_dialogue_turn
```

然后删除：

```text
stageScopedQuestions()
stageQuestionTopicHints()
questions[] fallback selection
```

### CLEAN-4 recommender 降级

`recommend_questions()` 继续产出候选，但不再作为最终客户选择。

新增字段：

```text
candidate_source = question_recommender_candidate
decision_owner = dialogue_brain
```

### CLEAN-5 graph 降级

`QuestionDialogueGraph.next_question_id` 保留兼容，但客户面不直接使用。

新增边界：

```text
question_dialogue_graph_is_memory_not_customer_decision_owner
```

### CLEAN-6 hidden factor 收编

隐藏属性不再作为独立问卷策略，而是：

```text
DialoguePlanner action=drill_hidden
```

问题必须绑定：

```text
target_claim_ids
posterior_uncertainty
semantic_driver
```

### CLEAN-7 删除旧 UI 和字段泄漏

删除或隐藏：

```text
candidate_count from customer dialogue ✅
diagnostic wording in customer answer
question list based rendering
legacy local-only question memory as source of truth
```

## 风险

1. 直接删除 `questions[]` 会破坏现有 API 和测试。
2. 直接删除 recommender 会丢失训练权重和 policy consumption。
3. 直接删除 graph 会丢失 answered suppression。
4. 直接删除 hidden factor strategy 会丢失跳过冷却和边界保护。

因此第一阶段只清客户侧旧入口和无调用代码。后端旧模块要迁移，不做硬删。

## 当前状态

```text
DBR cleanup audit: complete
safe frontend cleanup: complete
current_dialogue_turn projection: first version complete
frontend current_dialogue_turn rendering: first version complete
semantic ontology: first version complete
dialogue training trace: first version complete
questions[] fallback contract: first version complete
next required implementation: remove remaining compatibility fallback after answer path is fully current_turn based
second cleanup pass: answer submit path is current_turn based
```
