# 核心算法总纲 V2.6 (The Core Algorithm Constitution)
**版本号**: 2.6 (The Quantum Relative Field)
**生效日期**: 2025-01-XX
**状态**: ACTIVE (Implemented in V13.0 Probability Engine)

---

## 序言 (Preamble)

本算法总纲将东方传统玄学（八字命理）完全降维打击为现代物理学模型（矢量场、流体力学、波动力学、概率云）。
从 V13.0 起，系统引入**概率波函数 (Probabilistic Wave Function)** 与 **五态相对论 (Five States Relativity)**，不再使用确定性标量，而是计算能量的概率分布与相对状态。

---

## 第一章：基础场域 (Field Environment)

### 第 1 条：五行相对论与五态 (Elemental Relativity & The 5 States)
五行能量的大小并非绝对值，而是取决于粒子与时空指令长（月令/Commander）的相对关系。该关系遵循"旺相休囚死"五态物理模型。

* **物理模型**: $E = E_{base} \times State(Node, Month)$

* **五态定义**:
    1.  **旺 (Wang / Prosperous)**: 同频共振 (Resonance)。日干与月令五行相同。能量 **极大**。
    2.  **相 (Xiang / Assist)**: 能量注入 (Inductance)。月令生助日干。能量 **强**。
    3.  **休 (Xiu / Rest)**: 能量耗散 (Emission)。日干生月令（泄气）。能量 **中下**。（*注：物理上优于"死"*）
    4.  **囚 (Qiu / Trapped)**: 能量做功 (Resistance)。日干克月令（耗身）。能量 **弱**。
    5.  **死 (Si / Dead)**: 能量坍缩 (Collapse)。月令克日干（被克）。能量 **极弱**。（*注：物理上最不稳定的状态*）

* **参数**: `physics.seasonWeights` (Wang 1.2 / Xiang 1.0 / Xiu 0.9 / Qiu 0.6 / Si 0.45)
    * **V13.1 调优**: 泄气(xiu)从0.85提升到0.90，被克(si)从0.50降低到0.45，确保显著差异

### 第 2 条：壳核结构 (Shell-Core Model)
地支被视为包含多种粒子的"能量包"。其内部能量分布遵循特定比例。
* **参数**: `physics.hiddenStemRatios` (本气 0.6 / 中气 0.3 / 余气 0.1)

### 第 3 条：宫位引力透镜 (Palace Gravitational Lensing)
四柱并非平权。观测者（日柱）位于引力中心，具有扭曲时空权重的能力。时空结构遵循 $Day > Month > Hour > Year$ 的引力阶梯。
* **定义**: 相同的能量，落在日支（座下）的影响力远大于落在年支（远方）。
* **参数**: `physics.pillarWeights` (Year 0.7 / Month 1.2 / Day 1.35 / Hour 0.9)
    * **V13.1 调优**: 日支权重从1.2提升到1.35，解决Group C倒挂问题

---

## 第二章：粒子动态 (Particle Dynamics)

### 第 4 条：非线性垂直作用 (Non-linear Vertical Interaction)
地支（根）通过垂直通道向天干（苗）输送能量。此过程遵循非线性饱和效应（Sigmoid/Tanh）。

* **通根饱和 (Root Saturation)**: 根气的叠加遵循边际递减效应。第一个根是雪中送炭，第三个根是锦上添花。
    * 参数: `structure.rootingWeight`, `structure.saturationSteepness`

* **自坐结构 (Sitting Bonus)**: 同柱干支（如甲寅）拥有额外的结构稳定性乘数，不受饱和函数压缩。
    * 参数: `structure.samePillarBonus` (Post-Nonlinear Multiplier)
    * **V13.1 调优**: 从1.8提升到3.0，显著拉开自坐强根与远根的差距

* **透干 (Projection)**: 隐藏能量显化后的爆发系数。 (`structure.exposedBoost`)

* **📖 详细机制**: 参见 `ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md` 第 2 章：垂直传导

