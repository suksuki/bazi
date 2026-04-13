# Qiazhi-Bazi 插件系统全量审计与健康度报告（V6 前置）

- **生成时间（UTC）**: 2026-04-13T01:58:48.269726+00:00
- **审计方式**: 只读加载 `PluginRegistry` + `l1_physics_manifest.json`；**不**启动 SSE/HTTP，**不**写入运行时遥测 `_PLUGIN_STATS`。
- **代码根**: `/home/hlsystem/bazi/qiazhi_bazi/backend`

## 1. 契约说明：evaluate / dry_run / metadata

| 维度 | 现状 | 说明 |
|------|------|------|
| **evaluate()** | `PluginSpec.runner(**context)` | `context` 含 `is_preview` / `dry_run`；契约见 `app/plugins/spec.py`。 |
| **dry_run()** | `PluginService.dry_run_on_physics_complete` | 深拷贝入参后 `is_preview=True`+`dry_run=True` 调 `run_hook`；Orchestrator 在 `is_preview` 时仍 **跳过** `attach_plugin_selection_trace` 等落库。 |
| **metadata** | `get_manifest()` 合并 `skill_manifest` + `merge_plugin_manifest_into_metadata` | L1 原子算子另从 `l1_physics_manifest.json` 注入 `physical_impact` / `judgment_protocol` 等。 |

## 2. 影子态（is_preview）与 side-effects

- **协议位置**: API `is_preview` → `OrchestratorService.run_internal_loop(..., is_preview=True)`；`physics_update` 载荷可带 `is_preview: true`。
- **插件上下文**: `PluginService.run_on_physics_complete(..., is_preview=, dry_run=)` 将标志传入 `run_hook`；插件仍可能 **改写** 传入的 `physics_tensor` / `meta`（`dry_run_on_physics_complete` 使用深拷贝保护调用方）。
- **持久化门闩**: `orchestrator_service` 在 `not is_preview` 时附加 `plugin_selection_trace` / `inference_trace` 等到 metadata 对象。
- **仓库扫描**: `app/plugins/**/*.py` 中 **未发现** SQLAlchemy `session`/`commit`/原生 SQL 写入；侧效应以 **张量与 meta 内存写**为主。

## 3. Registry 插件清单（逻辑完整性摘要）

| plugin_id | Hook | 逻辑完整性 | 物理影响（摘要） | 影子兼容 |
|-----------|------|------------|------------------|----------|
| `base.chronos` | `on_physics_complete` | runner 已注册 | meta.chronos_v1 / 司令余气（不直接改 L1 delta） | 预览可跑；须依赖 orchestrator 跳持久化 |
| `classical.blind_school.v1` | `on_physics_complete` | runner 已注册 | work_vector、盲派 η、chip 日志、meta 穿透语义 | 预览可跑；须依赖 orchestrator 跳持久化 |
| `classical.wangshuai.v1` | `on_physics_complete` | runner 已注册 | 消费 deity_axes，写旺衰审计（默认不改写张量） | 预览可跑；须依赖 orchestrator 跳持久化 |
| `modern.wealth_risk.v1` | `on_verdict_ready` | runner 已注册 | `on_verdict_ready`：work_vector + structure，风险叙事 | 仅终判后；预览 SSE 不触发本 hook |
| `sys.core.physics` | `on_physics_complete` | runner 已注册 | L0 合成场、流水线、physics_trace（全张量） | 预览可跑；须依赖 orchestrator 跳持久化 |

## 4. L1 原子算子（manifest 注册）物理锚点

- **算子数量**: 23
- **轴类型归纳**: 多数算子作用在 **`deity_energy_axes.absolute_energy`**（Abs）或 **L1 interaction delta**；`op_interdimensional` 另涉传导率与 **Structural** 垂直摩擦。

## 5. 冲突矩阵（共享 `physics_settings_keys`）

### 5.1 总闸键（多算子共享，预期行为）

| 配置键 | 引用算子数 |
|--------|------------|
| `L1_CORE_CONFLICT_OPS_ENABLE` | 14 |
| `L1_SUB_BRANCH_OP_ENABLE` | 7 |
| `L1_STEM_FUSION_ENABLE` | 2 |

### 5.2 非总闸：潜在「逻辑对冲」锚点（同一键被多个算子读取）

| 配置键 | 算子 id（节选） | 风险 |
|--------|-----------------|------|
| `STEM_FUSION_VECTOR_LEAK_RATIO` | `base.physics.op_stem_fusion_stuck`, `base.physics.op_stem_fusion_transformed` | 中：调参时因果顺序敏感 |

