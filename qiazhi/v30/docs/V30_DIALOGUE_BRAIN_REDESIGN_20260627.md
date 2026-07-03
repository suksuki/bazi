# V30 Dialogue Brain Redesign

Updated: 2026-06-27

## 目标

重构 V30 智能对话系统，把它从“问题推荐 + 回答面板”升级为中枢智能大脑的一条可训练决策链。

新系统的核心不是聊天框，也不是问题池，而是：

```text
八字事实和推演材料
-> 中枢证据图谱
-> 候选断语池
-> 十神与宏观相语义映射
-> 对话决策
-> 一个必要问题
-> 用户极简反馈
-> 权重更新
-> 结论与建议
-> 训练样本
```

用户看到的是一步一步更准的结论和建议。系统内部必须做到可解释、可训练、可合成验证，并且不污染命盘事实。

## 设计原则

1. 每次最多出现一个问题。
2. 问题必须绑定候选断语、隐藏属性或当前页面推演缺口。
3. 问题必须有必要性，不能幽灵一样随机出现。
4. 用户回答必须转成结构化信号，并更新中枢状态。
5. LLM 只负责表达和整理，不负责发明命盘事实。
6. 结论和建议必须优先，解释和过程服务于结论。
7. 智能相关策略从第一天开始可训练。
8. 可训练的是权重、排序、问题策略和表达，不可训练的是四柱、十神事实、历法和大运流年事实。

## 需要清理的旧系统

当前 V30 已经有不少能力，但对话相关逻辑分散在多个层里，容易继续缝缝补补。

必须清理或收编的旧逻辑：

| 旧模块/行为 | 问题 | 目标处理 |
|---|---|---|
| 问题池直接展示 | 用户看到多个问题挤在一起 | 废弃客户侧问题池，只保留一个当前问题 |
| 前端自行挑问题 | UI 越权决策 | 前端只消费中枢 `current_dialogue_turn` |
| `question_followup` 被当成阶段小结页 | 智能问答被推演 LLM 卡住 | 保持独立问答流 |
| 旧 `renderQuestionUxPanel` / 历史表单 | 工程字段和复杂输入泄漏 | 删除客户侧入口，保留结构化提交能力 |
| `QuestionDialogueGraph` 和 `recommend_questions` 各自决策 | 内部策略和用户可见策略混杂 | 收编进 Dialogue Brain，图谱只做证据和候选 |
| 隐藏属性复杂表单 | 用户填写模型变量 | 改成核心现象选择、年份、重复性 |
| fallback 答案伪装智能回答 | 无 LLM 时输出无价值文字 | 不伪造结论，等待或明确失败 |
| 诊断口径/证据计数/JSON/schema 外露 | 破坏产品体验 | 仅 admin/practitioner 可见 |

清理目标不是把已有能力推倒重写，而是明确所有权：

```text
中枢智能大脑：决定问不问、问什么、何时问、如何更新权重
问题图谱：记录候选问题关系和已回答状态
隐藏属性模块：维护后验状态，不直接决定 UI
LLM：把结构化结论表达成人话
前端：渲染一个当前问题、一个回答、一个下一步动作
```

## 总架构

```text
M1/M2 命盘事实层
  六柱、日主、月令、藏干、十神、五行、时运事实

M3/M4/M5/M6 推演材料层
  知识库、规则、画像、特征、做功路径、领域读盘

BaziSemanticOntology
  十神抽象维度、宏观相维度、六亲映射、健康五行映射、关键词词典

EvidenceGraph
  把规则、画像、路径、时运、用户信号连接成证据图

ClaimPool
  生成候选断语、反证、置信度、行动价值和缺口

DialogueBrainState
  当前 belief state、已知用户信号、隐藏属性后验、页面上下文

DialoguePlanner
  选择 conclude / ask / drill_hidden / continue / stop

QuestionIntentGenerator
  从断语缺口生成种子问题和下一轮问题链

QuestionPolicy
  用信息增益、用户成本、训练权重选择一个当前问题

SignalUpdater
  用户回答后更新 claim score、hidden factor belief、question policy state

AnswerComposer
  中枢裁决后的结论与建议，由 LLM 做表达增强

TrainingRecorder
  记录每次决策、问题、回答、权重变化和输出质量
```

## 中枢智能大脑状态

目标对象：

```text
DialogueBrainState v1
```

建议字段：

