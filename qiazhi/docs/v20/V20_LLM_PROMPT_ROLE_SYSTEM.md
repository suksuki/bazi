# V20 LLM Prompt Role System

V20 的 LLM 不做排盘、不裁决规则、不生成命理事实。LLM 承担的是角色化辅助：

```text
Intent Router
-> Question Designer
-> Feature Gap Assistant
-> Rule Drafter
-> Answer Rewriter
-> Practitioner Answer
-> Safety Reviewer
```

## 角色分工

| Role | Prompt Profile | Runtime Responsibility |
| --- | --- | --- |
| `intent_router` | `bazi_question_router` | 理解用户问题，路由到已有主题和问题候选 |
| `question_designer` | `bazi_followup_question_designer` | 只从已有问题候选中生成追问建议 |
| `feature_assistant` | `bazi_feature_gap_assistant` | 提出证据缺口，不写入 runtime feature |
| `rule_drafter` | `bazi_knowledge_rule_drafter` | 从已审核知识中抽取规则草案，不激活规则 |
| `answer_rewriter` | `plain_language_bazi_editor` | 改写确定性答案，不新增事实 |
| `practitioner` | `professional_bazi_practitioner` | 像命理师一样，用白话回答用户问题 |
| `safety_reviewer` | `bazi_answer_safety_reviewer` | 检查固定吉凶、无证据断语、隐私推断和内部标识泄露 |

## 对话回答 Prompt

对话回答不再把厚重内部图谱直接塞给 LLM，而是给它最需要的材料：

```text
selected_question
八字基础元数据: 四柱、日主、显性十神、藏干十神、时间层
key_features
rule_decisions
portrait_projection
question_intent
interaction_session
knowledge_semantic_domains
verified_fallback_answer
```

LLM 可以做：

```text
组织主线
白话解释
选择证据顺序
生成自然追问
按 locale 输出中文 / English / 한국어
```

LLM 不可以做：

```text
生成 ChartFacts
修改规则
裁决格局真伪
新增事件或私生活推断
保证结果
绕过 deterministic validator
```

## 多语言

每个 prompt 都带 `prompt_profile.language_instruction`：

```text
zh -> 中文白话文
en -> English, with readable Bazi terms
ko -> 한국어, with easy explanations
```

最终回答仍需通过 deterministic safety review。
