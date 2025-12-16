# Antigravity 核心算法二级补充文档 (Level 2)
## 专题：能量传导机制 (Energy Conduction Mechanism)
**版本：** V2.5 (Unified Field Theory)
**依赖：** `Core_Algorithm_Master_V2.5`
**状态：** ✅ 已实现 (Implemented in FlowEngine & GraphNetworkEngine)

---

## 1. 物理定义 (Physics Definition)

**能量传导 (Energy Conduction)** 是八字系统中能量在不同粒子（天干、地支）之间流动的物理过程。

### 1.1 传导路径分类

能量传导遵循三种基本路径：

1. **垂直传导 (Vertical Conduction)**: 同柱内天干 ↔ 地支
2. **水平传导 (Horizontal Conduction)**: 不同柱之间的天干 ↔ 天干、地支 ↔ 地支
3. **跨维度传导 (Cross-Dimensional Conduction)**: 天干 ↔ 地支（跨柱）

---

## 2. 垂直传导 (Vertical Conduction)

### 2.1 通根 (Rooting) - 天干 → 地支

**物理意义**: 天干在地支藏干中找到同属性粒子，形成能量锚定。

**传导公式**:
$$ E_{\text{stem}}' = E_{\text{stem}} \times (1 + \text{rootingWeight} \times \text{rootRatio}) $$

**参数**:
- `structure.rootingWeight`: 通根系数（默认 4.8）
- `rootRatio`: 藏干中匹配天干的比例（0.6 主气 / 0.3 中气 / 0.1 余气）

**距离衰减**:
- **自坐 (Same Pillar)**: 无衰减，应用 `samePillarBonus` (默认 1.2)
- **跨柱通根**: 应用距离衰减 $1/D^N$，其中 $D$ 为柱间距离

**示例**:
```
日干（甲）在年支（寅）中找到藏干（甲），形成通根
- 如果自坐（甲寅）：能量 × 1.2（自坐强根）
- 如果跨柱（甲子 + 寅）：能量 × 1.0 × 0.6（距离衰减）
```

### 2.2 透干 (Projection) - 地支 → 天干

**物理意义**: 地支藏干能量显化到天干，形成能量爆发。

**传导公式**:
$$ E_{\text{stem}}' = E_{\text{stem}} + E_{\text{hidden}} \times \text{exposedBoost} $$

**参数**:
- `structure.exposedBoost`: 透干爆发系数（默认 1.5）
- `E_{\text{hidden}}`: 藏干能量（按 60/30/10 比例加权）

**示例**:
```
年支（寅）藏干（甲、丙、戊）中的（甲）透到年干（甲）
- 透干能量 = 藏干（甲）能量 × 1.5
- 年干总能量 = 基础能量 + 透干能量
```

---

## 3. 水平传导 (Horizontal Conduction)

### 3.1 天干之间的传导

#### 3.1.1 生 (Generation) - 能量传递

**物理意义**: 母元素向子元素传递能量，形成能量流。

**传导公式**:
$$ E_{\text{target}}' = E_{\text{target}} + E_{\text{source}} \times \text{generationEfficiency} \times K_{\text{distance}} $$

**参数**:
- `flow.generationEfficiency`: 生的传递效率（默认 0.2-0.4）
- `K_{\text{distance}}`: 距离衰减系数（见第 4 条）

**传导路径**:
- **顺生链 (Sequential Chain)**: 年→月→日→时，形成连续能量传递
  - 每增加一环，最终受益者能量放大
  - 放大倍率: `Sequential_Gain_Factor ^ 链长度` (默认 1.20)
- **合力共振 (Coherent Resonance)**: 多个天干同时生同一目标
  - 放大倍率: `1 + (N - 1) × Coherence_Boost_Factor` (默认 0.15)

**示例**:
```
年干（木）生月干（火），月干（火）生日干（土）
- 顺生链长度 = 2
- 日主（土）能量 *= 1.20^2 = 1.44（放大 44%）
```

