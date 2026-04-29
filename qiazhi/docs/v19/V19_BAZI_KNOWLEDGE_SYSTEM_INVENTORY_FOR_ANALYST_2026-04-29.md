# V19 八字知识库系统盘点报告（给分析师 Review）

日期：2026-04-29

状态：分析师审阅稿

范围：V17/V18 旧系统知识资产 + 当前 V19 知识系统状态

## 1. 总结结论

之前的 V17/V18 系统里确实存在一套比较完整的八字知识系统。它不是单一数据库，而是由多种资产混合组成：设计报告、运行时 JSON 知识库、插件转化知识、特征定义、规则候选、财富领域知识包、测试与审核记录等。

V19 当前采用的是更保守、更干净的迁移策略：

```text
先只使用 A 类基础知识。
不直接复用旧系统预测插件。
不导入旧评分、旧断语、旧叙事、旧吉凶判断。
旧资产只能作为来源材料，不能直接成为运行时权威。
```

因此，当前 V19 的知识库更小，但边界更干净。它已经具备核心结构知识、证据单元、反馈治理、引导问题治理、规则归因和规则提案账本，但还不是完整的可执行八字规则数据库。

建议给当前状态的定义是：

```text
V17/V18 = 范围较广但混杂的旧八字知识语料库
V19 = 干净、可治理的知识基础 + 面向未来规则库的提案管线
```

## 2. 找到的最重要旧系统报告

核心旧报告：

```text
v17_rebirth/docs/V18_2_KNOWLEDGE_CORPUS_TO_RULE_KERNEL_2026-04-27.md
```

这是旧系统中最重要的知识系统设计文档。

它定义了旧系统计划中的知识流转链路：

```text
知识语料库
→ 知识卡
→ 规则内核
→ 机制图
→ 预测契约
→ 专题插件
```

这份报告里的核心原则是：

```text
插件不应该是最终权威。
知识应该先进入知识语料库，再转为规则候选，进入规则内核，然后进入机制图，最后进入预测契约。
```

这与当前 V19 的治理方向是兼容的。但 V19 必须保留更严格的边界：任何旧预测规则都不能直接激活，必须先进入提案、校验、分析师/管理员审核流程。

## 3. V18.2 的知识分类

V18.2 报告将八字知识分成五类：

```text
A. 基础事实类
B. 结构判断类
C. 机制推理类
D. 象义经验类
E. 断语案例类
```

### A. 基础事实类

例子：

```text
天干
地支
五行
阴阳
十神
藏干
十二长生
地支关系
天干关系
墓库
```

V19 处理方式：

```text
可以作为干净核心知识迁移。
可以支持排盘结构、特征抽取和关系检测。
不能直接生成吉凶、断语或预测结论。
```

### B. 结构判断类

例子：

```text
格局
体用
扶抑
调候
通关
从格
专旺
用神忌神
```

V19 处理方式：

```text
不直接迁移为 active rule。
未来可以作为规则提案进入审查流程。
```

### C. 机制推理类

例子：

```text
食伤生财
食伤制杀
杀印相生
财官印链条
比劫夺财
财库开合
伤官见官
```

V19 处理方式：

```text
未来对 Rule Knowledge DB 很有价值。
但必须先进入规则提案账本。
必须明确输入、输出、证据、置信度和来源。
```

### D. 象义经验类

例子：

```text
盲派象法
宫位象
十神象
职业象
疾病象
婚恋象
```

V19 处理方式：

```text
风险较高。
当前只能作为弱证据、分析师参考或叙事假设。
不能作为 V19 当前确定性推理逻辑。
```

### E. 断语案例类

例子：

```text
组合断语
应期断语
职业倾向断语
传统口诀断语
```

V19 处理方式：

```text
污染风险最高。
不能导入 active runtime。
只能作为归档来源材料。
```

## 4. 找到的 V18 运行时知识资产

旧系统运行时知识主要在：

```text
v17_rebirth/.runtime/v18_1/
```

重要文件包括：

```text
bazi_knowledge_units.json
bazi_feature_definitions.json
bazi_knowledge_sources.json
v18_1_core_bazi_strength_bundles.json
v18_1_core_bazi_structure_effect_bundles.json
v18_1_core_bazi_feature_bundles.json
v18_1_wealth_domain_bundles.json
knowledge_cards.json
active_knowledge_cards.json
knowledge_pr_queue.json
rule_kernels.json
active_rules.json
rule_candidates.json
rule_test_suites.json
rule_test_cases_v02.json
rule_quality_scores.json
rule_kernel_audit.json
candidate_rule_suggestions.json
```

