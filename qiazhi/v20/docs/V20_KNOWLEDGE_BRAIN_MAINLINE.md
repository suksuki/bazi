# V20 知识库 × 中枢大脑主线

更新时间：2026-05-16

当前状态：`knowledge_completeness_audit` 第一版已完成，P0 外部专题缺口清零；知识 guidance 已进入回答链路，回答治理质量评分已进入训练迭代，并能反向调整 knowledge runtime pointer 的 answer guidance 权重；角色视图已消费回答治理 profile，为游客、用户、命理师、管理员生成不同的边界密度和复核口径；角色答案治理质量已纳入 synthetic replay 统计，并直接进入 answer_governance_training 的参数目标；`role_answer_governance_weight` 已接入 role-view runtime pointer 和角色答案投影，即使没有点击候选也能直接影响角色答案策略；训练包已接通多 pointer 自动生效；中枢大脑已能报告训练策略是否参与主线排序和问题聚焦；`mainline_status` 已提供机器可读的主线收口状态，明确训练参数目标直生效、无人工审核 gate。
新增：`knowledge_rule_orchestrator` 已把新增知识点、规则候选生成、合成验证、知识规则 overlay 和 runtime pointer 生效路径合成一个中枢编排任务，Admin 训练页可直接运行“知识规则联合训练”。
新增：中枢大脑智能架构已落成独立主线文档 `docs/V20_CENTRAL_BRAIN_INTELLIGENCE_ARCHITECTURE.md`，并提供 `/api/v20/admin/central-brain-architecture` 机器状态，后续 Admin UI 以此升级为中枢训练控制台。

## 目标

当前主线不是继续堆脚本，而是把八字知识库做完备，并让它真正进入中枢大脑。

```text
八字知识点
-> KnowledgeUnit / KnowledgeRuleDefinition
-> knowledge_basis evidence
-> MainlineArbitration
-> BrainState.knowledge_basis
-> BrainState.runtime_policy_coordination
-> AnswerGuidance
-> 训练后自动优化 knowledge/runtime pointer
```

原则：

- 知识库是结构事实和判断边界的来源，不直接输出吉凶断语。
- 中枢大脑必须能看到知识依据，不能只看到 decision 结果。
- 每个知识点最终都要绑定：证据原子、规则路径、画像投射、推荐问题、回答边界、反例。
- 训练不走人工审核；机器 gate 通过后直接写 active pointer，未通过则显示阻断原因。
- 训练包会同时尝试中枢、问题、角色视图、规则、画像、知识和语料 pointer，某个 gate 阻断不影响其他可生效 writer。
- 中枢大脑必须解释训练 pointer 当前是 baseline、生效命中、已启用但未命中，还是暂无可用策略。

## 当前状态

本地知识目录已经覆盖 13 个节点：

| 节点 | 主题 | 当前判断 |
|---|---|---|
| L0 | 排盘与基础符号 | 已补排盘边界、藏干权重原子知识和 synthetic case |
| L1 | 五行与气候 | 已补日主 × 月令调候原子知识，进入规则/画像/问答链路 |
| L2 | 强弱与承载 | 主线已覆盖，仍需更多边界与反例 |
| L3 | 十神系统 | 覆盖较广，位置/组合细则需增强 |
| L4 | 干支关系 | 覆盖较广，多重关系仲裁需增强 |
| L5 | 格局系统 | 规则数最多，需加强特殊格局与假格反例 |
| L6 | 用神与取用路径 | 已补用神路径冲突仲裁原子知识，保留候选、反证和降权原因 |
| L7 | 宫位与象法 | 已补宫位主题、事业宫位、时柱家庭/晚景 3 类 synthetic case |
| L8 | 盲派系统 | 已补辅助取象、做功链、反证边界 3 类 synthetic case，只作线索入口并回到结构复核 |
| L9 | 岁运时间系统 | 已补原局/大运/流年/流月触发栈边界，不输出确定事件 |
| L10 | 领域应用 | 已补学业考试、子女家庭、迁移远行、房产居住、人际合作、创业管理第一批应用专题，并补第一批反例边界 |
| L11 | 辅助体系与归档 | 已补第一批神煞/空亡/纳音低权重辅助边界和 synthetic case；下一步继续原子拆分 |
| L12 | 回答表达与治理 | 已补证据边界、角色边界、下一步问题 3 类 synthetic case |

