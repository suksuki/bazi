# 全量插件化物理闭环（sys.core.physics）

## 目标

- **单一审计面**：`physics_tensor.plugin_outputs` 为 Debug / 路由 / LLM 血统引用的插件集合。
- **L1 实名子插件**：`sys.l1.sanhe`（三合）、`sys.l1.liuhe`（六合）、`sys.l1.liuchong`（六冲）各为独立虚拟插件行；`sys.core.physics` 为总线摘要（流水线、天干锁相、塌缩统计），不含地支结构重复叙述。
- **CausalRouter**：将 `sys.core.physics` 与 `classical.*` 置于同一套层级权重（L1 / `priority_base_physics`）语义下；三合成立时在 `skill_sovereignty_rank` 中追加 `l1_branch_sanhe`。
- **前端**：`extractSanheClusters` 优先读取 `plugin_outputs.sys.core.physics.payload.sanhe_clusters`，再回退 `composite_field_impact`（兼容旧快照与未走 analyze 的本地态）。

## 数据流

1. `PhysicsInferenceSkill` + `evaluate_interactions` 照常写入张量内部字段（算法图未拆除）。
2. `PluginRegistry.run_hook(on_physics_complete, …)` 得到盲派、旺衰等。
3. `inject_sys_core_physics_plugin(physics_tensor, plugin_outputs, metadata)` **覆盖写入** `sys.l1.sanhe` / `sys.l1.liuhe` / `sys.l1.liuchong` / `sys.core.physics` 四行标准结构（均含 `verdict`、`evidence`、`confidence_score`、`payload`）；`metadata` 用于六合/六冲（`conflict_matrix.points`）。
4. `CausalRouter.negotiate_impact(plugin_outputs, physics_tensor=…)` 读取全量插件输出并写入 `meta.causal_routing`。
5. `physics_tensor["plugin_outputs"]` 回传前端；`PluginCollisionHub` **按固定顺序遍历全量键**，不再区分「基础 / 第三方」分区。

## 与「内核不再散装吐出」的关系

当前迭代：**不删除** `composite_field_impact` / `l1_atomic_pipeline` 等张量字段，以免破坏能量拓扑、终判证据链等既有消费者。语义上已将 **裁决可见的 L1 摘要** 收敛到 `sys.core.physics`；后续若要做物理内核纯内部态，可逐步让消费方改读 `plugin_outputs` 再移除顶层字段。

## Debug 降噪

- **移除**：`logic_diff` 面板、`lastSeed` JSON、`interaction_hub` 脚手架列表、拓扑 / 检察院 / 原始 JSON 专页、Hub 因果链文本、`audit_log` 大块直出。
- **logic_diff**：开发态写入 `console.debug('[telemetry] logic_diff', …)`，不占用裁决者主视野。
- **保留**：终审证书（可隐藏 Δabs 遥测块）、LLM 断言正文、插件碰撞博弈、决策时序轴、状态仪表盘、血统证明链、折叠的模型交互。

## 扩展

新增流派或神煞时：实现 `on_physics_complete` 注册 runner 并写入 `plugin_outputs`；Debug 的碰撞列表与路由层将自动纳入，无需再改 `PluginCollisionHub` 的分区逻辑。
