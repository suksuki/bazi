# Antigravity L3 补充文档：格局拓扑协议
**主题**: 格局结构的通用物理接口
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`

## 1. 核心定义 (Core Definition)
在 Antigravity 引擎中，"格局 (Pattern)" 被定义为一种 **特定形态的能量流动拓扑**。
所有格局模块必须实现 `IPatternPhysics` 接口，包含以下三个强制组件：

1.  **门控 (Gating)**: 决定该结构能否形成的能量阈值。
2.  **拓扑 (Topology)**: 该结构在不同边界条件下的同分异构体。
3.  **安全阀 (Safety)**: 维持该结构稳定所需的负反馈机制。

---

## 2. 能量门控协议 (Energy Gating Protocol)

### 2.1 物理原理
并不是所有命局都能支撑得起特定的高能结构（如七杀、伤官）。
* **临界质量 (Critical Mass)**: 日主（Self）或关键用神必须达到特定的能量密度，才能激活格局。
* **坍缩风险 (Collapse Risk)**: 若未通过门控，该格局被视为“破格”或“假格”，能量结构处于坍缩态。

### 2.2 实现要求
* 配置系统必须提供 `thresholds.pattern_gating` 参数。
* 逻辑必须检查：`Energy(Core) >= Threshold`。
* **硬性条件**: 某些格局必须要求“通根”或“透干”作为物理前置条件。

---

## 3. 拓扑分型标准 (Topology Standard)

### 3.1 同分异构体 (Isomers)
一个主格局 ID (如 A-01 正官) 不是单一状态，而是包含多个子形态（Sub-Patterns）。
子形态的区分通常基于：
* **能量流向**: 是流向印（转化）还是流向财（耗散）？
* **辅助元素**: 是否有特定元素（如食伤）介入？

### 3.2 命名规范
* **秩序型 (Order Type)**: 强调稳定性、守恒、转化。 (e.g., Director, Guardian)
* **耗散型 (Chaos Type)**: 强调流动性、做功、熵减。 (e.g., Tycoon, Performer)

---

## 4. 安全阀机制 (Safety Valve Mechanism)

### 4.1 物理原理
高能格局往往伴随不稳定性（High Volatility）。为了防止计算溢出或系统崩溃，必须定义冷却或制动机制。

### 4.2 类型定义
* **阻尼 (Damping)**: 引入“印星”吸收过剩能量，降低系统震荡。
* **疏导 (Conductance)**: 引入“财星”导出滞留能量，防止阻塞。
* **对抗 (Counter-Acting)**: 引入“食伤”进行矢量抵消，制衡高压。

### 4.3 警告状态
当安全阀缺失或失效时，系统应输出 `WARNING` 或 `DANGER` 级别的结构风险提示。
