# 核心算法总纲 V2.5 (The Core Algorithm Constitution)
**版本号**: 2.5 (The Unified Field)
**生效日期**: 2025-12-14
**状态**: ACTIVE (Implemented in V7.3 Architecture)

---

## 序言 (Preamble)

本算法总纲将东方传统玄学（八字命理）完全降维打击为现代物理学模型（矢量场、流体力学、波动力学）。
从 V2.5 起，系统不再使用简单的算术累加，而是进行全参数化的物理仿真。所有参数均通过 `FullAlgoParams` (V7.3) 接口暴露给 AI 或用户进行动态调优。

---

## 第一章：基础场域 (Field Environment)

### 第 1 条：五行矢量的定义 (Elemental Vectors)
宇宙由五种基本能量态构成。每一种五行不是一个标量，而是一个具有方向和大小的矢量。
*   **参数**: `physics.seasonWeights` (旺相休囚死: 1.2 / 1.0 / 0.8 / 0.6 / 0.4)

### 第 2 条：壳核结构 (Shell-Core Model)
地支被视为包含多种粒子的“能量包”。其内部能量分布遵循特定比例。
*   **参数**: `physics.hiddenStemRatios` (本气 0.6 / 中气 0.3 / 余气 0.1)

### 第 3 条：宫位引力透镜 (Palace Gravitational Lensing)
四柱并非平权。观测者（日柱）位于引力中心，具有扭曲时空权重的能力。
*   **定义**: 相同的能量，落在日支的影响力远大于落在年支。
*   **参数**: `physics.pillarWeights` (Year 0.8 / Month 1.2 / Day 1.0 / Hour 0.9)

---

## 第二章：粒子动态 (Particle Dynamics)

### 第 4 条：垂直作用与透干 (Vertical Interaction)
地支（根）通过垂直通道向天干（苗）输送能量。
*   **通根 (Rooting)**: 能量通道的宽度。 (`structure.rootingWeight`)
*   **透干 (Projection)**: 隐藏能量显化后的爆发系数。 (`structure.exposedBoost`)
*   **自坐 (Sitting)**: 同柱干支的强相互作用。 (`structure.samePillarBonus`)

### 第 5 条：黑洞效应 (The Black Hole Effect / Void)
当处于**空亡 (Void/Kong Wang)** 状态时，时空发生坍缩，能量被吞噬。
*   **参数**: `structure.voidPenalty` (0.0=完全吞噬, 1.0=无影响)

---

## 第三章：几何交互 (Interactions)

### 第 6 条：横向聚合与聚变 (Fusion & Binding)
*   **天干五合 (Stem Fusion)**: 满足条件（月令支持+相邻）时，两种元素发生聚变，释放巨大能量；否则形成羁绊。
    *   参数: `interactions.stemFiveCombine` (Threshold / Bonus / Penalty)
*   **地支事件 (Branch Events)**: 刑冲合害修正是对时空结构的扰动。
    *   参数: `interactions.branchEvents` (ThreeHarmony / SixHarmony / ClashDamping)

---

## 第四章：能量流转 (Energy Flow / Flux)

### 第 7 条：流体力学模拟 (Flux Simulation)
五行能量遵循生克路径流转。系统不仅计算静态存量，更计算动态流量。
*   **参数**: `flow`
    *   `generationEfficiency`: 生的传递效率。
    *   `generationDrain`: 母体的泄气程度。
    *   `controlImpact`: 克的破坏力。
    *   `dampingFactor`: 系统的总阻尼（熵增），防止计算发散。

### 第 8 条：空间衰减 (Spatial Decay)
能量在传递过程中随距离衰减 (类似于 1/D^2)。
*   **参数**: `flow.spatialDecay` (Gap1 0.6 / Gap2 0.3)

---

## 第五章：时空修正 (Spacetime Modifiers)

### 第 9 条：大运背景辐射 (Background Radiation)
大运作为十年期的背景引力场，对原局产生持续的干涉。
*   **参数**: `spacetime.luckPillarWeight` (0.0 - 1.0)

### 第 10 条：相对论修正 (Relativistic Modifiers)
*   **真太阳时 (Solar Time)**: 时间维度的校准。 (`spacetime.solarTimeImpact`)
*   **地域修正 (Regional Climate)**: 空间维度的温度校准。 (`spacetime.regionClimateImpact`)

---

**批准人**: Architect & Antigravity
**执行代码库**: V7.3 Auto-Tuning Architecture
