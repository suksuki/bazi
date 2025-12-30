# QGA-HR V2.0 规范与 BAZI_FUNDAMENTAL 兼容性分析

**分析日期**: 2025-12-30  
**规范版本**: QGA-HR V2.0  
**主题**: BAZI_FUNDAMENTAL (八字基础规则主题)

---

## 一、QGA-HR V2.0 规范概述

### 1.1 规范定义

**QGA-HR V2.0** (QGA Holographic Registry V2.0) 是**格局全息注册表标准**，定义在 `docs/QGA_FDS_V1.1_Specification.md` 附录 B 中。

### 1.2 核心要求

QGA-HR V2.0 规范要求每个格局（pattern）必须包含以下模块：

| 模块 | 必需性 | 说明 |
|------|--------|------|
| **semantic_seed** | ✅ 必需 | 语义种子，物理意象描述 |
| **feature_anchors** | ✅ 必需 | 特征锚点（标准质心和奇点质心） |
| **tensor_operator** | ✅ 必需 | 张量算子（五维权重、激活函数） |
| **algorithm_implementation** | ✅ 必需 | 算法实现路径映射 |
| **kinetic_evolution** | ✅ 必需 | 动力学演化规则 |
| **audit_trail** | ✅ 必需 | 审计轨迹（版本历史、FDS拟合） |
| **physics_kernel** | ⚠️ 条件 | 物理内核（V2.1格局需要transfer_matrix） |
| **dynamic_states** | ⚠️ 条件 | 动态状态（V2.1格局需要collapse/crystallization规则） |

### 1.3 五维张量要求

QGA-HR V2.0 规范**强制要求**使用**五维张量投影**（E, O, M, S, R）：

- **E (能级轴)**: 生命总量与抗压底气
- **O (秩序轴)**: 权力、名誉、社会地位
- **M (物质轴)**: 财富、资产、执行转化
- **S (应力轴)**: 健康损耗、结构扭曲、意外
- **R (关联轴)**: 六亲交互、情感、人际网络

**归一化约束**: 所有五维向量必须满足 $\sum_{i=1}^{5} v_i = 1.0$

---

## 二、BAZI_FUNDAMENTAL 模块特性分析

### 2.1 模块类型

BAZI_FUNDAMENTAL 包含的模块类型：

| 模块类型 | 示例 | 是否涉及五维张量 |
|---------|------|----------------|
| **基础物理引擎** | MOD_00_SUBSTRATE, MOD_01_TRIPLE | ❌ 否 |
| **格局识别引擎** | MOD_02_SUPER | ⚠️ 部分（从格/化气） |
| **交互动力学** | MOD_03_TRANSFORM, MOD_04_STABILITY | ❌ 否 |
| **时空场耦合** | MOD_14_TIME_SPACE_INTERFERENCE | ⚠️ 部分（概率波函数） |
| **结构传导** | MOD_15_STRUCTURAL_VIBRATION | ❌ 否 |
| **应期预测** | MOD_16_TEMPORAL_SHUNTING | ❌ 否 |
| **应用模块** | MOD_05_WEALTH, MOD_06_RELATIONSHIP | ⚠️ 部分（有独立维度） |

### 2.2 核心差异

| 维度 | HOLOGRAPHIC_PATTERN | BAZI_FUNDAMENTAL |
|------|---------------------|------------------|
| **目标** | 格局识别与状态判定 | 基础物理规则与引擎 |
| **输出** | 五维张量 (E, O, M, S, R) | 多维指标（不一定是五维） |
| **识别** | 格局匹配（质心相似度） | 物理计算（能量、熵、阻抗等） |
| **状态** | CRYSTALLIZED/COLLAPSED/STABLE | 各种物理状态（稳定/混乱/奇点等） |
| **质心** | 基于Tier A样本的质心 | 不适用（不是格局识别） |

---

## 三、兼容性分析

### 3.1 完全兼容的部分

✅ **可以完全遵守 QGA-HR V2.0 规范的部分**：

1. **semantic_seed** - ✅ 完全兼容
   - BAZI_FUNDAMENTAL 模块都有物理意象描述
   - 可以定义 `physical_image` 和 `classical_meaning`

2. **algorithm_implementation** - ✅ 完全兼容
   - 所有模块都需要映射引擎函数路径
   - 这是100%算法复原的核心要求

3. **kinetic_evolution** - ✅ 完全兼容
   - 所有模块都有触发算子和增益算子
   - 可以定义动态仿真参数

4. **audit_trail** - ✅ 完全兼容
   - 所有模块都需要版本历史和FDS拟合记录

5. **physics_kernel** - ✅ 完全兼容
   - 可以定义核心物理参数和计算公式
   - 不强制要求 `transfer_matrix`（仅V2.1格局需要）

### 3.2 部分兼容的部分

⚠️ **需要适配的部分**：

1. **feature_anchors** - ⚠️ 部分兼容
   - **问题**: BAZI_FUNDAMENTAL 模块不涉及格局识别，不需要质心匹配
   - **解决方案**: 
     - 可以定义"标准稳定态"和"奇点态"的特征向量
     - 但向量维度不一定是五维（E, O, M, S, R）
     - 可以使用模块特定的指标维度（如：PHASE_PROGRESS, ENERGY_DISPERSION_DELTA等）

2. **tensor_operator** - ⚠️ 部分兼容
   - **问题**: 不是所有模块都使用五维张量投影
   - **解决方案**:
     - 对于使用五维张量的模块（如MOD_14时空耦合），完全兼容
     - 对于不使用五维张量的模块，可以定义模块特定的权重和公式
     - `core_equation` 可以不是五维张量公式