#### 3.1.2 克 (Control) - 能量抵消

**物理意义**: 控制元素削弱被控元素，形成能量对抗。

**传导公式**:
$$ E_{\text{target}}' = E_{\text{target}} \times (1 - \text{controlImpact} \times K_{\text{distance}}) $$

**参数**:
- `flow.controlImpact`: 克的打击力系数（默认 0.7-1.25）
- `K_{\text{distance}}`: 距离衰减系数

**多重抵消 (Multi-Force Cancellation)**:
- 如果同时存在生和克，计算净能量系数
- 净能量 = `(N_support - N_control × Cancellation_Factor) / (N_support + N_control)`
- `Cancellation_Factor`: 默认 0.60（克的力量是生的 60%）

**示例**:
```
年干（木）生日干（火），月干（水）克日干（火）
- N_support = 1, N_control = 1
- 净能量系数 = (1 - 1 × 0.60) / (1 + 1) = 0.20
- 日主能量 *= 0.20（保留 20%）
```

#### 3.1.3 合 (Combination) - 能量聚合

**物理意义**: 两个天干发生量子纠缠，能量聚合或羁绊。

**传导公式**:
- **合化成功**: $E_{\text{new}} = (E_1 + E_2) \times \text{bonus}$ (默认 2.5)
- **合绊**: $E_1' = E_1 \times \text{penalty}$, $E_2' = E_2 \times \text{penalty}$ (默认 0.4)

**参数**:
- `interactions.stemFiveCombination.bonus`: 合化成功倍率（默认 2.5）
- `interactions.stemFiveCombination.penalty`: 合绊折损（默认 0.4）
- `interactions.stemFiveCombination.threshold`: 合化阈值（默认 0.8）

---

### 3.2 地支之间的传导

#### 3.2.1 六冲 (Clash) - 能量湮灭

**物理意义**: 两个反向矢量对撞，能量湮灭或释放。

**传导公式**:
$$ E_{\text{branch}}' = E_{\text{branch}} \times (1.0 - \text{clashDamping}) $$

**参数**:
- `interactions.branchEvents.clashDamping`: 冲的折损系数（默认 0.2-0.8）
- `interactions.branchEvents.clashScore`: 冲的基础扣分（默认 -5.0）

**贪合忘冲 (Resolution Logic)**:
- 如果地支参与合局（六合/三合），则豁免冲的伤害
- 但需支付 `resolutionCost` 能量税（默认 0.1-0.4）

#### 3.2.2 六合 (Six Harmony) - 能量耦合

**物理意义**: 两个地支形成近场耦合，能量增强。

**传导公式**:
$$ E_{\text{branch}}' = E_{\text{branch}} + E_{\text{partner}} \times \text{sixHarmony} $$

**参数**:
- `interactions.branchEvents.sixHarmony`: 六合加成（默认 5.0-15.0）

#### 3.2.3 三合 (Three Harmony) - 能量共振

**物理意义**: 三个地支形成相位锁定，产生强共振。

**传导公式**:
$$ E_{\text{target}}' = E_{\text{target}} \times \text{trineBonus} $$

**参数**:
- `interactions.comboPhysics.trineBonus`: 三合倍率（默认 1.2-2.5）
- `interactions.comboPhysics.halfBonus`: 半合倍率（默认 1.5）
- `interactions.comboPhysics.archBonus`: 拱合倍率（默认 1.1）

---

## 4. 距离衰减 (Spatial Decay)

### 4.1 衰减公式

能量在传递过程中随距离衰减，遵循 $1/D^N$ 规律。

**衰减系数**:
$$ K_{\text{distance}} = \begin{cases}
\text{spatialDecay.gap1} & \text{if } D = 1 \text{ (相邻柱)} \\
\text{spatialDecay.gap2} & \text{if } D = 2 \text{ (隔一柱)} \\
\text{spatialDecay.gap2}^2 & \text{if } D = 3 \text{ (隔两柱)}
\end{cases} $$

