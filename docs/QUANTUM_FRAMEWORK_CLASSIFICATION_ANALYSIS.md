# 量子通用框架分类体系分析报告

**版本**: V13.7.0  
**分析日期**: 2025-01-XX  
**状态**: ✅ 完整分析

---

## 📋 执行摘要

通过深度分析 `core/logic_manifest.json`，发现量子通用框架确实注册了**数学模型**、**物理模型**和**算法**，但分类方式是通过 `type` 和 `fusion_type` 字段**隐式分类**，而非明确的顶层分类结构。

---

## 🔍 现有分类体系

### 1. 顶层结构

```json
{
  "themes": {...},        // 主题分类
  "modules": {...},       // 模块列表
  "registry": {...},      // 规则注册表
  "metrics": {...},       // 指标定义
  "bazi_parameters": {...}, // 八字参数
  "tools": {...}          // 工具定义
}
```

### 2. 隐式分类字段

#### A. `registry` 中的 `type` 字段（物理模型分类）

| Type | 中文名称 | 规则数量 | 示例规则 |
|------|---------|---------|---------|
| `QUANTUM_ENGINE` | 量子引擎 | 5+ | PH_QUANTUM_DISPERSION, PH_COMBINATION_PHASE, PH_ROOTING_GAIN, PH_PILLAR_GRAVITY, PH_FLUID_VISCOSITY |
| `CRITICAL_PHYSICS` | 关键物理 | 2+ | PH_SHEAR_BURST, PH_RISK_NODE_DETECT |
| `流体动力学` | 流体动力学 | 3+ | PH_WEALTH_PERMEABILITY, PH_WEALTH_VISCOSITY, PH_BI_JIE_SHIELD |
| `引力动力学` | 引力动力学 | 4+ | PH_GRAVITY_BINDING, PH_PERTURBATION_3BODY, PH_LUCK_BACKGROUND, PH_ANNUAL_IMPULSE |
| `量子动力学` | 量子动力学 | 2+ | PH_PHASE_COLLAPSE, PH_PEACH_BLOSSOM |
| `涌现物理` | 涌现物理 | 2+ | PH_CAUSAL_ENTROPY, PH_SINGULARITY_DETECT |
| `KINETIC_ENERGY` | 动能 | 1+ | PH_LIFE_CYCLE_RESONANCE |
| `FIELD_MODIFIER` | 场修正器 | 2+ | PH_STELLAR_ENTROPY_DAMPING, PH_STELLAR_SNR_BOOST |
| `ATTRACTION` | 吸引力 | 1+ | PH_STELLAR_QUANTUM_ATTRACTION |
| `KINETIC` | 动能 | 1+ | PH_STELLAR_KINETIC_IMPULSE |
| `INTELLIGENCE_ASSET` | 智能资产 | 1+ | PH_DESTINY_TRANSLATION |
| `STRUCTURAL` | 结构 | 1+ | PH_JITTER |
| `结构格局` | 结构格局 | 1+ | PH29_CAPTURE |

#### B. `registry` 中的 `fusion_type` 字段（算法分类）

| Fusion Type | 中文名称 | 规则数量 | 说明 |
|------------|---------|---------|------|
| `CORE_ALGORITHM` | 核心算法 | 1+ | PH_QUANTUM_DISPERSION |
| `CORE_MODULE` | 核心模块 | 8+ | PH_SHEAR_BURST, PH_COMBINATION_PHASE, PH_ROOTING_GAIN, PH_PILLAR_GRAVITY, PH_FLUID_VISCOSITY |
| `PARTIAL_INTEGRATION` | 部分集成 | 10+ | PH_JITTER, PH_WEALTH_PERMEABILITY, PH_WEALTH_VISCOSITY, PH_BI_JIE_SHIELD, PH_GRAVITY_BINDING, PH_PERTURBATION_3BODY, PH_PHASE_COLLAPSE, PH_PEACH_BLOSSOM, PH_LIFE_CYCLE_RESONANCE, PH_SAN_HE, PH_LIU_HE, PH_HE_HUA |
| `CRITICAL_SYSTEM_RULE` | 关键系统规则 | 2+ | PH25-26_COLLAPSE, PH28_ANNIHILATION |
| `EMERGENT_PROPERTY` | 涌现属性 | 2+ | PH_CAUSAL_ENTROPY, PH_SINGULARITY_DETECT |
| `CORE_PATTERN` | 核心格局 | 5+ | PH17-20_CONG, PH19_BEATING, PH27_VOID, PH29_CAPTURE, PH30_CUTTING, PH31_CONTAMINATION |
| `COMPOSITE_EFFECT` | 复合效应 | 2+ | PH_LUCK_BACKGROUND, PH_ANNUAL_IMPULSE |
| `CORE_RULE` | 核心规则 | 4+ | PH_STELLAR_ENTROPY_DAMPING, PH_STELLAR_SNR_BOOST, PH_STELLAR_QUANTUM_ATTRACTION, PH_STELLAR_KINETIC_IMPULSE |
| `INTELLIGENCE_LAYER` | 智能层 | 1+ | PH_DESTINY_TRANSLATION |
| `CORE_ENGINE_RULE` | 核心引擎规则 | 1+ | PH_RISK_NODE_DETECT |

