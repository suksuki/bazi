# V30 Decision-Centered Architecture 主线设计

更新时间：2026-06-29

## 结论

V30 下一阶段主线升级为：

```text
干净事实与素材
-> 可训练权重
-> Decision Engine 裁决
-> LLM 表达
-> 智能对话
```

这次调整的核心不是继续增加页面，也不是让 LLM 每一步多写一段解释，而是把八字测算过程从“逐页生成长文”改成“逐步沉淀干净素材，最后由裁决引擎统一断事”。

当前 13 步流程太长，且每一步都让 LLM 解释，会把规则、画像、路径、用神、时运等素材洗成长文。长文看似专业，实际上会污染后续判断：素材变啰嗦、证据边界变模糊、分支概率被语言掩盖，最终中枢大脑拿到的是被表达层加工过的二手材料。

新主线必须把“食材”和“成菜”分开：

- 步骤页负责快速产出事实、候选、分支、证据、反证和待校准项。
- 中枢智能大脑负责调度、记忆、训练、权重和对话策略。
- Decision Engine 是唯一最终命理裁决出口。
- LLM 负责最终表达、必要解释、问题措辞和边界复核，不负责最终断命理结论。

## 架构宪法

### 1. LLM 没有最终断语权

LLM 可以：

- 把裁决结果翻译成通俗、专业、有温度的用户语言。
- 根据已给素材组织候选解释。
- 为智能对话生成自然的问题措辞。
- 辅助发现文本里的选项、数字、列表、风险和追问需求。
- 做输出边界自检。

LLM 不可以：

- 修改四柱、十神、五行、旺衰、规则命中、路径计算等事实层。
- 凭语言感觉推翻结构化证据。
- 在没有 Decision Engine 裁决的情况下直接生成最终结论。
- 在步骤页默认输出大段解释，把素材污染成长文。

### 2. 可训练中枢权重没有最终断语权

训练系统和 Central Feedback Overlay 可以改变：

- claim ranking
- branch probability
- evidence weight
- next question priority
- final synthesis ordering
- practitioner feedback weight

但训练系统不能直接改变：

- 命盘事实
- 原始规则命中
- 大运流年计算
- 决策边界
- 断语等级

训练结果是权重输入，不是最终裁判。最终裁判仍然必须经过 Decision Engine。

### 3. 规则、画像、特征、路径都不是最终结论

这些模块是素材层：

- 规则负责命中特定命理条件。
- 画像负责提供人格、领域、倾向信号。
- 特征负责抽取可复用标签。
- 路径负责解释力量流向和做功结构。
- 用神忌神负责提供取用候选与风险边界。

它们都可以提出候选，不能单独下最终断语。

### 4. 分支与概率必须保留

之前把“可能、候选、几选一”全部清理掉是不对的。八字判断经常存在分支，只是分支有不同证据强度和概率。

新规则：

- 允许候选、分支、概率、待复核。
- 每个分支必须绑定证据、反证、置信度、复核条件和适用范围。
- 普通用户默认看到主分支，必要时看到 2 到 3 个重要分支，但不能直接修改权重。
- 命理师和 admin 可以看到完整分支，选择采纳、降权、排除、待问或备注。
- 命理师选择反馈给中枢权重和训练样本，不改命盘事实。

## 分层架构

```text
L0 输入与事实层
出生资料、历法、四柱、藏干、十神、五行、大运、流年

L1 素材候选层
规则命中、画像标签、特征标签、路径候选、用神候选、时运触发、领域信号

L2 学习权重层
Central Feedback Overlay、用户回答、命理师选择、历史样本、合成验证分布

L3 Decision Engine
证据评分、路径连贯、冲突处理、分支概率、断语等级、允许/禁止断语

L4 Boundary Verifier
事实边界、过度断言、安全边界、角色边界、用户可读边界

L5 LLM Expression
最终表达、摘要、建议、对话问题、必要解释

L6 UI Projection
步骤页素材、边栏记忆、命理师校准、最终断语、智能对话
```

中枢智能大脑不是一个单点函数，而是一组协作模块：

