# V19 P41 Condition Topic Deep Validation

## 目标

P41 接在 P40 后面，把 268 条 condition model 队列规则按专题拆开，并进行更严格的深度合成验证。

P40 已经证明这些候选具备基础条件轴和 4 类基础样本；P41 进一步验证：

- 同层作用路径是否成立。
- 承载强弱是否足够。
- 只有关系名但合化/制化不成立时是否会误触发。
- 时间层是否只作引动背景。
- 藏干层是否只作背景，不替代显性作用路径。

## 专题批次

P41 将 268 条规则分为 6 个专题批次：

- `ten_god_mechanism`：93。
- `branch_time_activation`：74。
- `wealth_career_bridge`：38。
- `pattern_structure`：30。
- `core_strength_foundation`：20。
- `blind_lifa_palace`：13。

## 深度样本

每条规则生成 10 条样本：

- `positive_all_axes_present`
- `positive_rescue_path_present`
- `positive_same_layer_action_present`
- `negative_missing_source_layer`
- `negative_missing_action_path`
- `negative_capacity_insufficient`
- `negative_cross_layer_no_action`
- `negative_relation_name_no_transformation`
- `distractor_time_trigger_only`
- `distractor_hidden_stem_only`

样本总数：268 * 10 = 2680。

## 回归标准

- 正例必须产生中性结构信号。
- 反例不能产生正向信号。
- 时间层不能改写本命结构。
- 藏干层不能替代显性作用路径。
- 关系名存在但作用条件不成立时不能误触发。
- 禁词和领域预测表达不能出现。
- 不能启用运行规则。

## 当前结果

- 专题批次：6。
- 深度样本：2680。
- 样本失败：0。
- 误触发：0。
- 禁词失败：0。
- 智能门禁候选批次：6。
- 可进入门禁候选规则：268。
- 运行规则启用：0。
- 状态：pass。

## 下一步

P42 可以在 P41 的基础上做智能门禁：

- 低风险、低复杂度规则进入 dry-run 激活候选。
- 中复杂度规则继续保持 shadow scoring。
- 高复杂度或领域敏感规则继续保留为候选，不进入运行层。
