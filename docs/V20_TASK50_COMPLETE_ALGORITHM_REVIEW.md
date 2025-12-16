# V20.0 任务 50：第一层算法完整审查报告（详细版）

## 1. 第二层参数冻结确认 ✅

### 1.1 ObservationBiasFactor (观测者效应)
```json
{
  "Wealth": 2.7,
  "CareerBiasFactor_LowE": 2.0,
  "CareerBiasFactor_HighE": 0.95,
  "Relationship": 3.0,
  "CaseSpecificBias": {
    "C02": 2.682,
    "C07": 1.338
  }
}
```
**状态：✅ 已冻结，不参与本轮调优**

### 1.2 SpacetimeCorrector (时空修正器)
```json
{
  "CorrectorBaseFactor": 1.0,
  "LuckPillarWeight": 0.6,
  "AnnualPillarWeight": 0.4,
  "Enabled": true,
  "ExclusionList": ["C01", "C02", "C07"],
  "CaseSpecificCorrectorFactor": {
    "C03": 1.464,
    "C04": 3.099,
    "C06": 0.786,
    "C08": 0.900
  }
}
```
**状态：✅ 已冻结，不参与本轮调优**

### 1.3 Amplifiers (放大器)
```json
{
  "WealthAmplifier": 1.2,
  "CareerAmplifier": 1.2,
  "RelationshipAmplifier": 1.0
}
```
**状态：✅ 已冻结，不参与本轮调优**

---

## 2. 第一层算法完整总纲：十神波函数计算

### 2.1 阶段一：天干地支 → 五行能量 (PhysicsProcessor)

#### 步骤 1：天干能量计算
```
对于每个天干（除日主外）：
  元素 = STEM_ELEMENTS[天干字符]
  基础得分 = BASE_SCORE (10.0) × 宫位权重
  五行能量[元素] += 基础得分
```

#### 步骤 2：地支藏干能量计算
```
对于每个地支：
  藏干列表 = GENESIS_HIDDEN_MAP[地支字符]
  对于每个藏干 (字符, 权重)：
    元素 = STEM_ELEMENTS[藏干字符]
    得分 = 宫位权重 × 藏干权重 (10/7/3)
    五行能量[元素] += 得分
```

#### 步骤 3：通根加成 (Rooting Bonus)
```
对于每个天干（除日主外）：
  如果该天干在地支藏干中出现：
    通根加成 = 基础得分 × (ROOT_BONUS - 1.0)  // ROOT_BONUS = 1.2
    五行能量[元素] += 通根加成
```

#### 步骤 4：时代修正 (Era Multipliers) - 可选
```
如果提供了 era_multipliers：
  对于每个元素：
    五行能量[元素] *= era_multiplier[元素]
```

**输出：** `raw_energy = {wood: X, fire: Y, earth: Z, metal: W, water: V}`

### 2.2 阶段二：五行能量 → 十神能量 (DomainProcessor._calculate_ten_gods)

#### 步骤 1：确定日主在五行循环中的位置
```
elements = ['wood', 'fire', 'earth', 'metal', 'water']
dm_idx = elements.index(dm_element)

// 根据生克循环确定相对位置：
self_idx = dm_idx           // 同我（比肩/劫财）
output_idx = (dm_idx + 1) % 5   // 我生（食神/伤官）
wealth_idx = (dm_idx + 2) % 5   // 我克（正财/偏财）
officer_idx = (dm_idx + 3) % 5  // 克我（正官/七杀）
resource_idx = (dm_idx + 4) % 5 // 生我（正印/偏印）
```

#### 步骤 2：提取基础能量
```
self_energy = raw_energy[elements[self_idx]]
output_energy = raw_energy[elements[output_idx]]
wealth_energy = raw_energy[elements[wealth_idx]]
officer_energy = raw_energy[elements[officer_idx]]
resource_energy = raw_energy[elements[resource_idx]]
```

#### 步骤 3：应用粒子权重 (Particle Weights)
```
// 当前算法（V19.0稳定版）：
self_weight = max(particle_weights['BiJian'], particle_weights['JieCai'])
output_weight = max(particle_weights['ShiShen'], particle_weights['ShangGuan'])
wealth_weight = max(particle_weights['ZhengCai'], particle_weights['PianCai'])
officer_weight = max(particle_weights['ZhengGuan'], particle_weights['QiSha'])
resource_weight = max(particle_weights['ZhengYin'], particle_weights['PianYin'])

// 最终十神能量：
gods = {
  'self': self_energy * self_weight,
  'output': output_energy * output_weight,
  'wealth': wealth_energy * wealth_weight,
  'officer': officer_energy * officer_weight,
  'resource': resource_energy * resource_weight
}
```

---

## 3. 复杂交互逻辑审查

### 3.1 天干五合 (Stem Five Combination)

**定义：**
- 甲己合化土、乙庚合化金、丙辛合化水、丁壬合化木、戊癸合化火