```json
{
  "version": "v30.dialogue_brain_state.v1",
  "reading_id": "...",
  "active_stage_id": "domain_synthesis",
  "macro_focus": "career",
  "semantic_focus": {
    "ten_god_family": "authority",
    "ten_gods": ["正官", "七杀"],
    "macro_domains": ["事业", "压力", "责任"]
  },
  "top_claim_ids": [],
  "uncertain_claim_ids": [],
  "known_user_signals": [],
  "hidden_factor_belief": {},
  "answered_question_ids": [],
  "suppressed_question_ids": [],
  "current_dialogue_turn": {},
  "next_action": {
    "action": "ask",
    "reason": "career_claim_needs_path_discrimination"
  },
  "training_trace_id": "..."
}
```

边界：

```text
DialogueBrainState 可以更新 claim 权重、问题策略、隐藏属性后验。
DialogueBrainState 不可以更新四柱、十神事实、藏干事实、大运流年事实。
```

## 命理语义本体

目标对象：

```text
BaziSemanticOntology v1
```

它是智能对话系统的基础字典。它既服务传统命理推演，也服务宏观相映射和种子问题生成。

### 十神抽象维度

十神从日主关系生成：

| 关系 | 阴阳细分 | 十神 | 抽象家族 |
|---|---|---|---|
| 同我 | 同性 | 比肩 | peer |
| 同我 | 异性 | 劫财 | peer |
| 我生 | 同性 | 食神 | output |
| 我生 | 异性 | 伤官 | output |
| 我克 | 异性/正配 | 正财 | wealth |
| 我克 | 同性/偏配 | 偏财 | wealth |
| 克我 | 异性/正配 | 正官 | authority |
| 克我 | 同性/偏配 | 七杀 | authority |
| 生我 | 异性/正配 | 正印 | resource |
| 生我 | 同性/偏配 | 偏印 | resource |

说明：不同流派对正偏的阴阳描述可能有表述差异，V30 采用内部统一算法生成十神事实；本文只定义语义层。

### 十神关键词

| 十神 | 核心相 | 成事关键词 | 失衡风险 | 常见宏观落点 |
|---|---|---|---|---|
| 比肩 | 自我、同类、同侪 | 自主、坚持、同伴、合伙 | 固执、竞争、分资源 | 人际、事业、竞争 |
| 劫财 | 抢夺、朋友、人情、冲劲 | 破局、社交、行动、竞争力 | 破财、冲动、人情耗损 | 财富、人际、风险 |
| 食神 | 稳定输出、福气、照料 | 产品、表达、教学、享受 | 贪安逸、节奏慢、泄气 | 表达、财富、健康 |
| 伤官 | 锋芒、突破、反规则 | 技术、创意、话语权、突破 | 口舌、抗上、规则冲突 | 事业、表达、风险 |
| 正财 | 稳定财富、经营、现实 | 工资、资产、执行、秩序 | 保守、为财所累、紧绷 | 财富、男命感情 |
| 偏财 | 机会财富、市场、外部资源 | 生意、资源、人脉、机会 | 投机、波动、外缘复杂 | 财富、人脉、父缘 |
| 正官 | 规则、职位、名分 | 职责、秩序、名誉、职位 | 压抑、怕错、责任重 | 事业、女命感情 |
| 七杀 | 压力、竞争、危机 | 魄力、执行、权力、突破 | 焦虑、伤灾、压迫 | 事业、风险、压力 |
| 正印 | 保护、资质、学习、母性 | 学历、证书、贵人、恢复 | 依赖、慢、空想 | 学业、事业、亲情 |
| 偏印 | 非常规认知、偏门能力 | 研究、灵感、洞察、特殊技能 | 孤立、偏执、枭神夺食 | 学习、隐藏属性、健康消耗 |

### 宏观相维度

用户真正关心的是宏观相：

