# V30 中枢智能大脑 V2 主线任务

更新时间：2026-06-29

## 目的

本文合并两轮讨论结论：

- 当前中枢智能大脑深度 review。
- 适合 V30 八字测算系统的建模、算法、框架建议。

从本文件开始，中枢智能大脑的主线不再是“页面小结更像 LLM”或“对话少一点问题”，而是升级为一个可追踪、可训练、可合成验证的八字诊断决策系统。

## 核心结论

当前 V30 已经有中枢大脑雏形，但还没有真正完成智能化。

已有能力：

- `v30.brain.orchestrator` 已能产出 `CentralBrainTrace`，负责角色、会话、反馈、训练路由和运行边界。
- `v30.brain.reading_engine` 已能产出 `CentralReadingState`，负责 claim 评分、结论合成、对话计划、反馈权重和训练信号。
- `v30.brain.dialogue_planner` 已经支持每次只聚焦一个问题，而不是一次性堆问题。
- `v30.brain.final_synthesis` 已能把候选断语合成为结论、建议、证据链和可视化提示。
- `v30.llm` 已经把 Gemma/Ollama thinking 当作页面推演候选，并由中枢做清洗和验收。
- `v30.diagnosis.contracts` 已有 `DiagnosisGraph`，但它还没有成为中枢大脑的第一等输入。
- 2026-06-29 `Stage Intelligence Point Framework` 已完成基础落地：页面级 LLM 输出不再只是自然语言小结，而是生成候选 `StagePoint`，由中枢大脑验收、排序、沉淀到页面与边栏；命理师可选项、专项合成验证和 Admin 回放保留后续任务。Canonical 文档为 `V30_STAGE_INTELLIGENCE_LLM_BRAIN_FRAMEWORK_20260629.md`。
- 2026-06-29 `Text-to-Option Practitioner Interaction Framework` 已完成基础落地：把测算文本和对话文本中的候选、列表、数字、行动建议和追问需求抽成 `TextSemanticUnit / OptionSet / PractitionerSelection`，让命理师选择和用户点击式回答进入中枢 belief update 与训练样本。Canonical 文档为 `V30_TEXT_TO_OPTION_PRACTITIONER_INTERACTION_FRAMEWORK_20260629.md`。

主要缺口：

- 中枢仍偏结构化协调脑和规则评分脑，不是学习型决策脑。
- Evidence Graph 已存在，但中央评分仍主要吃扁平 claims。
- claim 权重、问题策略、最终合成策略仍以固定启发式为主。
- LLM 当前更像推演候选和表达增强器，中枢裁决还不够强。
- 训练样本结构已经出现，但还没有完整沉淀“这次为什么这么断、为什么这么问、用户反馈后如何改变判断”。

## V2 定位

中枢智能大脑 V2 的定位：

```text
Evidence Graph
+ Belief State
+ Value-of-Information Dialogue
+ LLM Candidate Derivation
+ Brain Judge
+ Training / Validation Loop
```

它不是普通聊天 agent，也不是一个大 prompt。

八字测算的本质是：

```text
命盘事实
-> 证据组织
-> 断言候选
-> 不确定性判断
-> 必要追问
-> 置信度更新
-> 结论排序
-> 建议生成
-> 反馈训练
```

因此最适合 V30 的框架是诊断型决策系统，而不是模板系统。

## 核心建模

### 1. Evidence Graph

所有材料进入一张统一证据图。

节点类型：

- `chart_fact`：四柱、六柱、日主、月令、藏干、十神、旺衰等确定性事实。
- `feature`：五行分布、结构信号、十神能量、显隐关系。
- `matched_rule`：命中的规则、规则族、规则强度。
- `portrait`：画像投影。
- `path`：做功路径、力量流向、流通或阻滞。
- `timing_activation`：大运、流年、流月对原局路径的激活。
- `feedback`：用户确认、否认、跳过、补充年份或状态。
- `claim`：候选断言。

边类型：