**算法位置：**
- `HarmonyEngine.detect_stem_interactions()` - 检测天干五合
- `QuantumEngine._calculate_energy_v7()` - **Legacy引擎中应用**，修改 raw_energy
- `EngineV88.calculate_energy()` - **当前引擎中未应用**

**当前状态：**
- ⚠️ **在 EngineV88 中未应用**：天干五合检测逻辑存在，但不修改 raw_energy
- ⚠️ **在 PhysicsProcessor 中未应用**：基础能量计算不包含天干五合
- ⚠️ **在 DomainProcessor 中未应用**：十神计算不包含天干五合

**配置参数：**
```json
{
  "stemFiveCombination": {
    "threshold": 0.8,
    "bonus": 2.0,
    "penalty": 0.4,
    "jealousyDamping": 0.3
  }
}
```

### 3.2 地支三合/三会 (Trine Harmony / Directional Assembly)

**定义：**
- 三合局：申子辰（水）、亥卯未（木）、寅午戌（火）、巳酉丑（金）
- 三会局：寅卯辰（木）、巳午未（火）、申酉戌（金）、亥子丑（水）

**算法位置：**
- `HarmonyEngine.detect_interactions()` - 检测三合/三会
- `HarmonyEngine.calculate_harmony_score()` - 计算分数加成
- `EngineV88.calculate_year_context()` - **仅用于流年计算**，不影响基础能量

**当前状态：**
- ⚠️ **仅用于流年计算**：三合/三会不影响基础的 raw_energy 或十神能量
- ⚠️ **不参与 DomainProcessor 计算**：十神波函数计算中未考虑三合/三会

**配置参数：**
```json
{
  "comboPhysics": {
    "trineBonus": 2.5,        // 三合倍率
    "halfBonus": 1.5,         // 半三合倍率
    "archBonus": 1.1,         // 拱合倍率
    "directionalBonus": 3.0,   // 三会倍率
    "resolutionCost": 0.1     // 解冲消耗
  }
}
```

### 3.3 地支六合 (Six Combinations)

**定义：**
- 子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合

**算法位置：**
- `HarmonyEngine.detect_interactions()` - 检测六合
- `HarmonyEngine.calculate_harmony_score()` - 计算分数加成
- `EngineV88.calculate_year_context()` - **仅用于流年计算**

**当前状态：**
- ⚠️ **仅用于流年计算**：六合不影响基础的 raw_energy

### 3.4 地支六冲 (Six Clashes)

**定义：**
- 子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲

**算法位置：**
- `HarmonyEngine.detect_interactions()` - 检测六冲
- `HarmonyEngine.calculate_harmony_score()` - 计算分数惩罚
- `EngineV88.calculate_year_context()` - **仅用于流年计算**

**当前状态：**
- ⚠️ **仅用于流年计算**：六冲不影响基础的 raw_energy
- ⚠️ **不参与 DomainProcessor 计算**：十神波函数计算中未考虑六冲

**配置参数：**
```json
{
  "branchEvents": {
    "clashDamping": 0.3,      // 冲的折损系数
    "clashScore": -5.0        // 冲的惩罚分数
  }
}
```

### 3.5 墓库物理 (Vault Physics)

**定义：**
- 辰（水库）、戌（火库）、丑（金库）、未（木库）
- 库 vs 墓的判定：能量阈值 20.0
- 冲开库：能量爆发（openBonus = 1.5）
- 闭库：能量折损（sealedDamping = 0.4）

**算法位置：**
- `TreasuryEngine.process_treasury_scoring()` - 处理墓库逻辑
- `EngineV88.calculate_year_context()` - **仅用于流年计算**

**当前状态：**
- ⚠️ **仅用于流年计算**：墓库物理不影响基础的 raw_energy
- ⚠️ **不参与 DomainProcessor 计算**：十神波函数计算中未考虑墓库

**配置参数：**
```json
{
  "vaultPhysics": {
    "threshold": 20.0,        // 库vs墓的能量阈值
    "sealedDamping": 0.4,     // 闭库时的能量折损率
    "openBonus": 1.5,         // 冲开后的爆发倍率
    "punishmentOpens": false, // 是否允许刑开库
    "breakPenalty": 0.5       // 冲破墓的惩罚系数
  }
}
```

### 3.6 相刑、相害 (Punishment & Harm)

**定义：**
- 相刑：子刑卯、寅刑巳申、丑刑未戌、辰午酉亥自刑
- 相害：子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害

**算法位置：**
- `core/interactions.py` - 定义了相刑相害的映射
- `EngineV88` - **未找到应用逻辑**

**当前状态：**
- ⚠️ **未应用**：相刑相害逻辑未在基础计算中使用

---

## 4. 关键发现：交互逻辑的应用位置

### 4.1 当前架构分析

**EngineV88 (当前主引擎) 的计算流程：**