**参数**:
- `flow.spatialDecay.gap1`: 相邻柱衰减（默认 0.6）
- `flow.spatialDecay.gap2`: 隔一柱衰减（默认 0.3）

**距离计算**:
- 年柱 ↔ 月柱: $D = 1$
- 年柱 ↔ 日柱: $D = 2$
- 年柱 ↔ 时柱: $D = 3$
- 月柱 ↔ 日柱: $D = 1$
- 月柱 ↔ 时柱: $D = 2$
- 日柱 ↔ 时柱: $D = 1$

---

## 5. 跨维度传导 (Cross-Dimensional Conduction)

### 5.1 天干 ↔ 地支（跨柱）

**物理意义**: 天干与不同柱的地支发生作用，形成跨维度能量传递。

**传导规则**:
1. **生克关系**: 天干五行与地支藏干五行发生生克
2. **距离衰减**: 应用水平传导的距离衰减
3. **藏干加权**: 地支能量按 60/30/10 比例加权

**示例**:
```
年干（木）生月支（午）中的藏干（火）
- 传导效率 = generationEfficiency × spatialDecay.gap1
- 月支（火）能量 += 年干（木）能量 × 0.3 × 0.6
```

---

## 6. 能量流转的全局约束 (Global Constraints)

### 6.1 阻抗 (Impedance) - 资源 → 自身

**物理意义**: 印星（生我）在传递能量时存在阻抗。

**阻抗公式**:
$$ E_{\text{self}}' = E_{\text{self}} + E_{\text{resource}} \times \text{generationEfficiency} \times (1 - K_{\text{imp}}) $$

**阻抗系数**:
$$ K_{\text{imp}} = \begin{cases}
\text{imp_base} & \text{if } E_{\text{self}} \ge \text{threshold} \\
\text{imp_base} + \text{imp_weak} & \text{if } E_{\text{self}} < \text{threshold} \text{ (虚不受补)}
\end{cases} $$

**参数**:
- `flow.resourceImpedance.base`: 基础阻抗（默认 0.3）
- `flow.resourceImpedance.weaknessPenalty`: 身弱时额外阻抗（默认 0.5）

### 6.2 粘滞 (Viscosity) - 自身 → 输出

**物理意义**: 食伤（我生）在输出能量时存在粘滞阻力。

**粘滞公式**:
$$ E_{\text{output}}' = E_{\text{output}} + E_{\text{self}} \times \text{generationEfficiency} \times (1 - K_{\text{vis}}) $$

**粘滞系数**:
$$ K_{\text{vis}} = \min(\text{maxDrainRate}, \text{drainFriction} \times \text{pressure}) $$

**参数**:
- `flow.outputViscosity.maxDrainRate`: 最大泄耗率（默认 0.6）
- `flow.outputViscosity.drainFriction`: 输出阻力（默认 0.2）
- `flow.outputDrainPenalty`: 食伤泄耗惩罚（默认 1.5-4.5）

### 6.3 全局熵增 (Global Entropy)

**物理意义**: 系统整体的能量损耗，模拟不可逆过程。

**熵增公式**:
$$ E_{\text{total}}' = E_{\text{total}} \times (1 - \text{globalEntropy}) $$

**参数**:
- `flow.globalEntropy`: 全局熵增系数（默认 0.05-0.22）

### 6.4 阻尼因子 (Damping Factor)

**物理意义**: 防止能量计算发散，保持系统稳定。

**阻尼公式**:
$$ H^{(t+1)} = \text{dampingFactor} \times A \times H^{(t)} + (1 - \text{dampingFactor}) \times H^{(0)} $$

**参数**:
- `flow.dampingFactor`: 阻尼系数（默认 0.0-0.6）

---

## 7. 通关机制 (Mediation Mechanism)

### 7.1 物理定义

**通关 (Mediation)** 是能量传导中的一种**转化机制**，当存在中间元素（通关神）时，原本的克制关系会被转化或豁免，形成"贪生忘克"的物理现象。

### 7.2 通关原理

