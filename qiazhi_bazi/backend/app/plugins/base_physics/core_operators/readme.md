# `core_operators/`

| 模块 | OP_ID / 记号 | Skill ID |
|------|----------------|----------|
| `op_production` | `L1_OP_PROD` | `l1_prod_01` |
| `op_destruction` | `L1_OP_DEST` | `l1_dest_01` |
| `op_connection` | `L1_OP_CONN` | `l1_conn_01` |
| `op_interdimensional`（盖头截脚步骤） | `L1_OP_VERTICAL_CRUSH` | `l1_interdim_vert_01` |
| `op_owl_food` / `op_wealth_seal` / `op_blade_clash` / `op_robber_wealth` / `op_gov_kill_mix` | `L1_OP_*` | `l1_*_01`（核心冲突族，见 `core_conflict_runner`） |

审计行由 `junction.build_l1_operator_audit_items_from_steps` 统一写入 `payload.skill_id`，与上表及 `skill_manifest.json` 的 `operator_to_skill` 一致。
