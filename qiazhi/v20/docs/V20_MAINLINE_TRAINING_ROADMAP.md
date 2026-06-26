# V20 主线训练推进计划

更新时间：2026-05-15

当前知识库与中枢大脑的专项主线见：

```text
docs/V20_KNOWLEDGE_BRAIN_MAINLINE.md
docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md
docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md
```

## 总原则

V20 的训练不是人工审核流程，也不是多跑几个脚本。
主线目标是让每一次训练都能经过机器验证，直接优化系统参数，并被 runtime 真正消费。

```text
训练专题
-> 原子训练脚本
-> 合成数据 / 回放验证
-> 参数候选
-> 机器 gate
-> active pointer
-> runtime 消费
-> Admin 可观测
```

不保留人工 accept/reject/defer 审核链路。
训练结果只有两种状态：

1. 通过机器 gate，自动生效。
2. 未通过机器 gate，阻塞并显示原因，runtime 不变。

## 当前完成度

| 维度 | 当前状态 | 完成度 |
|---|---|---:|
| 训练专题和原子脚本归类 | 六大专题已归类 | 100% |
| optimizer writer 就绪 | portrait、rule、knowledge、question、corpus、role_view、orchestrator 已有 writer/pointer | 100% |
| Admin 自我训练 UI | 任务、参数、gate、直接生效、计划、进度、暂停、日志、中枢 BrainGraph 编排已对齐 | 100% |
| runtime 参数消费审计 | 7 个 pointer family 已纳入审计，7 个确认被 runtime 消费 | 100% |
| 主线剩余重点 | runtime consumer 闭环已完成，下一步扩容合成 gate 和 518K shard replay | 已闭环 |

当前真实完成口径：

```text
writer readiness: 100%
runtime consumption: 7 / 7 = 100%
remaining runtime consumers: none
admin BrainGraph task map: ready
training bundle writer fan-out: ready
candidate quality signal: ready
candidate promotion score: ready
```

## 候选质量信号

Admin 训练计划现在把合成八字覆盖和 518K 回放 artifact 合并成 `candidate_quality_signal`。

它不写 runtime pointer，只负责告诉中枢：

```text
synthetic_gap_count: 合成验证还缺多少边界
corpus_training_status: 518K 回放训练 artifact 是否 ready
gate_blockers: 当前候选参数为什么可能被 machine gate 阻断
recommended_tasks: 下一步应该跑哪些原子训练
quality_scores: 合成验证和 518K 回放的标准化评分
candidate_promotion_score: 是否推进候选参数的总分
bazi_context_drift_score: 是否偏离当前八字上下文
central_brain_tuning_package: 中枢把八字上下文、合成验证和 518K 回放合并成统一调参决策
training_groups: 每个训练专题拆成原子训练组、参数目标和 runtime pointer 生效目标
```

第一版评分模型：

```text
synthetic_pass_rate: 合成边界覆盖通过率
rule_false_positive_rate: 规则误触风险，越低越好
portrait_drift_score: 画像漂移风险，越低越好
question_focus_score: 智能问题是否聚焦主线
corpus_distribution_shift: 518K 分布偏移风险，越低越好
similar_case_stability: 相似案例检索稳定性
candidate_promotion_score: 上述指标加权后的候选推进分
promotion_threshold: 0.82
```

当前策略：

```text
合成覆盖不足 -> synthetic_case_suite / rule_synthetic_training
518K 回放不足 -> nightly_executor_skeleton / full_precompute_preview
两者都 ready 且 candidate_promotion_score >= 0.82 -> 候选参数更容易直接进入 candidate_active
```

## 七大训练专题