- `supports`
- `weakens`
- `blocks`
- `requires`
- `activates`
- `explains`
- `asks_followup`

要求：

- 结论必须能追溯到图上的支持证据。
- 反证和缺口也必须进入图。
- LLM 不能直接创造图上的命盘事实。

### 2. Belief State

中枢每一步维护一个信念状态。

核心字段：

```text
active_stage
user_goal
top_claims
weak_claims
blocked_claims
missing_context
uncertainty_map
question_need
stage_decision
final_decision_readiness
```

它回答的问题：

- 当前最强结论是什么？
- 哪些结论证据不足？
- 哪些结论有冲突？
- 哪个问题能最大幅度减少不确定性？
- 哪些建议已经足够确定，可以直接给？

### 3. Candidate Claim

所有结论都必须先是结构化 claim，再进入用户可读表达。

```json
{
  "claim_id": "career.pressure_to_credentials",
  "domain": "career",
  "level": "domain",
  "text": "事业更适合把压力转成资质、规则、平台或可交付能力。",
  "supporting_nodes": ["path.guan_to_yin", "rule.official_seal", "portrait.responsibility_boundary"],
  "weakening_nodes": ["timing.missing_luck_context"],
  "confidence": 0.74,
  "actionability": 0.82,
  "requires_question": true
}
```

要求：

- 用户看到的是结论和建议。
- 系统内部保存的是 claim、证据、反证、置信度和行动价值。
- 最终报告不能直接从 LLM 文本拼出来。

### 4. Brain Decision Trace

每一次中枢决策都要留下 trace。

```json
{
  "decision_id": "...",
  "stage_id": "path_reasoning",
  "selected_action": "ask_stage_question",
  "selected_claim_ids": ["career.pressure_to_credentials"],
  "rejected_claim_ids": ["wealth.direct_gain"],
  "selected_question_id": "career.path.confirm_pressure_boundary",
  "reason_codes": ["high_information_gain", "claim_confidence_near_threshold"],
  "feature_vector": {
    "top_claim_score": 0.74,
    "uncertainty": 0.31,
    "information_gain": 0.62,
    "user_cost": 0.18
  }
}
```

要求：

- 页面为什么给这个结论，要能解释。
- 页面为什么问这个问题，要能解释。
- 用户回答后为什么改变或不改变判断，要能解释。

## 核心算法

### 1. Claim Score

初期继续使用可解释权重，后续进入训练。

```text
claim_score =
  support_strength * 0.26
+ evidence_diversity * 0.16
+ graph_path_coherence * 0.18
+ timing_activation * 0.10
+ user_feedback_alignment * 0.14
+ actionability * 0.10
- counter_evidence * 0.18
- missing_context_penalty * 0.14
- overclaim_risk * 0.20
```

解释：

- `support_strength`：支持证据强度。
- `evidence_diversity`：是否来自规则、画像、路径、时运等多个来源。
- `graph_path_coherence`：证据之间能否形成连贯路径。
- `timing_activation`：大运流年是否激活原局路径。
- `user_feedback_alignment`：用户回答是否支持该结论。
- `actionability`：能否形成具体建议。
- `counter_evidence`：反证力度。
- `missing_context_penalty`：缺少关键背景的惩罚。
- `overclaim_risk`：过度断言风险。

### 2. Belief Update

用户回答后不直接改结论，而是更新 claim posterior。

```text
logit(confidence_next) =
  logit(confidence_current)
+ feedback_support_delta
- feedback_contradiction_delta
+ graph_consistency_delta
- unresolved_conflict_delta
```

要求：

- 用户确认只升高相关 claim，不扩大成全局事实。
- 用户否认必须进入反证图。
- 跳过问题不能当作否认，只增加缺口或降低追问优先级。

### 3. Next Action Policy

每页都可以问，但不是每页都必须问。

```text
question_value =
  information_gain * 0.32
+ claim_impact * 0.22
+ hidden_attribute_gain * 0.14
+ training_value * 0.08
- user_cost * 0.12
- overask_penalty * 0.12
```