3. **dynamic_states** - ⚠️ 部分兼容
   - **问题**: 不是所有模块都有CRYSTALLIZED/COLLAPSED状态
   - **解决方案**:
     - 可以定义模块特定的状态（如：STABLE_DISPERSION, HIGH_ENTROPY等）
     - `collapse_rules` 和 `crystallization_rules` 可以适配为模块特定的相变规则

### 3.3 不兼容的部分

❌ **不适用 QGA-HR V2.0 规范的部分**：

1. **transfer_matrix** - ❌ 不适用
   - **原因**: 只有V2.1格局（如A-03）需要5x5转换矩阵
   - **BAZI_FUNDAMENTAL**: 基础规则模块不需要格局转换矩阵

2. **格局识别** - ❌ 不适用
   - **原因**: QGA-HR V2.0 的核心是格局识别和质心匹配
   - **BAZI_FUNDAMENTAL**: 是基础物理引擎，不涉及格局识别

---

## 四、适配方案

### 4.1 方案A：完全对齐（推荐）

**策略**: 完全遵守 QGA-HR V2.0 规范结构，但允许字段内容适配

**优点**:
- 结构统一，易于维护
- 可以使用相同的 RegistryLoader
- 便于未来扩展

**实现**:
- ✅ 保留所有必需字段
- ⚠️ `feature_anchors.vector` 使用模块特定维度（不强制五维）
- ⚠️ `tensor_operator.weights` 使用模块特定权重（不强制E/O/M/S/R）
- ⚠️ `dynamic_states` 使用模块特定状态定义

**示例**:
```json
{
  "MOD_00_SUBSTRATE": {
    "feature_anchors": {
      "standard_centroid": {
        "vector": {
          "PHASE_PROGRESS": 0.5,
          "ENERGY_DISPERSION_DELTA": 0.1,
          "CAUSAL_ENTROPY": 1.5,
          "SINGULARITY_INDEX": 0.2
        }
      }
    },
    "tensor_operator": {
      "weights": {
        "PHASE_PROGRESS": 0.3,
        "ENERGY_DISPERSION_DELTA": 0.25,
        "CAUSAL_ENTROPY": 0.3,
        "SINGULARITY_INDEX": 0.15
      },
      "core_equation": "D(t) = Σ |E_i(t) - E_i(t-1)| / N"
    }
  }
}
```

### 4.2 方案B：部分对齐

**策略**: 只对齐结构框架，不强制所有字段

**优点**:
- 更灵活
- 减少不必要的字段

**缺点**:
- 结构不统一
- 需要特殊的加载逻辑

---

## 五、推荐方案

### 5.1 推荐：方案A（完全对齐，内容适配）

**理由**:
1. **结构统一**: 与 HOLOGRAPHIC_PATTERN 保持相同的注册表结构
2. **易于维护**: 可以使用相同的 RegistryLoader 和工具
3. **未来扩展**: 如果未来某些模块需要五维张量，可以无缝升级
4. **算法复原**: `algorithm_implementation` 字段确保100%算法复原

### 5.2 适配规则

| 字段 | 适配规则 |
|------|---------|
| **feature_anchors.vector** | 使用模块特定的指标维度，不强制五维 |
| **tensor_operator.weights** | 使用模块特定的权重，不强制E/O/M/S/R |
| **tensor_operator.core_equation** | 使用模块特定的公式，不强制五维张量公式 |
| **dynamic_states** | 使用模块特定的状态定义（如：STABLE_DISPERSION, HIGH_ENTROPY） |
| **algorithm_implementation** | ✅ 必须完全遵守，映射所有引擎函数路径 |

---

## 六、结论

### 6.1 BAZI_FUNDAMENTAL 可以遵守 QGA-HR V2.0 规范吗？

**答案**: ✅ **可以，但需要适配**

### 6.2 适配程度

- **结构层面**: ✅ **100%兼容** - 可以使用相同的JSON结构
- **内容层面**: ⚠️ **部分兼容** - 字段内容需要适配模块特性
- **算法层面**: ✅ **100%兼容** - `algorithm_implementation` 完全遵守

### 6.3 实施建议

1. ✅ **采用 QGA-HR V2.0 规范结构**
2. ⚠️ **允许字段内容适配模块特性**
3. ✅ **确保 `algorithm_implementation` 完整映射所有引擎函数**
4. ✅ **保持与 HOLOGRAPHIC_PATTERN 的结构一致性**

---

## 七、实施检查清单

重构 BAZI_FUNDAMENTAL 模块时，检查以下项目：

- [ ] ✅ `semantic_seed` - 完整的物理意象描述
- [ ] ⚠️ `feature_anchors` - 使用模块特定维度（不强制五维）
- [ ] ⚠️ `tensor_operator` - 使用模块特定权重和公式（不强制E/O/M/S/R）
- [ ] ✅ `algorithm_implementation` - 完整映射所有引擎函数路径
- [ ] ✅ `kinetic_evolution` - 定义触发算子和增益算子
- [ ] ✅ `audit_trail` - 记录版本历史和FDS拟合状态
- [ ] ⚠️ `dynamic_states` - 使用模块特定状态定义
- [ ] ❌ `transfer_matrix` - 不需要（仅V2.1格局需要）

---

**总结**: BAZI_FUNDAMENTAL **可以遵守 QGA-HR V2.0 规范**，但需要在内容层面进行适配，允许使用模块特定的指标维度和状态定义，而不是强制使用五维张量（E, O, M, S, R）。

