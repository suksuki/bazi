# V19 P63 Silent Eval Queue

P63 把 P62 的静默训练账本推进成“可执行的静默评估队列”。它仍然不启动后台常驻任务，也不改规则，而是生成下一批应该反复运行的 eval jobs，并为每个 job 固定 runner、输入范围、验收不变量和禁止动作。

## 来源

P63 读取：

- P62 training ledger entries。
- P62 tuning queue。
- P60 domain route eval。
- P61 route-only wrapper regression。

## 队列任务

当前生成 4 类任务：

- `route_weight_shadow_review`：检查关系/健康是否继续命中 `domain_safety_bridge`。
- `recurring_route_wrapper_regression`：把 P61 的 6 条 route-only wrapper 和 24 条样本纳入周期回归。
- `domain_gap_watch_closeout`：持续确认 P60 的 relationship / health gap 保持关闭。
- `domain_safety_negative_sample_expansion`：扩展关系/健康负样本，先 shadow，不进入生产规则。

## 队列边界

所有 queue item 只能：

- 记录 eval result。
- 记录 checkpoint。
- 打开 silent tuning proposal。

所有 queue item 禁止：

- 改核心规则真值。
- 启用生产规则。
- 用户反馈直接改规则。
- 改写回答结论。
- 输出领域预测。

## 入口

- `v19.synthetic_validation.silent_eval_queue.build_p63_silent_eval_queue`
- `v19.synthetic_validation.silent_eval_queue.run_p63_silent_eval_queue_regression`
- `GET /api/lab/silent-eval-queue`
- `POST /api/lab/silent-eval-queue/run`

## 验收

新增回归：

`test_p63_silent_eval_queue_turns_training_ledger_into_checkpointed_jobs`

要求：

- 至少 4 个 queue item。
- 必须包含 P60 domain route runner 和 P61 route backfill regression runner。
- 每个 item 都有 runner、expected invariants、blocked actions。
- runtime / answer / rule activation 全部为 0。
- 中风险样本扩展必须停留在 `shadow_required`。