可选动作：

- `conclude_stage`：本页证据足够，直接给结论和建议。
- `ask_stage_question`：本页有一个高价值问题。
- `ask_hidden_attribute_probe`：隐藏属性判断需要一个低成本问题。
- `request_timing_context`：必须补充年份或状态。
- `continue_next_stage`：本页只是材料页，进入下一页。
- `final_synthesis`：收束全盘结论。

规则：

- 每次最多一个问题。
- 问题必须绑定当前页面、当前 claim 或隐藏属性校准。
- 问题必须能改变后续判断，否则不问。
- 问题成本要低，优先选择题、数字、极短输入。

### 4. LLM Candidate + Brain Judge

LLM 不直接决定最终答案。

### 5. Central Brain Synthesis Policy

Brain Judge 不只做一次性质量报告，还要进入可训练策略候选。

训练信号：

```text
v30.training_signal.central_brain_judge_quality
```

策略候选：

```text
question_policy.weights.central_brain_synthesis_policy
```

策略只允许调整：

- `final_synthesis_quality`
- `evidence_binding`
- `conclusion_strength`
- `advice_actionability`
- `template_risk_penalty`
- `overclaim_risk_penalty`
- `min_quality_score`

策略禁止调整：

- 排盘事实
- 四柱、六柱、日主、十神等基础事实
- 规则命中本身
- 原始 claim 文本
- 大运流年换算

运行时消费：

- `CentralReadingState` 从 `question_policy` 中读取 `central_brain_synthesis_policy`。
- `FinalSynthesis` 使用该策略进行质量门槛、证据绑定、建议行动性和过度断言惩罚的只读投影。
- `final_synthesis.synthesis_policy_effect` 记录策略是否生效。
- `quality_contract.synthesis_policy_applied` 记录最终综合是否吃到策略。
- `final_synthesis.synthesis_blueprint` 先结构化生成主断语、证据抓手、行动步骤、风险边界，再生成用户可读结论和建议。
- 客户端只投影 `decision_focus`、`action_steps`、`risk_boundary` 等安全字段，不暴露权重、训练信号或内部策略。

边界：

```text
central_brain_synthesis_policy_trains_quality_and_dialogue_strategy_not_chart_facts
```

### 6. Final Synthesis Blueprint

最终综合不再直接把 top claim 包成一句话，而是先形成蓝图：

```json
{
  "primary_domain": "career",
  "core_claim": "事业主线落在职责压力与资质承接",
  "decision_focus": "职责压力能否转成资质、平台和可交付成果",
  "evidence_handles": ["官杀 -> 印星"],
  "action_steps": ["把职责压力拆成资质、规则和可交付成果"],
  "risk_boundary": "没有现实反馈时一次性铺开过多方向"
}
```

蓝图作用：

- 结论必须明确说明领域主线、核心 claim、证据抓手和判断焦点。
- 建议必须给出可执行动作和风险边界。
- Brain Judge 继续评估证据绑定、结论强度、建议行动性、模板风险和过度断言风险。
- 蓝图只组织已有 claim、path、portrait、practical reading 和反馈，不生成新命盘事实。

训练闭环：

- `central_reading_synthetic_validation` 增加 `final_synthesis_blueprint_quality` 检查。
- `extract_training_signals` 产出 `v30.training_signal.central_brain_synthesis_blueprint_quality`。
- `central_brain_synthesis_policy` 同时消费 Brain Judge 质量信号和蓝图质量信号。
- 蓝图质量信号只训练综合策略、判断焦点、建议行动性、风险边界清晰度，不训练排盘或规则事实。

正确流程：

```text
中枢打包结构化证据
-> LLM thinking 生成推演候选
-> 中枢检查证据、反证、断言强度
-> 中枢裁决最终结论与建议
-> UI 只显示对用户有价值的结论、建议和必要 thinking
```

LLM 可以做：

