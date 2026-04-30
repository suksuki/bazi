# V19 P59 Silent Evolution System

P59 启动静默进化系统第一版。

它不是自动改规则，也不是黑盒训练。它是一个只读、可审计、可回放的 silent training loop：

```text
synthetic cases
→ framework chain audit
→ auto evaluator
→ run ledger entry
→ tuning proposals
→ shadow / smart gate / canary backlog
```

## 当前主动模型

`deterministic_rule_graph_plus_eval_scoring`

当前启用的算法：

- Rule Graph path selection
- condition model eval dataset
- dry-run shadow scoring
- canary runtime trial
- auto evaluator scorecard

## 暂不启用的模型

- Bayesian scoring：后续只用于内部排序，不输出概率断语。
- GNN：后续只用于 path embedding / rerank。
- RL：后续只用于问题排序和对话策略，不用于核心命理规则真假。

## 入口

`v19.synthetic_validation.silent_evolution.run_p59_silent_evolution_cycle`

Lab API:

`POST /api/lab/silent-evolution/run`

输出：

- `run_id`
- `scorecard`
- `run_ledger_entry`
- `tuning_proposals`
- `model_policy`
- `downstream_plan`

## 自动评分

P59A/B 第一版评分项：

- guided synthetic 是否通过。
- P53 framework backfill 是否通过。
- P54 framework chain audit 是否通过。
- P43 feedback ledger 是否 ready。
- forbidden text 是否为 0。
- mutation failure 是否为 0。
- topic lane 覆盖是否包含 core / branch-time / ten-god / wealth-career。

## 调优提案

当前只生成 proposal，不写规则：

- 扩展领域路由 eval。
- 记录首屏问题多样性为长期指标。
- 保持 Rule Graph 作为主动核心模型。
- 抽样 shadow-scored candidates 进入扩展 silent eval。
- 对 rule DB backlog 生成回填建议。

## 边界

- 不修改知识库。
- 不修改规则库。
- 不改变测算结果。
- 不改变用户回答。
- 不使用用户反馈直接改规则。
- 不启用生产 rule engine。

## 验收

新增回归：

`test_p59_silent_evolution_cycle_scores_and_generates_tuning_proposals`

要求：

- cycle status 为 `silent_shadow_pass`。
- score 至少 90。
- run ledger 标记 rollback ready。
- tuning proposals 全部是 silent proposal。
- GNN/RL 仅作为 reserved model slots。