- **盲派 × L1**: `MANGPAI_*` 与 `op_interdimensional` / `op_destruction` 等在叙事上可能 **叠乘 abs 通道**；已由 `CausalRouter` 与审计链缓解，V6 建议保留 **显式 hotspot 表**。

## 6. 依赖边（Registry）

| from | to |
|------|-----|
| `base.physics_l1` | `sys.core.physics` |
| `base.physics_l1` | `classical.blind_school.v1` |
| `base.chronos` | `classical.blind_school.v1` |
| `base.physics_l1` | `classical.wangshuai.v1` |
| `base.chronos` | `classical.wangshuai.v1` |
| `base.physics_l1` | `modern.wealth_risk.v1` |
| `classical.blind_school.v1` | `modern.wealth_risk.v1` |

## 7. 插件清单（扩展列：版本 / 状态 / 影子得分 / V6）

| id | 版本 | Registry 状态 | Active/Deprecated | 影子预览得分 | 准确度 | V6 建议 |
|----|------|-----------------|-------------------|---------------------|--------|---------|
| `base.chronos` | 1.0 | HEALTHY | Active | READY_FOR_AI | READY_FOR_AI | READY_FOR_AI |
| `classical.blind_school.v1` | skill_manifest v1 | HEALTHY | Active | READY_FOR_AI | READY_FOR_AI | READY_FOR_AI |
| `classical.wangshuai.v1` | 1.0 | HEALTHY | Active | READY_FOR_AI | READY_FOR_AI | READY_FOR_AI |
| `modern.wealth_risk.v1` | 1.0 | HEALTHY | Active | READY_FOR_AI | READY_FOR_AI | READY_FOR_AI |
| `sys.core.physics` | bundle（lazy） | HEALTHY | Active | READY_FOR_AI | READY_FOR_AI | READY_FOR_AI |

_L0 三卡与 L1 `base.physics.op_*` 行详见 `get_manifest()` 完整 JSON；本表聚焦 **Registry `PluginSpec`** 级插件。_

## 8. Registry 显式互斥对与因果优先级

- **因果优先级**: `run_hook` 排序键为 `(-_plugin_causal_tier(plugin_id), -priority)`：`sys.core.physics` > `base.chronos` > `classical.*` > `modern.*`。

_当前 `_PLUGIN_MUTEX_PAIRS` 为空元组；可在 `registry.py` 填入互斥对。_

## 9. 验证声明

- 本报告由 `qiazhi_bazi/scripts/generate_plugin_audit_report.py` 生成，**不** import `uvicorn`、**不** 打开 SSE 端口。
- 重新生成: `python3 qiazhi_bazi/scripts/generate_plugin_audit_report.py`

## 10. L1 算子注册表（manifest 自动摘录）