- 推演表达。
- 解释证据链。
- 生成候选结论和候选建议。
- 生成候选 `StagePoint`。
- 生成用户可读 thinking。

LLM 不可以做：

- 修改四柱、六柱、日主、月令、大运流年等事实。
- 跳过中枢 claim 评分直接下结论。
- 用模板语言冒充推演。
- 在没有证据时输出确定断语。

页面级 LLM 正确角色：

```text
中枢大脑给定 stage_scope + context_pack
-> LLM 生成 public_derivation + candidate_points
-> 中枢做 scope gate / evidence binding / point scoring
-> 中枢选择 StagePoint
-> 页面展示列表
-> 边栏沉淀短标签
-> 训练信号记录质量与采用结果
```

### 5. Final Synthesis

最终合成不是摘要，而是裁决。

输入：

- Top claims。
- 证据图路径。
- 用户反馈。
- LLM 推演候选。
- 冲突和缺口。

输出：

- 核心结论。
- 核心建议。
- 关键证据链。
- 风险边界。
- 下一步是否需要追问。
- 可视化提示。

## 训练设计

训练目标不是让模型背模板，而是训练中枢策略。

### BrainTrainingExample

每次页面推演、追问或最终合成，都生成训练样本。

```json
{
  "example_id": "...",
  "input": {
    "stage_id": "domain_synthesis",
    "evidence_graph_snapshot": "...",
    "belief_state": "...",
    "candidate_claims": ["..."],
    "candidate_questions": ["..."],
    "user_goal": "career"
  },
  "decision": {
    "selected_action": "ask_stage_question",
    "selected_claim_ids": ["..."],
    "selected_question_id": "..."
  },
  "outcome": {
    "user_answered": true,
    "answer_type": "choice",
    "claim_delta": {"career.pressure_to_credentials": 0.08},
    "followup_useful": true
  },
  "labels": {
    "question_information_gain": 0.72,
    "advice_actionability": 0.81,
    "overask": false,
    "contradiction_found": false
  }
}
```

### 训练对象

可训练：

- claim score 权重。
- next action policy 权重。
- question selection policy。
- hidden attribute probe policy。
- final synthesis 排序。
- expression density 和建议具体度。

不可训练：

- 命盘事实。
- 四柱、六柱、日主、月令。
- 大运流年确定性计算。
- 未经用户确认的隐藏属性事实。
- 未通过验证的规则结论。

### 训练路径

```text
runtime trace
-> BrainTrainingExample
-> synthetic replay
-> policy candidate
-> central brain validation
-> 518k sample / shard validation
-> operator review
-> explicit promotion
```

默认不自动上线策略。中枢大脑 V2 的训练结果必须先进入候选和验证。

## 验证设计

### 单元验证

- claim score 不允许无证据高分。
- 反证必须降低置信度。
- 用户跳过不能被当作否认。
- LLM 输出不得新增命盘事实。
- 每次最多一个可见问题。

### 合成验证

覆盖场景：

- 事业压力转资质。
- 食伤生财与财务节奏。
- 关系反复和边界。
- 健康负荷与风险提示。
- 隐藏属性校准。
- 缺时柱、缺年份、用户跳过。

### 回放验证

同一命盘在不同反馈下必须产生合理差异：

- 用户确认事业压力后，事业 claim 升权。
- 用户否认关系反复后，关系 claim 降权或转为弱断。
- 用户补充明显年份后，时运激活路径变化。
- 用户跳过问题后，不继续幽灵追问。

### LLM 验收

- 没有可用 LLM 时，不输出假推演。
- LLM 返回慢时等待，但 UI 明确显示正在推演。
- LLM thinking 必须绑定本页证据。
- 中枢必须能拒绝空泛、模板化、无证据的 LLM 文本。

## 主线任务计划

### CBI-V2-0：文档与边界冻结

目标：

- 本文作为中枢智能大脑 V2 主线入口。
- 原有 reading engine、dialogue training、stage prompt 文档作为支持文档。
- 后续中枢大脑任务以 CBI-V2 编号推进。