| 宏观相 | 用户关键词 | 十神入口 | 推演重点 |
|---|---|---|---|
| 财富 | 收入、资产、投资、现金流、债务、分配 | 财星、食伤、比劫、官杀 | 财源、守财、分配、风险 |
| 事业 | 工作、职位、平台、晋升、责任、转型 | 官杀、印星、食伤、财星 | 责任、平台、输出、授权 |
| 感情 | 婚恋、伴侣、承诺、关系反复、边界 | 男命财星，女命官杀，兼看比劫/食伤/印 | 关系角色、冲突模式、承诺压力 |
| 亲情 | 父母、兄弟姐妹、子女、家庭牵制 | 印、财、比劫、食伤、官杀 | 资源、照顾、分担、边界 |
| 健康 | 睡眠、压力、消耗、脾胃、恢复、伤病 | 五行为主，十神为压力模式 | 五行脏腑、压力来源、恢复方式 |
| 学业资质 | 学习、证书、学历、专业能力、贵人 | 印星、官星、食伤 | 资质承接、学习路径、证书平台 |
| 表达作品 | 才华、产品、教学、内容、技术输出 | 食神、伤官、财星 | 输出能否变现、表达与规则关系 |
| 人际竞争 | 合伙、朋友、同事、竞争、资源抢夺 | 比肩、劫财、官杀、财星 | 合作边界、资源分配、竞争压力 |
| 风险变动 | 官非、冲突、事故、破财、突发压力 | 七杀、伤官、劫财、刑冲 | 压力触发、冲突边界、规避建议 |
| 时机阶段 | 哪一年、哪步运、何时触发 | 大运、流年、流月、刑冲合害 | 原局路径是否被时运激活 |

健康映射边界：

```text
健康建议只能做生活方式和压力模式提示。
不能输出疾病诊断、治疗建议或确定性健康事件。
```

### 默认语义权重矩阵

初始矩阵用于排序和生成种子问题，后续可训练微调。

| 宏观相 | peer | output | wealth | authority | resource | timing |
|---|---:|---:|---:|---:|---:|---:|
| 财富 | 0.45 | 0.70 | 0.95 | 0.35 | 0.25 | 0.55 |
| 事业 | 0.35 | 0.60 | 0.45 | 0.95 | 0.75 | 0.65 |
| 感情 | 0.55 | 0.45 | 0.75 | 0.75 | 0.40 | 0.50 |
| 亲情 | 0.65 | 0.45 | 0.65 | 0.35 | 0.85 | 0.35 |
| 健康 | 0.30 | 0.50 | 0.35 | 0.65 | 0.70 | 0.60 |
| 学业资质 | 0.25 | 0.45 | 0.20 | 0.70 | 0.95 | 0.45 |
| 表达作品 | 0.30 | 0.95 | 0.60 | 0.45 | 0.35 | 0.35 |
| 人际竞争 | 0.95 | 0.45 | 0.55 | 0.60 | 0.25 | 0.40 |
| 风险变动 | 0.65 | 0.75 | 0.55 | 0.85 | 0.35 | 0.75 |

训练边界：

```text
可训练：矩阵权重、宏观相排序、问题优先级。
不可训练：十神生成关系、排盘事实、五行事实。
```

## 种子问题生成

种子问题不能从固定模板列表里硬挑，必须从断语缺口生成。

流程：

```text
ClaimPool
-> 找出高价值但不确定的候选断语
-> 用 BaziSemanticOntology 找到关联十神和宏观相
-> 找出缺失用户信号槽位
-> 生成 QuestionIntent
-> 预测不同回答对 claim score 的影响
-> 选择信息增益最高且用户成本最低的问题
```

目标对象：

```json
{
  "version": "v30.question_intent.v1",
  "question_id": "q_career_authority_resource_path_001",
  "intent_type": "path_discrimination",
  "macro_domain": "career",
  "semantic_driver": {
    "ten_god_family": "authority",
    "path": "官杀 -> 印星"
  },
  "target_claim_ids": [],
  "missing_signal_slots": ["recent_responsibility_change", "platform_authorization"],
  "answer_mode": "single_choice",
  "options": [
    {"value": "responsibility_increased", "label": "职责变重"},
    {"value": "platform_changed", "label": "平台变化"},
    {"value": "want_transition", "label": "想转型"},
    {"value": "no_obvious_change", "label": "没明显变化"}
  ],
  "expected_score_delta": {
    "responsibility_increased": {"claim_boost": 0.16},
    "no_obvious_change": {"claim_weaken": 0.10}
  }
}
```

问题链不是一次全部展示。中枢只展示当前最高价值问题。

建议对话链长度：

```text
普通页面：0-1 个问题
领域综合：最多 1 个问题
最终继续追问：一轮一个问题，可连续，但每轮重新计算
隐藏属性定位：最多 3 个核心问题，用户可随时跳过
```

## 问题策略算法

采用轻量 POMDP + Value of Information + Contextual Bandit + Adaptive Testing。

中枢状态视为 belief state：