### 4.1 `bazi_knowledge_units.json`

路径：

```text
v17_rebirth/.runtime/v18_1/bazi_knowledge_units.json
```

观察结果：

```text
类型：dict
数量：28 条知识单元
```

样例：

```text
wealth.001_wealth_star_strength
wealth.002_wealth_star_visible_stem
wealth.003_wealth_star_hidden_branch
wealth.004_wealth_has_root
wealth.005_wealth_no_root
wealth.006_wealth_vault
wealth.007_wealth_vault_opened_by_clash
wealth.008_wealth_vault_combined
```

判断：

```text
这是旧系统中真实存在的知识单元库，主要偏财富领域。
它适合成为 V19 未来规则提案的来源材料。
但不应该直接激活。
```

### 4.2 `bazi_feature_definitions.json`

路径：

```text
v17_rebirth/.runtime/v18_1/bazi_feature_definitions.json
```

观察结果：

```text
类型：dict
数量：9 个特征定义
```

特征样例：

```text
wealth_strength
wealth_vault_activation
output_generate_wealth
wealth_constraint
wealth_flow_activation
wealth_stability
wealth_risk
wealth_vault_state
peer_competition
```

判断：

```text
这个文件价值较高，因为它是 feature-oriented，而不是 narrative-oriented。
可以用来参考 V19 的特征 Schema 设计。
但每个特征仍然需要审核后才能进入运行时。
```

### 4.3 核心八字结构包

路径：

```text
v17_rebirth/.runtime/v18_1/v18_1_core_bazi_strength_bundles.json
v17_rebirth/.runtime/v18_1/v18_1_core_bazi_structure_effect_bundles.json
v17_rebirth/.runtime/v18_1/v18_1_core_bazi_feature_bundles.json
```

判断：

```text
这些应该是 V18.1 中关于旺衰、结构效果和特征抽取的结构化包。
需要仔细审计，因为里面可能同时包含干净特征和判断逻辑。
```

### 4.4 财富领域知识包

路径：

```text
v17_rebirth/.runtime/v18_1/v18_1_wealth_domain_bundles.json
```

判断：

```text
这是旧系统中最适合给 income_stability / 财富领域扩展做参考的资产。
但它只能作为候选证据，不能直接作为 active logic。
```

## 5. 旧插件转化知识文件

旧系统还有一些插件转化知识文件：

```text
v17_rebirth/backend/logic/knowledge/
```

### 5.1 象义基础知识

路径：

```text
v17_rebirth/backend/logic/knowledge/bazi_symbolic_primitives.v1.json
```

观察到的顶层字段：

```text
id
version
mode
palace_context
stem_image_rules
branch_image_rules
vault_rules
ten_god_family
```

判断：

```text
这是偏象义、符号、意象层的知识。
可以给分析师参考，也可以用于未来解释层设计。
但它有较高预测污染风险。
当前不能作为 V19 确定性推理规则。
```

### 5.2 财富代码知识

路径：

```text
v17_rebirth/backend/logic/knowledge/wealth_code_knowledge.v1.json
```

观察到的顶层字段包括：

```text
id
version
mode
path_keywords
god_groups
path_claim_rules
path_templates
signal_labels
```

判断：

```text
这是旧系统的财富领域知识文件。
其中一部分可以作为特征标签、路径模板或规则候选参考。
但其中任何 claim / rule / path 都必须经过 V19 提案校验后才能使用。
```

## 6. 当前 V19 干净知识库

当前 V19 相关知识文件：

```text
docs/bazi_knowledge/core/core_units_v1.md
docs/bazi_knowledge/wealth/wealth_units_v1.md
docs/bazi_knowledge/legacy_algorithm_review.md
v19/.runtime/knowledge_units.json
v19/knowledge/schema.py
v19/knowledge/kernel.py
v19/knowledge/seeds.py
```

### 6.1 核心八字知识单元 v1

路径：

```text
docs/bazi_knowledge/core/core_units_v1.md
```

用途：

```text
干净的基础八字知识库。
来自旧系统 A-only migration。
只保留结构性基础知识。
```

允许迁移：

```text
稳定常量
结构表
关系配对表
层级边界
纯特征定义
旧插件或协议的来源引用
```

拒绝迁移：

```text
格局判断
用神 / 忌神判断
财富专项规则
盲派推理
象法推理
神煞推理
插件匹配率
旧结算权重
旧冲突解决权重
旧叙事提示词
```

核心单元索引：