- Orchestrator：决定当前该跑哪些素材模块。
- Working Memory：把关键素材同步到边栏和后续上下文。
- Learning Overlay：吸收用户回答和命理师选择形成权重信号。
- Decision Engine：唯一生成可输出断语的裁决模块。
- Dialogue Planner：只在信息增益足够时发起智能追问。
- Final Synthesis：消费 Verdict，不直接消费未裁决长文。

## 核心数据契约

### DecisionInputBundle

```text
chart_facts
rule_candidates
portrait_signals
feature_signals
path_candidates
useful_god_candidates
timing_signals
domain_signals
feedback_overlay
practitioner_selections
dialogue_answers
```

要求：

- 只收结构化事实和候选。
- 不收页面长文解释作为主证据。
- LLM 文本只能作为 expression note 或 candidate text，不能直接作为事实。

### Candidate

每个候选统一包含：

```text
id
type
claim
domain
evidence_refs
counter_evidence_refs
confidence
source_module
scope
requires_calibration
role_visibility
```

典型候选：

- `RuleCandidate`
- `PathCandidate`
- `PortraitSignal`
- `FeatureSignal`
- `UsefulGodCandidate`
- `TimingSignal`
- `DialogueNeed`

### Verdict

Decision Engine 输出 `Verdict`：

```text
id
domain
headline
assertion_level
confidence
primary_branch
alternative_branches
evidence_refs
counter_evidence_refs
allowed_assertions
forbidden_assertions
advice_points
next_question_slots
trace
```

`assertion_level` 只能取：

- `confirmed`：证据强、路径顺、反证弱，可以明确断。
- `supported`：证据较强，可以作为当前主判断。
- `mixed`：证据分裂，必须列分支。
- `weak_candidate`：只能作为候选，不能下重断语。
- `blocked`：关键事实缺失或冲突过高，必须追问或提示无法定论。

## Decision Engine 算法

### 1. 素材归一化

把规则、画像、特征、路径、用神、时运、对话反馈统一成候选。

重点：

- 统一命名。
- 统一 evidence refs。
- 去掉工程枚举。
- 保留分支和概率。
- 不使用 LLM 长文作为素材主干。

### 2. 证据评分

每个候选计算：

```text
evidence_score
= fact_strength
* source_reliability
* path_coherence
* domain_relevance
* feedback_weight
- counter_evidence_penalty
- overclaim_penalty
- missing_fact_penalty
```

解释：

- `fact_strength` 看命盘事实和规则命中强度。
- `source_reliability` 看模块可靠性和验证历史。
- `path_coherence` 看是否能被做功路径解释。
- `domain_relevance` 看是否贴合当前页面或对话主题。
- `feedback_weight` 来自用户回答和命理师校准。
- 惩罚项用于防止模糊、过断、无证据和事实缺失。

### 3. 路径连贯评分

八字不是关键词匹配，必须看力量如何流动。

路径评分关注：

- 日主强弱与承载能力。
- 十神之间是否形成生克制化链。
- 财官印食伤是否有通关、承接、泄秀或阻断。
- 用神候选是否能解释主要矛盾。
- 时运触发是否与原局路径一致。

路径不连贯的候选，不允许进入高等级断语。

### 4. 冲突处理

冲突不应该被语言抹掉，而应该结构化：

```text
Conflict
- conflict_type
- branch_a
- branch_b
- evidence_for_a
- evidence_for_b
- resolution_policy
- needed_question
```

处理策略：

- 证据明显强弱分明：主分支 + 次分支。
- 证据接近：输出 `mixed`，等待命理师或用户校准。
- 关键事实缺失：输出 `blocked` 或生成一个必要追问。
- 领域不相关：降权，不进入当前页。

### 5. 断语等级门控

示例门槛：

```text
confirmed: confidence >= 0.82 且无强反证
supported: confidence >= 0.65 且路径连贯
mixed: 主分支与次分支差距不足 0.15
weak_candidate: 有证据但缺关键事实
blocked: 事实缺失、冲突过高或安全边界触发
```

