# V19 P28L 十神机制 Shadow 信号门禁

## 定位

P28L 接在 P28K 之后，把自动生成的正反样本转为机制信号门禁报告。

本阶段不是生产启用。它只确认：

- 正例能命中对应机制信号。
- 反例、时间层干扰例、藏干干扰例不会误触发。
- Rule DB 中的 R2 机制候选记录仍保持关闭。

## 入口

- `v19.synthetic_validation.ten_god_conflict_matrix.run_p28l_ten_god_mechanism_signal_gate`

## 门禁结果

- 机制数：20
- 样本数：172
- shadow 信号通过机制：20
- 误触发：0
- 正例漏触发：0
- 生产激活数：0
- 生产激活延后：20

## 为什么仍不直接启用 R2 机制

P28K/P28L 已经证明“条件模型数据集”和“shadow 信号匹配”可用，但运行时还缺一个完整的机制条件解释器：

- 需要把 `source_layer`、`capacity_strength`、`same_layer_action`、`rescue_path` 等条件轴接入 runtime adapter。
- 需要 P29 的内部评分或排序门禁，避免多个机制同时命中时互相污染。
- R2 机制可以解释结构路径，但不能直接进入吉凶、应期、财富、健康、职业等结果判断。

因此 P28L 的结论是 shadow-ready，不是 production-active。

## 通过阈值

- P28K regression 必须 pass。
- 正例必须全部命中。
- 非正例误触发必须为 0。
- 禁止文本必须为 0。
- shadow 候选置信度下限为 0.60。
- R2 机制规则激活数必须为 0。

## 下一步

P29 进入内部评分层：

- 为机制候选增加排序分。
- 处理多个机制同见时的优先级。
- 仍然不向用户输出概率或断言，只用于内部排序和门禁。