状态：当前执行。

### CBI-V2-1：中枢决策契约

目标：

- 定义 `CentralBrainDecisionEngine` 输入输出契约。
- 定义 `BrainDecisionTrace`。
- 定义 `BrainTrainingExample`。
- 明确中枢不改命盘事实、不直接发布策略、不让 LLM 越权。

验收：

- 有稳定 dataclass / schema。
- 单测覆盖 trace 完整性和事实不可变边界。

状态：已完成基础契约落地。

落地产物：

- `BrainEvidenceGraphSnapshot`
- `BrainClaimBelief`
- `BrainUncertaintySlot`
- `BrainBeliefState`
- `BrainQuestionCandidate`
- `BrainLLMCandidateDerivation`
- `BrainDecisionTrace`
- `BrainDecisionOutcome`
- `BrainTrainingExample`

验证：

```bash
python -m pytest -q tests/unit/test_central_brain_v2_contracts.py tests/unit/test_central_brain.py tests/unit/test_central_reading_synthetic_validation.py
```

结果：

```text
10 passed
```

### CBI-V2-2：Evidence Graph 第一等输入

目标：

- 把现有 `DiagnosisGraph` 接入 `reading_engine`。
- claim 评分从扁平列表升级为图路径评分。
- 支持 supports / weakens / blocks / requires 的基础图推理。

验收：

- 有图时优先走图评分。
- 无图时不 fallback 成假智能，只标记 graph_missing。
- 至少覆盖规则、画像、路径、反馈四类节点。

状态：已完成基础接入。

落地产物：

- `real_bazi_diagnosis.graph` 现在随 runtime diagnosis payload 输出完整 graph。
- `central_reading_state.evidence_graph_snapshot` 记录图 id、节点数、边数、节点类型、边类型、top claims、top paths。
- `central_reading_state.graph_detail_status` 区分 `ready` 和 `graph_detail_missing`。
- `central_reading_state.graph_claim_metric_count` 记录被图评分覆盖的 claim 数量。
- `claim_scores[].graph_metrics` 暴露支持边、反证边、requires/asks 边、source kinds、图路径连贯度和 top claim prior。
- `claim_scores[].components` 增加 `graph_support`、`graph_prior`、`graph_path_coherence`。
- 训练目标新增 `graph_claim_score_weight`、`graph_counterevidence_weight`。

验证：

```bash
python -m pytest -q tests/unit/test_central_brain_v2_evidence_graph.py tests/unit/test_central_brain_v2_contracts.py tests/unit/test_central_brain.py tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_failure_routing.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_central_reading_synthetic_validation.py
```

结果：

```text
23 passed
```

### CBI-V2-3：Belief State 与 Claim Posterior

目标：

- 每个 claim 保存当前置信度、反证、缺口、用户反馈影响。
- 用户回答后只更新相关 claim。
- 支持同一命盘不同反馈产生不同结论排序。

验收：

- 确认、否认、跳过三种反馈有不同 posterior delta。
- 回放测试能证明 claim 排序变化。

状态：已完成基础落地。

落地产物：

- `central_reading_state.belief_state`
- `belief_state.top_claims`
- `belief_state.weak_claims`
- `belief_state.blocked_claims`
- `belief_state.uncertainty_map`
- `BrainClaimBelief.posterior_delta`

已验证：

- 用户确认会让相关 claim 的 posterior delta 上升。
- 用户否认会让相关 claim 的 posterior delta 下降，并可能从 top claim 降入 weak claim。
- 反馈只影响 claim belief，不改命盘事实。

### CBI-V2-4：Value-of-Information 对话策略

目标：

- 用信息增益决定是否追问。
- 每页最多一个问题。
- 隐藏属性问题也纳入同一策略，不单独幽灵出现。

验收：