---

## 📊 数学模型分类

### 基于 `type` 和 `fusion_type` 的数学模型识别

#### 1. 量子数学模型 (`QUANTUM_ENGINE`)

**规则列表**:
- `PH_QUANTUM_DISPERSION`: 正弦弥散 `P(t) = A * sin²(πt + φ) * e^(-τt)`
- `PH_COMBINATION_PHASE`: 合化相位判定（阈值模型）
- `PH_ROOTING_GAIN`: 通根增益模型（Main/Medium/Residual/None映射）
- `PH_PILLAR_GRAVITY`: 动态引力权重 `Month Weight = 0.40 + 0.15*sin(pi*t)`
- `PH_FLUID_VISCOSITY`: 流体粘滞模型 `W_prev = exp(-t/tau)`

**数学特征**:
- 正弦函数、指数衰减
- 阈值判定
- 映射函数
- 动态权重

#### 2. 统计力学模型 (`涌现物理`)

**规则列表**:
- `PH_CAUSAL_ENTROPY`: 因果熵 `S = -sum(p*log(p))`
- `PH_SINGULARITY_DETECT`: 奇点探测（重叠计数）

**数学特征**:
- 信息熵公式
- 概率分布
- 统计计数

#### 3. 动力学模型 (`KINETIC_ENERGY`, `KINETIC`)

**规则列表**:
- `PH_LIFE_CYCLE_RESONANCE`: 十二长生动能谐振（峰值增益 2.0x）
- `PH_STELLAR_KINETIC_IMPULSE`: 星辰动能冲量

**数学特征**:
- 动能倍率
- 冲量计算

---

## 🔬 物理模型分类

### 基于 `type` 字段的物理模型识别

#### 1. 流体动力学模型 (`流体动力学`)

**规则列表**:
- `PH_WEALTH_PERMEABILITY`: 财富渗透率（雷诺数）
  - 公式: `Re = (Density * Velocity * Length) / Viscosity`
- `PH_WEALTH_VISCOSITY`: 粘性阻力
  - 公式: `ν = 1.0 + (E_rival ** 2) * 0.05 - (E_control * 2.0)`
- `PH_BI_JIE_SHIELD`: 比劫护盾（干扰屏蔽分析）

**物理特征**:
- 纳维-斯托克斯方程
- 雷诺数
- 粘滞系数
- 流动状态（层流/过渡/湍流）

#### 2. 引力动力学模型 (`引力动力学`)

**规则列表**:
- `PH_GRAVITY_BINDING`: 引力绑定
  - 公式: `E = -G * M_dm * M_spouse / (2 * r)`
- `PH_PERTURBATION_3BODY`: 三体摄动（轨道不稳定性分析）
- `PH_LUCK_BACKGROUND`: 大运背景场（引力背景辐射）
- `PH_ANNUAL_IMPULSE`: 流年轨道冲量
  - 公式: `Δr = +50 (clash) | -30 (join)`

**物理特征**:
- 万有引力公式
- 三体问题
- 轨道力学
- 冲量计算

#### 3. 量子动力学模型 (`量子动力学`)