**传统命理概念**: "贪生忘克" - 当 A 克 B，但有 C 在中间通关（A 生 C，C 生 B）时，A 对 B 的克制被转化。

**物理模型**: 能量通过中间节点（通关神）进行**路径重定向**，原本的对抗性传导（克）被转化为支持性传导（生）。

### 7.3 通关判定标准

#### 7.3.1 食伤通关 (Output Mediation)

**场景**: 比劫夺财时，如果存在食伤（我生）作为通关神。

**判定条件**:
- 比劫（Rob）攻击财星（Wealth）
- 食伤能量 `raw_e_output > 4.0`（阈值可调）

**效果**:
$$ \text{Penalty}_{\text{effective}} = \text{Penalty}_{\text{raw}} \times 0.2 $$

即：夺财惩罚减少 80%，通关神吸收了大部分对抗能量。

**物理意义**: 食伤作为"泄气通道"，将比劫的攻击能量转化为输出，保护财星。

#### 7.3.2 官杀护财 (Officer Shield)

**场景**: 比劫夺财时，如果存在官杀（克我）作为护财神。

**判定条件**:
- 比劫（Rob）攻击财星（Wealth）
- 官杀能量 `raw_e_guan_sha >= 3.0`（阈值可调）

**效果**:
$$ \text{Penalty}_{\text{effective}} = 0.0 $$

即：完全豁免夺财惩罚，官杀形成"护盾"。

**物理意义**: 官杀作为"控制力"，直接压制比劫，形成能量屏障。

### 7.4 通关参数

**开关参数**:
- `logic_switches.enable_mediation_exemption`: 是否启用通关豁免（默认 `True`）

**阈值参数**（在代码中硬编码，未来可参数化）:
- 食伤通关阈值: `raw_e_output > 4.0`
- 官杀护财阈值: `raw_e_guan_sha >= 3.0`
- 食伤通关折损率: `0.2`（保留 20% 惩罚）

### 7.5 通关优先级

1. **官杀护财** (最高优先级)
   - 如果同时满足官杀护财和食伤通关，优先使用官杀护财（完全豁免）

2. **食伤通关** (次优先级)
   - 如果只满足食伤通关，应用 80% 折损

3. **无通关** (默认)
   - 应用完整的夺财惩罚

### 7.6 实现位置

**代码位置**: `core/quantum_engine.py` (Legacy) 和 `core/engine_v88.py` (Current)

**应用场景**: 主要在"比劫夺财"计算中应用，未来可扩展到其他克制关系的转化。

---

## 8. 传导优先级 (Conduction Priority)

### 7.1 优先级规则

能量传导遵循以下优先级（从高到低）：

1. **同柱内传导** (最高优先级)
   - 自坐通根
   - 同柱透干
   - 同柱天干地支生克

2. **合局锁定** (高优先级)
   - 参与合局（三合/六合/天干五合）的粒子被锁定
   - 锁定的粒子豁免冲的伤害
   - 但需支付 `resolutionCost` 能量税

3. **相邻柱传导** (中优先级)
   - 年↔月、月↔日、日↔时
   - 应用 `spatialDecay.gap1` 衰减

4. **跨柱传导** (低优先级)
   - 年↔日、年↔时、月↔时
   - 应用 `spatialDecay.gap2` 或更高衰减

5. **全局修正** (最后应用)
   - 全局熵增
   - 阻尼因子

---

## 8. 传导效率总结表