当前 `KnowledgeRuleLibrary` 统计：

```text
definition_count: 494
runtime_allowed_count: 494
domains:
  strength: 16
  ten_god: 32
  useful_god: 10
  element: 11
  branch: 104
  wealth: 36
  pattern: 187
  time: 57
  career: 16
  relationship: 20
  health: 5
```

最新中枢接入状态：

```text
knowledge_rule_refs -> knowledge_basis evidence -> mainline arbitration -> brain_state.knowledge_basis
runtime_policy_pointer -> mainline/question policy effect -> brain_state.runtime_policy_coordination
```

运行样例：

```text
orchestrator evidence: 177
knowledge_basis evidence: 111
brain knowledge_basis: 3
primary mainline: 伤官见官
```

## 外部知识体系对照

外部常见八字知识体系基本集中在这些层：

| 外部常见层 | 外部资料观察 | 本地覆盖 | 缺口判断 |
|---|---|---|---|
| 四柱与排盘 | 四柱由年、月、日、时四组干支构成，月令是旺衰、格局、用神的重要依据 | L0 已覆盖 | 第一批真太阳时、节气、早晚子时边界已原子化，继续扩历史时区 case |
| 天干地支与藏干 | 天干、地支、藏干、季节旺衰、通根透出是基础材料 | L0/L4 已覆盖 | 第一批藏干权重已原子化，继续扩透干通根、同柱/邻柱作用权重 |
| 五行与气候 | 五行生克、寒暖燥湿、调候是判断平衡的重要层 | L1 已覆盖 | 第一批日主 × 月令调候已原子化，继续扩调候候选表 |
| 十神系统 | 十神用于描述日主与其他干支关系，是性格、事业、财运、关系等主题的核心标签 | L3 已覆盖 | 需补十神落年/月/日/时、明透/暗藏/重复/混杂的差异 |
| 强弱与用神 | 身强身弱、喜忌、用神是大运流年判断关键 | L2/L6 已覆盖 | 第一批取用路径冲突仲裁已原子化，继续扩岁运动态权重 |
| 格局与特殊格 | 正格、特殊格、从格、成败清浊是进阶体系 | L5 覆盖最多 | 缺“假从/破格/清浊混杂”的合成反例 |
| 大运流年 | 大运看十年环境，流年必须和原局、大运合看 | L9 已覆盖 | 第一批原局/大运/流年/流月触发栈已原子化，继续扩岁运并临、伏吟反吟、墓库开闭 |
| 神煞/纳音/空亡/十二长生 | 多数资料把神煞视为辅助，不能替代原局干支生克制化 | L11 已归档 | 第一批低权重辅助边界已原子化，继续扩常见神煞反例 |
| 宫位象法 | 年月日时、夫妻宫、事业环境、子女晚景等用于定位主题 | L7 已覆盖 | 已补宫位主题投射边界，下一步扩夫妻宫、事业宫位和时柱晚景细分 case |
| 领域应用 | 事业、财富、婚恋、健康、学业、迁移、房产、人际、创业等是用户真实问题入口 | L10 已覆盖第一批 | 已补第一批过度推断反例，下一步扩细分 case |

参考资料：

- MingDecode 对四柱、月令、日主、十神、大运流年的基础定义和层级说明：https://www.mingdecode.com/zh/bazi/explain/what-is-chart
- 明明观止对天干地支、藏干、季节旺衰、通根透出、纳音辅助定位的说明：https://mingming3.com/cn/bazi/articles/bazi_detail
- 明明观止对大运、流年、命宫、神煞顺序的说明：https://mingming3.com/cn/bazi/articles/bazi_period
- Shen-Shu 对常见神煞计算和“神煞是辅助星”的定位说明：https://www.shen-shu.com/en/blog/detailed-explanation-of-the-calculation-methods-for-divine-evils

