# V19 P45 Canary Runtime Trial

## 目标

P45 执行最小 ring0 canary 试验。

这一步只允许 canary 沙箱内启用规则，不写入生产 Rule DB，不改用户回答链路。

## 输入

P44 已生成：

- ring0 canary：2。
- ring1 internal：108。
- shadow hold：158。
- 回滚清单覆盖：110。

## Canary 范围

本次只试验 2 条 R0 规则：

- `core.five_element_relations.v1`
- `core.stem_attributes.v1`

两条都属于 `core_strength_foundation`，只产出结构元数据，不输出领域判断。

## 样本合同

每条 canary 生成 6 条样本：

- `canary_internal_signal_contract`
- `production_route_no_signal_contract`
- `answer_text_no_mutation_contract`
- `forbidden_text_contract`
- `rollback_execution_contract`
- `kill_switch_contract`

样本总数：2 * 6 = 12。

## 当前结果

- ring0 canary：2。
- canary 沙箱启用：2。
- 生产 engine 启用：0。
- canary 样本：12。
- 样本失败：0。
- 生产信号泄漏：0。
- 禁词失败：0。
- 回滚覆盖：2。
- kill switch 覆盖：2。
- 回答变更：0。
- 生产 runtime mutation：false。
- 状态：pass。

## 下一步

P46 可以在 canary 结果稳定后，将 ring0 canary 的内部信号接入真实回答链路前的审计层，但仍需：

- 继续禁止预测性文本。
- 只输出结构解释，不输出结果断语。
- 保留 kill switch 和回滚。