| 传导类型 | 效率参数 | 默认值 | 范围 | 说明 |
|---------|---------|--------|------|------|
| **生 (Generation)** | `generationEfficiency` | 0.2-0.4 | 0.1-0.5 | 母向子传递效率 |
| **克 (Control)** | `controlImpact` | 0.7-1.25 | 0.1-1.5 | 控制打击力 |
| **合化 (Combination)** | `bonus` | 2.5 | 1.2-5.0 | 合化成功倍率 |
| **合绊 (Binding)** | `penalty` | 0.4 | 0.1-0.8 | 合绊折损 |
| **冲 (Clash)** | `clashDamping` | 0.2-0.8 | 0.1-1.0 | 冲的折损系数 |
| **六合 (Six Harmony)** | `sixHarmony` | 5.0-15.0 | 0.0-30.0 | 六合加成 |
| **三合 (Three Harmony)** | `trineBonus` | 1.2-2.5 | 0.5-5.0 | 三合倍率 |
| **通根 (Rooting)** | `rootingWeight` | 4.8 | 3.0-30.0 | 通根系数 |
| **透干 (Projection)** | `exposedBoost` | 1.5 | 1.0-3.0 | 透干爆发系数 |
| **距离衰减 (Gap 1)** | `spatialDecay.gap1` | 0.6 | 0.1-1.0 | 相邻柱衰减 |
| **距离衰减 (Gap 2)** | `spatialDecay.gap2` | 0.3 | 0.1-1.0 | 隔一柱衰减 |
| **阻抗 (Impedance)** | `resourceImpedance.base` | 0.3 | 0.0-0.9 | 基础阻抗 |
| **粘滞 (Viscosity)** | `maxDrainRate` | 0.6 | 0.1-1.0 | 最大泄耗率 |
| **熵增 (Entropy)** | `globalEntropy` | 0.05-0.22 | 0.0-0.5 | 全局熵增 |
| **阻尼 (Damping)** | `dampingFactor` | 0.0-0.6 | 0.0-1.0 | 阻尼系数 |
| **通关开关** | `enable_mediation` | True | True/False | 是否启用通关豁免 |

---

## 9. 能量结算示例 (Energy Settlement Example)

### 9.1 案例：月干生、时干克的抵消计算

**八字案例**:
```
年柱: 甲子 (木-水)
月柱: 丙寅 (火-木)  ← 月干（火）生日主（土）
日柱: 戊午 (土-火)  ← 日主（土）
时柱: 甲子 (木-水)  ← 时干（木）克日主（土）
```

**假设参数**:
- `pillarWeights`: Year 0.8, Month 1.2, Day 1.0, Hour 0.9
- `generationEfficiency`: 0.3
- `controlImpact`: 0.7
- `spatialDecay.gap1`: 0.6 (月→日)
- `spatialDecay.gap2`: 0.3 (时→日，隔一柱)

#### 步骤 1: 计算月干生身的能量输入

**月干（丙火）生日主（戊土）**:
- 月干基础能量: `E_month_base = 10.0` (假设值)
- 月令权重: `pillarWeights['month'] = 1.2`
- 距离衰减: `spatialDecay.gap1 = 0.6` (月→日，相邻柱)
- 生的传递效率: `generationEfficiency = 0.3`

**传导公式**:
$$ E_{\text{month→day}} = E_{\text{month_base}} \times W_{\text{month}} \times K_{\text{distance}} \times \eta_{\text{gen}} $$

**计算**:
$$ E_{\text{month→day}} = 10.0 \times 1.2 \times 0.6 \times 0.3 = 2.16 $$

**结果**: 月干向日主输入 **+2.16** 的正向能量。

#### 步骤 2: 计算时干克身的能量抵消

**时干（甲木）克日主（戊土）**:
- 时干基础能量: `E_hour_base = 8.0` (假设值)
- 时柱权重: `pillarWeights['hour'] = 0.9`
- 距离衰减: `spatialDecay.gap2 = 0.3` (时→日，隔一柱)
- 克的打击力: `controlImpact = 0.7`

**传导公式**:
$$ E_{\text{hour→day}} = -E_{\text{hour_base}} \times W_{\text{hour}} \times K_{\text{distance}} \times \eta_{\text{control}} $$

**计算**:
$$ E_{\text{hour→day}} = -8.0 \times 0.9 \times 0.3 \times 0.7 = -1.512 $$

**结果**: 时干向日主施加 **-1.512** 的负向压力。

#### 步骤 3: 矢量叠加（净能量计算）