```text
belief =
  chart_facts
  + evidence_graph
  + claim_scores
  + hidden_factor_posterior
  + known_user_signals
  + active_stage
```

问题评分：

```text
question_score =
  information_gain * 0.35
+ claim_impact * 0.22
+ advice_value * 0.18
+ hidden_factor_gain * 0.14
+ training_value * 0.06
- user_cost * 0.12
- ghost_penalty * 0.20
- repetition_penalty * 0.30
- overask_penalty * 0.18
```

动作评分：

```text
action_score =
  user_value * 0.30
+ confidence_gain * 0.22
+ actionability * 0.18
+ timing_relevance * 0.10
+ training_value * 0.06
- interaction_cost * 0.12
- overclaim_risk * 0.20
```

可选动作：

| 动作 | 含义 |
|---|---|
| `conclude` | 证据足够，直接给结论和建议 |
| `ask` | 当前页面有一个必要问题 |
| `drill_hidden` | 隐藏属性后验不稳定且会影响结论 |
| `ask_negative_evidence` | 高分断语需要反证确认 |
| `request_timing_context` | 时运信息缺失会影响判断 |
| `continue` | 当前页面不问，进入下一页 |
| `stop` | 不再打扰用户，收束报告 |

问题出现阈值：

```text
show_question if:
  question_score >= page_threshold
  and information_gain > user_cost
  and not recently_asked_same_semantic_slot
  and current_stage_allows_question
```

## 页面出现策略

问题必须贴着页面主题出现。

| 页面 | 可出现问题 | 不该出现 |
|---|---|---|
| 排盘页 | 出生时间、时区、阴阳历、是否使用真太阳时、当前年份 | 事业财运泛问 |
| 规则匹配 | 关键规则冲突、某条规则是否贴近现实 | 关系/健康泛问 |
| 特征抽取 | 哪类十神表现更明显：压力、输出、资源、财务、同侪 | 复杂隐藏属性表单 |
| 画像投影 | 哪个画像更像用户的现实行为 | 多个画像一起问 |
| 做功路径 | 路径判别：输出换资源、压力转资质、资源承接、比劫分财 | 年份细节长表单 |
| 结构判断 | 旺衰/格局/用神候选的反证或承接方式 | 低价值兴趣问题 |
| 时运层 | 明显年份、阶段压力、当前大运是否贴身 | 和时运无关的问题 |
| 领域综合 | 用户最关心的现实选择和建议方向 | 多领域问题池 |
| 最终追问 | 用户主动继续时的一问一答链 | 阶段推演失败提示 |

## 隐藏属性对话

隐藏属性是为了解释“同盘不同命”和用户现实差异。它不是玄学标签，也不是让用户填模型变量。

核心信号槽：

```text
domain: career / wealth / relationship / family / health / learning
recurrence: once / repeated / periodic
year_anchor: concrete year
trigger: self_initiated / external_pressure / family_drag / partnership / platform
cost: money / energy / relationship / opportunity / health
outcome: improved / worsened / stuck / repeated
confidence: high / medium / low
```

隐藏属性后验：

```text
P(hidden_attribute | user_signals)
  ∝ P(user_signals | hidden_attribute) * P(hidden_attribute | chart_context)
```

问题选择采用自适应测试思路：

```text
select question with max expected posterior entropy reduction
```

隐藏属性问题示例：

```text
这个盘里有一条反复消耗线，需要先定位落点。
近两年最反复牵制你的，是哪一类？

[职责压力] [财务波动] [关系拉扯] [家庭牵制]
```

如果用户选择“职责压力”，下一轮才问：

```text
这种职责压力更像哪一种？

[责任变重后能力提升]
[压力变重但消耗变大]
[平台/上级变化]
[没有明显年份]
```

隐藏属性边界：

```text
可以更新：hidden_factor_belief、question_policy、claim_score_delta。
不可以更新：命盘事实、十神事实、大运流年事实。
```

## 结论与建议生成

用户关心的是结论和建议。

每次回答都必须按这个顺序：

```text
结论
建议
依据
下一步是否需要追问
```

不要用空话：

```text
不合格：这个问题需要结合实际情况综合判断。
合格：这个盘事业不是单纯求变，而是先把职责和平台授权做实，再争取位置上升。
```

LLM 输入必须是中枢裁决后的结构化材料：

```text
accepted_claims
supporting_evidence
counter_evidence
user_signals
hidden_factor_belief_summary
advice_constraints
forbidden_claims
```

