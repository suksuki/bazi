# V20 角色化问题叙事与 LLM 提示词框架

状态：已并入主线并完成 runtime 消费。框架合同、问题叙事 schema、角色视图 voice profile、问题卡 UI、LLM answer prompt profile 和合成回放质量检查已落地。

机器入口：

```text
role_view/narrative_prompt_framework.py
```

LLM prompt/context 设计：

```text
docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md
```

## 目标

把问题链路和 LLM 回复提示词统一到同一套角色 voice profile。

```text
八字结构结果
-> 中枢主线
-> 角色视图
-> 问题叙事
-> LLM 提示词
-> 角色化回复
-> 回答治理
-> 合成验证与训练
```

## Voice Profile

| Profile | 角色 | 叙事 |
|---|---|---|
| `guest_soft_entry` | 游客 | 少术语，先给你抓住重点 |
| `user_guided_reading` | 普通用户 | 本次阅读主线，解释为什么现在问 |
| `practitioner_evidence_review` | 命理师 | 证据、边界、反证、复核链路 |
| `admin_runtime_observe` | 管理员/观测 | 来源、策略、runtime pointer、gate |

## Question Narrative

问题不再只是一句 `title`，而是角色化包装。

```text
question_key / domain / rank 保持结构化
question_narrative 负责展示和语气
```

Schema:

```text
role_key
voice_profile
title
why_now
bazi_basis
boundary
next_step
tone_guardrails
```

## Answer Prompt Profile

LLM 回复提示词不直接散落在 prompt 字符串里，而是从角色 profile 生成。

Schema:

```text
role_key
voice_profile
system_style
answer_structure
forbidden_patterns
required_elements
locale_policy
```

实际 runtime 中，`answer_prompt_profile` 会进入 `answer_contract`，而不是被展开成一长串重复提示词。LLM 主要读取 `context.system_understanding` 中的 role_context、bazi_context_profile、chart、rules、features、portrait、brain-state 和 knowledge domains。

## 角色提示词原则

游客：

```text
少术语，短句，不制造压力。
先告诉用户可以从哪里看。
禁止绝对断语和吓人表达。
```

普通用户：

```text
用“你”来解释当前主线。
必须说明为什么现在问这个问题。
把命理依据翻译成生活主题。
```

命理师：

```text
保留官杀、印星、日主承载、冲合、岁运等术语。
必须说明证据、边界、反证条件。
候选不能说成结论。
```

管理员/观测：

```text
面向系统观测。
必须说明来源、策略、排序、runtime pointer 或 gate。
不输出用户命理解读。
```

## 合成验证

```text
guest: no_dense_jargon, soft_next_step, no_absolute_prediction
user: has_why_now, has_plain_bazi_basis, has_next_step
practitioner: has_evidence, has_boundary, has_counterexample_condition
admin: has_source, has_policy, has_runtime_or_gate
all_roles: no_fatalism, no_private_inference, no_internal_ids_in_user_view
```

## 训练专题

```text
role_question_narrative_training
answer_prompt_profile_training
```

调参目标：

```text
voice_profile_weight
why_now_density
term_density_by_role
next_step_presence
forbidden_phrase_penalty
answer_structure_weight
role_prompt_tone
evidence_boundary_density
llm_forbidden_pattern_penalty
```

生效目标：

```text
role_view_runtime_policy_pointer
question_runtime_policy_pointer
knowledge_runtime_policy_pointer
```

## 主线步骤

```text
S1 define_framework_contract: completed
S2 add_question_narrative_schema: completed
S3 attach_voice_profile_to_role_view_model: completed
S4 llm_prompt_reads_answer_prompt_profile: completed
S5 ui_consumes_question_narrative: completed
S6 synthetic_voice_replay_validates_tone: completed
S7 role_question_narrative_training_auto_applies: completed
```

## Runtime 消费点

```text
role_view_model.question_profile.voice_profile
questions[].question_narrative
llm.practitioner_answer_prompt.answer_prompt_profile
llm.practitioner_answer_prompt.context.system_understanding
llm.practitioner_answer_prompt.context.system_understanding.role_context
llm.practitioner_answer_prompt.context.system_understanding.bazi_context_profile
llm.practitioner_answer_prompt.answer_contract
synthetic_replay.role_views[].question_narrative_quality
```

原则：训练结果不进入人工审核 gate；可用的 voice profile 和 prompt profile 由 runtime 直接消费，合成回放只负责发现缺口。
