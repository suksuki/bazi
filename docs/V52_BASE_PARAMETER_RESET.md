# V52.0 基础物理常数重置方案 (Base Parameter Hard-Reset)

## 概述

V52.0 版本对最底层的**基础物理常数（Base Parameters）**进行了硬重置，将这些"地基"参数从旧版本的"温室环境"值锚定到基于黄金比例的计算值，旨在打破"泄耗不足"和"克制无力"的僵局。

**执行日期**: 2025-01-16

---

## 更新参数列表

### 1. 🏗️ 结构层 (Structure) - 强化根气

#### `structure.rootingWeight` (通根系数)
- **旧值**: `4.1975` (或更早的 `0.5 ~ 2.0`)
- **新值**: **`4.25`** ✅
- **物理理由**: 之前的通根系数太低，导致地支对天干的支撑力不足。提升到 π + 1.1 的近似值，确保身旺者有足够的"质量"去抗衡强克。
- **对应文档**: `ALGORITHM_CONSTITUTION_v2.5.md` 第4条

---

### 2. 🌊 能量流转层 (Flow) - 疏通泄耗，增强克制

#### `flow.controlImpact` (克制影响)
- **旧值**: `9.7` (正数，甚至可能是"生")
- **新值**: **`-2.618`** ✅ (黄金比例平方的负值)
- **物理理由**: 必须是负值！且必须足够大。这是为了让"七杀"产生真实的破坏力，从而将虚胖的"中和"八字压回原形。
- **对应文档**: `ALGORITHM_CONSTITUTION_v2.5.md` 第7条

#### `flow.outputDrainPenalty` (泄耗速度)
- **旧值**: `1.0` (或更早的 `0.6`)
- **新值**: **`2.80`** ✅
- **物理理由**: 之前的泄气速度像是在滴水。对于"食伤泄秀"的格局，我们需要它像"泄洪"一样（2.8），快速带走日主的能量，解决 Balanced 误判为 Strong 的问题。
- **对应文档**: `QUANTUM_LAB_SIDEBAR_PARAMETERS_REPORT.md` 5.4

#### `flow.generationEfficiency` (生成效率)
- **旧值**: `0.15` (或更早的 `0.6` 或更高)
- **新值**: **`0.25`** ✅
- **物理理由**: "生多必滞"。降低生的传导率，防止能量在网络中无限增殖（通胀）。
- **对应文档**: `ALGORITHM_CONSTITUTION_v2.5.md` 第7条

#### `flow.dampingFactor` (阻尼因子)
- **旧值**: `0.25`
- **新值**: **`0.33`** ✅
- **物理理由**: 与黄金比例相关，保持能量传导的平衡。

#### `flow.outputViscosity.drainFriction` (泄耗摩擦)
- **旧值**: `0.3`
- **新值**: **`0.2`** ✅
- **物理理由**: 降低摩擦，允许更顺畅的能量泄耗。

#### `flow.globalEntropy` (全局熵)
- **旧值**: `0.06`
- **新值**: **`0.1`** ✅
- **物理理由**: 增加系统的不确定性，避免过度确定性导致的误判。

---

### 3. 🌍 基础场域层 (Physics) - 调整时空权重

#### `physics.pillarWeights` (宫位权重)
- **旧值**:
  - Year: `0.65`
  - Month: `1.8`
  - Day: `1.15`
  - Hour: `0.5`
- **新值**: ✅
  - Year: **`0.82`** (背景权重，适度提升)
  - Month: **`1.88`** (月令是提纲，必须拥有接近 2 倍的统治力)
  - Day: **`1.62`** (日主是观测点，权重需提升，黄金分割 1.618)
  - Hour: **`0.95`** (时柱权重提升，作为背景补充)
- **物理理由**: 月令是提纲，必须拥有接近 2 倍的统治力。日主是观测点，权重需提升到黄金分割值。
- **对应文档**: `ALGORITHM_CONSTITUTION_v2.5.md` 第3条

---

## 更新前后对比

| 参数路径 | 旧值 | 新值 | 变化 |
|---------|------|------|------|
| `structure.rootingWeight` | 4.1975 | **4.25** | +0.05 |
| `flow.controlImpact` | 9.7 | **-2.618** | 符号反转 + 绝对值降低 |
| `flow.outputDrainPenalty` | 1.0 | **2.80** | +180% |
| `flow.generationEfficiency` | 0.15 | **0.25** | +67% |
| `flow.dampingFactor` | 0.25 | **0.33** | +32% |
| `flow.outputViscosity.drainFriction` | 0.3 | **0.2** | -33% |
| `flow.globalEntropy` | 0.06 | **0.1** | +67% |
| `physics.pillarWeights.year` | 0.65 | **0.82** | +26% |
| `physics.pillarWeights.month` | 1.8 | **1.88** | +4% |
| `physics.pillarWeights.day` | 1.15 | **1.62** | +41% |
| `physics.pillarWeights.hour` | 0.5 | **0.95** | +90% |

---

## 预期效果

### 1. 解决"泄耗不足"问题
- **`outputDrainPenalty` 提升到 2.80**: 快速带走日主能量，避免 Balanced 误判为 Strong
- **`drainFriction` 降低到 0.2**: 减少泄耗阻力，允许更顺畅的能量流动

### 2. 解决"克制无力"问题
- **`controlImpact` 改为 -2.618**: 确保克制力是负值且足够大，让"七杀"产生真实破坏力
- **`rootingWeight` 提升到 4.25**: 增强地支对天干的支撑力，让身旺者有足够"质量"抗衡强克

### 3. 防止能量通胀
- **`generationEfficiency` 降低到 0.25**: 防止能量在网络中无限增殖
- **`globalEntropy` 提升到 0.1**: 增加系统不确定性，避免过度确定性

### 4. 强化时空权重
- **月令权重 1.88**: 接近 2 倍的统治力，确保月令的提纲作用
- **日主权重 1.62**: 黄金分割值，提升观测点的权重

---

## 验证步骤

1. **运行批量验证**:
   ```bash
   python3 scripts/batch_verify.py
   ```

2. **检查准确率变化**:
   - 特别关注 "Balanced" 案例的准确率
   - 检查 "Strong" 和 "Weak" 的误判情况

3. **对比更新前后**:
   - 记录更新前的准确率基准
   - 对比更新后的准确率变化

---

## 相关文档

- `docs/ALGORITHM_CONSTITUTION_v2.5.md` - 核心算法总纲
- `docs/QUANTUM_LAB_SIDEBAR_PARAMETERS_REPORT.md` - 参数统计报告
- `docs/V51_GOLDEN_RATIO_RESET.md` - V51.0 黄金比例重置
- `docs/V52_MEDIATION_AND_LIFE_STAGES.md` - V52.0 通关导管与十二长生

---

## 版本信息

- **版本**: V52.0
- **日期**: 2025-01-16
- **作者**: Antigravity Team
- **类型**: 基础参数硬重置 (Base Parameter Hard-Reset)

