# 现代财富风险（`modern.wealth_risk.v1`）

在 **`on_verdict_ready`** 阶段运行，输入为：

- `work_vector.host_abs`、`work_vector.work_expectation`
- `work_vector.spatial_audit.is_exit_locked`
- `structure_final_decision.primary_structure_humanized`

## 风险带（示意）

- **high**：`host_abs ≥ 20` 且 `work_net ≤ 0` 且出口闭锁。
- **medium**：`work_net > 0`。
- **medium-high**：其余过渡区。

各 Skill 的语义与断言模板见同目录 `skill_manifest.json`；管理台经 `/api/v1/plugins/manifest?plugin_id=modern.wealth_risk.v1` 拉取蓝图 Markdown。