| 专题 | 面向角色 | 原子训练 | 主要调优参数 | 合成验证重点 | 当前状态 |
|---|---|---|---|---|---|
| 画像训练 | guest, user, practitioner, admin | `rule_portrait_batch`, `dynamic_decision_training`, `practitioner_calibration_training` | 画像轴权重、置信阈值、角色深度、主题投影 | 画像贴合、反例边界、角色区分 | runtime consumed |
| 规则训练 | practitioner, admin | `rule_synthetic_training`, `rule_subcondition_split`, `rule_replay_eval`, `decision_registry_iteration` | 规则权重、子条件阈值、反例惩罚、registry priority | 命中率、误触发、反例 replay | runtime consumed |
| 知识库训练 | practitioner, admin | `knowledge_rule_review_overlay`, `extract_rules_llm_draft`, `training_iteration_deep` | 知识-规则映射、来源信任、答案边界、反例覆盖 | 知识对齐、可追踪、禁止越界 | runtime consumed |
| 智能问答训练 | guest, user, practitioner, admin | `question_source_training`, `question_ranking_training`, `question_dag_training`, `training_iteration_fast` | 问题来源权重、排序权重、DAG 转移、主线聚焦 | 问题聚焦、链路连贯、角色不泄露 | runtime consumed |
| 角色体验训练 | guest, user, practitioner, admin | `role_interaction_training`, `question_dag_training`, `synthetic_case_suite` | 角色排序、可见深度、问题数量、seed-fit | 角色隔离、点击反馈、体验路径 | runtime consumed |
| LLM 上下文训练 | guest, user, practitioner, admin | `answer_governance_training`, `role_interaction_training`, `synthetic_case_suite`, `training_iteration_fast` | 角色上下文密度、八字上下文权重、回答结构约束、上下文预算 | 角色贴合、八字结构模式、回答合同、prompt budget | runtime consumed |
| 特征语料训练 | admin | `nightly_executor_skeleton`, `full_precompute_preview`, `training_iteration_deep` | 特征阈值、覆盖先验、相似案例权重、分片质量 | 518K 分布、核心特征、负例边界 | runtime consumed |

## 测算页叙事展示

八字画像、八字特征、角色阅读和智能问答链路已进入测算页 `readingProgressPanel`。

当前完成度口径：

| 链路 | Runtime 来源 | UI 展示 | 完成度 |
|---|---|---|---:|
| 八字特征 | `feature_state_model` | 阅读进度：八字特征 | 100% |
| 八字画像 | `decision_report.portrait_projection` + `role_view_model.portrait_profile` | 阅读进度：八字画像、角色画像 | 100% |
| 角色阅读 | `role_view_model` | 游客/用户/命理师/管理员不同叙事口吻 | 100% |
| 智能问答 | `questions` + `role_view_model.question_profile` + `question_intent_model` | 阅读进度：智能问答、问题分组 | 100% |
| 问题叙事与 LLM 提示词 | `role_question_narrative_prompt_framework` + `questions[].question_narrative` + `answer_prompt_profile` + `context.system_understanding` | 问题卡展示 why_now / next_step，LLM prompt 消费系统理解和角色 voice profile | 100% |

UI 叙事原则：

```text
游客：少术语，先告诉“先看什么”
普通用户：围绕“本次阅读主线”说明特征、画像和问题
命理师：强调“校准链路、证据边界、主题候选”
管理员/观测：强调“运行闭环、runtime pointer、排序稳定性”
```

## 角色化问题叙事与 LLM 提示词

主文档：

```text
docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md
```

目标是让问题链路、LLM 回复提示词、回答治理和训练使用同一套 voice profile。

```text
guest_soft_entry
user_guided_reading
practitioner_evidence_review
admin_runtime_observe
```

当前状态：

```text
framework contract: ready
question_narrative_schema: completed
role_view voice_profile consumption: completed
answer_prompt_profile_schema: runtime consumed
llm_context_design: compact system_understanding + role_context + bazi_context_profile + context_budget + answer_contract consumed
legacy_prompt_context: removed; answer_plan_rewrite uses context.v2
ui consumption: completed for question cards
synthetic voice replay: completed
runtime pointer auto apply: direct runtime consumption, no human review gate
```

当前 LLM 主线预算：

