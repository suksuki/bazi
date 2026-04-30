# V19 P30 十神机制仲裁与旧知识迁移策略

## 定位

P30 把 P29 的内部排序分用于多机制同见时的回答焦点仲裁。

它仍然不是生产启用层：

- 不启用 R2 机制规则。
- 不展示概率。
- 不输出吉凶、应期、财富、健康、职业等断语。
- 只决定内部优先讲哪条结构路径，哪些作为背景。

## 入口

- `v19.synthetic_validation.ten_god_conflict_matrix.run_p30_ten_god_mechanism_arbitration`

## 仲裁场景

当前覆盖 5 类高频碰撞：

- 官杀压力与制化救应同见。
- 印枭牵制输出与救应同见。
- 财星路径、分夺与生官生杀同见。
- 去留、救应与特殊驾驭机制同见。
- 混杂结构与制化路径同见。

每个场景输出：

- `primary_focus`
- `secondary_context`
- `background_context`
- `answer_focus_policy`
- `forbidden_outputs`

仲裁分数由 P29 内部分数加上下文权重构成。场景锚点机制会获得轻量 context weight，避免全局分数略高的旁支机制抢走当前问题主线。

## 旧知识迁移结论

采用双轨策略：

1. 新知识和当前专题知识直接使用新框架。
2. 旧知识不做一次性大重构。
3. 被当前专题碰到的旧知识，顺手迁入条件模型、正反样本、shadow gate、内部评分。
4. 全部目录补完后，再做全库 migration audit。

迁移优先级：

- R1 元数据：已稳定可保留，补 manifest 与回答边界即可。
- R2 机制：必须迁入条件模型和合成样本后才能考虑激活。
- R3/R4 断语：继续 archive-only，只抽取中性结构表达。
- 财富、事业、感情、健康等领域：等十神机制稳定后复用同一框架。

## 当前结果

- 仲裁场景：5
- 通过：5
- blocked：0
- migration backlog：5
- runtime 激活：0

## 下一步

P31 可以开始把仲裁结果接入回答选择层：

- primary focus 决定回答主线。
- secondary context 只作为补充。
- background context 不抢占回答。
- 禁词、禁断语、禁预测继续强制审计。
