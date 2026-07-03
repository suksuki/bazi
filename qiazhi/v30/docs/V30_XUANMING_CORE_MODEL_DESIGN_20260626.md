# V30 玄明中枢建模层设计

## 目标

V30 不能只把八字材料摆出来，也不能把每个页面小结写成模板文案。核心目标是建立一个可版本化、可测试、可追溯的中枢模型，把命盘事实、十神能量、规则证据、做功路径和大运流年合成为稳定的“当前最好判断”。

## 分层架构

1. 事实层：四柱、日主、月令、藏干、十神显隐、五行分布。事实层只读，追问和 LLM 都不能改写。
2. 评分层：日主强弱、五行支持/压力、十神角色能量、路径分数、规则反证。评分是模型信号，不是命运概率。
3. 合参层：把强弱、十神、结构、路径、时运合成为 mainline thesis，并保留风险、反证、下一问。
4. 表达层：页面小结和 LLM 只消费合参层，不直接从散乱 runtime 数据自由发挥。

## 当前算法

- 强弱模型：读取 `element_distribution`、`base_fact_summary.root_fact_summary`、显干十神和地支关系，合成五个子分：五行分布、月令季气、通根、透干、关系扰动。当前算法版本为 `weighted_month_root_stem_relation_v1`，给出 `偏旺`、`有根有助`、`偏弱或受压`、`明显偏弱或受压`、`中和待复核`。
- 十神模型：消费 `visible_ten_gods`、`hidden_ten_gods` 和 `ten_god_energy_summary`，把十神归并到比劫、食伤、财星、官杀、印星五类角色。
- 结构模型：消费 `StructureState` 和 `ranked_decisions`，输出结构语义、主链、候选决策、反证数量。
- 路径模型：消费 `real_bazi_diagnosis.paths` 和结构图节点边，排序机制、领域落点和风险说明。
- 用神候选模型：消费强弱、十神、结构、做功路径和旧 ranked decision，输出扶抑、泄秀生财、官杀制衡、调候、通关制化、补偏平衡等候选策略。
- 时运模型：消费大运、流年、六柱上下文，只用于激活原局路径，不允许凭流年制造新结构。
- 主线模型：生成 `thesis`、`key_reasons`、`risks`、`next_questions` 和 `quality_gate`。

## 强弱模型 v1.1

强弱不再只看五行比例，而是由以下子模型合成：

- `distribution`：日主同类/印星支持比例，和食伤/财星/官杀压力比例。
- `seasonal_model`：根据月支映射季气，再按旺、相、休、囚、死给出月令权重。
- `root_model`：消费通根事实摘要，按月、日、时、年位置和藏干权重给日主承载力加分。
- `stem_model`：看天干是否透出生扶或泄耗财官，判断力量是否能表达出来。
- `relation_model`：地支冲刑害破降低稳定性，三合三会等合会若归到日主五行则增加承载。

所有子分都进入 `scoring_components`，页面和 LLM 可以解释原因，但仍不能把该分数说成绝对吉凶。

## 用神候选模型 v1

算法版本为 `multi_strategy_useful_god_candidate_v1`。它不输出固定用神，而是输出候选策略：

- `support`：扶抑补身，偏弱或承载不足时看比劫、印星。
- `release`：泄秀生财，偏旺时看食伤、财星能否承接。
- `regulate`：官杀制衡，偏旺或需要规制时看官杀与印星承接。
- `climate`：调候候选，火水寒暖失衡时保留调候五行。
- `mediation`：通关制化，冲突、官印、财官印、食伤制杀等路径存在时看中介五行。
- `balance`：补偏平衡，强弱未明时保留薄弱五行。

每个候选都有 `elements`、`families`、`score`、`reasons`、`counter_evidence` 和边界。主线报告只能说“当前候选策略”，不能说“唯一用神已定”。

## 边界

- `chart_fact_mutation_allowed=false`：任何交互都不能修改四柱事实。
- LLM 的角色是 `expression_only_after_core_model`：只润色中枢模型已经给出的判断。
- 分数是排序和置信信号，不是吉凶概率。
- 反证和不确定性必须进入输出，而不是被隐藏。

## 接入方式

新增 `v30.reasoning.xuanming_model.build_xuanming_core_model(runtime)`。`thinking.py` 在构建步骤前调用一次，把 `reasoning_model` 放入 thinking payload，并让每个页面的 `analysis_result` 从该模型读取结论。

## 后续建模方向

- 把强弱评分从简单五行比例升级为月令权重、通根、透干、合冲刑害、寒暖燥湿的矩阵。
- 把十神角色改成图模型，区分显性角色、潜伏角色、时运引动角色。
- 把做功路径升级为可解释 DAG，支持路径竞争、阻断、通关、制化和领域投影。
- 加入案例校准队列，用真实反馈调参，但只调评分权重，不回写命盘事实。