- 问题必须有 `target_claim_id` 或 `target_uncertainty`。
- 无高价值问题时直接结论或下一页。
- 用户回答后不刷新页面步骤，只更新对话状态和 belief state。
- 对话不得被投影成测算步骤；前端只渲染当前页面里的 dialogue surface。
- 对话出现必须由中枢 `brain_decision_trace.selected_action` 控制，不能因为存在候选 `next_question` 就展示。
- 问题必须和当前 stage、topic 或 target claim 相关，并通过 VOI 相关性门控。

状态：已完成基础落地。

落地产物：

- `central_reading_state.value_of_information_policy`
- `question_value`
- `information_gain`
- `claim_impact`
- `user_cost`
- `overask_penalty`
- `hidden_attribute_gain`

已验证：

- 高信息增益问题会被选为 `ask_stage_question`。
- 每次 decision trace 只绑定一个 selected question。
- 策略理由进入 `brain_decision_trace.reason_codes`。

硬性边界：

- 中枢大脑可以在任意阶段选择 `ask_stage_question`，但这个动作只生成 `reading_surface.current_dialogue_turn`。
- `current_dialogue_turn` 是对话 surface 的输入，不是 reading journey 的 step。
- `current_dialogue_turn.action=ask` 的必要条件：中枢选择追问、存在有效问题、绑定真实 stage、target claim 或 VOI 阈值通过。
- 测算步骤的 active step 只能来自真实 stage；对话回答只触发 belief update、hidden factor update、answer panel 和下一问选择。
- LLM 候选回答先回到中枢大脑清洗、验收、列表化和风险过滤，再显示给用户；若仍在 deferred/loading，不展示规则草稿或诊断文本。
- `question_followup` 已从运行态 steps 删除，不得再作为产品页面、导航项、阶段小结入口或内部 fallback stage 使用。

### CBI-V2-5：LLM Candidate + Brain Judge

目标：

- LLM 输出成为候选推演，不直接成为最终答案。
- 中枢检查 used evidence、结论强度、建议具体度、空话比例。
- 被拒绝的 LLM 输出要记录 reason code。

验收：

- 空泛模板化 LLM 输出会被拒绝。
- 有证据输出会被收束成结论、建议、证据链。
- 页面 thinking 和结论都来自同一次推演链路。

状态：完成基础决策 trace 地基，LLM 深度验收后续继续增强。

落地产物：

- `BrainLLMCandidateDerivation`
- `BrainDecisionTrace`
- `central_reading_state.brain_decision_trace`

已完成边界：

- LLM candidate 不能生成事实。
- 被接受的 LLM candidate 必须绑定 belief state 中已有证据。
- 中枢最终动作由 `BrainDecisionTrace.selected_action` 表达，不直接让 LLM 接管。

### CBI-V2-6：训练样本沉淀

目标：

- 每次中枢决策产出 `BrainTrainingExample`。
- 保存问题选择、结论排序、用户反馈、claim delta、建议质量标签。
- 与现有 dialogue training pipeline 对齐。

验收：

- 训练样本不含敏感明文。
- 样本可用于离线 replay。
- 样本不会自动写 production pointer。

状态：已完成基础落地。

落地产物：

- `central_reading_state.brain_training_example`
- `BrainTrainingExample`
- `BrainDecisionOutcome`
- `claim_delta`
- `labels.question_information_gain`
- `labels.advice_actionability`

已验证：

- 训练样本捕获 decision、candidate claims、candidate questions、outcome 和 labels。
- `blocked_targets` 固定包含 `chart_facts`、`calendar_conversion`、`pillar_calculation`、`unconfirmed_hidden_factor_facts`。
- `production_policy_write_allowed` 固定为 false。

### CBI-V2-7：合成验证与回放闸门

目标：

- 新增中枢大脑 V2 synthetic tier。
- 新增长会话 replay。
- 新增 LLM 输出验收。

验收：

- 单元测试。
- synthetic smoke。
- central brain replay。
- LLM configured / unconfigured 双路径验收。

状态：已完成基础闸门扩展。

落地产物：