**规则列表**:
- `PH_PHASE_COLLAPSE`: 相位坍缩（波函数坍缩为确定性事件）
  - 公式: `η = cos²(Δφ / 2)`
- `PH_PEACH_BLOSSOM`: 桃花波函数（概率波）

**物理特征**:
- 波函数坍缩
- 量子相干性
- 概率波

#### 4. 关键物理模型 (`CRITICAL_PHYSICS`)

**规则列表**:
- `PH_SHEAR_BURST`: 羊刃相变（非线性能量增益 2.26x）
- `PH_RISK_NODE_DETECT`: 风险节点探测（SAI/Entropy/IC阈值）

**物理特征**:
- 相变
- 非线性增益
- 临界点检测

---

## 🧮 算法分类

### 基于 `fusion_type` 字段的算法识别

#### 1. 核心算法 (`CORE_ALGORITHM`)

**规则列表**:
- `PH_QUANTUM_DISPERSION`: 量子弥散算法
  - 函数: `QuantumDispersionEngine.get_dynamic_weights()`

**算法特征**:
- 核心计算引擎
- 动态权重计算
- 正弦弥散

#### 2. 核心模块算法 (`CORE_MODULE`)

**规则列表**:
- `PH_SHEAR_BURST`: 羊刃相变算法
  - 函数: `AntigravityEngine.check_shear_burst()`
- `PH_COMBINATION_PHASE`: 合化相位判定算法
  - 函数: `check_combination_phase()`
- `PH_ROOTING_GAIN`: 通根增益算法
  - 函数: `ResonanceBooster.calculate_resonance_gain()`
- `PH_PILLAR_GRAVITY`: 动态引力权重算法
  - 函数: `PillarGravityEngine.calculate_dynamic_weights()`
- `PH_FLUID_VISCOSITY`: 流体粘滞算法
  - 函数: `SpacetimeInertiaEngine.calculate_inertia_weights()`

**算法特征**:
- 模块化实现
- 独立函数
- 可复用

#### 3. 部分集成算法 (`PARTIAL_INTEGRATION`)

**规则列表**:
- `PH_JITTER`: 相位抖动检测
- `PH_WEALTH_PERMEABILITY`: 雷诺数计算
  - 函数: `calculate_reynolds()`
- `PH_WEALTH_VISCOSITY`: 粘滞系数计算
  - 函数: `calculate_viscosity()`
- `PH_BI_JIE_SHIELD`: 比劫护盾分析
  - 函数: `analyze_rival_shield()`
- `PH_GRAVITY_BINDING`: 绑定能计算
  - 函数: `calculate_binding_energy()`
- `PH_PERTURBATION_3BODY`: 三体摄动分析
  - 函数: `analyze_perturbation()`
- `PH_PHASE_COLLAPSE`: 相位坍缩概率计算
  - 函数: `calculate_collapse_probability()`
- `PH_PEACH_BLOSSOM`: 桃花波函数计算
  - 函数: `calculate_peach_blossom_amplitude()`
- `PH_LIFE_CYCLE_RESONANCE`: 十二长生动能谐振
- `PH_SAN_HE`: 地支三合局
- `PH_LIU_HE`: 地支六合
- `PH_HE_HUA`: 干合化气

**算法特征**:
- 部分集成到系统
- 特定功能函数
- 需要进一步整合

#### 4. 关键系统规则算法 (`CRITICAL_SYSTEM_RULE`)

**规则列表**:
- `PH25-26_COLLAPSE`: 结构坍塌检测
- `PH28_ANNIHILATION`: 系统湮灭检测

**算法特征**:
- 系统级检测
- 高优先级
- 关键路径

#### 5. 涌现属性算法 (`EMERGENT_PROPERTY`)

**规则列表**:
- `PH_CAUSAL_ENTROPY`: 因果熵计算
  - 函数: `calculate_causal_entropy()`
- `PH_SINGULARITY_DETECT`: 奇点探测
  - 函数: `detect_singularities()`

**算法特征**:
- 系统级属性
- 全局计算
- 涌现性

---

## 📈 分类统计

### 数学模型统计

| 类别 | 规则数量 | 占比 |
|------|---------|------|
| 量子数学模型 | 5 | 12.5% |
| 统计力学模型 | 2 | 5.0% |
| 动力学模型 | 2 | 5.0% |
| **总计** | **9** | **22.5%** |

