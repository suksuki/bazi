# V20 LLM 提示词与上下文设计

状态：已并入主线，目标是让 LLM 拿到准确的系统理解，而不是用冗长提示词反复约束。

## 原则

```text
Prompt 负责任务、结构和边界。
Context 负责提供系统已经确认的八字理解。
LLM 负责自然语言整合表达。
```

提示词保持短、清楚、可执行。不要把同一条禁令写多遍，也不要用模板把 LLM 管死。

## Prompt 结构

```text
task
locale
prompt_profile
answer_prompt_profile
answer_contract
context
instruction
```

其中 `instruction` 只保留核心任务：

```text
用已验证上下文作材料，以命理师身份回答当前问题；先直接回答，再说明最强证据和边界；不外推新事实。
```

## Context 结构

`context.system_understanding` 是给 LLM 的案头材料，只放不会在顶层重复展开的系统理解。

```text
role_context: 当前角色的信息密度、关注点、语气 profile
bazi_context_profile: 当前八字的结构模式、活跃领域、时间层状态
mainline_rules: 已触发规则信号、支持、削弱、条件原子
feature_states: 八字特征状态
portrait_axes: 八字画像轴
knowledge_domains: 知识库领域摘要
answer_policy: 冲突时优先中枢/主线，并保留边界
```

`chart`、`time`、`brain_state`、`mainline`、`portrait_tags`、`evidence` 放在顶层 context。这样 LLM 能直接读取当前盘材料，同时避免同一份事实在多个字段里重复出现。

当前预算：

```text
practitioner_answer target <= 8500 chars
practitioner_answer hard test <= 9000 chars
practitioner streaming payload hard test <= 7800 chars
answer_rewrite target <= 6500 chars
```

`context.context_budget` 进入 runtime prompt，作为后续训练调参的直接目标。

流式回答不会把完整 prompt 对象原样发给 Ollama。`llm.client._plain_text_messages` 会生成更窄的纯回答卡，只保留：

```text
task
locale
required_output
answer_contract
context
instruction
```

不发送 `prompt_profile`、`answer_prompt_profile`、`output_schema` 等只对结构化调用有用的外壳字段。

这部分只放系统可产生、可验证、可压缩的信息，不放内部 debug 文本。

## 角色与八字差异放在 Context

不同角色、不同八字，不靠 prompt 反复说明，而靠 context 给 LLM 明确案头材料。

`role_context`：

```text
guest: plain_entry，关注先看什么、软边界、下一步
user: guided_plain_language，关注直接回答、为什么重要、八字依据、下一步
analyst/practitioner: practitioner_evidence_review，关注证据、边界、反证条件、复核
admin/lab: runtime_observation，关注来源、策略、runtime pointer、blocker
```

`bazi_context_profile`：

```text
selected_domain: 当前问题领域
active_domains: 当前盘被中枢、规则、特征共同激活的领域
has_time_context: 是否有大运/流年/流月触发
structure_mode:
  core_bazi_structure
  applied_domain_structure
  time_triggered_structure
  general_structure
```

LLM 应根据这些 context 调整表达重点。例如时间层触发的盘，先说明原局与岁运触发的关系；财运/事业等应用主题，先回到承载力、十神和结构主线；游客视图降低术语密度，命理师视图保留证据和反证。

## Answer Contract

`answer_contract` 是给 LLM 的轻量输出合同。

```text
voice_profile
structure
required
forbidden
locale_policy
length_limit
output
```

它告诉 LLM 该按什么口吻和结构回答，但不写成一整篇模板。

## 放权边界

允许 LLM：

```text
综合和排序已提供证据
把术语转成自然语言
选择更顺的叙事顺序
用命理师口吻解释结构
```

不允许 LLM：

```text
编造经历
把候选当结论
输出内部 ID / debug / rule key
绕开证据边界
做医疗、灾祸、死亡等高风险断言
```

## Runtime 消费点

```text
llm.prompts.practitioner_answer_prompt
context.system_understanding
context.context_budget
answer_prompt_profile
answer_contract
questions[].question_narrative
answer_plan_rewrite.context.v2
```

这条链路不走人工审核 gate。合成回放和安全校验负责发现缺口，runtime 直接消费稳定字段。

流式回答完成后会附带 `answer_governance_quality`，作为训练和观测信号；它不阻断回答、不改写回答、不写 runtime pointer。

流式质量信号会以 append-only ledger 写入 `llm_stream_answer_quality`。记录只包含质量分、维度、角色和预算摘要，不保存原始回答文本。`answer_governance_training` 会读取该 ledger 或合成 replay 里的 `stream_answer_governance_summary`，产出：

```text
prompt_context_budget_weight
stream_answer_quality_weight
```

这两个参数目标进入 role-view runtime pointer 的 answer governance policy，用于直接影响后续 LLM 上下文预算和角色回答策略，不走人工审核。

## 训练专题

LLM 上下文不是单独造一个空脚本，而是作为中枢大脑的正式训练专题，复用已经能产生训练信号的原子训练。

```text
topic_key: llm_context
brain_node: llm_context_policy_generation
atomic_trainings:
  - answer_governance_training
  - role_interaction_training
  - synthetic_case_suite
  - training_iteration_fast
parameter_targets:
  - role_context_density_weight
  - bazi_context_profile_weight
  - answer_contract_structure_weight
  - prompt_context_budget_weight
  - stream_answer_quality_weight
runtime_pointer_targets:
  - role_view_runtime_policy_pointer
  - knowledge_runtime_policy_pointer
  - orchestrator_runtime_policy_pointer
```

训练目标是让系统持续调优“给 LLM 什么上下文”，而不是让 prompt 越写越长。中枢只提供准确信号：角色、八字结构、规则画像证据、知识边界和回答合同；LLM 负责自然组织表达。

## 遗留上下文清理

`answer_plan_rewrite` 保留任务名用于兼容，但不再使用旧的 `answer/prompt_context.py`。新流程直接消费：

```text
verified_answer_text
brain_state
answer_sections
domain_boundary
evidence_summary
answer_contract
```

这让 rewrite 和 practitioner answer 使用同一套原则：短 prompt、结构化 context、明确边界。
