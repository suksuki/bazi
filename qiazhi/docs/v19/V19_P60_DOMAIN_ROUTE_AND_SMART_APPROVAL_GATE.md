# V19 P60 Domain Route and Smart Approval Gate

P60 接在 P59 后面，把静默进化系统推进到两个方向：

- 四大领域路由静默评估。
- 调优提案智能审批门禁。

## 领域路由

入口：

- `v19.synthetic_validation.silent_evolution.run_p60_domain_route_eval`
- `GET /api/lab/domain-route-eval`

覆盖领域：

- 财富 / 收入：`income_structure`
- 事业：`career_structure`
- 感情 / 关系：`relationship_structure`
- 健康：`health_structure`

P60 同步补强 Rule Graph intent router，让“感情关系”和“健康”不再落回 generic `structure_overview`。

P60 的初始发现：

- 财富、事业已有直接 domain candidate 命中。
- 感情、健康可以通过十神、地支关系、强弱、时间层做安全桥接，但直接 domain rule candidate 仍不足。

因此 P60 当时不把感情/健康 direct domain 缺口当作失败，而是记录为 `domain_candidate_gaps`，交给 smart gate 生成 backfill proposal。

P61 已经把这两个缺口补成 route-only 安全包装候选。当前 P60 回归应满足：

- 8 条 domain route samples 全部 pass。
- wealth / career / relationship / health 都有 direct domain hit。
- `domain_candidate_gaps` 为空。
- 感情和健康的 direct domain path 只作为 `domain_safety_bridge`，不输出领域结论。

## 智能审批门禁

入口：

- `v19.synthetic_validation.silent_evolution.run_p60_smart_approval_gate`
- `POST /api/lab/smart-approval-gate/run`

策略：

- low risk：`auto_dry_run_allowed`
- medium risk：`shadow_dry_run_required`
- high risk：`human_review_required`
- blocked：上游 P59 或 domain route eval 未通过

所有提案仍然只是 silent/dry-run 计划：

- 不启用生产规则。
- 不修改知识库。
- 不修改测算结果。
- 不修改用户回答。

## 汇总入口

`v19.synthetic_validation.silent_evolution.run_p60_silent_evolution_extension`

API：

`POST /api/lab/silent-evolution-extension/run`

## 验收

新增回归：

`test_p60_domain_route_eval_and_smart_approval_gate_are_silent`

要求：

- 四大领域 intent 都能被识别。
- 8 条 domain route samples 全部 pass。
- 感情/健康缺口已由 P61 route-only wrapper 消化，不再进入 backfill proposal。
- low risk 提案可自动进入 dry-run。
- medium risk 提案进入 shadow dry-run。
- runtime / answer / result mutation 全部为 0。