门槛后续可训练，但训练只能调整权重和阈值候选，不能绕过门控。

### 6. 允许断语与禁止断语

每个 Verdict 必须同时生成：

- `allowed_assertions`：可以对用户说什么。
- `forbidden_assertions`：不可以说什么。

例如：

```text
allowed_assertions:
- 当前更适合先稳住职责和资质承接，再谈转型。
- 财务判断应优先看资源转化和输出兑现。

forbidden_assertions:
- 不能断某一年必发财。
- 不能把未确认的职业背景说成事实。
- 不能把用神候选说成已经定死。
```

LLM 最终表达必须只在 `allowed_assertions` 内发挥。

## 八字测算步骤重构

现有 13 步需要压缩。新的用户体验不再每步都等 LLM 长文，而是快速沉淀素材，最后统一裁决。

建议新流程：

```text
1. 资料与排盘校准
2. 结构、十神与用神候选
3. 规则、画像与特征素材
4. 做功路径、时运与领域触发
5. 分支冲突与命理师校准
6. Decision Engine 裁决
7. 最终断语、建议与智能对话
```

### 第 1 步：资料与排盘校准

输出：

- 四柱/六柱事实。
- 日主、月令、藏干、十神基础。
- 数据置信度。
- 是否需要校准出生时间。

LLM：

- 默认不调用。
- 只有用户要求解释排盘时才调用表达层。

### 第 2 步：结构、十神与用神候选

输出：

- 强弱候选。
- 格局候选。
- 用神候选。
- 忌神候选。
- 关键反证。

命理师模式：

- 可选择主用神候选。
- 可标记待复核。
- 可降权明显不合理候选。

LLM：

- 默认不生成长文。
- 只在最终表达时解释“为什么这么取用”。

### 第 3 步：规则、画像与特征素材

输出：

- 命中的规则。
- 画像标签。
- 特征标签。
- 与领域相关的素材。
- 每条素材的证据引用。

UI：

- 列表化展示。
- 不展示工程字段。
- 不把素材扩写成报告。

### 第 4 步：做功路径、时运与领域触发

输出：

- 主要路径。
- 阻断路径。
- 时运触发。
- 财富、事业、感情、健康、亲情等领域信号。

注意：

- 这一步只做路径素材，不做最终人生结论。
- 领域判断只作为 Decision Engine 输入。

### 第 5 步：分支冲突与命理师校准

输出：

- 分支列表。
- 冲突列表。
- 需要回答的关键问题。
- 命理师可选项。

普通用户：

- 只显示必要的一两个关键确认。
- 不显示复杂权重控件。

命理师：

- 可以采纳、降权、排除、待问、备注。
- 选择进入 Central Feedback Overlay。

### 第 6 步：Decision Engine 裁决

输出：

- Verdict 列表。
- assertion level。
- 主分支与备选分支。
- 证据链。
- 反证边界。
- 允许断语和禁止断语。

LLM：

- 不参与裁决。
- 可作为 verifier 检查最终表达是否越界。

### 第 7 步：最终断语、建议与智能对话

输出：

- 用户可读结论。
- 具体建议。
- 风险提醒。
- 可执行行动。
- 智能对话入口。

LLM：

- 负责把 Verdict 转成自然语言。
- 对话只围绕 Decision Engine 给出的 `next_question_slots` 展开。
- 回答后更新 belief 和分支概率，再由 Decision Engine 重新裁决相关部分。

## LLM 调用策略

### 默认不在每个步骤页调用 LLM

步骤页默认只跑结构化模块：

- 排盘
- 规则
- 画像
- 特征
- 路径
- 用神
- 时运
- Text-to-Option
- Decision Engine

LLM 调用点收敛到：

1. 最终断语表达。
2. 用户点击“解释这一项”。
3. 智能对话回答生成。
4. 对话问题措辞生成。
5. 输出边界 verifier。
6. 管理员或命理师主动要求看 LLM 候选解释。

### 禁止 LLM 污染素材

禁止流程：

```text
规则素材
-> LLM 长文解释
-> 中枢再从长文里抽素材
```