LLM 输出必须被中枢清洗：

```text
remove unsupported facts
remove schema/internal words
remove vague phrases
ensure conclusion first
ensure actionable advice
```

## 可训练设计

所有智能相关策略都要可训练。

### 可训练对象

| 模块 | 可训练内容 | 不可训练内容 |
|---|---|---|
| BaziSemanticOntology | 十神到宏观相权重、领域排序 | 十神生成关系 |
| ClaimScorer | 证据权重、反证权重、行动价值权重 | 候选断语的事实来源 |
| QuestionPolicy | 问题出现阈值、问题排序、用户成本 | 命盘事实 |
| HiddenFactorBelief | 信号似然、后验更新权重 | 确定性隐藏干支事实 |
| DialoguePlanner | conclude/ask/continue 策略 | 四柱和大运事实 |
| AnswerComposer | 表达密度、建议力度、反空话规则 | 八字事实 |

### 训练样本

每次对话都记录：

```json
{
  "version": "v30.dialogue_decision_trace.v1",
  "reading_id": "...",
  "stage_id": "path_reasoning",
  "semantic_state": {},
  "claim_scores_before": [],
  "hidden_factor_belief_before": {},
  "candidate_questions": [],
  "selected_action": "ask",
  "selected_question_id": "...",
  "user_answer_signal": {},
  "claim_scores_after": [],
  "hidden_factor_belief_after": {},
  "answer_quality": {
    "conclusion_first": true,
    "advice_actionable": true,
    "vague_phrase_count": 0,
    "unsupported_fact_count": 0
  },
  "user_feedback": {
    "continued": true,
    "skipped": false,
    "liked": null
  },
  "training_targets": [
    "question_policy",
    "claim_score_weights",
    "hidden_factor_belief",
    "answer_expression"
  ],
  "blocked_targets": [
    "chart_facts",
    "pillar_calculation",
    "luck_cycle_facts"
  ]
}
```

### 训练目标函数

```text
brain_score =
  conclusion_accuracy * 0.28
+ advice_actionability * 0.24
+ evidence_binding * 0.18
+ question_necessity * 0.14
+ hidden_factor_alignment * 0.10
+ user_continuation_quality * 0.06
- user_effort * 0.10
- vague_answer_penalty * 0.20
- ghost_question_penalty * 0.30
- unsupported_fact_penalty * 0.50
```

### 训练闭环

```text
runtime dialogue trace
-> training signal extraction
-> policy candidate
-> synthetic validation
-> 518K sample/shard validation
-> shadow replay
-> promotion candidate
-> runtime pointer
-> rollback metadata
```

训练信号：

```text
v30.training_signal.dialogue_brain_action
v30.training_signal.semantic_domain_mapping
v30.training_signal.seed_question_policy
v30.training_signal.hidden_factor_belief_update
v30.training_signal.answer_actionability_quality
```

所有训练候选都必须声明：

```text
trains_question_strategy_not_chart_facts
trains_expression_not_bazi_facts
trains_hidden_factor_belief_not_hidden_stems
```

## 天府系统参考点

天府系统值得参考的是产品体验和推演组织方式：

- 多步骤拆解，让用户看到专业推演过程。
- 类 Agent 的分工感，而不是一次性黑盒输出。
- 用户能在推演过程中互动，而不是最后才问。
- token/成本意识可以作为未来接口预留。

V30 不照抄 UI，也不把 LLM 变成算命主体。V30 的优势应是：

```text
传统命理结构化事实
+ 中枢证据图
+ 可训练对话策略
+ 合成验证
+ LLM 表达增强
```

## 目标 API 投影

未来前端只消费一个当前回合：

```json
{
  "current_dialogue_turn": {
    "version": "v30.current_dialogue_turn.v1",
    "stage_id": "domain_synthesis",
    "action": "ask",
    "question": {
      "question_id": "...",
      "label": "最近一年你的工作更像哪一种变化？",
      "answer_mode": "single_choice",
      "options": []
    },
    "why_now": "这个问题会决定事业建议是稳定承接还是转型突破。",
    "target_claim_ids": [],
    "hidden_factor_probe": false,
    "ui_policy": {
      "max_visible_questions": 1,
      "allow_free_text": false,
      "show_engine_diagnostics": false
    }
  }
}
```

前端禁止从 `questions[]` 自行挑选问题。`questions[]` 可以继续作为兼容字段，但客户 UI 只渲染 `current_dialogue_turn`。

