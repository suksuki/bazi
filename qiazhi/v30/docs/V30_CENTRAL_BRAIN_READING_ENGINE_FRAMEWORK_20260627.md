# V30 中枢智能测算引擎框架

Updated: 2026-06-27

## 核心判断

V30 的核心不是把六柱排盘、规则、画像、特征、路径分别展示出来，而是把这些材料合成为一个可推演、可追问、可训练、可合成验证的读盘决策系统。

产品体验上，用户看到的是一步一步形成的结论和建议。系统内部必须有一个中枢智能大脑，负责判断：

- 当前八字最值得下的断语是什么。
- 哪些断语证据足够，哪些还只是候选。
- 哪个场景应该追问用户，哪个场景应该直接给结论。
- 用户回答后，哪些候选断语升权、降权或被阻断。
- 哪些行为可以进入训练，哪些绝对不能训练或改写。

这不是模板系统。模板只能把话说整齐，不能决定“该不该断、断到哪一层、下一问问什么”。

## 总架构

```text
六柱排盘 / 命盘事实
-> 特征抽取
-> 规则匹配
-> 画像投影
-> 做功路径
-> 时运激活
-> 用户反馈
-> 中枢证据图
-> 候选断语池
-> 主动追问策略
-> 最终结论与建议
-> 训练观测 / 合成验证
```

现有 V30 已经有不少底层材料：

- `v30.diagnosis.contracts` 已有 `DiagnosisGraph`、`DiagnosisClaim`、`DiagnosisPath`、`DiagnosisPortrait`。
- `v30.brain.orchestrator` 已有 `CentralBrainTrace`、`BrainState`、`QuestionDialogueStrategy`。
- `v30.questions.recommender` 已有多因子问题评分。
- `v30.reasoning.xuanming_model` 已有强弱、十神、结构、路径、用神候选等推理模型。
- `v30.presentation.thinking` 已经把每个阶段拆成用户可看的步骤。

缺的不是材料，而是一个统一的“读盘决策引擎”。

## 核心对象

### 1. CentralReadingState

中枢当前读盘状态。

```json
{
  "version": "v30.central_reading_state.v1",
  "reading_id": "...",
  "active_stage_id": "rule_matching",
  "user_goal": "overview",
  "known_context": ["birth_chart_bound", "rule_signals_ready"],
  "unknown_context": ["timing_activation", "domain_priority"],
  "top_claim_ids": [],
  "blocked_claim_ids": [],
  "next_action": "ask_stage_question",
  "training_observations": []
}
```

中枢状态只协调，不改写四柱、六柱、日主、月令、藏干等命盘事实。

### 2. Evidence Graph

所有材料进入一张统一证据图。

节点类型：

- `chart_fact`：六柱、日主、月令、藏干、十神显隐。
- `feature`：五行分布、强弱、十神角色、结构信号。
- `matched_rule`：命中的规则。
- `portrait`：画像投影。
- `path`：做功路径。
- `timing_activation`：大运流年是否激活原局路径。
- `user_feedback`：用户结构化回答。
- `claim`：候选断语。

边类型：

- `supports`
- `weakens`
- `blocks`
- `requires`
- `activates`
- `explains`
- `asks_followup`

这张图是“食材如何组合”的基础。

### 3. Candidate Claim Pool

每个候选断语都是一个可评分对象，而不是一段模板话。

```json
{
  "claim_id": "career.output_to_wealth",
  "level": "domain",
  "domain": "career",
  "text": "事业更适合通过表达、技术、作品或专业输出换取资源。",
  "support": ["食伤生财路径", "规则命中", "画像倾向"],
  "counter": ["时运未绑定", "用户领域优先级未知"],
  "confidence": 0.72,
  "actionability": 0.86,
  "requires_question": true
}
```

候选断语必须有来源，不能由 LLM 直接生成。

## 评分算法

### Claim Score

候选断语分数不应该只看单条规则强弱，而要看证据组合。

```text
claim_score =
  support_strength * 0.28
+ evidence_diversity * 0.18
+ path_coherence * 0.18
+ timing_activation * 0.12
+ user_feedback_alignment * 0.12
+ actionability * 0.08
- counter_evidence * 0.18
- missing_context_penalty * 0.14
- overclaim_risk * 0.20
```

解释：

- `support_strength`：规则、特征、路径、画像共同支持的力度。
- `evidence_diversity`：是否来自多个模块，而不是单条规则。
- `path_coherence`：做功路径是否能把规则和画像串起来。
- `timing_activation`：大运流年是否激活原局路径。
- `user_feedback_alignment`：用户回答是否支持该候选。
- `actionability`：能不能给出具体建议。
- `counter_evidence`：反证数量和强度。
- `missing_context_penalty`：缺少时运、领域、现实反馈等关键条件。
- `overclaim_risk`：是否容易说成绝对断语。

### Next Action Score

中枢每一页都可以决定下一步是给结论、追问、等待时运信息、还是进入下一页。

```text
next_action_score =
  user_value * 0.30
+ information_gain * 0.24
+ claim_impact * 0.18
+ uncertainty_reduction * 0.14
+ training_value * 0.08
- interaction_cost * 0.06
- overclaim_risk * 0.12
```

可选动作：

- `conclude_stage`：本页证据足够，直接给结论和建议。
- `ask_stage_question`：本页有高价值不确定点，插入智能追问。
- `ask_negative_evidence`：高分断语缺反证，需要问“是否不像你”。
- `request_timing_context`：判断需要大运流年。
- `continue_next_stage`：本页只是中间材料，进入下一页。
- `final_synthesis`：所有主线证据足够，生成总判断。