正确流程：

```text
规则素材
-> 结构化候选
-> Decision Engine 裁决
-> LLM 最终表达
```

## 边栏工作记忆

边栏不应该显示长文，也不应该显示工程状态。

边栏同步：

- 当前命盘：日主、月令、性别、八字。
- 结构判断：强弱、格局、用神候选、忌神候选。
- 素材摘要：规则命中、画像标签、特征标签。
- 路径摘要：主路径、阻断路径、时运触发。
- 分支状态：已定、待定、冲突、需要校准。
- 裁决摘要：关键 Verdict、置信度、当前建议方向。

边栏展示原则：

- 只显示短标签、分数、状态和关键证据。
- 不放 LLM 长文。
- 点击后可以展开证据。
- 命理师模式可在边栏快速切换分支或标记待问。

## UI 调整原则

### 步骤页从“解释页”改成“素材页”

每个步骤页只保留：

- 本页主题。
- 本页产出的关键素材。
- 本页是否有冲突。
- 本页是否需要用户或命理师校准。
- 下一步按钮。

删除：

- 长篇小结。
- 工程状态。
- 模板化“结论：建议：”。
- 和本页无关的智能对话块。
- 重复展示全部步骤。

### 最终页才是“断语页”

最终页展示：

- 核心断语。
- 证据链。
- 建议清单。
- 风险边界。
- 后续智能对话。

文本应该由 LLM 表达，但必须绑定 Verdict。

### 智能对话是独立 surface

智能对话可以出现在任意页面，但不能成为测算步骤。

对话出现条件：

- Decision Engine 明确需要补关键事实。
- 当前分支冲突需要用户确认。
- 用户主动点击追问。
- 命理师触发校准问题。

对话不应该幽灵式出现，也不应该自问自答。

## 训练与验证

训练目标不是让模型会写漂亮话，而是让系统越来越会判断：

- 哪些候选更可靠。
- 哪些反证更关键。
- 哪些问题信息增益最高。
- 哪些分支应该保留。
- 哪些断语容易过度。
- 哪些建议更可执行。

训练样本必须包含：

```text
DecisionInputBundle
candidate_scores
practitioner_selection
user_feedback
verdict_before
verdict_after
assertion_level
forbidden_assertion_hits
final_expression_quality
```

验证必须覆盖：

- 素材不被 LLM 长文污染。
- 普通用户不会看到复杂命理师控件。
- 命理师选择不会修改命盘事实。
- Verdict 不越过 assertion level。
- LLM 最终表达不越过 allowed assertions。
- 13 步压缩后信息不丢失。
- 边栏 memory 与当前步骤同步。

## 主线任务计划

### DCA-1 文档与主线合并

状态：进行中。

目标：

- 新增本 canonical 文档。
- 更新文档索引。
- 更新主线状态。
- 更新下一阶段计划。

### DCA-2 Decision Contract

状态：基础落地完成。

新增或整理：

- `DecisionInputBundle`
- `Candidate`
- `Conflict`
- `Verdict`
- `AllowedAssertion`
- `ForbiddenAssertion`
- `DecisionTrace`

验收：

- 已新增 `DecisionInputBundle / DecisionCandidate / DecisionConflict / DecisionVerdict / DecisionEngineResult`。
- final synthesis 已开始优先消费 Decision Verdict。
- 每条 Verdict 都带 evidence refs、assertion level、allowed assertions 和 forbidden assertions。

### DCA-3 素材归一化管线

状态：基础落地完成。

把现有规则、画像、特征、路径、用神、时运统一转为候选。

验收：

- 现阶段已把 `diagnosis.claims + claim_scores + evidence refs + counter evidence + calibration flags` 归一化为 Decision Candidate。
- 候选已经保留分支、置信度、反证和待校准标记。
- 不需要 LLM 即可完成 DecisionInputBundle 生成。
- 后续仍需把规则、画像、特征、路径、用神、时运拆成更细 Candidate source，而不是只从 claim_scores 汇总。

### DCA-4 Decision Engine V1

状态：基础落地完成。