## 轻量可视化设计

在简洁智能对话之上，可以加一个小的可视化元素，但它必须服务“更直观看懂结论和建议”，不能变成新的复杂面板。

第一版可视化对象：

```text
current_dialogue_turn.visual_hint
answer_panel.visual_hint
```

形态：

| kind | 用途 | 内容 |
|---|---|---|
| `advice_compass` | 普通智能追问 | 主题 chips、信息增益、输入成本、回答后会收束到的建议方向 |
| `hidden_signal_probe` | 隐藏属性校准 | 领域、重复性、年份线索、只作校准不改命盘事实 |
| `stage_conclusion_marker` | 不追问时 | 说明本页证据足够，直接给结论 |

设计规则：

1. 每次最多一个视觉元素。
2. 视觉元素必须来自中枢结构化结果，不从 LLM 文本硬猜。
3. 不显示 raw score、policy weight、schema、JSON、内部诊断。
4. 不影响主阅读顺序，结论和建议仍然优先。
5. 隐藏属性可视化只显示用户可理解的领域、年份、重复性、代价，不显示模型变量。

后续可扩展：

```text
career_path_card      事业路径：稳定承接 / 职责上升 / 转型突破
wealth_risk_meter     财务风险：主动争取 / 保守积累 / 合作分配
relationship_loop     关系模式：拉扯点 / 边界点 / 改善建议
hidden_signal_map     隐藏线索：领域 / 年份 / 重复性 / 代价
timing_trigger_line   时运触发：大运 / 流年 / 当前阶段
```

## 任务计划

### DBR-0 设计冻结

状态：本轮完成。

输出：

- `V30_DIALOGUE_BRAIN_REDESIGN_20260627.md`
- 明确旧系统清理边界。
- 明确命理语义本体、问题策略、隐藏属性、训练闭环。

验收：

- 文档覆盖旧系统清理、中枢建模、算法、训练和任务计划。

### DBR-1 旧对话系统审计与清理清单

状态：已启动，第一版审计完成。

输出：

```text
docs/V30_DIALOGUE_SYSTEM_CLEANUP_AUDIT_20260627.md
```

目标：

- 列出所有当前对话入口、问题选择入口、隐藏属性入口、前端渲染入口。
- 标记保留、收编、废弃、迁移。
- 先清除无调用旧 UI/函数，再迁移仍被运行时依赖的旧决策链。

重点文件：

```text
v30/questions/recommender.py
v30/questions/dag.py
v30/interaction_brain.py
v30/brain/reading_engine.py
v30/hidden_factor/*
v30/presentation/client_model.py
frontend/app.js
```

验收：

- 客户侧只有一个问题入口。
- 前端不再自行挑选问题。
- admin 诊断和客户投影彻底分开。
- `recommend_questions()` 降级为 candidate scorer。
- `QuestionDialogueGraph` 降级为 memory/relation graph。
- `current_dialogue_turn` 成为客户 UI 唯一对话出口。

### DBR-2 BaziSemanticOntology v1

状态：已完成第一版。

目标：

- 建立十神、宏观相、六亲、健康五行、关键词、权重矩阵。
- 给中枢、问题生成、训练信号统一使用。

建议模块：

```text
v30/semantics/ontology.py
v30/semantics/domain_mapping.py
```

验收：

- 每个候选断语能映射到 macro_domain 和 semantic_driver。
- 每个问题能说明来自哪个十神/宏观相缺口。
- 训练信号能记录 semantic weight slot。

实现：

- `v30/semantics/ontology.py`
- `v30/semantics/domain_mapping.py`
- `recommend_questions().semantic_projection`
- `central_reading_state.semantic_ontology`
- `dialogue_plan.semantic_trace`
- `reading_surface.current_dialogue_turn.semantic_focus`

### DBR-3 DialogueBrainState v1

目标：

- 在 `CentralReadingState` 之上增加对话决策状态。
- 合并当前 claim、semantic focus、hidden belief、known user signals、current turn。

验收：

- thinking/view payload 能看到 `dialogue_brain_state`。
- 每个 current turn 都有 `target_claim_ids` 和 `why_now`。
- 无 current turn 时明确 action=`conclude` 或 `continue`。

### DBR-4 种子问题生成器

目标：

- 从 ClaimPool 缺口生成 `QuestionIntent`。
- 不再依赖固定问题池作为主要来源。