| id | op_id | physics_settings_keys（节选） |
|----|-------|----------------------------------|
| `base.physics.op_blade_clash` | `L1_OP_BLADE_CLASH` | L1_CORE_CONFLICT_OPS_ENABLE, L1_BLADE_CLASH_INSTABILITY, ENTROPY_W_BLADE, ENTROPY_BLADE_REF |
| `base.physics.op_branch_banhe` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_BANHE_PHI, SUB_BRANCH_BANHE_ABS_BOOST, SUB_BRANCH_BANHE_VECTOR_BOOST |
| `base.physics.op_branch_liuchong` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_LIUCHONG_ABS_DAMP |
| `base.physics.op_branch_liuhai` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_LIUHAI_ENABLE, SUB_BRANCH_LIUHAI_ABS_DAMP |
| `base.physics.op_branch_liuhe` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_LIUHE_ABS_BOOST |
| `base.physics.op_branch_liupo` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_LIUPO_ENABLE, SUB_BRANCH_LIUPO_ABS_DAMP |
| `base.physics.op_branch_sanhe` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_SANHE_ABS_BOOST, SUB_BRANCH_SANHE_REQ_WANG_ZHI, SANHE_ALPHA_LEAKAGE |
| `base.physics.op_branch_sanxing` | `L1_OP_SUB_BRANCH_INTERACTION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_SUB_BRANCH_OP_ENABLE, SUB_BRANCH_SANXING_ABS_DAMP |
| `base.physics.op_destruction` | `L1_OP_DEST` | L1_OP_DEST_ETA |
| `base.physics.op_gov_kill_mix` | `L1_OP_GOV_KILL_MIX` | L1_CORE_CONFLICT_OPS_ENABLE, L1_GOV_KILL_EFFICIENCY_LOSS |
| `base.physics.op_interdimensional` | `STEM_BRANCH_COUPLING` | INTERDIMENSIONAL_CONDUCTIVITY, INTERDIMENSIONAL_BARRIER_STRENGTH, CONDUCTIVITY_DECAY_RATE, GHOST_ENERGY_DAMPING, MANGPAI_ETA_DIMENSIONAL_CRUSH, MANGPAI_ROOT_RESONANCE, INTERDIMENSIONAL_SHIELD_ENABLE, STEM_BRANCH_ROOT_RESONANCE_ENABLE, …(+1) |
| `base.physics.op_lab_climate_topology` | `L1_LAB_CLIMATE_TOPOLOGY` | CLIMATE_INTENSITY, STEM_RESONANCE_BOOST, TRANSFER_DISTANCE_DECAY, WORK_MIN_THRESHOLD |
| `base.physics.op_lab_risk_tomb` | `L1_LAB_RISK_TOMB` | BASE_BACKFIRE_RISK, HIGH_IMBALANCE_RISK, TOMB_LOCK_RATE |
| `base.physics.op_lab_timing_weights` | `L1_LAB_TIMING_WEIGHTS` | WEIGHT_LUCK, WEIGHT_YEAR |
| `base.physics.op_lab_work_visibility` | `L1_LAB_WORK_VISIBILITY` | SHOW_WEAK_WORK_PATHS |
| `base.physics.op_owl_food` | `L1_OP_OWL_FOOD` | L1_CORE_CONFLICT_OPS_ENABLE, L1_OWL_FOOD_DAMPING |
| `base.physics.op_production` | `L1_OP_PROD` | L1_OP_PROD_ETA |
| `base.physics.op_robber_wealth` | `L1_OP_ROBBER_WEALTH` | L1_CORE_CONFLICT_OPS_ENABLE, L1_ROBBER_WEALTH_ALLOC_LOSS |
| `base.physics.op_shangguan_jian_guan` | `L1_JUNCTION_SGJG` | SGJG_COORDINATE_DISTORTION_DECAY, SGJG_COORDINATE_DISTORTION_BASE, SGJG_MINOR_ABS_LOSS_CAP_RATIO |
| `base.physics.op_status` | `L1_OP_STATUS` | L1_STATUS_OP_ENABLE, STATUS_BOOST_MULTIPLIER, STATUS_DRAIN_MULTIPLIER |
| `base.physics.op_stem_fusion_stuck` | `L1_OP_STEM_FUSION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_STEM_FUSION_ENABLE, STEM_FUSION_BRANCH_SUPPORT_RATIO, STEM_FUSION_VECTOR_LEAK_RATIO |
| `base.physics.op_stem_fusion_transformed` | `L1_OP_STEM_FUSION` | L1_CORE_CONFLICT_OPS_ENABLE, L1_STEM_FUSION_ENABLE, STEM_FUSION_VECTOR_LEAK_RATIO |
| `base.physics.op_wealth_seal` | `L1_OP_WEALTH_SEAL` | L1_CORE_CONFLICT_OPS_ENABLE, L1_WEALTH_SEAL_COLLAPSE, L1_WEALTH_SEAL_ROUTING_YIN_FACTOR, L1_WEALTH_SEAL_ROUTING_CAI_FACTOR |

## 11. 与生产 SSE / 运行时隔离

- 本审计 **仅** 使用 `PluginRegistry` 与 JSON manifest 的内存结构；**不** 调用 `run_hook`、**不** 向 `orchestrator` 注册回调、**不** 占用 `asyncio` 事件循环。
- 生成报告时设置的 `DATABASE_URL` 占位符 **仅** 用于通过 `app.db.session` 模块导入校验；脚本不执行 `session_scope()`。

## 12. 附录：前端「影子预览」与插件的边界

- 前端 Hover 预览依赖 Orchestrator `is_preview` + `physics_update`；**水位线等多语言文案** 由 `frontend/src/constants/locales.ts` 与 `PatternWaterlinePanel` 的 `key={lang}` 驱动，与插件 manifest 分离维护。
- V6 若引入「插件推荐」模型，建议以本报告 **§5.2 + §10** 为 **RAG 结构化切片** 来源，避免 LLM 误读自由文本 readme。