```text
practitioner_answer prompt target: <= 8500 chars
practitioner_answer test ceiling: < 9000 chars
上下文优先级: brain_state -> mainline -> evidence -> portrait_tags -> boundary
stream answer quality: 写入 llm_stream_answer_quality ledger，不保存原始回答
direct parameter targets: prompt_context_budget_weight + stream_answer_quality_weight
```

## Runtime 消费计划

训练是否有效，以 active pointer 是否被 runtime 消费为准。

| Pointer Family | 当前消费状态 | 下一步 |
|---|---|---|
| orchestrator | consumed | 保持审计和回滚 |
| role_view | consumed | 保持审计和回滚 |
| question | consumed | 扩大合成 replay 批量 |
| corpus | consumed | 扩大相似案例分布验证 |
| rule | consumed | 已接入 `rules.engine`，输出 `policy_effect.rule_policy` 并影响规则运行分 |
| portrait | consumed | 已接入 `interaction.portrait_projection`，输出 `policy_effect.portrait_policy` 并影响画像轴排序 |
| knowledge | consumed | 已接入 `decision.knowledge_bridge`，输出 `policy_effect.knowledge_policy` 并影响知识映射优先级 |

完成标准：

```text
7 pointer families consumed / 7 pointer families audited
Admin runtime 参数消费审计显示 complete
```

## Admin UI 对齐计划

Admin 训练页只保留对主线有用的信息：

1. 每个训练专题的作用、脚本、参数、gate、writer、runtime consumer。
2. 后台任务进度、暂停、日志、最近任务结果。
3. 是否直接优化参数。
4. active pointer / candidate pointer / blocking gate。
5. runtime 参数消费审计。
6. 去掉人工审核型页面和无主线价值页面。

当前已经对齐：

```text
自我训练任务
训练计划
机器优化 gate
直接生效状态
激活历史
重复训练 cooldown
runtime 参数消费审计
```

## 下一步执行顺序

### P1: Rule Runtime Consumer

状态：2026-05-15 已完成。

目标：规则训练通过 gate 后，直接影响 runtime 规则权重、子条件阈值和反例惩罚。

交付：

1. runtime 读取 rule active pointer。已完成。
2. decision/rule engine 输出 `policy_effect.rule_policy`。已完成。
3. Admin 审计从 `rule: needs_consumer` 变为 `rule: consumed`。已完成。
4. 合成八字 replay 覆盖规则误触发和漏触发。待扩容。

### P2: Portrait Runtime Consumer

状态：2026-05-15 已完成。

目标：画像训练通过 gate 后，直接影响画像轴权重、主题排序和角色展示深度。

交付：

1. runtime 读取 portrait active pointer。已完成。
2. portrait projection 输出 `policy_effect.portrait_policy`。已完成。
3. guest/user/practitioner 三类角色展示继续通过 role view 降维消费。已对齐。
4. 合成案例验证画像不过度断语、不套标签。待扩容。

### P3: Knowledge Runtime Consumer

状态：2026-05-15 已完成。

目标：知识库训练通过 gate 后，直接影响知识桥、规则映射优先级和答案边界。

交付：

1. runtime 读取 knowledge active pointer。已完成。
2. knowledge bridge 输出 `policy_effect.knowledge_policy`。已完成。
3. 知识引用和规则命中保持可追踪。已完成。
4. 合成案例验证知识不覆盖命理主线。待扩容。

### P4: Gate 扩容

目标：把 smoke gate 扩到可持续的合成批量验证。

交付：

1. 每个专题至少一组 synthetic replay suite。
2. 每个 suite 包含正例、反例、边界例、metamorphic pair。
3. gate 结果进入 Admin 训练任务详情。
4. 重复训练基于 artifact hash / ledger cursor，而不是只靠 cooldown。

## 近期主线完成定义

下一阶段不是继续堆训练脚本，而是扩容每个 consumer 背后的合成 replay gate。

```text
当前阶段目标:
rule consumed
portrait consumed
knowledge consumed

完成后:
runtime consumption = 7 / 7 = 100%
训练才真正变成系统参数优化闭环
```