## 缺口优先级

### P0: 必须补齐

1. 排盘边界知识
   - 状态：已补第一批 `birth_time_boundary` 和 `hidden_stem_weight_boundary`，继续扩更多边界 case。

2. 调候知识
   - 状态：已补 `month_command_adjustment`，调候只作为候选路径，不直接断健康或吉凶。

3. 用神路径仲裁
   - 状态：已补 `conflict_path`，保留扶抑、调候、通关、病药候选、反证和降权。

4. 时间层
   - 状态：已补 `trigger_stack_boundary`，按原局/大运/流年/流月分层进入，不给确定应期。

5. 神煞辅助层
   - 状态：已补 `common_symbol_low_weight`，神煞/空亡/十二长生/纳音只做低权重辅助。

### P1: 重要扩容

1. 十神位置细则
   - 年柱/月柱/日支/时柱的十神主题。
   - 明透、暗藏、重复、混杂。
   - 十神组合：官杀混杂、食伤混杂、财破印、枭神夺食等。

2. 干支关系仲裁
   - 三合、三会、六合、半合、拱夹、暗合、合而不化。
   - 冲合并见时谁优先。
   - 刑冲合害破混杂时的稳定性评分。

3. 格局反例
   - 假从格、从而不真。
   - 格局成而不纯。
   - 破格但可被岁运修复。

4. 宫位与领域投射
   - 夫妻宫、事业环境、父母长辈、子女晚景。
   - 宫位被冲合刑害后的主题变化。

### P2: 应用专题扩容

1. 学业考试专题。
2. 子女与家庭专题。
3. 迁移、远行、海外、变动专题。
4. 房产、居住、家庭资产专题：已补第一批。
5. 人际、贵人、小人、合作专题：已补第一批。
6. 创业、管理、团队、职业路径专题：已补第一批。

## 下一步执行计划

### Step 1: 建知识完备度审计脚本

状态：已完成第一版。

目标：自动输出每个目录节点的 coverage、缺口、runtime 影响面。

输出：

```text
knowledge_completeness_audit
  node_key
  seed_count
  rule_count
  runtime_allowed_count
  synthetic_case_count
  brain_evidence_count
  answer_guidance_count
  gap_tags
```

已新增运行入口：

```text
/api/v20/knowledge/completeness-audit
/api/v20/admin/knowledge-completeness-audit
/api/v20/admin/mainline-status
/api/v20/admin/central-brain-architecture
/api/v20/learning/orchestrator/knowledge-rule-plan
```

最新审计：

```text
status: complete
rule_count: 494
runtime_allowed_count: 494
synthetic_case_count: 55
external_topic_covered_count: 21 / 21
external_completeness_percent: 100
p0_gaps: none
```

### Step 2: 建外部知识点映射表

目标：把外部常见知识点映射到 L0-L12。

第一批 topic：

```text
true_solar_time
early_late_zi_hour
day_master_month_command_climate
hidden_stem_weight
ten_god_by_position
useful_god_conflict_arbitration
luck_pillar_start_age
annual_monthly_trigger_stack
common_shen_sha_low_weight
empty_branch
twelve_growth_stage
na_yin_archive
```

### Step 3: 补 P0 知识单元

先补小而可验证的原子知识，不写长篇玄学文本。

每个新知识单元必须包含：

```text
knowledge_id
directory_node
condition_atoms
rule_path
portrait_outputs
question_outputs
answer_guidance
counterexamples
synthetic_cases
runtime_boundary
```

### Step 4: 接入中枢大脑

新增或强化：

- `knowledge_completeness_audit`
- `knowledge_basis evidence`
- `brain_state.knowledge_basis`
- `answer_guidance_consumer`
- Admin 训练页里的知识专题状态

### Step 5: 训练计划

训练专题：