1. **PhysicsProcessor** → 计算基础五行能量（raw_energy）
   - ✅ 天干能量
   - ✅ 地支藏干能量
   - ✅ 通根加成
   - ❌ **不包含**：天干五合、三合、六合、六冲、墓库

2. **DomainProcessor** → 计算十神能量
   - ✅ 五行→十神映射
   - ✅ 应用粒子权重
   - ❌ **不包含**：交互系数（InteractionFactors）
   - ❌ **不包含**：相合、相冲、墓库修正

3. **HarmonyEngine / TreasuryEngine** → **仅用于流年计算**
   - ✅ 检测三合、六合、六冲
   - ✅ 检测墓库开启
   - ⚠️ **但不修改** raw_energy 或十神能量
   - ⚠️ **只影响** 流年分数（calculate_year_context）

### 4.2 问题诊断

**核心问题：**
1. **天干五合、三合、六合、六冲、墓库等复杂交互逻辑存在，但未应用于基础能量计算**
2. **这些逻辑只在流年计算中使用，不影响静态的十神波函数**
3. **InteractionFactors 已定义但未应用**

**影响：**
- 基础十神能量计算可能不完整
- 缺少相合、相冲、墓库等对基础能量的修正
- 这可能导致系统性偏差

---

## 5. 系统性偏差诊断

### 5.1 当前批量校准结果（未应用复杂交互）

**成功率：75% (6/8)**

**重点关注案例：**
- **C02 (事业)**: 模型=98.0, GT=95.0, MAE=3.0 ✅ PASS
- **C07 (事业)**: 模型=70.7, GT=80.0, MAE=9.3 ❌ FAIL

**诊断：**
- C02 事业相已通过
- C07 事业相存在系统性偏差（模型偏低约 9.3 分）

### 5.2 可能的原因

1. **缺少天干五合修正**：如果 C07 有天干五合，未应用可能导致能量计算偏差
2. **缺少三合/六合修正**：如果 C07 有三合/六合，未应用可能导致能量增强不足
3. **缺少墓库修正**：如果 C07 有墓库，未应用可能导致能量被低估
4. **缺少 InteractionFactors**：生克合化系数未应用，可能导致关系强度不准确

---

## 6. 算法完整性评估

### 6.1 已实现的算法

✅ **基础物理层（PhysicsProcessor）**
- 天干能量计算
- 地支藏干能量计算
- 通根加成
- 时代修正

✅ **十神映射层（DomainProcessor）**
- 五行→十神映射
- 粒子权重应用

✅ **流年交互层（HarmonyEngine / TreasuryEngine）**
- 三合/六合/六冲检测
- 墓库物理
- 天干五合检测

### 6.2 缺失的算法（在第一层）

❌ **天干五合能量转换**
- 检测逻辑存在，但未修改 raw_energy

❌ **三合/六合能量增强**
- 检测逻辑存在，但未修改 raw_energy

❌ **六冲能量折损**
- 检测逻辑存在，但未修改 raw_energy

❌ **墓库能量修正**
- 检测逻辑存在，但未修改 raw_energy

❌ **InteractionFactors 应用**
- 配置已定义，但未在代码中应用

❌ **相刑相害修正**
- 定义存在，但未应用

---

## 7. 结论与建议

### 7.1 算法状态总结

**当前状态：**
- ✅ 第二层参数已冻结（V18.0稳定配置）
- ✅ 基础五行能量计算完整（PhysicsProcessor）
- ✅ 十神映射逻辑清晰（DomainProcessor）
- ⚠️ **复杂交互逻辑存在但未应用于基础计算**
- ⚠️ **InteractionFactors 已定义但未应用**

### 7.2 关键问题

**问题 1：交互逻辑的应用位置**
- 天干五合、三合、六合、六冲、墓库等逻辑**只在流年计算中使用**
- **未应用于基础的 raw_energy 或十神能量计算**
- 这可能导致基础能量计算不完整

**问题 2：InteractionFactors 未应用**
- Support_Factor、Control_Factor 等已定义
- 但在 `_calculate_ten_gods()` 中未使用
- 十神关系强度可能不准确

### 7.3 下一步行动建议

**选项 A：在第一层应用交互逻辑**
- 在 PhysicsProcessor 中应用天干五合、三合、六合、六冲
- 在 DomainProcessor 中应用 InteractionFactors
- 在 DomainProcessor 中应用墓库修正

**选项 B：保持当前架构**
- 交互逻辑仅用于流年计算
- 只调整 particleWeights 和 InteractionFactors（如果启用）

**Master，请指示：**
1. 是否需要在第一层（基础计算）中应用这些复杂交互逻辑？
2. 如果需要，应该在哪里应用（PhysicsProcessor 还是 DomainProcessor）？
3. 还是保持当前架构，只调整参数？

---

**报告生成时间：** V20.0 Task 50 (Complete Review)
**审查状态：** ✅ 完成（详细版）