- `central_brain_v2_decision_loop` 验收项。
- central reading synthetic validation 现在检查 graph snapshot、belief state、VOI policy、decision trace、training example。

验证：

```bash
python -m pytest -q tests/unit/test_central_brain_v2_belief_voi.py tests/unit/test_central_brain_v2_evidence_graph.py tests/unit/test_central_brain_v2_contracts.py tests/unit/test_central_brain.py tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_failure_routing.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_central_reading_synthetic_validation.py tests/unit/test_real_bazi_runtime_integration.py
```

结果：

```text
30 passed
```

### CBI-V2-8：老旧脑路径收束

目标：

- 审查 `interaction_brain.py`、旧 question 入口、旧 summary 路径。
- 能并入中枢大脑的并入。
- 不能并入的标记为 adapter 或 archive candidate。

验收：

- 不再出现两个互相竞争的“脑”。
- 页面问题、隐藏属性问题、最终问答都走统一决策 trace。

状态：已完成基础收束。

落地产物：

- `interaction_brain` 明确降级为 `structured_feedback_adapter`。
- `interaction_brain_result.customer_decision_owner` 指向 `central_reading_state.brain_decision_trace`。
- `interaction_brain_result.can_select_next_question` 固定为 false。
- `interaction_brain_result.can_generate_public_conclusion` 固定为 false。

已验证：

- 隐藏属性结构化反馈仍可进入反馈链。
- 旧 interaction brain 不再被语义上视为并行决策脑。

### CBI-V2-9：产品投影与可视化

目标：

- UI 不展示工程语言。
- 用户看到结论、建议、必要 thinking、一个问题、简洁可视化。
- 可视化来自中枢输出的 `visual_hint`，例如路径流向、证据强度、领域优先级。

验收：

- 页面不显示无用状态文案。
- 问题只在小结和建议之后出现。
- 对话 thinking 与页面 thinking 一致走同一推演链路。

状态：已完成基础接入。

落地产物：

- `reading_surface.current_dialogue_turn.decision_source`
- `reading_surface.current_dialogue_turn.decision_basis`
- `dialogue_visual_hint` 使用 VOI 的 `information_gain` 和 `user_cost`。
- 用户可见 current dialogue turn 优先服从 `brain_decision_trace.selected_action`。

已验证：

- 前端仍只暴露一个当前问题。
- 用户可见字段只展示安全摘要，不暴露完整内部 trace。
- 当前问题、目标 claim、视觉提示和决策依据同源于中枢大脑。

## 当前执行顺序

近期已推进到：

```text
CBI-V2-0 文档与边界冻结
-> CBI-V2-1 中枢决策契约
-> CBI-V2-2 Evidence Graph 第一等输入
-> CBI-V2-3 Belief State 与 Claim Posterior
-> CBI-V2-4 Value-of-Information 对话策略
-> CBI-V2-5 Brain Decision Trace 基础
-> CBI-V2-6 训练样本沉淀
-> CBI-V2-7 合成验证闸门扩展
-> CBI-V2-8 老旧脑路径收束
-> CBI-V2-9 产品投影与可视化
```

## CBI-V2-Q：中枢智能质量增强

目标：

- 让中枢大脑不仅能记录决策 trace，还能判断结论和建议是否真的有质量。
- Brain Judge 必须能拒绝空话、模板话、弱证据、过度断言和不可执行建议。
- LLM thinking 只能作为候选推演，必须经过 Brain Judge 质量审查。

### CBI-V2-Q1：Brain Judge 质量评分

状态：已完成基础落地。

落地产物：

- `v30.brain.judge`
- `BRAIN_JUDGE_VERSION`
- `judge_final_synthesis_quality`
- `judge_llm_derivation_quality`

评分维度：

- `evidence_binding`
- `conclusion_strength`
- `advice_actionability`
- `feedback_alignment`
- `template_risk`
- `overclaim_risk`

拒绝原因：