| 训练专题 | 原子训练 | 目标 |
|---|---|---|
| 排盘边界训练 | calendar_boundary_training | 避免时辰/节气错误污染全链路 |
| 调候训练 | climate_useful_god_training | 让调候参与用神候选 |
| 时间层训练 | time_trigger_training | 让大运流年流月进入事件引动 |
| 神煞辅助训练 | auxiliary_symbol_training | 低权重辅助，不抢主线 |
| 应用专题训练 | application_topic_training | 已补学业/子女家庭/迁移/房产/人际/创业第一批，继续扩细分反例 |
| 回答边界训练 | answer_governance_training | 已接入训练迭代和 knowledge runtime pointer，把边界、证据、复核/反证、下一步问题变成自动生效权重 |
| 角色答案治理 | role_answer_governance_profile | 已接入角色视图、synthetic replay、role-view runtime pointer 和答案投影，直接生成并消费 `role_answer_governance_weight` |
| LLM 上下文训练 | llm_context | 已接入中枢大脑 `llm_context_policy_generation`，复用回答治理、角色体验、合成回放和快训，持续优化角色上下文、八字结构上下文、回答合同和上下文预算 |

训练原则：

```text
训练结果不进入人工审核流程。
机器训练产物 -> 参数目标 -> runtime pointer/角色策略直接生效。
只保留可观测记录和回滚能力，不把“审计/审核”作为生效 gate。
```

应用专题第一批反例已覆盖：

```text
考试成绩/录取/证书结果
子女家庭隐私/生育结果/具体时间
合作成败/背叛/诉讼/第三方隐私
搬迁日期/事故/移民结果
资产价格/债务金额/投资收益/财务时间
房价/购房结果/贷款成败/确定房产事件
创业成败/融资结果/团队稳定/收益时间
```

### Step 6: 训练后自动生效

状态：已接通第一版，并已对齐 Admin UI 和中枢大脑状态。

训练包完成后会直接尝试这些 runtime pointer writer：

```text
orchestrator_policy
question_policy
role_view_policy
rule_policy
portrait_policy
knowledge_policy
corpus_policy
```

原则：

- 不需要人工审核。
- 每个 writer 独立过机器 gate。
- gate 通过的直接写 active pointer。
- gate 阻断的只记录阻断原因，不影响其他 writer 生效。
- 回滚仍然走版本化 pointer。

Admin 页面会展示每个 writer 的结果：

```text
已写入 active pointer
或
未生效：具体 machine gate 阻断原因
```

中枢大脑会输出：

```text
runtime_policy_coordination.status
runtime_policy_coordination.public_note
```

### Step 7: 主线状态机器报告

状态：已完成第一版。

新增入口：

```text
/api/v20/admin/mainline-status
```

当前输出：

```text
status: continuous_iteration_ready
completion_label: 99%+
blockers: none
knowledge.rule_count: 489
knowledge.synthetic_case_count: 50
answer_guidance_weight: 0.014
role_answer_governance_weight: 0.012
runtime_consumption.status: complete
```

定位：

- 只做机器状态汇总，不写 runtime，不作为审核 gate。
- 用来让 Admin UI 直接展示主线完成度、知识完备度、训练参数目标和 runtime 消费路径。
- 后续新增训练专题必须产出 `parameter_targets`，并接入 runtime pointer 或角色策略。
- 训练结果继续坚持直接生效原则：机器产物可用就进入参数目标和 runtime 策略，不增加人工审核流程。

### Step 8: 新增知识点 × 规则生成 × 合成验证统一编排

状态：已完成第一版。

新增入口：

```text
/api/v20/learning/orchestrator/knowledge-rule-plan
scripts/run_knowledge_rule_orchestrator.py
Admin 训练页：知识规则联合训练
```

中枢统一安排：

```text
knowledge_gap_pick
-> knowledge_atom_contract
-> rule_candidate_generation
-> synthetic_case_binding
-> rule_synthetic_validation
-> knowledge_rule_overlay
-> runtime_parameter_apply
```

新增知识点必须一次性绑定：

```text
knowledge_id
directory_node
source_refs
condition_atoms
rule_path
portrait_outputs
question_outputs
answer_guidance
counterexamples
synthetic_cases
runtime_boundary
```

当前下一批知识专题：