实现：

- candidate scoring
- path coherence
- conflict resolution
- branch probability
- assertion level gating
- allowed/forbidden assertions

验收：

- 已新增 `v30/brain/decision_engine.py`。
- 已接入 `build_central_reading_state`，输出 `decision_input_bundle / decision_verdicts / decision_result`。
- final synthesis 已优先消费 Verdict，并在 quality contract 标记 `uses_decision_verdicts`。
- LLM expression contract 明确不能 override Verdict。

### DCA-5 LLM Expression Boundary

状态：基础落地完成。

调整提示词和调用链：

- LLM 只消费 Verdict。
- LLM 输出必须通过 boundary verifier。
- 步骤页默认不触发 LLM 长文解释。

验收：

- `Bazi LLM context pack` 已新增 `decision_verdicts` section。
- prompt contract 已新增 `decision_verdict_boundary` 与 `allowed_forbidden_assertion_gate`。
- LLM context fact boundary 已声明 `llm_can_override_decision_verdict = False`。
- 页面素材不会依赖 LLM 长文回写。
- LLM 返回慢后续应只影响最终表达或对话，不阻塞素材步骤；这点还需要配合 DCA-6 页面流程压缩继续落地。

### DCA-6 13 步压缩为 7 步

状态：基础落地完成。

重构测算导航：

```text
13 个细碎步骤
-> 7 个高层阶段
-> 每阶段内部可展开素材
```

验收：

- 后端 `thinking_projection` 已新增 7 个 `journey_steps`。
- 旧 `steps` 保留为细粒度素材池，用于 StagePoint、LLM 细步接口和回归兼容。
- 前端导航和当前页面已优先使用 `journey_steps`。
- 7 个 journey step 默认 `llm_enhancement = not_required`，不再每页自动生成 LLM 长文。
- 边栏记忆仍映射到旧素材 step 顺序，随 7 阶段逐步释放。
- 智能对话不进入步骤导航；后续 DCA-9 继续让对话只由 `next_question_slots` 与 VOI 触发。

### DCA-7 命理师分支校准

状态：基础落地完成。

实现：

- 分支候选选择。
- 采纳、降权、排除、待问、备注。
- 选择进入 Central Feedback Overlay。

验收：

- Decision Verdict 的分支已能生成 `stage_point_branch` OptionSet。
- `collect_thinking_option_sets` 已扫描 `journey_steps`，命理师可在 7 阶段裁决页看到分支校准项。
- 普通用户隐藏，命理师和 admin interactive。
- 命理师选择仍走 `PractitionerSelection`，只影响 belief、权重、排序和训练信号，不改命盘事实。
- 命理师选择对下一次 Verdict 的深度重算仍需后续加强。

### DCA-8 边栏工作记忆同步

状态：基础落地完成。

实现：

- material memory projection。
- verdict memory projection。
- branch memory projection。

验收：

- 边栏持续同步命盘入口、规则、特征、画像、做功路径、结构、用神、时运、领域和 Decision Verdict。
- 新增 `decision.verdict` 记忆项，来自 Decision Engine Verdict，不来自 LLM 文本。
- 前端 7 阶段导航会把边栏可见范围映射回细粒度素材 step，做到阶段推进时逐步释放信息。
- 不显示 LLM 长文。
- 点击查看证据仍需后续 UI 打磨。

### DCA-9 智能对话重接入

状态：基础落地完成。

对话只由 Decision Engine 的 `next_question_slots` 和 VOI 策略触发。

验收：

- `DecisionVerdict.next_question_slots` 已能生成 `decision_engine_next_question_slot` 推荐问题。
- 当旧推荐问题存在时，保持旧问题优先，避免重复问题。
- 当推荐问题缺席时，Decision slot 补位进入 `reading_surface.current_dialogue_turn`。
- 前端 7 阶段页面会把对话 `stage_id` 映射到当前 journey 的 `material_stage_ids`，但对话仍是独立 surface，不进入步骤导航。
- 不自问自答、不幽灵出现和每次只聚焦一个问题已有基础保障。
- 回答后重算相关 Verdict 已在 DCA-11 形成基础反馈重算摘要，深度 UI 与质量 diff 继续后移。

