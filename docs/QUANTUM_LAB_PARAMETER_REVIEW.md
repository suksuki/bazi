# 量子验证页面参数归类与清理报告

## 📋 参数归类分析

### Phase 1: 初始能量场参数

**位置**: `🌍 Phase 1: 初始能量场 (Initial Energy Field)`

#### 1. 宫位引力 (Pillar Gravity)
- `pillarWeights.year` (年柱)
- `pillarWeights.month` (月令) ⭐
- `pillarWeights.day` (日主)
- `pillarWeights.hour` (时柱)

#### 2. 五态相对论 (Five States Relativity)
- `seasonWeights.wang` (旺)
- `seasonWeights.xiang` (相)
- `seasonWeights.xiu` (休)
- `seasonWeights.qiu` (囚)
- `seasonWeights.si` (死)

#### 3. Phase 1 其他参数
- `physics.self_punishment_damping` (自刑惩罚)

#### 4. 粒子动态 (Structure) - Phase 1 相关
- `structure.rootingWeight` (通根系数)
- `structure.exposedBoost` (透干加成)
- `structure.samePillarBonus` (自坐强根)
- `structure.voidPenalty` (黑洞/空亡)

#### 5. 旺衰概率场 (Strength Probability Field) - Phase 1 相关
- `strength.energy_threshold_center` (能量阈值中心点)
- `strength.phase_transition_width` (相变宽度)
- `strength.follower_threshold` (从格判定阈值)
- `strength.weak_score_threshold` (弱判定分数阈值)
- `strength.strong_score_threshold` (强判定分数阈值)
- `strength.strong_probability_threshold` (强判定概率阈值)
- `gat.use_gat` (启用 GAT 动态注意力)
- `gat.attention_dropout` (噪声过滤)

---

### Phase 2: 动态生克场参数

**位置**: `⚡ Phase 2: 动态生克场 (Dynamic Interaction Field)`

#### 1. 流体力学参数 (Fluid Dynamics)
- `flow.generationEfficiency` (生的效率)
- `flow.generationDrain` (泄的程度)
- `flow.controlImpact` (克的破坏力)
- `flow.dampingFactor` (系统阻尼/熵增)

#### 2. 空间场参数 (Spatial Field)
- `flow.spatialDecay.gap0` (同柱)
- `flow.spatialDecay.gap1` (相邻)
- `flow.spatialDecay.gap2` (隔一柱)
- `flow.spatialDecay.gap3` (隔两柱)

#### 3. 量子纠缠参数 (Quantum Interactions)
- `interactions.stemFiveCombination.threshold` (合化阈值)
- `interactions.stemFiveCombination.bonus` (合化增益)
- `interactions.stemFiveCombination.penalty` (合化失败惩罚)
- `interactions.branchEvents.clashDamping` (冲的折损)

#### 4. 合局参数 (Harmony Parameters)
- `interactions.branchEvents.threeHarmony.bonus` (三合增益)
- `interactions.branchEvents.halfHarmony.bonus` (半合增益)
- `interactions.branchEvents.archHarmony.bonus` (拱合增益)
- `interactions.branchEvents.sixHarmony.bonus` (六合增益)
- `interactions.branchEvents.sixHarmony.bindingPenalty` (六合羁绊惩罚)

---

## 🔍 重复参数分析

### 重复参数列表

#### 1. 三合/半合/拱合增益参数重复

**重复位置 1**: `⚗️ 几何交互 (Interactions)` 面板
- `comboPhysics.trineBonus` (三合)
- `comboPhysics.halfBonus` (半合)
- `comboPhysics.archBonus` (拱合)

**重复位置 2**: `⚡ Phase 2: 动态生克场` 面板
- `branchEvents.threeHarmony.bonus` (三合增益)
- `branchEvents.halfHarmony.bonus` (半合增益)
- `branchEvents.archHarmony.bonus` (拱合增益)

**实际使用情况**:
- ✅ Phase 2 传播代码 (`phase3_propagation.py`) 使用 `branchEvents.threeHarmony.bonus` 等
- ❌ `comboPhysics` 仅在旧的 `harmony_engine.py` 中使用，新引擎不再使用

**清理建议**: 
- 删除 `⚗️ 几何交互` 面板中的 `comboPhysics.trineBonus`, `comboPhysics.halfBonus`, `comboPhysics.archBonus`
- 保留 `comboPhysics.directionalBonus` (三会) 和 `comboPhysics.resolutionCost` (解冲消耗)，因为 Phase 2 中没有这些参数

#### 2. 天干五合参数重复

**重复位置 1**: `⚗️ 几何交互 (Interactions)` 面板
- 已删除（注释说明已移至 Phase 2）

**重复位置 2**: `⚡ Phase 2: 动态生克场` 面板
- `interactions.stemFiveCombination.threshold`
- `interactions.stemFiveCombination.bonus`
- `interactions.stemFiveCombination.penalty`

