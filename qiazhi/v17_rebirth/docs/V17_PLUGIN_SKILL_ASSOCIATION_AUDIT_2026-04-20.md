---
title: V17 插件审计 — 完整性与 Skill 关联性
date: 2026-04-20
---

本次审计基于 `/api/v17/admin/plugins` 数据源（`registry_rows_for_admin()`）与
`SpecValidator.scan_all_plugins()` 输出比对。

## 一、总体结论

- 插件扫描完整性：**完整**（当前一共 77 条插件记录，未发现重复 `plugin_id`）。
- 模块加载完整性：**完整**（`backend/logic` 下 31 个可扫描子模块全部可 import）。
- L0-L3 归类分布：
  - L0: 5
  - L1: 22
  - L2: 49
  - L3: 1
  - L4: 0
- 与 Skill 清单（`V17_SKILL_MANIFEST`）绑定情况：
  - 标准化成功（`is_standard_skill=True`）：77
  - 未绑定（`is_standard_skill=False`）：0
- 策略通过率（`policy_valid=True`）：
  - 77 / 77（admin 视角已全部纳入统一 skill 治理）
  - 0 / 77（当前无未纳管插件）

## 二、结论解释

从系统侧链路看，**当前插件注册/发现链路是完整的**，并未出现“漏发现”。
  
此前在“Skill 规范化”层面，确实存在大量历史或专题插件仍为“非标准记录”，这会导致：

- 管理界面显示为 `policy_valid: false`；
- 参数治理无法走统一 `V17_SKILL_MANIFEST` 工具链；
- 审计/策略联动能力不完整。

因此当前不是“插件不完整”，而是“插件的规范化覆盖率不完整”。  
本轮补齐后，L0/L1/L2/L3 全部插件都已经可以在 admin 中按“标准 skill”身份被识别。

## 三、未关联 Skill 的插件明细（按层）

当前已清零。  
admin 注册表中的 77 条插件均已拥有标准 skill 身份，来源分为三类：

- 显式 `V17_SKILL_MANIFEST`
- `manifest-backed skill`
- `spec-backed skill`

## 四、标准化通过的插件（示例）

已通过标准化/可直接进入 skill 治理链的 77 条。

- `l1.physics.op_status`
- `l1.physics.full_bandwidth`
- 其中：
- `显式 manifest`：原本已声明 `V17_SKILL_MANIFEST` 的插件
- `manifest-backed skill`：由 `l1_physics_manifest.json` 物化并在 admin 中升级为标准 skill 的插件
- `spec-backed skill`：由正式 `V17PluginSpec` 自动合成为标准 skill 的插件

这意味着当前 admin / 审计 / 参数治理 / UI 展示已经可以用统一协议理解整套插件系统。

## 五、建议动作（下一步）

1. 先决定标准化范围：是“先全部收口到 Skill”，还是“仅核心 15 条 + 风险保留”。  
2. 若决定全量收口，给我一个“先处理优先级”我来分三轮补齐：
   - 先补 L1 关系算子；
   - 再补 L2 子平/盲派；
   - 最后补 L2 格局专题。
3. 我建议把 `SpecValidator` 警告纳入 CI 保护：`policy_valid=False` 触发告警不阻塞发布。
