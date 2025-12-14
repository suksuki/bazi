# Antigravity 核心算法二级补充文档 (Level 2)
## 专题：时空相对论与宏观国运 (Spacetime Relativity & Macro-Destiny)
**版本：** V3.0 (The Environmental Field)
**依赖：** `Core_Algorithm_Master_V2.5`
**状态：** 📝 已注入 (Injected)

### 1. 宏观场：国运与三元九运 (The Macro-Field: Era & National Destiny)

#### 1.1 物理定义
**国运 (National Destiny)** 是笼罩在所有个体之上的**总背景辐射 (Background Radiation)**。
在 Antigravity 物理引擎中，我们采用**“三元九运”**模型。
* **当前历元:** 九紫离火运 (Period 9 - Fire Era) [2024-2043]。

#### 1.2 算法逻辑：时代共振 (Epochal Resonance)
算法不再视八字为孤立系统，必须叠加时代红利。

* **参数:**
    * `eraElement`: 当前主气 (e.g., 'Fire')
    * `eraBonus`: 顺应时代的加成 (e.g., +0.2)
    * `eraPenalty`: 背离时代的折损 (e.g., -0.1)

* **公式:**
    $$ \mathbf{E}_{\text{Final}} = \mathbf{E}_{\text{Base}} \times (1 + \text{ResonanceFactor}) $$

    * **若喜火 (Needs Fire):** ResonanceFactor = `eraBonus`
    * **若忌火 (Fears Fire):** ResonanceFactor = -`eraPenalty`

### 2. 中观场：地理物理学 (The Meso-Field: Geophysics)

#### 2.1 物理定义
环境决定调候。
* **纬度 (Latitude):** 决定**寒暖**。
* **南北半球:** 决定**季节**。

#### 2.2 算法逻辑：地理修正系数 (K_geo)

* **南方/赤道 (Heat Boost):**
    $$ E_{\text{Fire}}' = E_{\text{Fire}} \times (1 + \text{latitudeHeat}) $$
* **北方/高纬 (Cold Boost):**
    $$ E_{\text{Water}}' = E_{\text{Water}} \times (1 + \text{latitudeCold}) $$
* **南北半球反转 (Seasons Inversion):**
    * 若 `invertSeasons` 为 True，月令的旺相休囚死表反转（子月变为午月的气候特征）。

### 3. 微观场：真太阳时相对论 (The Micro-Field: True Solar Time)

#### 3.1 物理定义
北京时间 12:00 在不同经度的实际太阳角不同。

#### 3.2 算法逻辑：时空扭曲
* **经度校准:**
    $$ T_{\text{solar}} = T_{\text{clock}} + (\text{Longitude} - 120^\circ) \times 4 \text{min} $$
* **开关:** `useSolarTime`

---

### 4. 数据结构更新
Antigravity 需将 `MacroPhysics` 注入 `FinalAlgoParams`。