**矢量叠加公式**:
$$ E_{\text{net}} = E_{\text{month→day}} + E_{\text{hour→day}} + E_{\text{day_base}} $$

**假设日主基础能量**: `E_day_base = 5.0`

**计算**:
$$ E_{\text{net}} = 2.16 + (-1.512) + 5.0 = 5.648 $$

**结果**: 日主最终净能量为 **5.648**，相比基础能量（5.0）增加了 **+0.648**。

#### 步骤 4: 结论分析

- **月干生身的力量** (2.16) > **时干克身的力量** (1.512)
- **净效果**: 日主能量增加，表现为**身强**
- **关键因素**: 
  - 月令权重（1.2）远大于时柱权重（0.9）
  - 月→日距离近（gap1=0.6），时→日距离远（gap2=0.3）

---

### 9.2 案例：年、月、时合力生身的计算

**八字案例**:
```
年柱: 甲子 (木-水)  ← 年干（木）生日主（火）
月柱: 丙寅 (火-木)  ← 月干（火）= 日主（火），同元素共振
日柱: 丙午 (火-火)  ← 日主（火）
时柱: 甲子 (木-水)  ← 时干（木）生日主（火）
```

**假设参数**:
- `pillarWeights`: Year 0.8, Month 1.2, Day 1.0, Hour 0.9
- `generationEfficiency`: 0.3
- `spatialDecay.gap1`: 0.6
- `spatialDecay.gap2`: 0.3
- `Coherence_Boost_Factor`: 0.15 (合力共振系数)

#### 步骤 1: 计算各柱对日主的能量输入

**年干（甲木）生日主（丙火）**:
$$ E_{\text{year→day}} = 10.0 \times 0.8 \times 0.3 \times 0.3 = 0.72 $$

**月干（丙火）与日主（丙火）同元素共振**:
$$ E_{\text{month→day}} = 12.0 \times 1.2 \times 0.6 \times 1.0 = 8.64 $$
(同元素共振，效率 = 1.0)

**时干（甲木）生日主（丙火）**:
$$ E_{\text{hour→day}} = 8.0 \times 0.9 \times 0.3 \times 0.3 = 0.648 $$

#### 步骤 2: 检测合力共振

**统计生日主的天干数量**: `N_support = 2` (年干、时干)

**合力共振公式**:
$$ E_{\text{coherence}} = E_{\text{base}} \times (1 + (N - 1) \times \text{Coherence_Boost}) $$

**计算**:
$$ E_{\text{coherence_boost}} = (0.72 + 0.648) \times (1 + (2 - 1) \times 0.15) = 1.368 \times 1.15 = 1.573 $$

#### 步骤 3: 总能量叠加

**假设日主基础能量**: `E_day_base = 5.0`

**总能量**:
$$ E_{\text{total}} = E_{\text{day_base}} + E_{\text{month→day}} + E_{\text{coherence_boost}} $$

$$ E_{\text{total}} = 5.0 + 8.64 + 1.573 = 15.213 $$

**结果**: 日主最终能量为 **15.213**，相比基础能量（5.0）增加了 **+10.213**（204% 增幅）。

**关键因素**:
- 月干与日主同元素，形成强共振（8.64）
- 年、时合力生身，触发合力共振加成（+15%）
- 月令权重（1.2）放大了月干的贡献

---

### 9.3 案例：通关机制的转化计算

**八字案例**:
```
年柱: 甲子 (木-水)
月柱: 丙寅 (火-木)
日柱: 戊午 (土-火)  ← 日主（土）
时柱: 庚申 (金-金)  ← 时干（金）克日主（土）
```

**特殊条件**: 月干（丙火）生日主（戊土），且日主生时干（庚金），形成"火生土生金"的顺生链。

**假设参数**:
- `enable_mediation = True`
- `raw_e_output = 5.0` (食伤能量，满足通关阈值 4.0)
- 比劫夺财惩罚: `Penalty_raw = 10.0`

#### 步骤 1: 检测通关条件

**场景**: 比劫（Rob）攻击财星（Wealth）