- `weak_evidence_binding`
- `weak_or_missing_conclusion`
- `weak_or_missing_actionable_advice`
- `template_or_filler_language`
- `overclaim_or_fixed_verdict_risk`
- `conclusion_not_first`
- `advice_not_explicit`

### CBI-V2-Q2：Final Synthesis Judge 接入

状态：已完成基础落地。

落地产物：

- `final_synthesis.brain_judge`
- `final_synthesis.quality_contract.brain_judge_accepted`
- `final_synthesis.quality_contract.brain_judge_quality_score`
- 训练目标新增 `central_brain_judge_quality`、`final_synthesis_template_risk`

验收：

- central reading synthetic validation 的 `final_synthesis_quality` 现在必须检查 Brain Judge。
- Brain Judge 未通过时，final synthesis 不再被视为高质量结果。

### CBI-V2-Q3：LLM Derivation Judge 接入

状态：已完成基础落地。

落地产物：

- `central_brain_review.brain_judge`
- `central_brain_review.brain_judge_version`
- LLM derivation 若缺少 used evidence、public thinking、明确结论或可执行建议，会被 Brain Judge 拒绝。

边界：

- Brain Judge 不生成新命盘事实。
- Brain Judge 不改四柱、六柱、大运、流年。
- Brain Judge 只裁决质量、证据绑定和表达风险。

### CBI-V2-Q4：Brain Judge 训练信号接入

状态：已完成基础落地。

落地产物：

- `v30.training_signal.central_brain_judge_quality`
- `customer_reading_surface.final_synthesis.quality_judge`
- central reading validation 的 `training_targets` 纳入 Brain Judge 训练目标。

训练信号字段：

- `observed_count`
- `accepted_count`
- `rejected_count`
- `average_quality_score`
- `average_template_risk`
- `average_overclaim_risk`
- `average_advice_actionability`
- `failure_counts`
- `reason_counts`

训练边界：

- `can_tune_final_synthesis_quality = true`
- `can_tune_template_risk_penalty = true`
- `can_tune_chart_facts = false`
- 不训练四柱、六柱、大运、流年、原始 claim 文本。

验证：

```bash
python -m pytest -q tests/unit/test_training_signals.py tests/unit/test_central_brain_judge.py tests/unit/test_presentation_projection.py tests/unit/test_interaction_constraints.py tests/unit/test_synthetic_validation.py::test_synthetic_interaction_brain_structured_constraints_tier_passes tests/unit/test_central_brain_v2_belief_voi.py tests/unit/test_central_brain_v2_evidence_graph.py tests/unit/test_central_brain_v2_contracts.py tests/unit/test_central_brain.py tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_failure_routing.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_central_reading_synthetic_validation.py tests/unit/test_real_bazi_runtime_integration.py
```

结果：

```text
48 passed
BT1 central brain acceptance: passed 5/5
BT2 central brain session replay: passed 6/6
central reading synthetic validation: ready 8/8
```

暂缓：

- 大规模 UI 细节优化。
- 自动上线训练策略。
- 引入完整外部 agent 框架。
- 重写已有 runtime。

## 外部框架态度

当前不建议把 V30 迁移成完整 LangGraph 或其他 agent 框架。

原因：

- V30 已经有自己的 runtime、trace、stage flow 和训练验证体系。
- 当前核心缺口不是流程编排，而是证据图、信念状态、策略学习和验证闭环。
- 外部框架可以后续作为运行编排参考，但不应替代八字诊断模型。

DSPy 后续可以作为 prompt 和 LLM 程序优化工具引入，但前提是先有 `BrainTrainingExample`、评价指标和离线 replay。

## 成功标准

中枢智能大脑 V2 完成后，系统应该做到：

- 每个结论都有证据链。
- 每个追问都有信息增益理由。
- 用户回答会改变相关 claim 置信度。
- LLM thinking 只做推演候选，中枢负责裁决。
- 最终建议具体、明确、可执行。
- 所有策略可训练、可回放、可合成验证。
- 没有 LLM 时明确失败，不用 fallback 冒充智能。
