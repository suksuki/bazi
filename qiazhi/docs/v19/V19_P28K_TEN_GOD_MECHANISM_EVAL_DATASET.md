# V19 P28K 十神机制自动正反样本数据集

## 定位

P28K 将 P28J 的十神机制条件模型转为可回归的 eval dataset。

本阶段只验证“机制信号是否具备可识别条件”，不启用机制规则，不改写回答结果，不输出吉凶、应期、发财破财、健康疾病、职业断语等结论。

## 输入

- P28J 十神机制条件模型。
- P28G 十神组合合成盘矩阵。
- Rule DB 中的 R2 机制候选记录。

## 输出

入口函数：

- `v19.synthetic_validation.ten_god_conflict_matrix.build_p28k_ten_god_mechanism_eval_dataset`
- `v19.synthetic_validation.ten_god_conflict_matrix.run_p28k_ten_god_mechanism_regression`

数据集规模：

- 机制数：20
- 样本数：172
- 正例：66
- 反例：66
- 时间层干扰例：20
- 藏干干扰例：20

普通机制每条 8 个样本：

- 3 个正例
- 3 个反例
- 1 个时间层干扰例
- 1 个藏干干扰例

复杂机制每条 12 个样本：

- 合杀留官
- 合官留杀
- 羊刃驾杀

复杂机制额外增加专题正例和专题反例，用于覆盖合化去留、路径断裂、禄刃驾杀等更高阶条件。

## 样本字段

每个样本固定输出：

- `case_id`
- `source_mechanism_id`
- `polarity`
- `expected_signal`
- `forbidden_signals`
- `expected_question_keys`
- `forbidden_text`
- `condition_axes_expected`
- `audit_tags`

## 正例标准

正例必须满足条件模型中的必要轴：

- `source_layer`
- `capacity_strength`
- `same_layer_action`
- `palace_position`
- `answer_boundary`
- 该机制所属 family 的专属轴
- 该机制 title 的专题轴

正例的 `expected_signal` 必须等于当前机制的 `source_mechanism_id`。

## 反例与干扰例

反例覆盖：

- 只有同见但无作用路径
- 跨层不可作用
- 承载不足
- 只有关系名但合化、去留、驾驭条件不成立
- 路径断裂

干扰例覆盖：

- 时间层触发，但不改写本命结构
- 只在藏干背景出现，不能作为机制主信号

所有非正例必须把当前机制放入 `forbidden_signals`，且至少有一个条件轴被标记为 `blocked`。

## 通过阈值

- precision 必须为 100%
- 误触发必须为 0
- 禁止文本失败必须为 0
- P28K 规则激活数必须为 0

P28K 的目标是把机制规则推进到可验证状态，而不是推进到运行时启用状态。

## 下一步

P28L 才进入智能门禁：

- 基于 P28K 绿灯数据集运行机制信号匹配。
- 对低风险、可解释、无误触发的机制候选生成 gate report。
- 高风险机制继续阻断，只保留 audit 和 draft。