```text
十神位置细则：年/月/日/时位置、明透/暗藏/混杂 -> 已补第一批原子知识和 synthetic case
地支关系仲裁：冲合并见、半合/拱夹/暗合 -> 已补第一批原子知识和 synthetic case
格局反例：假从、清浊混杂、破格边界 -> 已补第一批原子知识和 synthetic case
岁运触发细分：伏吟反吟、墓库开闭 -> 已补第一批原子知识和 synthetic case
宫位应用细分：夫妻宫、事业环境、时柱家庭晚景 -> 已补第一批原子知识和 synthetic case
```

原则：

- API 只给轻量计划，不在页面请求里跑重验证。
- Admin 后台任务独立运行合成验证和 overlay 写入。
- 训练成功后走 training bundle，直接尝试 knowledge/rule/portrait/question/orchestrator runtime pointer 生效。
- 不加人工审核 gate；只保留机器状态、日志和版本化回滚。

### Step 9: 中枢大脑智能架构

状态：已完成第一版设计、机器状态入口、Admin 中枢控制台和 BrainGraph 任务编排。

主文档：

```text
docs/V20_CENTRAL_BRAIN_INTELLIGENCE_ARCHITECTURE.md
```

新增入口：

```text
/api/v20/admin/central-brain-architecture
```

架构原则：

```text
中枢大脑统一调配
高迭代训练
免人工审核
机器训练产物直接生效
UI 可见、可启动、可追踪、可回滚
```

BrainGraph：

```text
knowledge_gap_pick
-> knowledge_atom_contract
-> rule_candidate_generation
-> portrait_mapping_generation
-> question_policy_generation
-> role_policy_generation
-> synthetic_case_binding
-> synthetic_validation
-> corpus_replay_518k
-> parameter_optimizer
-> runtime_pointer_publish
-> ui_observability
```

下一步实施：

```text
Admin UI 读取 central_brain_architecture。已完成。
训练任务 registry 按 BrainGraph 节点分组。已完成。
训练卡片展示主节点、参数生效 pointer、阻断原因和重试入口。已完成。
training_bundle 统一 fan-out 到 orchestrator/question/role/rule/portrait/knowledge/corpus pointer writer。已完成。
Admin 训练计划输出 candidate_quality_signal，把合成覆盖和 518K 回放 artifact 合成候选质量信号。已完成。
candidate_quality_signal 已加入 quality_scores 和 candidate_promotion_score，用合成通过率、规则误触、画像漂移、问题聚焦、518K 分布偏移和相似案例稳定性共同决定候选推进。已完成第一版。
测算页已加入 readingProgressPanel，把八字特征、八字画像、角色阅读、智能问答四条链路用不同角色叙事展示。已完成。
角色化问题叙事与 LLM 提示词框架已新增 `docs/V20_ROLE_QUESTION_NARRATIVE_PROMPT_FRAMEWORK.md` 和机器合同 `role_view/narrative_prompt_framework.py`。LLM prompt/context 设计见 `docs/V20_LLM_PROMPT_CONTEXT_DESIGN.md`。`questions[].question_narrative`、`role_view_model.question_profile.voice_profile`、问题卡 UI、LLM `answer_prompt_profile`、`context.system_understanding.role_context`、`context.system_understanding.bazi_context_profile`、`answer_contract` 和合成回放 `question_narrative_quality` 已接入；该链路按直接 runtime 消费执行，不走人工审核 gate。
下一步：扩容 518K shard replay，让更多训练候选从 blocked_by_machine_gate 进入 candidate_active。
```

## 完成度

当前估算：

```text
知识目录覆盖：85%
知识规则数量：79%
知识进入中枢证据：85%
知识进入 BrainState：85%
知识影响答案 guidance：92%
训练后自动生效闭环：96%
外部知识体系完备度：100%
主线状态机器报告：100%
知识规则联合编排：100%
中枢大脑智能架构：100%

综合：约 99%+
```

下一阶段目标：

```text
下一阶段：
主线收口完成，后续进入持续迭代：新增知识/训练任务必须直接产出参数目标并接入 runtime pointer 或角色策略
知识影响答案 guidance 持续保持 >= 92%
训练后自动生效闭环持续保持 >= 96%
综合完成度：99%+
```