### 物理模型统计

| 类别 | 规则数量 | 占比 |
|------|---------|------|
| 流体动力学模型 | 3 | 7.5% |
| 引力动力学模型 | 4 | 10.0% |
| 量子动力学模型 | 2 | 5.0% |
| 关键物理模型 | 2 | 5.0% |
| **总计** | **11** | **27.5%** |

### 算法统计

| 类别 | 规则数量 | 占比 |
|------|---------|------|
| 核心算法 | 1 | 2.5% |
| 核心模块算法 | 5 | 12.5% |
| 部分集成算法 | 12 | 30.0% |
| 关键系统规则算法 | 2 | 5.0% |
| 涌现属性算法 | 2 | 5.0% |
| **总计** | **22** | **55.0%** |

---

## 🎯 建议：显式分类结构

### 建议在 `logic_manifest.json` 中添加显式分类

```json
{
  "classifications": {
    "mathematical_models": {
      "quantum_models": [
        "PH_QUANTUM_DISPERSION",
        "PH_COMBINATION_PHASE",
        "PH_ROOTING_GAIN",
        "PH_PILLAR_GRAVITY",
        "PH_FLUID_VISCOSITY"
      ],
      "statistical_models": [
        "PH_CAUSAL_ENTROPY",
        "PH_SINGULARITY_DETECT"
      ],
      "kinetic_models": [
        "PH_LIFE_CYCLE_RESONANCE",
        "PH_STELLAR_KINETIC_IMPULSE"
      ]
    },
    "physics_models": {
      "fluid_dynamics": [
        "PH_WEALTH_PERMEABILITY",
        "PH_WEALTH_VISCOSITY",
        "PH_BI_JIE_SHIELD"
      ],
      "gravitational_dynamics": [
        "PH_GRAVITY_BINDING",
        "PH_PERTURBATION_3BODY",
        "PH_LUCK_BACKGROUND",
        "PH_ANNUAL_IMPULSE"
      ],
      "quantum_dynamics": [
        "PH_PHASE_COLLAPSE",
        "PH_PEACH_BLOSSOM"
      ],
      "critical_physics": [
        "PH_SHEAR_BURST",
        "PH_RISK_NODE_DETECT"
      ]
    },
    "algorithms": {
      "core_algorithms": [
        "PH_QUANTUM_DISPERSION"
      ],
      "module_algorithms": [
        "PH_SHEAR_BURST",
        "PH_COMBINATION_PHASE",
        "PH_ROOTING_GAIN",
        "PH_PILLAR_GRAVITY",
        "PH_FLUID_VISCOSITY"
      ],
      "integration_algorithms": [
        "PH_JITTER",
        "PH_WEALTH_PERMEABILITY",
        "PH_WEALTH_VISCOSITY",
        "PH_BI_JIE_SHIELD",
        "PH_GRAVITY_BINDING",
        "PH_PERTURBATION_3BODY",
        "PH_PHASE_COLLAPSE",
        "PH_PEACH_BLOSSOM"
      ],
      "system_rules": [
        "PH25-26_COLLAPSE",
        "PH28_ANNIHILATION"
      ],
      "emergent_algorithms": [
        "PH_CAUSAL_ENTROPY",
        "PH_SINGULARITY_DETECT"
      ]
    }
  }
}
```

---

## 📝 详细分类清单

### 数学模型详细清单

#### 量子数学模型 (5个)

1. **PH_QUANTUM_DISPERSION** - 正弦弥散
   - 公式: `P(t) = A * sin²(πt + φ) * e^(-τt)`
   - 函数: `QuantumDispersionEngine.get_dynamic_weights()`
   - 模块: MOD_00_SUBSTRATE

2. **PH_COMBINATION_PHASE** - 合化相位判定
   - 公式: `threshold = 0.65`
   - 函数: `check_combination_phase()`
   - 模块: MOD_09_COMBINATION

3. **PH_ROOTING_GAIN** - 通根增益模型
   - 公式: `G_res = Main(2.0) / Medium(1.5) / Residual(1.2) / None(0.5)`
   - 函数: `ResonanceBooster.calculate_resonance_gain()`
   - 模块: MOD_10_RESONANCE

