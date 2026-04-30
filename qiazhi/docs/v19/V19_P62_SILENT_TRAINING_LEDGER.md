# V19 P62 Silent Training Ledger

P62 开始把“自我学习 / 自我进化”落到一个稳定入口：静默训练账本。它不训练黑盒模型，也不自动改命理规则，而是把 P59/P60/P61 的结果统一整理成可回放、可审计的 learning signal。

## 输入

- P59：静默进化评分和调优提案。
- P60：财富、事业、关系、健康四类 domain route eval。
- P61：关系 / 健康 route-only wrapper 回归。

## 输出

- 3 条 training ledger entry。
- 低风险调优队列：路由权重复核、eval sample 复核、P60 缺口关闭记录。
- 中风险调优队列：关系 / 健康负样本扩展。
- 明确的学习权限边界。

## 学习权限

允许：

- 问题路由权重复核。
- eval sampling 优先级复核。
- draft priority 复核。
- shadow dataset 扩展。

禁止：

- 直接改核心命理规则真值。
- 直接启用生产规则。
- 用户反馈直接改规则。
- 改写回答结论。
- 输出领域预测。

## 入口

- `v19.synthetic_validation.silent_training_ledger.build_p62_silent_training_ledger`
- `v19.synthetic_validation.silent_training_ledger.run_p62_silent_training_ledger_regression`
- `GET /api/lab/silent-training-ledger`
- `POST /api/lab/silent-training-ledger/run`

## 验收

新增回归：

`test_p62_silent_training_ledger_collects_learning_signals_without_rule_updates`

要求：

- P59/P60/P61 三类信号全部进入 ledger。
- P60 direct domain hit 保持 8/8。
- P61 回归保持 pass。
- runtime / answer / result mutation 全部为 0。
- learning permissions 必须阻止核心规则自动学习和生产激活。
