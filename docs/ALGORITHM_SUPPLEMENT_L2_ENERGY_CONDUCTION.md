# Antigravity L2 补充文档：能量传导机制 (Energy Conduction)
**主题**: 能量流动的拓扑路径
**版本**: V3.0 (Flow Topology)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`
**状态**: ACTIVE (Logic Standard)

---

## 1. 传导路径拓扑 (Topology of Conduction)

### 1.1 垂直通道 (Vertical)
* **通根 (Rooting)**: 天干向下汲取地支同气能量。
    * *逻辑*: 强度取决于根气的类型（本气/中气/余气），具体权重引用 `@config.physics.rooting_weights`。
* **透干 (Projection)**: 地支能量向上显化。
    * *逻辑*: 透干者获得 **显化加成** (`@config.physics.projection_bonus`)。

### 1.2 水平通道 (Horizontal)
* **生克流转**: 遵循流体力学模型。
    * **生**: 能量传递效率受 `@config.flow.generation_efficiency` 控制。
    * **克**: 能量抵消效率受 `@config.flow.control_impact` 控制。
* **距离衰减**: 作用力随柱间距离衰减，衰减曲线由 `@config.physics.spatial_decay` 定义。

---

## 2. 交互逻辑 (Interaction Logic)

### 2.1 聚合与对撞
* **合 (Combination)**: 能量纠缠态。
    * 合化成功应用 `bonus`，合绊应用 `penalty` (均引用 Config)。
* **冲 (Clash)**: 能量对撞态。
    * 造成能量的不稳定性震荡 (`@config.interactions.clash_damping`)。
* **优先律**: 遵循 **贪合忘冲** 原则。

### 2.2 通关机制 (Mediation)
* **定义**: 当 A 克 B 时，若存在 C 使得 A->C->B 成立。
* **逻辑**: 能量路由重定向。若中间节点 C 的能量满足 `@config.mediation.threshold`，则豁免 A 对 B 的克制惩罚。

---

## 3. 全局约束 (Global Constraints)
系统必须模拟真实物理损耗：
* **阻抗 (Impedance)**: 资源传递的损耗。
* **粘滞 (Viscosity)**: 输出过程的阻力。
* **熵增 (Entropy)**: 系统级的能量自然衰减 (`@config.physics.global_entropy`)。