算法：

```text
claim_gap -> semantic_driver -> missing_signal_slot -> question_intent -> expected_score_delta
```

验收：

- 事业、财富、感情、健康、亲情至少各有一类动态生成问题。
- 问题选项可直接转成 structured signal。
- 问题不是模板裸问，必须绑定当前八字证据。

### DBR-5 隐藏属性自适应对话

目标：

- 用后验模型定位隐藏属性，不让用户填复杂表单。
- 每次只问一个核心现象。

验收：

- 隐藏属性问题覆盖 domain、recurrence、year、trigger、cost、outcome。
- 用户选择能更新 hidden_factor_belief。
- 跳过/否认能降权，不反复骚扰用户。

### DBR-6 QuestionPolicy 与 DialoguePlanner

目标：

- 统一 decide ask/conclude/continue。
- 加入 ghost penalty、overask penalty、user cost。

验收：

- 每个页面最多一个问题。
- 问题只在 threshold 通过时出现。
- 低价值问题不会出现。
- 回答后下一问题重算，不重复当前问题。

### DBR-7 AnswerComposer 与 LLM 边界

目标：

- 回答由中枢结构化结论驱动，LLM 只做表达。
- 输出结论优先、建议具体、无空话。

验收：

- 回答必须包含结论和建议。
- 不出现 schema、JSON、诊断口径、证据计数。
- 无 LLM 时不伪造智能结论。

### DBR-8 训练链路

状态：已完成第一版。

目标：

- 每次对话产生 `DialogueDecisionTrace`。
- 训练提取 semantic mapping、question policy、hidden belief、answer quality。

验收：

- synthetic validation 能消费 dialogue trace。
- candidate policy 不可触碰 chart facts。
- 回滚和 pointer lineage 可追踪。

实现：

- `v30/brain/dialogue_training.py`
- `central_reading_state.dialogue_training_trace`
- `central_reading_synthetic_validation.dialogue_training_trace`
- blocked targets 固定包含 `chart_facts`、`calendar_conversion`、`pillar_calculation`。

### DBR-9 前端产品化

状态：已完成第一版。

目标：

- 前端只渲染 `current_dialogue_turn`。
- 问题、回答、下一步动作极简。

验收：

- 没有问题池。
- 没有工程语言。
- 隐藏属性输入不超过一组选择 + 可选年份。
- 用户点击后看到回答，回答后刷新下一问。

实现：

- `projection_contract.dialogue_entry_policy` 明确客户主入口是 `reading_surface.current_dialogue_turn`。
- `questions[]` 保留为兼容字段和非客户诊断字段。
- `current_dialogue_turn.ui_policy.max_visible_questions = 1`。

### DBR-10 合成验证与回归

目标：

- 为新对话脑建立专门 synthetic tier。

建议用例：

```text
dialogue_brain.career_authority_resource_path
dialogue_brain.wealth_output_to_wealth_vs_peer_loss
dialogue_brain.relationship_spouse_star_conflict
dialogue_brain.hidden_factor_repeated_pressure
dialogue_brain.no_question_when_low_value
dialogue_brain.no_chart_fact_mutation
dialogue_brain.answer_conclusion_first
dialogue_brain.frontend_single_question_projection
```

验收：

- 新 tier 全过。
- 旧 question interaction 测试保留兼容。
- UI 回归保证每屏一个问题。

## 第一轮实施顺序

建议从最能消除历史包袱的地方开始：

1. 做 DBR-1 审计，列清旧入口。
2. 做 DBR-2 语义本体，不先动 UI。
3. 做 DBR-3/DBR-4，让中枢产生 `current_dialogue_turn`。
4. 前端改为只消费 `current_dialogue_turn`。
5. 再做隐藏属性自适应和训练链路。

这样不会又变成前端补丁，也不会让 LLM 或问题池继续越权。

## 外部方法参考

- POMDP dialogue management: belief state and policy based dialogue control.
- Value of Information: only ask when expected information gain beats user cost.
- Contextual bandit: train question ordering from interaction outcomes.
- Computerized Adaptive Testing: hidden attribute question selection by posterior uncertainty reduction.
- Tianfu Agent product pattern: staged decomposition, visible professional process, agent-like reasoning flow.

V30 采用这些方法的工程化简化版，不把系统做成纯学术模型。核心是让中枢智能大脑在每个页面做出稳定、可解释、可训练的下一步决策。