```text
core.heavenly_stems
core.earthly_branches
core.five_elements
core.yin_yang
core.five_element_generation_control
core.stem_element_yinyang
core.branch_main_elements
core.ten_god_mapping
core.hidden_stems
core.pillar_structure
core.month_command
core.root_strength
core.visible_and_hidden_layers
core.six_combination
core.six_clash
core.three_harmony
core.three_meeting
core.branch_penalty
core.six_harm
core.six_break
core.stem_fusion
core.vault_structure
core.chang_sheng_12
core.time_structure_context
core.cross_layer_boundaries
```

### 6.2 财富知识单元 v1

路径：

```text
docs/bazi_knowledge/wealth/wealth_units_v1.md
```

覆盖范围：

```text
财星强弱
财星透干 / 藏支
财星有根 / 无根
财库
财库冲开
财库被合
食伤生财
食伤太过泄身
官杀制约财富
印星克制食伤影响生财
比劫夺财
财旺身弱
身旺财弱
财官相生
大运引动财星
流年引动财库
合局导致财富稳定性变化
冲导致财富流动性变化
刑害导致财富风险
财在夫妻宫 / 家内家外位置影响财富来源
```

规范特征类型：

```text
wealth_strength
wealth_vault_state
wealth_vault_activation
output_generate_wealth
wealth_constraint
peer_competition
wealth_flow_activation
wealth_stability
wealth_risk
```

重要治理规则：

```text
这些知识单元不是运行时预测规则。
它们只能生成特征映射、沙盒规则候选或测试用例。
沙盒候选仍然需要审核和激活，才能成为 active rule。
```

### 6.3 V19 运行时知识单元

路径：

```text
v19/.runtime/knowledge_units.json
```

观察结果：

```text
类型：dict
数量：13 条知识单元
```

样例：

```text
core.day_master_strength_boundary
core.earthly_branches
core.five_elements
core.heavenly_stems
core.inference_input_boundary
core.pillar_structure
core.six_clash
core.six_combination
```

判断：

```text
V19 当前运行时知识库是有意保持小而干净的。
它聚焦核心结构、安全边界和证据解释。
它还不是完整的八字 active rule database。
```

## 7. 当前 V19 知识系统定位

当前 V19 应该定义为：

```text
Guided Bazi Agent
+ Knowledge Evidence Store
+ Feedback Ledger
+ Guided Question Governance
+ Rule Attribution
+ Rule Knowledge Proposal Ledger
```

不应该定义为：

```text
完整 active 八字规则知识库
自学习算命引擎
生产级流年预测系统
```

当前系统可以支持：

```text
命盘结构展示
六柱可读层
income_stability 有边界信号
规则归因
证据解释
引导问题
反馈治理
提案工作流
校验工作流
管理员审核
```

当前系统不应该宣称支持：

```text
完整命运预测
健康预测
婚恋预测
职业预测
完整大运判断
time-aware income_stability inference
传统断语输出
```

## 8. 迁移建议

建议迁移路线：

```text
1. 保持 V19 active runtime 小而干净。
2. V17/V18 资产只作为来源材料。
3. 将旧知识单元转为 Rule Knowledge Proposal，而不是 active rule。
4. 提案先做 schema validation。
5. 通过分析师/管理员审核后，未来才允许进入激活流程。
6. 象义类和案例断语类知识暂时只做归档参考。
```

优先级建议：

```text
A. 核心结构基础知识
B. 特征定义
C. 财富领域证据单元
D. 机制推理候选
E. 象义 / 案例材料，只作为归档参考
```

## 9. 给分析师的 Review 问题

请分析师重点审查：

```text
1. V18 财富知识单元里，哪些可以安全转成 V19 规则提案？
2. 哪些 feature definitions 应该成为 V19 规范特征 Schema？
3. 哪些旧文件明显包含断语污染，只能归档不能迁移？
4. 当前 V19 core_units_v1 是否缺少关键基础八字知识？
5. wealth_units_v1 应继续保持 evidence-only，还是可以开始做 proposal conversion？
6. 与大运 / 流年相关的财富知识，是否应该推迟到 time-aware inference 正式设计后再处理？
```

## 10. 最终判断

旧 V17/V18 系统确实有一套较丰富的八字知识体系，尤其在财富特征和 knowledge-to-rule 架构方面做过不少工作。但旧系统混合了干净结构知识、预测规则、象义解释、插件逻辑和传统断语。

V19 当前走的是更正确、更安全的路线：

```text
结构优先
有边界推理其次
证据解释第三
先治理，再激活
```

最安全的下一步不是直接导入旧知识，而是把旧知识作为来源语料，逐步进入 V19 的 Rule Knowledge Proposal Ledger。

推荐统一命名：

```text
V17/V18 旧八字知识语料库
→ V19 可治理规则知识提案管线
```