**通关检测**:
- 食伤能量 `raw_e_output = 5.0 > 4.0` ✅ 满足阈值
- 触发**食伤通关**

#### 步骤 2: 应用通关折损

**通关公式**:
$$ \text{Penalty}_{\text{effective}} = \text{Penalty}_{\text{raw}} \times 0.2 $$

**计算**:
$$ \text{Penalty}_{\text{effective}} = 10.0 \times 0.2 = 2.0 $$

**结果**: 夺财惩罚从 **10.0** 减少到 **2.0**（减少 80%）。

**物理意义**: 食伤作为"泄气通道"，将比劫的攻击能量转化为输出，保护财星。

---

### 9.4 能量结算流程图

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: 基础能量计算 (PhysicsProcessor)                  │
│ - 天干基础能量                                            │
│ - 地支藏干能量（60/30/10）                                │
│ - 月令权重修正                                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: 垂直传导 (Vertical Conduction)                   │
│ - 通根加成 (Rooting)                                      │
│ - 透干爆发 (Projection)                                   │
│ - 自坐强根 (Same Pillar Bonus)                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: 水平传导 (Horizontal Conduction)                │
│ - 生 (Generation): +Energy × efficiency × distance       │
│ - 克 (Control): -Energy × impact × distance              │
│ - 合 (Combination): 聚合或羁绊                            │
│ - 冲 (Clash): 湮灭或释放                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: 能量流耦合效应 (Energy Flow Coupling)            │
│ - 顺生链放大 (Sequential Amplification)                  │
│ - 合力共振 (Coherent Resonance)                          │
│ - 多重抵消 (Multi-Force Cancellation)                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: 全局约束 (Global Constraints)                    │
│ - 阻抗 (Impedance): 资源→自身                             │
│ - 粘滞 (Viscosity): 自身→输出                              │
│ - 熵增 (Entropy): 全局损耗                                │
│ - 阻尼 (Damping): 防止发散                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 6: 通关机制 (Mediation)                              │
│ - 食伤通关 (Output Mediation)                            │
│ - 官杀护财 (Officer Shield)                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 7: 矢量叠加 (Vector Summation)                      │
│ E_final = Σ(E_vertical + E_horizontal + E_coupling)      │
│         - E_impedance - E_viscosity - E_entropy          │
│         + E_mediation                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
                   最终能量值
```

---

## 10. 实现位置

### 11.1 代码实现

能量传导机制在以下模块中实现：

1. **`core/engines/flow_engine.py`** (FlowEngine)
   - 实现阻抗、粘滞、熵增、阻尼
   - 模拟能量流转的动态过程

2. **`core/engine_graph.py`** (GraphNetworkEngine)
   - 实现邻接矩阵构建
   - 实现能量传播迭代

3. **`core/processors/physics.py`** (PhysicsProcessor)
   - 实现基础能量计算
   - 应用能量流耦合效应（V21.0）

4. **`core/engines/harmony_engine.py`** (HarmonyEngine)
   - 实现合局检测
   - 实现贪合忘冲逻辑

---

## 10. 与核心总纲的对应关系

| 核心总纲条目 | 本补充文档章节 | 实现状态 |
|------------|--------------|---------|
| 第 4 条：垂直作用与透干 | 第 2 章：垂直传导 | ✅ 已实现 |
| 第 7 条：流体力学模拟 | 第 3 章：水平传导 | ✅ 已实现 |
| 第 8 条：空间衰减 | 第 4 章：距离衰减 | ✅ 已实现 |
| 第 6 条：横向聚合与聚变 | 第 3.1.3、3.2.2、3.2.3 节 | ✅ 已实现 |
| **通关机制** | 第 7 章：通关机制 | ✅ 已实现（代码中） |
| **能量结算示例** | 第 9 章：能量结算示例 | ✅ 已文档化 |

---

**批准人**: Architect & Antigravity
**执行代码库**: V7.3 Auto-Tuning Architecture + V21.0 Energy Flow Coupling