**状态**: ✅ 已清理（注释说明已移至 Phase 2）

#### 3. 冲的折损参数重复

**重复位置 1**: `⚗️ 几何交互 (Interactions)` 面板
- 已删除（注释说明已移至 Phase 2）

**重复位置 2**: `⚡ Phase 2: 动态生克场` 面板
- `interactions.branchEvents.clashDamping`

**状态**: ✅ 已清理（注释说明已移至 Phase 2）

#### 4. controlImpact 和 spatialDecay 参数重复

**重复位置 1**: `🌊 能量流转 (Flow / Damping)` 面板
- 已删除（注释说明已移至 Phase 2）

**重复位置 2**: `⚡ Phase 2: 动态生克场` 面板
- `flow.controlImpact`
- `flow.spatialDecay` (gap0, gap1, gap2, gap3)

**状态**: ✅ 已清理（注释说明已移至 Phase 2）

---

## 🧹 清理方案

### 需要删除的参数

#### 1. `⚗️ 几何交互 (Interactions)` 面板

**删除以下参数**:
- ❌ `comboPhysics.trineBonus` (三合) - 与 Phase 2 的 `branchEvents.threeHarmony.bonus` 重复
- ❌ `comboPhysics.halfBonus` (半合) - 与 Phase 2 的 `branchEvents.halfHarmony.bonus` 重复
- ❌ `comboPhysics.archBonus` (拱合) - 与 Phase 2 的 `branchEvents.archHarmony.bonus` 重复

**保留以下参数**:
- ✅ `comboPhysics.directionalBonus` (三会) - Phase 2 中没有对应参数
- ✅ `comboPhysics.resolutionCost` (解冲消耗) - Phase 2 中没有对应参数
- ✅ `stemFiveCombination.jealousyDamping` (争合损耗) - Phase 2 中没有对应参数

**修改建议**:
```python
# 删除三合/半合/拱合的输入框
# 保留三会和解冲消耗
st.caption("地支成局 (Branch Combo)")
cp = fp['interactions'].get('comboPhysics', {'directionalBonus': 3.0, 'resolutionCost': 0.1})

dir_bonus_val = cp.get('directionalBonus', 3.0)
resolution_cost_val = cp.get('resolutionCost', 0.1)

c1, c2 = st.columns(2)
with c1:
    cp_db = st.number_input("三会(Dir)", 0.5, 6.0, dir_bonus_val, 0.1, key='cp_db')
with c2:
    cp_rc = st.number_input("解冲消耗", 0.0, 1.0, resolution_cost_val, 0.05, key='cp_rc')

# 添加提示信息
st.info("💡 **三合/半合/拱合** 参数已移至 **Phase 2: 动态生克场**，请使用 Phase 2 参数调优面板")
```

---

## 📊 参数归类总结

### Phase 1 参数 (初始能量场)
- 宫位引力: 4 个参数
- 五态相对论: 5 个参数
- 自刑惩罚: 1 个参数
- 粒子动态: 4 个参数
- 旺衰概率场: 8 个参数
- **总计**: 22 个参数

### Phase 2 参数 (动态生克场)
- 流体力学: 4 个参数
- 空间场: 4 个参数
- 量子纠缠: 4 个参数
- 合局参数: 5 个参数
- **总计**: 17 个参数

### 其他参数 (非 Phase 1/2)
- 能量流转: 5 个参数（resourceImpedance, outputViscosity, globalEntropy, outputDrainPenalty）
- 几何交互: 3 个参数（三会、解冲消耗、争合损耗）
- 粒子权重: 10 个参数（十神粒子权重）
- **总计**: 18 个参数

---

## ✅ 清理检查清单

- [x] 确认 Phase 1 参数归类正确
- [x] 确认 Phase 2 参数归类正确
- [x] 识别重复参数
- [ ] 删除 `comboPhysics.trineBonus` (三合)
- [ ] 删除 `comboPhysics.halfBonus` (半合)
- [ ] 删除 `comboPhysics.archBonus` (拱合)
- [ ] 添加提示信息，引导用户使用 Phase 2 参数面板
- [ ] 测试清理后的参数面板功能

---

## 📝 注意事项

1. **comboPhysics 的保留**: `comboPhysics.directionalBonus` (三会) 和 `comboPhysics.resolutionCost` (解冲消耗) 需要保留，因为 Phase 2 中没有这些参数。

2. **向后兼容**: 如果 `comboPhysics` 在旧代码中仍被使用，需要确保清理不会破坏现有功能。

3. **用户引导**: 在删除重复参数时，应该添加清晰的提示信息，引导用户使用 Phase 2 参数面板。

4. **配置同步**: 确保清理后的参数面板与配置文件 (`config/parameters.json`) 保持一致。