### 第 5 条：黑洞效应 (The Black Hole Effect / Void)
当处于**空亡 (Void/Kong Wang)** 状态时，时空发生坍缩，能量被吞噬。
* **参数**: `structure.voidPenalty` (0.0=完全吞噬, 1.0=无影响)

---

## 第三章：几何交互 (Interactions)

### 第 6 条：横向聚合与聚变 (Fusion & Binding)
* **天干五合 (Stem Fusion)**: 满足条件（月令支持+相邻）时，两种元素发生聚变，释放巨大能量；否则形成羁绊。
    * 参数: `interactions.stemFiveCombine` (Threshold / Bonus / Penalty)
* **地支事件 (Branch Events)**: 刑冲合害修正是对时空结构的扰动。
    * 参数: `interactions.branchEvents` (ThreeHarmony / SixHarmony / ClashDamping)
* **通关机制 (Mediation)**: 当存在中间元素（通关神）时，原本的克制关系会被转化或豁免，形成"贪生忘克"。
    * 参数: `logic_switches.enable_mediation_exemption` (True/False)
* **📖 详细机制**: 参见 `ALGORITHM_V6.1_CLASH_COMBINATION.md` 和 `ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md` 第 3.1.3、3.2.2、3.2.3、7 节

---

## 第四章：能量流转 (Energy Flow / Flux)

### 第 7 条：流体力学模拟 (Flux Simulation)
五行能量遵循生克路径流转。系统不仅计算静态存量，更计算动态流量。
* **参数**: `flow`
    * `generationEfficiency`: 生的传递效率。
    * `generationDrain`: 母体的泄气程度。
    * `controlImpact`: 克的破坏力。
    * `dampingFactor`: 系统的总阻尼（熵增），防止计算发散。
* **📖 详细机制**: 参见 `ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md` 第 3 章：水平传导、第 6 章：全局约束

### 第 8 条：空间衰减 (Spatial Decay)
能量在传递过程中随距离衰减 (类似于 1/D^2)。
* **参数**: `flow.spatialDecay` (Gap1 0.6 / Gap2 0.3)
* **📖 详细机制**: 参见 `ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md` 第 4 章：距离衰减

---

## 第五章：时空修正 (Spacetime Modifiers)

### 第 9 条：大运背景辐射 (Background Radiation)
大运作为十年期的背景引力场，对原局产生持续的干涉。
* **参数**: `spacetime.luckPillarWeight` (0.0 - 1.0)

### 第 10 条：相对论修正 (Relativistic Modifiers)
* **真太阳时 (Solar Time)**: 时间维度的校准。 (`spacetime.solarTimeImpact`)
* **地域修正 (Regional Climate)**: 空间维度的温度校准。 (`spacetime.regionClimateImpact`)
* **📖 详细机制**: 参见 `ALGORITHM_SUPPLEMENT_L2_SPACETIME.md`

---

## 二级补充文档索引 (Level 2 Supplements)

本总纲的详细实现机制和扩展算法请参考以下二级补充文档：

1. **能量传导机制** (`ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md`)
   - 垂直传导（通根、透干）
   - 水平传导（天干间、地支间）
   - 跨维度传导（天干↔地支跨柱）
   - 距离衰减、全局约束（阻抗、粘滞、熵增、阻尼）
   - **通关机制**（食伤通关、官杀护财）
   - **能量结算示例**（生克抵消、合力共振、通关转化的完整计算流程）
   - 传导优先级规则

2. **墓库拓扑学** (`ALGORITHM_SUPPLEMENT_L2_STOREHOUSE.md`)
   - 库（Vault）与墓（Tomb）的物理定义
   - 闭库态、隧穿态、坍塌态的交互机制
   - 量子隧穿与能量释放

3. **时空相对论** (`ALGORITHM_SUPPLEMENT_L2_SPACETIME.md`)
   - 宏观场：国运与三元九运
   - 中观场：地理物理学修正
   - 微观场：真太阳时相对论

