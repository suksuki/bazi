# V19 P61 Relationship and Health Route Backfill

P61 解决 P60 留下的领域直连缺口：感情/关系、健康已经有知识归档，但因为原始知识风险较高，不能直接转成生产规则。P61 的做法是创建一层安全路由包装，只让 Rule Graph 识别“该走哪个知识路径”，不让它输出关系、健康结论。

## 范围

来源：

- `p36.relationship.spouse_palace.existence`
- `p36.relationship.spouse_palace.boundary`
- `p36.relationship.ten_god_context.existence`
- `p36.relationship.ten_god_context.boundary`
- `p36.health.archive_boundary.existence`
- `p36.health.archive_boundary.boundary`

输出：

- 6 条 R2 route-only 候选。
- 24 条 eval samples。
- 关系和健康问题进入 `domain_safety_bridge`。
- P60 domain route eval 的 direct domain hit 从部分命中变成 8/8。

## 约束

P61 不改变原始知识风险等级。P36 的 R3/R4 仍然保留为 archive source，P61 只是创建 R2 的安全路由包装。

这些候选只允许：

- 参与 Rule Graph path selection。
- 发出内部 route boundary signal。
- 帮助选择知识路径。

这些候选禁止：

- 启用生产规则。
- 修改测算结果。
- 修改回答文本。
- 输出感情结果、健康结果、疾病、寿命、应期或确定性断语。

## 入口

- `v19.synthetic_validation.domain_route_backfill.build_p61_domain_route_backfill_candidates`
- `v19.synthetic_validation.domain_route_backfill.build_p61_domain_route_backfill_eval_dataset`
- `v19.synthetic_validation.domain_route_backfill.run_p61_domain_route_backfill_regression`
- `GET /api/lab/domain-route-backfill`
- `POST /api/lab/domain-route-backfill/run`

## 验收

新增回归：

`test_p61_relationship_health_domain_route_backfill_is_safe_and_selected`

要求：

- 6 条候选全部保持 R2 wrapper。
- source risk 必须保留 R3/R4。
- engine / activation / runtime mutation 全部为 0。
- 24 条正反样本通过。
- 关系、健康问题都能选中 direct domain 的 `domain_safety_bridge` 路径。
- P60 不再产生 relationship / health domain candidate gap。
