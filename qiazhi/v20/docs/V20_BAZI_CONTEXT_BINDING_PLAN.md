# V20 八字上下文绑定主线计划

更新时间：2026-05-20

## 核心问题

所有模块必须围绕当前被测算八字运行：

```text
原局四柱
+ 大运
+ 流年
+ 流月
```

画像、结构动态、智能问题、规则、知识库、LLM 上下文、训练参数都不能脱离这个事实锚点。角色只改变可见范围、表达密度和问题节奏，不改变命盘事实和推理结果。

## 统一上下文

新增系统级合同：

```text
BaziContextFrame
```

职责：

```text
1. 生成当前测算唯一 context_id
2. 固定当前原局四柱、大运、流年、流月
3. 明确所有模块的事实来源
4. 给 UI、训练、LLM 提供漂移检测锚点
```

当前字段：

```text
context_id
natal_pillars
day_master
day_master_element
time_context_status
time_layers
time_relation_count
binding_policy
```

## 分层原则

```text
事实层：chart_facts + time_context
推理层：feature_state + rule + portrait + structure_dynamics + question_intent
表达层：UI + role_view + answer + LLM context
训练层：只调权重、阈值、排序、上下文密度，不改事实
```

## 漂移约束

每个关键模块必须有 `context_binding`：

```text
context_id
module_key
anchor_scope
natal_pillars
time_layers
evidence_domains
feature_ids
time_sensitive
drift_policy
evidence_anchor_count
evidence_anchors
```

如果模块输出不能绑定当前 `context_id`，后续训练和 UI 应降权、隐藏或标记为漂移风险。

## 当前已接入

```text
runtime_result.bazi_context_frame
runtime_result.context_alignment_report
training_plan.candidate_quality_signal.quality_scores.bazi_context_drift_score
training_plan.central_brain_tuning_package.context_drift_score
training_task.result_summary.context_quality_signal
structure_dynamics.context_binding
decision_report.portrait_projection.context_binding
question_intent_model.context_binding
question_context_binding
llm_assist.context_pack.context_binding
role_view_model.context_binding
role_view_model.portrait_profile.context_binding
role_view_model.question_profile.context_binding
Workbench UI 八字上下文面板
```

## 智能问题绑定升级

2026-05-20 新增 `BaziQuestionAnchor` 作为智能问题的 per-question 绑定合同。`question_intent_model.context_binding` 只能证明“问题模块绑定了当前盘”，不能证明“每一个展示问题都绑定了当前盘”。因此问题系统必须在每个候选问题上生成独立锚点。

新增要求：

```text
questions[].question_anchor.context_id == bazi_context_frame.context_id
questions[].question_anchor.day_master == bazi_context_frame.day_master
questions[].question_anchor.anchor_status == bound
questions[].display_title 由 question_anchor 渲染
selected_question_anchor 进入 LLM 上下文
```

禁止：

```text
QuestionAtom.template_zh 直接作为普通用户最终问题
KnowledgeUnit.question_seeds 直接作为普通用户最终问题
缺大运/流年时展示 timing 问题
缺 primary_dynamic_chain 时展示结构闭合问题
```

## 下一步

```text
1. 实施 BaziQuestionAnchor builder 和角色化 display question renderer
2. Admin 训练页展示“本次训练是否继承当前八字上下文”
3. 预留 geo_context，但必须作为 BaziContextFrame 扩展字段
```

## 验收标准

```text
结构动态只能来自当前八字和时间层
画像只能来自当前规则/特征/裁决
智能问题只能来自当前证据缺口和主线
智能问题每个展示项都必须有 per-question anchor
LLM 只能消费锁定后的上下文包
所有关键输出共享同一个 context_id
UI 能看到当前命盘、岁运、模块绑定数量和偏离分数
训练质量信号能看到 bazi_context_drift_score
训练结果摘要能看到 context_quality_signal
关键模块 context_binding 能看到 evidence_anchors
```