4. **PH_PILLAR_GRAVITY** - 动态引力权重
   - 公式: `Month Weight = 0.40 + 0.15*sin(pi*t)`
   - 函数: `PillarGravityEngine.calculate_dynamic_weights()`
   - 模块: MOD_11_GRAVITY

5. **PH_FLUID_VISCOSITY** - 流体粘滞模型
   - 公式: `W_prev = exp(-t/tau)`, tau=3.0
   - 函数: `SpacetimeInertiaEngine.calculate_inertia_weights()`
   - 模块: MOD_12_INERTIA

#### 统计力学模型 (2个)

1. **PH_CAUSAL_ENTROPY** - 因果熵
   - 公式: `S = -sum(p*log(p))`
   - 函数: `calculate_causal_entropy()`
   - 模块: MOD_00_SUBSTRATE

2. **PH_SINGULARITY_DETECT** - 奇点探测
   - 公式: 重叠计数
   - 函数: `detect_singularities()`
   - 模块: MOD_00_SUBSTRATE

#### 动力学模型 (2个)

1. **PH_LIFE_CYCLE_RESONANCE** - 十二长生动能谐振
   - 公式: 峰值增益 2.0x（帝旺态）
   - 模块: MOD_18_BASE_APP

2. **PH_STELLAR_KINETIC_IMPULSE** - 星辰动能冲量
   - 模块: MOD_17_STELLAR_INTERACTION

---

### 物理模型详细清单

#### 流体动力学模型 (3个)

1. **PH_WEALTH_PERMEABILITY** - 财富渗透率（雷诺数）
   - 公式: `Re = (Density * Velocity * Length) / Viscosity`
   - 函数: `calculate_reynolds()`
   - 模块: MOD_05_WEALTH

2. **PH_WEALTH_VISCOSITY** - 粘性阻力
   - 公式: `ν = 1.0 + (E_rival ** 2) * 0.05 - (E_control * 2.0)`
   - 函数: `calculate_viscosity()`
   - 模块: MOD_05_WEALTH

3. **PH_BI_JIE_SHIELD** - 比劫护盾
   - 函数: `analyze_rival_shield()`
   - 模块: MOD_05_WEALTH

#### 引力动力学模型 (4个)

1. **PH_GRAVITY_BINDING** - 引力绑定
   - 公式: `E = -G * M_dm * M_spouse / (2 * r)`
   - 函数: `calculate_binding_energy()`
   - 模块: MOD_06_RELATIONSHIP

2. **PH_PERTURBATION_3BODY** - 三体摄动
   - 函数: `analyze_perturbation()`
   - 模块: MOD_06_RELATIONSHIP

3. **PH_LUCK_BACKGROUND** - 大运背景场
   - 函数: `apply_luck_modifier()`
   - 模块: MOD_06_RELATIONSHIP

4. **PH_ANNUAL_IMPULSE** - 流年轨道冲量
   - 公式: `Δr = +50 (clash) | -30 (join)`
   - 函数: `apply_annual_impulse()`
   - 模块: MOD_06_RELATIONSHIP

#### 量子动力学模型 (2个)

1. **PH_PHASE_COLLAPSE** - 相位坍缩
   - 公式: `η = cos²(Δφ / 2)`
   - 函数: `calculate_collapse_probability()`
   - 模块: MOD_06_RELATIONSHIP

2. **PH_PEACH_BLOSSOM** - 桃花波函数
   - 函数: `calculate_peach_blossom_amplitude()`
   - 模块: MOD_06_RELATIONSHIP

#### 关键物理模型 (2个)

1. **PH_SHEAR_BURST** - 羊刃相变
   - 公式: 2.26x 增益（当羊刃遇冲时）
   - 函数: `AntigravityEngine.check_shear_burst()`
   - 模块: MOD_07_LIFEPATH

2. **PH_RISK_NODE_DETECT** - 风险节点探测
   - 条件: `SAI > 0.6 or Entropy > 1.5 or IC > 0.6`
   - 函数: `LifePathEngine._identify_risk_reason()`
   - 模块: MOD_07_LIFEPATH

---

### 算法详细清单

#### 核心算法 (1个)