4. **量子纠缠与粒子对撞** (`ALGORITHM_V6.1_CLASH_COMBINATION.md`)
   - 冲（Clash）：粒子对撞机模型
   - 合（Combination）：量子纠缠模型
   - 贪合忘冲（Resolution Logic）

---

## 附录 A：量子十二长生能级表 (Appendix A: Quantum Life Stage Coefficients)

本表定义了天干（粒子）在地支（环境）中的 **微观能级系数**。系统不再使用模糊的描述，而是使用精确的乘数因子。

**参数路径**: `physics.lifeStageCoefficients`

| 状态 (State) | 中文名 | 物理定义 (Definition) | 能量系数 (Coefficient) $\mu$ | 波动率 (Volatility) $\sigma$ |
| :--- | :--- | :--- | :--- | :--- |
| **Chang Sheng** | **长生** | **能量涌现 (Emergence)**。粒子处于加速上升期，源源不断。 | **1.30** | 0.10 (稳) |
| **Mu Yu** | **沐浴** | **震荡清洗 (Bath)**。能量不稳定，易受外界干扰（桃花/败地）。 | **1.10** | 0.25 (乱) |
| **Guan Dai** | **冠带** | **形态稳固 (Forming)**。粒子能量成型，具备抵抗力。 | **1.25** | 0.10 (稳) |
| **Jian Lu** | **临官** | **稳态峰值 (Prosperous)**。**禄神**。能量最纯粹、最稳定的状态。 | **1.50** | 0.05 (极稳) |
| **Di Wang** | **帝旺** | **极限峰值 (Peak)**。**羊刃**。能量极强，但接近临界点，伴随高波动。 | **1.60** | 0.20 (险) |
| **Shuai** | **衰** | **能量衰减 (Decline)**。虽然减弱，但余威尚存（惯性）。 | **0.90** | 0.10 (稳) |
| **Bing** | **病** | **功能障碍 (Sickness)**。能量流动受阻，效率下降。 | **0.60** | 0.15 (弱) |
| **Si** | **死** | **能量静止 (Stillness)**。完全被克制，无活性。 | **0.40** | 0.05 (死) |
| **Mu** | **墓** | **势能存储 (Storage)**。能量被封印。**开库前=0.5，开库后=1.5**。 | **0.50** (闭) | 0.00 (封) |
| **Jue** | **绝** | **断裂点 (Extinction)**。气机断绝，无根无气。 | **0.20** | 0.05 (无) |
| **Tai** | **胎** | **量子孕育 (Conception)**。微弱的能量扰动，尚未成型。 | **0.50** | 0.20 (虚) |
| **Yang** | **养** | **温和积蓄 (Nourish)**。能量缓慢增长，准备爆发。 | **0.80** | 0.10 (稳) |

**计算规则**:
1.  **叠加原则**: 若天干在多支中见长生，取最大值并按阻尼叠加。
2.  **阳刃特例**: 阳干见帝旺为"阳刃"，系数强制修正为 **1.80** (因其破坏力)。
3.  **墓库特例**: 见 `ALGORITHM_SUPPLEMENT_L2_STOREHOUSE.md`，若满足开库条件，系数从 0.5 跃迁至 1.5。

**物理意义**:
- **能量系数 ($\mu$)**: 表示该状态下粒子的平均能量倍数，直接应用于能量计算。
- **波动率 ($\sigma$)**: 表示该状态下能量的不确定度，用于概率分布计算（V13.0 概率波函数）。

**应用场景**:
- **Group B (通根)**: 坐禄 (临官 1.5) vs 远根 (其他状态) 的差距计算
- **Group C (宫位)**: 日支坐禄 (1.5) vs 时支归禄 (1.5 × 距离衰减) vs 年支其他状态 (1.1-1.3)
- **能量传导**: 不同长生状态的根气传导效率不同

---

**批准人**: Architect & Antigravity
**执行代码库**: V13.0 Probability Wave Engine + V2.6 Core Params