## 每页都可以问，但不是每页都必须问

用户的建议是对的：智能问答不应该只出现在最后。

每个分页面都有自己的追问机会：

| 页面 | 可追问的问题类型 | 目的 |
|---|---|---|
| 六柱排盘 | 出生时间、时区、是否看当前年份 | 防止时运和时柱误判 |
| 规则匹配 | 哪类规则最贴近现实表现 | 给规则候选升降权 |
| 特征抽取 | 表达、压力、资源、财务哪类更明显 | 校准十神角色 |
| 画像投影 | 哪个画像更像用户 | 校准画像和隐藏因素 |
| 做功路径 | 用户更像“输出换资源”还是“压力转资质” | 选择主路径 |
| 时运层 | 哪些年份变化明显 | 判断原局路径是否被激活 |
| 领域综合 | 事业、财富、关系、健康哪个最关心 | 排序最终输出 |

但中枢必须控制频率。追问只有在 `information_gain > interaction_cost` 时出现。

## LLM 的位置

LLM 不负责发明八字结论。

正确职责：

```text
中枢给出候选断语、证据、反证、建议方向
-> Gemma4 thinking 负责推演表达
-> 中枢清洗、裁决、合并
-> 用户看到结论和建议
```

LLM 可以帮助：

- 把中枢证据说得自然。
- 在页面等待时展示推演感。
- 生成用户可读的解释。

LLM 不可以：

- 改四柱、六柱、日主、月令。
- 直接创建候选断语事实。
- 跳过中枢评分给最终判断。
- 用模板替代证据合成。

## 可训练设计

训练目标不是“让模型背模板”，而是训练中枢权重和策略。

可训练：

- 规则权重。
- 路径权重。
- 画像权重。
- claim_score 参数。
- next_action_score 参数。
- 哪些页面适合追问。
- 用户回答后如何升权/降权。
- 表达层风格和精简度。

不可训练：

- 命盘事实。
- 日历换算。
- 四柱、六柱结果。
- 用户没有确认的隐藏因素。
- 没有验证的固定断语。

训练观测对象：

```json
{
  "state_snapshot_id": "...",
  "action": "ask_stage_question",
  "question_id": "...",
  "user_answer": "...",
  "claim_delta": {
    "career.output_to_wealth": 0.12,
    "career.authority_to_resource": -0.08
  },
  "accepted": true,
  "training_scope": ["question_policy", "claim_weight", "path_weight"]
}
```

## 合成验证设计

合成验证不是只看接口能不能跑，而是验证“中枢判断是否稳定”。

必须有这些 synthetic tiers：

1. `central_reading_claim_selection`
   - 同一命盘材料下，应该选中正确的高价值断语。

2. `stage_question_policy`
   - 缺时运时应追问时运，不应强断流年。
   - 画像冲突时应追问现实反馈，不应直接定性。

3. `negative_evidence_guard`
   - 高分但证据单一的断语，必须出现反证检查。

4. `same_bazi_divergent_feedback`
   - 同一八字，不同用户反馈，应产生不同画像/路径权重，但不改变命盘事实。

5. `final_synthesis_quality`
   - 总结必须以结论和建议为主，不能堆模块材料。

6. `llm_boundary`
   - LLM 输出不能新增未授权事实；中枢必须能清洗软话和模板话。

## 第一阶段实现建议

### CBRE-1 Central Reading State

新增：

```text
v30/brain/reading_engine.py
v30/brain/reading_contracts.py
```

输出：

```text
v30.central_reading_state.v1
v30.central_reading_action.v1
v30.central_claim_score.v1
```

先不做复杂机器学习，先把现有 diagnosis graph、reasoning model、thinking stages 接进统一状态。

### CBRE-2 Claim Scorer

把现有 `DiagnosisClaim` 统一打分，输出：

- top claims
- blocked claims
- needs-question claims
- final-ready claims

### CBRE-3 Stage Question Policy

每个页面输出一个可选问题：

```json
{
  "stage_id": "path_reasoning",
  "question": "这几年更明显的是靠表达/技术换资源，还是通过资质/平台承接压力？",
  "options": ["表达输出更明显", "资质平台更明显", "都不明显"],
  "target_claim_ids": ["career.output_to_wealth", "career.authority_to_resource"]
}
```

前端只在中枢认为有价值时显示，不固定每页都问。

### CBRE-4 Feedback Update

用户回答后，不直接改事实，只更新：

- claim weights
- path weights
- portrait alignment
- next question priority
- training observation

### CBRE-5 Final Synthesis

最后页面不再简单拼接各模块，而是：

```text
top claims
+ strongest path
+ most useful portrait
+ domain priority
+ timing status
+ unanswered high-value uncertainty
-> final conclusion
-> practical advice
-> next best question
```

## 产品原则

1. 用户只看结论和建议。
2. 中枢内部保留证据图、分数、反证和训练信号。
3. 每个页面可以问，但必须由中枢判断是否值得问。
4. LLM 是推演表达层，不是事实和断语来源。
5. 训练只调权重和策略，不改命盘事实。
6. 合成验证必须检查“判断行为”，不是只检查文案。

## 结论

V30 应该从“分页面测算展示”升级为“中枢读盘决策系统”。

最关键的框架级能力是：

```text
证据图建模
-> 候选断语评分
-> 主动追问策略
-> 用户反馈更新
-> 可训练权重
-> 合成验证
-> 最终结论和建议
```

这才是智能中枢大脑，而不是模板问答或 LLM 文案层。
