# Antigravity L3 补充文档：格局拓扑协议 (Pattern Topology)
**主题**: 格局结构的通用物理接口
**版本**: V3.0 (The Pattern Standard)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`, `QGA_HR_REGISTRY_SPEC_v3.0.md`
**状态**: ACTIVE (Interface Standard)

---

## 1. 核心定义 (Core Definition)
格局是特定能量流动的 **拓扑结构 (Topological Structure)**。
所有格局模块必须实现 `IPatternPhysics` 接口，包含三个强制组件。

---

## 2. 能量门控协议 (Energy Gating Protocol)
* **物理原理**: 只有达到 **临界质量 (Critical Mass)** 的命局才能支撑高阶结构。
* **实现要求**: 
    * 严禁在代码中写死阈值。
    * 必须调用 `@config.gating` 中的参数（如 `min_self_energy`）进行判定。
    * 未通过门控者，必须标记为 `COLLAPSED` (破格)。

---

## 3. 拓扑分型标准 (Topology Standard)
* **同分异构体**: 一个格局 ID 下必须包含多个子流形 (Sub-Patterns)，分别对应不同的能量路径（如"正官佩印" vs "财官双美"）。
* **数据映射**: L3 拓扑直接映射到 Registry JSON 中的 `sub_patterns_registry` 数组。

---

## 4. 安全阀机制 (Safety Valve Mechanism)
* **物理原理**: 防止系统过载的负反馈机制。
* **类型**:
    * **阻尼 (Damping)**: 印星吸收压力。
    * **疏导 (Conductance)**: 财星导出能量。
    * **对抗 (Counter-Acting)**: 食伤制衡七杀。
* **输出**: 必须在结果元数据中包含安全阀的状态报告。
