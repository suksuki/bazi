# V19 P43 Dry-Run Shadow Scoring

## 目标

P43 执行 P42 产生的非运行层计划：

- dry-run：只产生内部结构信号。
- shadow scoring：只记录命中、误触发、禁词、回滚合同。
- 不改变用户回答。
- 不启用运行规则。

## 输入

P42 已完成：

- dry-run 计划：110。
- shadow scoring 计划：158。
- 阻断：0。

## 执行样本

每条候选生成 4 条执行样本：

- `internal_signal_contract`
- `no_answer_mutation_contract`
- `forbidden_text_contract`
- `rollback_contract`

样本总数：268 * 4 = 1072。

## 当前结果

- 候选总数：268。
- dry-run 通过：110。
- shadow scored：158。
- 阻断：0。
- 执行样本：1072。
- 样本失败：0。
- 误触发：0。
- 禁词失败：0。
- 回滚合同覆盖：268。
- 用户回答变更：0。
- 运行规则启用：0。
- 状态：pass。

## 下一步

P44 可以基于 P43 feedback ledger：

- 对 dry-run 通过的 110 条做候选分层。
- 选择最安全的一小批 R0/R1 做受控运行试验。
- R2 继续留在 shadow scoring，不进入用户回答链路。
