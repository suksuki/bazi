# V19 P53 Legacy Synthetic Framework Backfill

P53 回溯 P10/P11 早期 synthetic collision 矩阵，让旧案例显式适配 P46-P52 的新框架。

## 背景

P10/P11 原来主要验证：

- 推荐问题是否命中。
- 知识检索是否带来 evidence 增量。
- 回答文本是否避开内部术语和预测断语。
- 失败样例是否生成 audit / draft。

P46 之后系统增加了 Rule Graph Orchestrator、Runtime Route Pack、路径评分、路径仲裁、问题个性化和 route-aware retrieval。P10/P11 虽然已经能被新链路执行，但它们没有显式声明新框架契约，容易形成“旧测试通过，但新框架语义没被验收”的空洞。

## 本次改动

新增 `v19.synthetic_validation.framework_backfill`。

每个 P10/P11 case 会生成一份 `framework_backfill`：

- `primary_intent`
- `expected_route_ids`
- `expected_topic_lanes`
- `expected_graph_features`
- `condition_axes_expected`
- `condition_axis_projection`
- `mutation_policy`

runner 会把该报告纳入每个 case 的 failure gate。也就是说，旧合成盘现在不仅要通过原来的推荐、检索、回答链路，还必须通过新 Rule Graph 框架兼容验收。

## P 流程适配总账

P53 同时新增 `build_legacy_framework_adaptation_matrix`，用于记录 P10-P52 在新框架下的位置：

- P10：回溯适配到 Rule Graph runtime contract。
- P11：回溯适配到 Rule Graph runtime contract。
- P12-P27：治理、晋级、目录扩展流程，本身不参与 runtime inference，按治理边界兼容。
- P28-P30：原生进入 condition model / eval dataset / mechanism scoring。
- P31-P38：原生进入知识目录和优先专题转换轨道。
- P39-P45：原生进入 rule conversion、smart gate、shadow scoring、canary。
- P46-P52：原生 Rule Graph runtime、个性化问题、route-aware retrieval 和 UI 对齐。

这张总账的目的不是宣称所有旧逻辑都已经变成生产规则，而是防止系统出现“旧 P 流程不知道该接到哪条新框架链路”的兼容空白。

## 适配策略

P53 不重写旧案例的命理意图，而是把旧案例映射到新框架：

- 月令 / 五行 / 日主类：`core_strength_foundation`
- 十神透藏类：`ten_god_mechanism`
- 冲合刑害破 / 三合三会 / 墓库 / 时间引动：`branch_time_activation`
- 收入结构 / 财富可达性：`wealth_career_bridge` + `ten_god_mechanism`

条件轴使用投影校验：

- `source_layer`、`capacity_strength`、`same_layer_action`、`answer_boundary` 必须能在 selected paths 中看到。
- 时间层案例用 `time_relation` / `time_boundary` 投影验收。
- 地支关系案例用 `branch_relation` feature 投影验收。

## 边界

P53 仍然不启用生产规则：

- 不激活 runtime rule engine。
- 不修改结果卡。
- 不修改回答结论。
- 不输出领域预测。
- 不引入 GNN/RL 黑盒推理。

## 验收

新增回归：

`test_p53_legacy_p10_p11_cases_backfill_to_new_rule_graph_framework`

该测试要求：

- P11 全矩阵通过，且包含 P10 legacy phase。
- 每个 case 的 `framework_backfill.status == pass`。
- 覆盖 `core_strength_foundation`、`branch_time_activation`、`ten_god_mechanism`、`wealth_career_bridge`。
- 覆盖 `stem`、`branch`、`hidden_stem`、`branch_relation`、`time_relation`、`ten_god`。
- 每条路径仍然保持 `NO_RUNTIME_RULE_ACTIVATION`、`NO_RESULT_MUTATION`、`NO_ANSWER_MUTATION`。