1. **PH_QUANTUM_DISPERSION** - 量子弥散算法
   - 类型: `CORE_ALGORITHM`
   - 函数: `QuantumDispersionEngine.get_dynamic_weights()`
   - 模块: MOD_00_SUBSTRATE

#### 核心模块算法 (5个)

1. **PH_SHEAR_BURST** - 羊刃相变算法
2. **PH_COMBINATION_PHASE** - 合化相位判定算法
3. **PH_ROOTING_GAIN** - 通根增益算法
4. **PH_PILLAR_GRAVITY** - 动态引力权重算法
5. **PH_FLUID_VISCOSITY** - 流体粘滞算法

#### 部分集成算法 (12个)

1. **PH_JITTER** - 相位抖动检测
2. **PH_WEALTH_PERMEABILITY** - 雷诺数计算
3. **PH_WEALTH_VISCOSITY** - 粘滞系数计算
4. **PH_BI_JIE_SHIELD** - 比劫护盾分析
5. **PH_GRAVITY_BINDING** - 绑定能计算
6. **PH_PERTURBATION_3BODY** - 三体摄动分析
7. **PH_PHASE_COLLAPSE** - 相位坍缩概率计算
8. **PH_PEACH_BLOSSOM** - 桃花波函数计算
9. **PH_LIFE_CYCLE_RESONANCE** - 十二长生动能谐振
10. **PH_SAN_HE** - 地支三合局
11. **PH_LIU_HE** - 地支六合
12. **PH_HE_HUA** - 干合化气

#### 关键系统规则算法 (2个)

1. **PH25-26_COLLAPSE** - 结构坍塌检测
2. **PH28_ANNIHILATION** - 系统湮灭检测

#### 涌现属性算法 (2个)

1. **PH_CAUSAL_ENTROPY** - 因果熵计算
2. **PH_SINGULARITY_DETECT** - 奇点探测

---

## 🔗 模块-规则-算法映射关系

### MOD_00_SUBSTRATE (晶格基底)
- **数学模型**: PH_QUANTUM_DISPERSION, PH_CAUSAL_ENTROPY, PH_SINGULARITY_DETECT
- **算法**: 量子弥散算法、因果熵计算、奇点探测

### MOD_05_WEALTH (财富流体力学)
- **物理模型**: PH_WEALTH_PERMEABILITY, PH_WEALTH_VISCOSITY, PH_BI_JIE_SHIELD
- **算法**: 雷诺数计算、粘滞系数计算、比劫护盾分析

### MOD_06_RELATIONSHIP (情感引力场)
- **物理模型**: PH_GRAVITY_BINDING, PH_PERTURBATION_3BODY, PH_PHASE_COLLAPSE, PH_PEACH_BLOSSOM, PH_LUCK_BACKGROUND, PH_ANNUAL_IMPULSE
- **算法**: 绑定能计算、三体摄动分析、相位坍缩概率计算、桃花波函数计算

### MOD_10_RESONANCE (干支通根增益)
- **数学模型**: PH_ROOTING_GAIN
- **算法**: 通根增益算法

### MOD_11_GRAVITY (宫位引力场)
- **数学模型**: PH_PILLAR_GRAVITY
- **算法**: 动态引力权重算法

### MOD_12_INERTIA (时空场惯性)
- **数学模型**: PH_FLUID_VISCOSITY
- **算法**: 流体粘滞算法

---

## ✅ 总结

### 发现

1. **确实存在分类**：通过 `type` 和 `fusion_type` 字段隐式分类
2. **数学模型**: 9个（量子数学模型5个、统计力学模型2个、动力学模型2个）
3. **物理模型**: 11个（流体动力学3个、引力动力学4个、量子动力学2个、关键物理2个）
4. **算法**: 22个（核心算法1个、核心模块算法5个、部分集成算法12个、关键系统规则算法2个、涌现属性算法2个）

### 建议

1. **添加显式分类结构**：在 `logic_manifest.json` 中添加 `classifications` 字段
2. **统一分类标准**：明确数学模型、物理模型、算法的定义和边界
3. **完善文档**：为每个分类补充详细说明和公式

---

**报告生成时间**: 2025-01-XX  
**分析人员**: AI Assistant  
**版本**: V13.7.0