### DCA-10 合成验证与 518K 分布观察

状态：基础落地完成。

新增专项 tier：

- decision_contract_validation
- material_bundle_cleanliness
- verdict_assertion_gate
- llm_expression_boundary
- step_compression_regression
- practitioner_branch_calibration
- sidebar_memory_projection

验收：

- 新增 `v30.validation.decision_centered_architecture` 轻量合成验证入口。
- 覆盖 Decision Engine current version、DecisionInputBundle 清洁边界、Verdict assertion gate、final synthesis Verdict 优先消费、LLM context 不越权、7 阶段压缩、边栏 Decision memory、命理师 Verdict 分支 OptionSet、Decision slot 对话补位和训练目标。
- 小样本 synthetic gate 可通过 `run_decision_centered_architecture_validation()` 执行。
- 518K sample/shard 分布观察保留为大节点任务，不作为每次小改默认动作。
- 大节点再跑全量重测试。

### DCA-11 Verdict 反馈与 Admin 训练联动

状态：基础落地完成。

目标：

- 用户回答和命理师选择进入 Central Feedback Overlay。
- Feedback Overlay 影响候选权重后，由 Decision Engine 重新生成 Verdict。
- Decision Engine 输出 `feedback_recalculation_summary`，说明反馈是否参与、影响哪些 candidate、claim、domain 和 verdict。
- Admin/训练系统可消费 `admin_training_projection`，但不能写生产策略或修改命盘事实。

验收：

- `DecisionEngineResult.feedback_recalculation_summary` 已新增。
- `CentralReadingState.decision_feedback_recalculation_summary` 已暴露。
- 摘要包含 `effect_count`、`domain_deltas`、`claim_deltas`、`score_adjustments`、`affected_candidate_ids`、`affected_verdict_ids` 和 `admin_training_projection`。
- 中枢训练目标新增 `decision_feedback_recalculation_quality`。
- DCA 轻量验证已覆盖反馈重算与 Admin training projection。
- 下一步是把这份 projection 接入 Admin 质量 diff、真实案例回放和命理师 UI 操作结果。

### DCA-12 Verdict 反馈质量 diff 与 UI 投影

状态：基础启动。

目标：

- 把 `feedback_recalculation_summary` 投影到用户、命理师和 Admin 可消费的数据模型。
- 普通用户只看到反馈是否参与校准，不看到 candidate id、score delta、训练目标等诊断细节。
- 命理师/Admin 可以看到 affected candidate、affected verdict、score adjustment 和 admin training projection。
- 后续再接 Admin 质量 diff、真实案例回放和 UI 交互细节。

验收：

- `reading_surface.decision_feedback` 已新增。
- user/guest 只输出 customer summary。
- practitioner/admin/analyst/lab 输出 diagnostic projection。
- 投影不允许 chart fact mutation，不推广 policy pointer。
- 已补角色隔离测试。

## 执行顺序

短期先做：

```text
DCA-1
-> DCA-2
-> DCA-3
-> DCA-4
```

然后做产品体验：

```text
DCA-5
-> DCA-6
-> DCA-8
-> DCA-9
```

最后补训练闭环：

```text
DCA-7
-> DCA-10
-> DCA-11
-> DCA-12
```

命理师模式可以和 DCA-7 提前并行，但不应该阻塞 Decision Engine 主闭环。

下一步 `DCA-12` 聚焦 Verdict 反馈质量 diff 与 UI 投影：把反馈重算摘要显示到 Admin 回放、命理师分支选择和真实案例验证里，形成可观察的训练改进闭环。

## 当前主线判断

这次架构调整会降低“每一步看起来都有 LLM 在说话”的表面热闹，但会显著提高系统判断质量。

V30 的目标不是做一个会写八字报告的聊天机器人，而是做一个：

```text
有事实层
有素材层
有分支
有概率
有命理师校准
有训练闭环
有最终裁决
有边界表达
```

的八字智能测算系统。
