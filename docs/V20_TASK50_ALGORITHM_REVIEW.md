# V20.0 任务 50：第一层算法与参数全面审查报告

## 1. 第二层参数冻结确认 ✅

### 1.1 ObservationBiasFactor (观测者效应)
```json
{
  "Wealth": 2.7,
  "CareerBiasFactor_LowE": 2.0,
  "CareerBiasFactor_HighE": 0.95,
  "Relationship": 3.0,
  "CaseSpecificBias": {
    "C02": 2.682,  // V18.0 最终稳定值
    "C07": 1.338   // V18.0 最终稳定值
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
    "C03": 1.464,  // V18.0 最终稳定值
    "C04": 3.099,  // V18.0 最终稳定值
    "C06": 0.786,  // V18.0 最终稳定值
    "C08": 0.900   // V18.0 最终稳定值
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

## 2. 第一层算法总纲：十神波函数计算

### 2.1 核心算法流程

#### 阶段一：天干地支 → 五行能量 (PhysicsProcessor)

**步骤 1：天干能量计算**
```
对于每个天干（除日主外）：
  元素 = STEM_ELEMENTS[天干字符]
  基础得分 = BASE_SCORE (10.0) × 宫位权重
  五行能量[元素] += 基础得分
```

**步骤 2：地支藏干能量计算**
```
对于每个地支：
  藏干列表 = GENESIS_HIDDEN_MAP[地支字符]
  对于每个藏干 (字符, 权重)：
    元素 = STEM_ELEMENTS[藏干字符]
    得分 = 宫位权重 × 藏干权重 (10/7/3)
    五行能量[元素] += 得分
```

**步骤 3：通根加成 (Rooting Bonus)**
```
对于每个天干（除日主外）：
  如果该天干在地支藏干中出现：
    通根加成 = 基础得分 × (ROOT_BONUS - 1.0)  // ROOT_BONUS = 1.2
    五行能量[元素] += 通根加成
```

**输出：** `raw_energy = {wood: X, fire: Y, earth: Z, metal: W, water: V}`

#### 阶段二：五行能量 → 十神能量 (DomainProcessor._calculate_ten_gods)

**步骤 1：确定日主在五行循环中的位置**
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

**步骤 2：提取基础能量**
```
self_energy = raw_energy[elements[self_idx]]
output_energy = raw_energy[elements[output_idx]]
wealth_energy = raw_energy[elements[wealth_idx]]
officer_energy = raw_energy[elements[officer_idx]]
resource_energy = raw_energy[elements[resource_idx]]
```

**步骤 3：应用粒子权重 (Particle Weights)**
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

### 2.2 生克合化关系映射

**生克循环定义：**
```python
# 相生循环 (Generation Cycle)
GENERATION = {
  'wood': 'fire',   # 木生火
  'fire': 'earth',  # 火生土
  'earth': 'metal', # 土生金
  'metal': 'water', # 金生水
  'water': 'wood'   # 水生木
}

# 相克循环 (Control Cycle)
CONTROL = {
  'wood': 'earth',  # 木克土
  'earth': 'water', # 土克水
  'water': 'fire',  # 水克火
  'fire': 'metal',  # 火克金
  'metal': 'wood'   # 金克木
}
```

**十神关系映射：**
- **Resource (印)** = 生我 = GENERATION 关系
- **Officer (官杀)** = 克我 = CONTROL 关系（反向）
- **Output (食伤)** = 我生 = GENERATION 关系（正向）
- **Wealth (财)** = 我克 = CONTROL 关系（正向）
- **Self (比劫)** = 同我 = 相同元素

### 2.3 当前算法与 InteractionFactors 的一致性分析

**问题：** 当前算法（V19.0稳定版）**未应用** InteractionFactors。

**当前状态：**
- `InteractionFactors` 在 `config/parameters.json` 中已定义
- 但在 `_calculate_ten_gods()` 中**未使用**
- 算法只应用了 `particle_weights`

**理论一致性：**
如果应用 InteractionFactors，应该在步骤 2 和步骤 3 之间插入：
```python
# 应用交互系数（当前未实现）
resource_energy = resource_energy * Support_Factor      # 生我
officer_energy = officer_energy * Control_Factor        # 克我
output_energy = output_energy * Exhaust_Factor          # 我生
wealth_energy = wealth_energy * Consume_Factor           # 我克
```

---

## 3. 系统性偏差诊断

### 3.1 当前配置状态

**第一层参数（待调优）：**
```json
{
  "InteractionFactors": {
    "Support_Factor": 1.20,    // 未应用
    "Control_Factor": 1.10,    // 未应用
    "Combine_Factor": 0.80,    // 未应用
    "Exhaust_Factor": 0.70,    // 未应用
    "Consume_Factor": 0.90     // 未应用
  },
  "particleWeights": {
    "PianCai": 1.3,
    "ZhengCai": 1.3,
    "ShiShen": 1.4,
    "ShangGuan": 1.2,
    "QiSha": 1.15,
    "BiJian": 1.5,
    "JieCai": 1.1,
    "ZhengYin": 0.9,
    "PianYin": 1.1,
    "ZhengGuan": 0.85
  }
}
```

### 3.2 批量校准结果（当前算法，未应用 InteractionFactors）

**成功率：75% (6/8)**

**重点关注案例：**
- **C02 (事业)**: 模型=98.0, GT=95.0, MAE=3.0 ✅ PASS
- **C07 (事业)**: 模型=70.7, GT=80.0, MAE=9.3 ❌ FAIL

**诊断：**
- C02 事业相已通过（MAE=3.0）
- C07 事业相存在系统性偏差（MAE=9.3，模型偏低）

---

## 4. 结论与建议

### 4.1 算法状态
- ✅ 第二层参数已冻结（V18.0稳定配置）
- ✅ 第一层算法逻辑清晰（五行→十神映射）
- ⚠️ InteractionFactors 已定义但未应用

### 4.2 下一步行动
1. **决策点：** 是否启用 InteractionFactors 应用逻辑？
2. **如果启用：** 需要修改 `_calculate_ten_gods()` 方法
3. **调优策略：** 逐步调整 InteractionFactors 和 particleWeights，观察 C02/C07 事业相 MAE 变化

---

**报告生成时间：** V20.0 Task 50
**审查状态：** ✅ 完成

