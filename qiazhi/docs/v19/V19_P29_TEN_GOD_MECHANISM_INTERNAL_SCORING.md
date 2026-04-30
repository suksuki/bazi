# V19 P29 十神机制内部评分

## 定位

P29 引入贝叶斯启发式的内部排序分，用于多机制同见时的候选排序。

它不是神经网络，也不是用户可见概率；当前阶段只把 Rule DB 先验置信度、P28K/P28L 的正反样本证据和样本覆盖度合并为一个内部 rank score。

## 入口

- `v19.synthetic_validation.ten_god_conflict_matrix.run_p29_ten_god_mechanism_internal_scoring`

## 输入

- P28L shadow 信号门禁报告。
- Rule DB R2 机制候选的 prior confidence。
- P28K 正反样本覆盖情况。

## 评分因子

- Rule DB prior confidence floor。
- P28K positive hit rate。
- P28K negative precision。
- P28K sample coverage。

输出字段：

- `prior_confidence_floor`
- `positive_hit_rate`
- `negative_precision`
- `coverage_factor`
- `evidence_likelihood`
- `internal_rank_score`
- `score_tier`
- `rank`

## 边界

- 不向用户展示概率。
- 不向用户输出“确定、必然、概率多少”的结论。
- 不启用 R2 机制规则。
- 不改变回答文本。
- 不做吉凶、应期、财富、健康、职业等断语。

## 当前结果

- 机制数：20
- rank-ready：20
- blocked：0
- runtime 激活：0

## 下一步

P30 可以把内部评分接入“机制冲突仲裁”：

- 多个机制同时命中时，按内部 rank score 做候选排序。
- 低分机制只作为背景，不抢占回答重点。
- 仍然保留禁词、禁断语、禁预测门禁。
