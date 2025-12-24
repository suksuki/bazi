# 八字基础规则主题深度审查报告

**版本**: V13.6.0  
**审查日期**: 2025-01-XX  
**审查范围**: 通用量子框架下"八字基础规则主题"的所有算法和规则

---

## 📋 目录

1. [框架概述](#框架概述)
2. [主题结构](#主题结构)
3. [模块详细分析](#模块详细分析)
4. [规则注册表分析](#规则注册表分析)
5. [算法实现细节](#算法实现细节)
6. [参数注入机制](#参数注入机制)
7. [输入输出规范](#输入输出规范)
8. [总结与建议](#总结与建议)

---

## 框架概述

### 通用量子框架架构

**系统ID**: `ANTIGRAVITY_CORE_ALPHA`  
**版本**: 13.6.0  
**描述**: Quantum Universal Framework with Plug-and-Play Influence Bus & Multi-Body Physics

### 核心设计理念

1. **模块化设计**: 所有算法以模块(Module)形式注册，支持插拔式架构
2. **规则驱动**: 物理规则以规则ID形式注册在注册表中
3. **主题分类**: 算法按主题(Themes)组织，便于管理和扩展
4. **参数可配置**: 所有算法参数通过配置文件管理，支持热加载

### 三阶段计算架构

```
Phase 1: 节点初始化 (Node Initialization)
  ↓
Phase 2: 邻接矩阵构建 (Adjacency Matrix Construction)
  ↓
Phase 3: 能量传播 (Energy Propagation)
```

---

## 主题结构

### 八字基础规则主题 (BAZI_FUNDAMENTAL)

**主题ID**: `BAZI_FUNDAMENTAL`  
**名称**: 八字基础规则主题  
**描述**: 包含晶格基底、能量分布、合化动力学及微观应力等基础物理模型。

**包含模块数量**: 18个核心模块  
**包含规则数量**: 40+条物理规则  
**状态**: ✅ ACTIVE

---

## 模块详细分析

### MOD_00_SUBSTRATE - 晶格基底与因果涌现

**模块ID**: `MOD_00_SUBSTRATE`  
**名称**: 🧬 晶格基底与因果涌现 (Substrate & Causal Emergence)  
**类型**: `CORE_SUBSTRATE`  
**优先级**: 1000 (最高)  
**层级**: `ENVIRONMENT`  
**状态**: ✅ ACTIVE

#### 功能描述
基底即因果 (Substrate is Causality) | 基于量子弥散与因果熵的全链路物理仿真监控室。

#### 关联规则
- `PH_QUANTUM_DISPERSION`: 正弦弥散算法
- `PH_CAUSAL_ENTROPY`: 因果熵计算
- `PH_SINGULARITY_DETECT`: 奇点探测

#### 关联指标
- `PHASE_PROGRESS`: 相位进度
- `ENERGY_DISPERSION_DELTA`: 能量弥散增量
- `CAUSAL_ENTROPY`: 因果熵值
- `SINGULARITY_INDEX`: 奇点指标

#### 输入
- 八字列表: `bazi: List[str]`
- 日主: `day_master: str`
- 大运: `luck_pillar: str` (可选)
- 流年: `year_pillar: str` (可选)
- 地理修正: `geo_modifiers: Dict[str, float]` (可选)

#### 输出
- 初始能量向量: `H^(0): np.ndarray`
- 节点列表: `nodes: List[GraphNode]`
- 因果熵值: `causal_entropy: float`
- 奇点指标: `singularity_index: float`

#### 算法实现位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`
- `core/trinity/core/engines/quantum_dispersion.py`: `QuantumDispersionEngine`

---

### MOD_01_TRIPLE - 大一统三元动力

**模块ID**: `MOD_01_TRIPLE`  
**名称**: ♾️ 大一统三元动力 (Integrated Triple Dynamics)  
**类型**: `CORE_MODULE`  
**优先级**: 900  
**层级**: `FUNDAMENTAL`  
**状态**: ✅ ACTIVE

#### 功能描述
焦点：克、泄、化控制逻辑分析 (Focus: Capture, Cutting & Contamination Control Logic)

#### 关联规则
- `PH29_CAPTURE`: 食神制杀/伤官合杀逻辑
- `PH30_CUTTING`: 枭神夺食/频谱切断逻辑
- `PH31_CONTAMINATION`: 财星坏印/介质污染逻辑

#### 关联指标
- `unified_metrics.capture`: 捕获效率
- `unified_metrics.cutting`: 切断效率
- `unified_metrics.contamination`: 污染程度

#### 输入
- 节点能量矩阵: `H: np.ndarray`
- 邻接矩阵: `A: np.ndarray`
- 日主元素: `dm_element: str`

#### 输出
- 捕获增益: `capture_gain: float`
- 切断损耗: `cutting_loss: float`
- 污染系数: `contamination_factor: float`

#### 算法公式
```python
# PH29_CAPTURE: 食神制杀
phi_shift = 0.5
q_gain = 1.5
capture_effect = q_gain * sin(phi_shift)

# PH30_CUTTING: 枭神夺食
phi_shift = 2.2
q_gain = 0.3
cutting_effect = q_gain * sin(phi_shift)

# PH31_CONTAMINATION: 财星坏印
phi_shift = 1.2
q_gain = 0.7
contamination_effect = q_gain * sin(phi_shift)
```

---

### MOD_02_SUPER - 极高位格局共振

**模块ID**: `MOD_02_SUPER`  
**名称**: 🔥 极高位格局共振 (Super-Structure Resonance)  
**类型**: `CORE_MODULE`  
**优先级**: 800  
**层级**: `STRUCTURAL`  
**状态**: ✅ ACTIVE

#### 功能描述
焦点：共振波场与能量趋势分析 (Focus: Resonance Wavefield & Energy Trend Analysis)

#### 关联规则
- `PH17-20_CONG`: 从格/专旺格局
- `PH19_BEATING`: 假从/拍频格局
- `PH28_ANNIHILATION`: 系统湮灭状态
- `PH27_VOID`: 空亡能量泄漏

#### 关联指标
- `resonance.sync_state`: 同步状态
- `resonance.flow_efficiency`: 流动效率
- `resonance.vibration_mode`: 振动模式

#### 输入
- 能量分布: `energy_distribution: Dict[str, float]`
- 锁定比例: `locking_ratio: float`
- 同步状态: `sync_state: float`

#### 输出
- 格局类型: `pattern_type: str` (从旺/从强/假从/湮灭)
- 共振增益: `resonance_gain: float`
- 能量趋势: `energy_trend: Dict[str, float]`

#### 算法判定条件
```python
# 从格判定
if mode == 'COHERENT' and locking_ratio > 2.0:
    pattern = "从旺/从强"
    effect = "超导状态"

# 假从判定
if mode == 'BEATING':
    pattern = "假从/拍频"
    effect = "干涉包络"

# 湮灭判定
if sync_state < 0.12:
    pattern = "系统湮灭"
    effect = "全反射状态"

# 空亡判定
if is_void == true:
    pattern = "空亡"
    effect = "ENERGY_LEAK"
    damping_factor = 0.45
```

---

### MOD_03_TRANSFORM - 合化动力学

**模块ID**: `MOD_03_TRANSFORM`  
**名称**: ⚗️ 合化动力学 (Transformation Chemistry)  
**类型**: `CORE_MODULE`  
**优先级**: 750  
**层级**: `STRUCTURAL`  
**状态**: ✅ ACTIVE

#### 功能描述
焦点：天干地支键合拓扑分析 (Focus: Heavenly Stems & Earthly Branches Bonding Topology)

#### 关联规则
- `PH_SAN_HE`: 地支三合局
- `PH_LIU_HE`: 地支六合
- `PH_HE_HUA`: 干合化气

#### 关联指标
- `structure.bond_strength`: 键合强度
- `structure.transform_success`: 化气成功率

#### 输入
- 天干对: `stem_pair: Tuple[str, str]`
- 地支组合: `branch_combo: List[str]`
- 月令能量: `month_energy: float`

#### 输出
- 化气状态: `transform_state: str` (成功/失败/纠缠)
- 键合强度: `bond_strength: float`
- 化气能量: `transform_power: float`

#### 算法实现
```python
# 天干五合判定
def check_stem_combination(stem1, stem2, month_energy):
    combination_map = {
        ('甲', '己'): '土',
        ('乙', '庚'): '金',
        ('丙', '辛'): '水',
        ('丁', '壬'): '木',
        ('戊', '癸'): '火'
    }
    
    target_element = combination_map.get((stem1, stem2))
    if target_element and month_energy > 0.65:
        return "化气成功", 1.0
    elif target_element:
        return "纠缠状态", 0.3
    else:
        return "无合化", 0.0

# 三合局判定
def check_san_he(branches):
    san_he_sets = [
        {'申', '子', '辰'},  # 水局
        {'亥', '卯', '未'},  # 木局
        {'寅', '午', '戌'},  # 火局
        {'巳', '酉', '丑'}   # 金局
    ]
    branch_set = set(branches)
    for he_set in san_he_sets:
        if he_set.issubset(branch_set):
            return True, "三合局成立"
    return False, "无三合"

# 六合判定
def check_liu_he(branch1, branch2):
    liu_he_map = {
        ('子', '丑'): True, ('寅', '亥'): True,
        ('卯', '戌'): True, ('辰', '酉'): True,
        ('巳', '申'): True, ('午', '未'): True
    }
    return liu_he_map.get((branch1, branch2), False)
```

---

### MOD_04_STABILITY - 刑害干涉动力学

**模块ID**: `MOD_04_STABILITY`  
**名称**: 🛡️ 刑害干涉动力学 (Penalty & Harm Dynamics)  
**类型**: `CORE_MODULE`  
**优先级**: 850  
**层级**: `FUNDAMENTAL`  
**状态**: ✅ ACTIVE

#### 功能描述
焦点：晶格缺陷与相位抖动分析 (Focus: Lattice Defects & Phase Jitter Analysis (SAI/IC))

#### 关联规则
- `PH_PENALTY_3`: 三刑检测
- `PH_HARM_6`: 六害检测
- `PH_SHEAR_STRESS`: 剪切应力

#### 关联指标
- `structure.stress_accumulation_index`: 应力累积指标 (SAI)
- `structure.interference_coefficient`: 干涉系数 (IC)

#### 输入
- 地支列表: `branches: List[str]`
- 节点能量: `node_energies: np.ndarray`

#### 输出
- 应力指标: `sai: float`
- 干涉系数: `ic: float`
- 风险等级: `risk_level: str`

#### 算法实现
```python
# 三刑检测
def detect_three_penalty(branches):
    penalty_sets = [
        {'丑', '未', '戌'},  # 三刑
        {'寅', '巳', '申'},  # 三刑
        {'子', '卯'},        # 无礼之刑
        {'辰', '午', '酉', '亥'}  # 自刑
    ]
    
    branch_set = set(branches)
    for penalty_set in penalty_sets:
        if penalty_set.issubset(branch_set):
            return True, -40.0  # 结构性崩塌重罚
    
    return False, 0.0

# 六害检测
def detect_harm_6(branch1, branch2):
    harm_map = {
        ('子', '未'): True, ('丑', '午'): True,
        ('寅', '巳'): True, ('卯', '辰'): True,
        ('申', '亥'): True, ('酉', '戌'): True
    }
    return harm_map.get((branch1, branch2), False)

# 相位抖动
def calculate_phase_jitter(nodes):
    jitter = 0.0
    for node in nodes:
        if hasattr(node, 'combination_conflict'):
            jitter += 0.1
    return min(jitter, 1.0)
```

---

### MOD_05_WEALTH - 财富流体力学

**模块ID**: `MOD_05_WEALTH`  
**名称**: 🌊 财富流体力学 (Wealth Fluid Dynamics)  
**类型**: `STANDALONE_MODULE`  
**优先级**: 700  
**层级**: `FLOW`  
**场景亲和**: `WEALTH`  
**状态**: ✅ ACTIVE

#### 功能描述
基于纳维-斯托克斯方程的财富能量流动分析 (Wealth Energy Fluid Analysis via Navier-Stokes)

#### 关联规则
- `PH_WEALTH_PERMEABILITY`: 财富渗透率 (雷诺数)
- `PH_WEALTH_VISCOSITY`: 粘性阻力
- `PH_BI_JIE_SHIELD`: 比劫护盾

#### 关联指标
- `REYNOLDS_NUMBER`: 雷诺数 (Re)
- `VISCOSITY`: 粘滞系数 (ν)
- `FLUX_Q`: 流量闸门 (Q)

#### 输入
- 八字: `bazi: List[str]`
- 日主: `day_master: str`
- 大运: `luck_pillar: str`
- 流年: `year_pillar: str`
- 性别: `gender: str`

#### 输出
- 财富势能: `wealth_potential: float`
- 流动向量: `flow_vector: Dict[str, float]`
- 容量向量: `capacity_vector: Dict[str, float]`
- 波动率: `volatility_sigma: float`

#### 算法公式
```python
# 雷诺数 (流动状态)
Re = (Density * Velocity * Length) / Viscosity
# Re < 2000: 层流
# 2000-4000: 过渡
# Re > 4000: 湍流

# 粘滞系数
nu = 1.0 + (E_rival ** 2) * 0.05 - (E_control * 2.0)
# E_rival: 比劫能量
# E_control: 食伤能量

# 流量闸门
Q = E_output * 2.0
# E_output: 食伤能量

# 财富势能
wealth_potential = (Q * Re) / (1 + nu)
```

#### 实现位置
- `core/wealth_engine/vectors.py`: `calculate_flow_vector()`, `calculate_capacity_vector()`
- `core/wealth_engine/timeline_simulator.py`: `simulate_life_wealth()`

---

### MOD_06_RELATIONSHIP - 情感引力场

**模块ID**: `MOD_06_RELATIONSHIP`  
**名称**: 🌌 情感引力场 (Relationship Gravity Field)  
**类型**: `STANDALONE_MODULE`  
**优先级**: 650  
**层级**: `FLOW`  
**场景亲和**: `RELATIONSHIP`  
**状态**: ✅ ACTIVE

#### 功能描述
基于引力耦合与相位坍缩的情感动力学 (Relationship Dynamics via Gravitational Coupling & Phase Collapse)

#### 关联规则
- `PH_GRAVITY_BINDING`: 引力绑定
- `PH_PERTURBATION_3BODY`: 三体摄动
- `PH_PHASE_COLLAPSE`: 相位坍缩
- `PH_PEACH_BLOSSOM`: 桃花波函数
- `PH_LUCK_BACKGROUND`: 大运背景场
- `PH_ANNUAL_IMPULSE`: 流年轨道冲量

#### 关联指标
- `BINDING_ENERGY`: 绑定能 (E)
- `ORBITAL_STABILITY`: 轨道稳定性 (σ)
- `PHASE_COHERENCE`: 相位相干性 (η)
- `LUCK_MODIFIER`: 大运修正系数 (λ)
- `ANNUAL_IMPULSE`: 流年冲量 (Δr)
- `GEO_FACTOR`: 地域介质常数 (ε)

#### 输入
- 八字: `bazi: List[str]`
- 日主: `day_master: str`
- 性别: `gender: str`
- 大运: `luck_pillar: str`
- 流年: `year_pillar: str`
- 地理坐标: `geo_context: Dict[str, float]`

#### 输出
- 绑定能量: `binding_energy: float`
- 轨道稳定性: `orbital_stability: float`
- 相位相干性: `phase_coherence: float`
- 关系预测: `relationship_prediction: Dict[str, Any]`

#### 算法公式
```python
# 绑定能 (负值表示绑定)
E = -G * M_dm * M_spouse / (2 * r)
# G: 引力常数
# M_dm: 日主质量
# M_spouse: 配偶星质量
# r: 轨道距离

# 轨道稳定性
σ = |E_binding| / E_perturbation

# 相位相干性
η = cos²(Δφ / 2)

# 大运修正系数
λ = 1.3 (support) | 0.7 (control) | 0.6 (clash)

# 流年冲量
Δr = +50 (clash) | -30 (join)

# 地域修正
G_eff = G * ε
```

#### 实现位置
- `core/trinity/core/engines/relationship_gravity.py`

---

### MOD_07_LIFEPATH - 个人生命轨道仪

**模块ID**: `MOD_07_LIFEPATH`  
**名称**: 🚀 个人生命轨道仪 (Personal Orbit Orrery)  
**类型**: `CORE_MODULE`  
**优先级**: 500  
**层级**: `TEMPORAL`  
**状态**: ✅ ACTIVE

#### 功能描述
用于生命轨迹能量审计的高频时次采样分析。

#### 关联规则
- `PH_DYNAMIC_DISPERSION_SIN`: 动态弥散正弦
- `PH_SHEAR_BURST`: 羊刃相变
- `PH_RISK_NODE_DETECT`: 风险节点探测

#### 关联指标
- `ORBITAL_ENTROPY`: 轨道熵
- `RISK_NODE_DENSITY`: 风险节点密度

#### 输入
- 八字: `bazi: List[str]`
- 日主: `day_master: str`
- 出生年份: `birth_year: int`
- 生命周期: `lifespan: int`

#### 输出
- 生命轨迹: `life_trajectory: List[Dict[str, Any]]`
- 风险节点: `risk_nodes: List[Dict[str, Any]]`
- 轨道熵: `orbital_entropy: float`

#### 算法实现
```python
# 风险节点探测条件
def detect_risk_node(sai, entropy, ic):
    if sai > 0.6 or entropy > 1.5 or ic > 0.6:
        return True, "高风险节点"
    return False, "正常"

# 羊刃相变 (非线性能量增益)
def check_shear_burst(yang_ren_node, clash_nodes):
    if yang_ren_node and clash_nodes:
        return 2.26  # 2.26倍能量增益
    return 1.0
```

---

### MOD_09_COMBINATION - 天干合化相位

**模块ID**: `MOD_09_COMBINATION`  
**名称**: ⚛️ 天干合化相位 (Stem Combination Phase)  
**类型**: `CORE_MODULE`  
**优先级**: 800  
**层级**: `STRUCTURAL`  
**状态**: ✅ ACTIVE

#### 功能描述
天干合化与纠缠态物理学。

#### 关联规则
- `PH_COMBINATION_PHASE`: 合化相位判定

#### 关联指标
- `COMBINATION_THRESHOLD`: 合化阈值 (0.65)
- `TRANSFORM_POWER`: 化气能量 (1.0成功/0.3纠缠)

#### 算法实现
```python
# 合化相位判定
def check_combination_phase(month_energy, threshold=0.65):
    if month_energy > threshold:
        return "化气成功", 1.0
    else:
        return "纠缠状态", 0.3
```

---

### MOD_10_RESONANCE - 干支通根增益

**模块ID**: `MOD_10_RESONANCE`  
**名称**: 📡 干支通根增益 (Stem-Branch Resonance)  
**类型**: `CORE_MODULE`  
**优先级**: 880  
**层级**: `FUNDAMENTAL`  
**状态**: ✅ ACTIVE

#### 功能描述
通过通根（天干地支谐振）实现的信号放大。

#### 关联规则
- `PH_ROOTING_GAIN`: 通根增益模型

#### 关联指标
- `ROOTING_GAIN`: 通根增益系数
- `STABILITY_STATUS`: 稳态标识

#### 算法实现
```python
# 通根增益计算
def calculate_rooting_gain(root_type):
    gain_map = {
        'main': 2.0,      # 本气
        'medium': 1.5,    # 中气
        'residual': 1.2,  # 余气
        'none': 0.5       # 无根（浮游）
    }
    return gain_map.get(root_type, 0.5)
```

#### 实现位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer._has_root()`

---

### MOD_11_GRAVITY - 宫位引力场

**模块ID**: `MOD_11_GRAVITY`  
**名称**: 🌌 宫位引力场 (Pillar Gravitational Field)  
**类型**: `CORE_MODULE`  
**优先级**: 840  
**层级**: `FUNDAMENTAL`  
**状态**: ✅ ACTIVE

#### 功能描述
基于节气深度的动态权重分布。

#### 关联规则
- `PH_PILLAR_GRAVITY`: 动态引力权重

#### 关联指标
- `PILLAR_WEIGHT_MATRIX`: 宫位权重矩阵

#### 算法实现
```python
# 动态引力权重
def calculate_dynamic_weights(time_factor):
    # 月令权重动态变化
    month_weight = 0.40 + 0.15 * sin(pi * time_factor)
    
    # 默认权重
    weights = {
        'year': 0.7,
        'month': month_weight,  # 动态
        'day': 1.35,
        'hour': 0.77
    }
    return weights
```

#### 实现位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`

---

### MOD_12_INERTIA - 时空场惯性

**模块ID**: `MOD_12_INERTIA`  
**名称**: 🌊 时空场惯性 (Spacetime Field Inertia)  
**类型**: `STANDALONE_MODULE`  
**优先级**: 550  
**层级**: `TEMPORAL`  
**状态**: ✅ ACTIVE

#### 功能描述
用于能量迁移的流体粘性建模。

#### 关联规则
- `PH_FLUID_VISCOSITY`: 流体粘滞模型

#### 关联指标
- `INERTIA_CONSTANT_TAU`: 惯性常数 (τ, 默认3.0个月)
- `VISCOSITY_INDEX`: 粘滞指数

#### 算法实现
```python
# 指数衰减模型
W_prev = exp(-t / tau)
# tau = 3.0 个月 (默认)
```

---

### MOD_14_TIME_SPACE_INTERFERENCE - 多维时空场耦合模型

**模块ID**: `MOD_14_TIME_SPACE_INTERFERENCE`  
**名称**: ⏳ 多维时空场耦合模型 (Multidimensional Spacetime Field Coupling)  
**类型**: `CORE_MODULE`  
**优先级**: 200  
**层级**: `TEMPORAL_INTERFERENCE_LAYER`  
**状态**: ✅ ACTIVE

#### 功能描述
实现原生概率波函数（Base Wave）与大运（Background）、流年（Impulse）、地域（GEO Bias）的相干叠加计算。

#### 关联规则
- `PH_QUANTUM_DISPERSION`: 量子弥散
- `PH_WEALTH_PERMEABILITY`: 财富渗透率
- `PH_GRAVITY_BINDING`: 引力绑定

#### 关联指标
- `spacetime_interference_index`: 时空干涉指数
- `geo_coupling_efficiency`: 地理耦合效率
- `phase_coherence`: 相位相干性

#### 输入
- 原局能量: `base_energy: np.ndarray`
- 大运干支: `luck_pillar: str`
- 流年干支: `year_pillar: str`
- 地理坐标: `geo_context: Dict[str, float]`

#### 输出
- 耦合能量: `coupled_energy: np.ndarray`
- 干涉波形: `interference_waveform: Dict[str, Any]`
- K-Geo效率: `k_geo_efficiency: float`

---

### MOD_15_STRUCTURAL_VIBRATION - 结构振动传导

**模块ID**: `MOD_15_STRUCTURAL_VIBRATION`  
**名称**: 🏗️ 结构振动传导 (Structural Vibration Transmission)  
**类型**: `CORE_MODULE`  
**优先级**: 150  
**层级**: `STRUCTURAL_INTERACTION_LAYER`  
**状态**: ✅ ACTIVE

#### 功能描述
基于非线性动力网络的能量传导、饱和与阻抗分析引擎。

#### 关联规则
- `PH_NONLINEAR_SATURATION`: 非线性饱和
- `PH_VERTICAL_COUPLING`: 垂直耦合
- `PH_ENTROPY_OPTIMIZATION`: 熵优化

#### 关联指标
- `vibration_efficiency`: 振动效率
- `impedance_break_index`: 阻抗断链指数
- `composite_deity_ratio`: 复合神格配比

---

### MOD_16_TEMPORAL_SHUNTING - 应期预测与行为干预

**模块ID**: `MOD_16_TEMPORAL_SHUNTING`  
**名称**: ⏳ 应期预测与行为干预 (Temporal Shunting)  
**类型**: `CORE_MODULE`  
**优先级**: 200  
**层级**: `TEMPORAL`  
**状态**: ✅ ACTIVE

#### 功能描述
Calculates future SAI singularity points and simulates behavior/geo shunting efficiency using differential decay equations.

#### 依赖模块
- `MOD_15_STRUCTURAL_VIBRATION`
- `MOD_14_TIME_SPACE_INTERFERENCE`

---

### MOD_17_STELLAR_INTERACTION - 星辰相干与喜剧真言

**模块ID**: `MOD_17_STELLAR_INTERACTION`  
**名称**: ✨ 星辰相干与喜剧真言 (Stellar Coherence & Comedy)  
**类型**: `CORE_INTELLIGENCE`  
**优先级**: 400  
**层级**: `INTELLIGENCE`  
**状态**: ✅ ACTIVE

#### 功能描述
将传统神煞（天乙、文昌、桃花、驿马）映射为高阶物理场增益与动能冲量，并提供周星驰风格的全息真言输出。

#### 关联规则
- `PH_STELLAR_ENTROPY_DAMPING`: 星辰熵衰减
- `PH_STELLAR_SNR_BOOST`: 星辰信噪比提升
- `PH_STELLAR_QUANTUM_ATTRACTION`: 星辰量子引力
- `PH_STELLAR_KINETIC_IMPULSE`: 星辰动能冲量

#### 关联指标
- `STELLAR_COHERENCE`: 星辰相干度
- `QUANTUM_ATTRACTION`: 量子引力增益
- `KINETIC_IMPULSE`: 动能冲量

#### 算法实现
```python
# 天乙贵人: 每个节点衰减系统熵10%
entropy_damping = 0.1 * tian_yi_count

# 文昌: 每个节点提升信噪比15%
snr_boost = 0.15 * wen_chang_count

# 桃花: 增加关系绑定能
binding_energy_boost = peach_blossom_count * attraction_factor

# 驿马: 减少移动阻力，增加delta-V
kinetic_impulse = post_horse_count * velocity_boost
```

---

### MOD_18_BASE_APP - 基础应用与全局工具

**模块ID**: `MOD_18_BASE_APP`  
**名称**: 🛠️ 基础应用与全局工具 (Basic Applications & Global Tools)  
**类型**: `CORE_MODULE`  
**优先级**: 100  
**层级**: `ENVIRONMENT`  
**状态**: ✅ ACTIVE

#### 功能描述
包含系统全局调用的基础算法、命运真言工具及跨模块物理干涉检测。

#### 关联规则
- `PH_DESTINY_TRANSLATION`: 命运真言翻译
- `PH_SINGULARITY_DETECT`: 奇点探测
- `PH_CAUSAL_ENTROPY`: 因果熵
- `PH_LIFE_CYCLE_RESONANCE`: 生命周期共振
- `PH_JITTER`: 相位抖动
- `PH_CHONG`: 地支六冲
- `PH25-26_COLLAPSE`: 结构坍塌
- `PH_LUCK_BACKGROUND`: 大运背景场
- `PH_ANNUAL_IMPULSE`: 流年轨道冲量

---

## 规则注册表分析

### 核心格局规则

#### PH17-20_CONG - 从格/专旺
- **条件**: `mode == 'COHERENT' and locking_ratio > 2.0`
- **优先级**: 950
- **效果**: 超导状态
- **标签**: 从旺、从强

#### PH19_BEATING - 假从/拍频
- **条件**: `mode == 'BEATING'`
- **优先级**: 940
- **效果**: 干涉包络
- **场景亲和**: WEALTH, CAREER

#### PH25-26_COLLAPSE - 结构坍塌
- **条件**: `clash_count >= 2`
- **优先级**: 990
- **效果**: 湮灭风险

#### PH27_VOID - 空亡
- **条件**: `is_void == true`
- **优先级**: 980
- **效果**: ENERGY_LEAK
- **阻尼系数**: 0.45

#### PH28_ANNIHILATION - 系统湮灭
- **条件**: `sync_state < 0.12`
- **优先级**: 1000
- **效果**: 全反射状态

### 控制逻辑规则

#### PH29_CAPTURE - 食神制杀
- **phi_shift**: 0.5
- **q_gain**: 1.5
- **优先级**: 950

#### PH30_CUTTING - 枭神夺食
- **phi_shift**: 2.2
- **q_gain**: 0.3
- **优先级**: 840

#### PH31_CONTAMINATION - 财星坏印
- **phi_shift**: 1.2
- **q_gain**: 0.7
- **优先级**: 830

### 合化规则

#### PH_SAN_HE - 地支三合局
- **优先级**: 820
- **冲突**: PH_CHONG, PH_HARM_6

#### PH_LIU_HE - 地支六合
- **优先级**: 810
- **冲突**: PH_CHONG

#### PH_HE_HUA - 干合化气
- **优先级**: 830
- **冲突**: PH_CHONG

#### PH_CHONG - 地支六冲
- **优先级**: 700

### 基础物理规则

#### PH_QUANTUM_DISPERSION - 正弦弥散
- **公式**: `P(t) = A * sin²(πt + φ) * e^(-τt)`
- **优先级**: 1000
- **功能**: `QuantumDispersionEngine.get_dynamic_weights()`

#### PH_ROOTING_GAIN - 通根增益
- **增益系数**: Main(2.0) / Medium(1.5) / Residual(1.2) / None(0.5)
- **优先级**: 890
- **功能**: `ResonanceBooster.calculate_resonance_gain()`

#### PH_PILLAR_GRAVITY - 动态引力权重
- **公式**: `Month Weight = 0.40 + 0.15*sin(pi*t)`
- **优先级**: 910
- **功能**: `PillarGravityEngine.calculate_dynamic_weights()`

#### PH_FLUID_VISCOSITY - 流体粘滞
- **公式**: `W_prev = exp(-t/tau)`, tau=3.0
- **优先级**: 580
- **功能**: `SpacetimeInertiaEngine.calculate_inertia_weights()`

#### PH_LIFE_CYCLE_RESONANCE - 十二长生动能谐振
- **峰值增益**: 2.0x (帝旺态)
- **优先级**: 870

#### PH_SHEAR_BURST - 羊刃相变
- **增益**: 2.26x (当羊刃遇冲时)
- **优先级**: 850
- **功能**: `AntigravityEngine.check_shear_burst()`

---

## 参数注入机制

### 大运参数注入

#### 注入位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`
- 参数: `luck_pillar: str`

#### 注入方式
```python
# 大运节点创建
if luck_pillar and len(luck_pillar) >= 2:
    luck_stem = luck_pillar[0]
    luck_branch = luck_pillar[1]
    
    # 使用 spacetime.luckPillarWeight 作为基准权重
    dayun_branch_multiplier = physics_config.get('dayun_branch_multiplier', 1.2)
    dayun_stem_multiplier = physics_config.get('dayun_stem_multiplier', 0.8)
    dayun_branch_weight = luck_pillar_weight * dayun_branch_multiplier
    dayun_stem_weight = luck_pillar_weight * dayun_stem_multiplier
    
    # 创建大运节点
    luck_stem_node = GraphNode(...)
    luck_stem_node.dayun_weight = dayun_stem_weight
    luck_branch_node = GraphNode(...)
    luck_branch_node.dayun_weight = dayun_branch_weight
```

#### 影响范围
- 节点初始化阶段: 大运节点作为额外节点加入网络
- 能量传播阶段: 大运节点参与能量传播计算
- 格局判定阶段: 大运影响格局判定结果

### 流年参数注入

#### 注入位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`
- 参数: `year_pillar: str`

#### 注入方式
```python
# 流年节点创建
if year_pillar and len(year_pillar) >= 2:
    year_stem = year_pillar[0]
    year_branch = year_pillar[1]
    
    # 流年权重：流年是君，权力最大，但衰减极快
    annual_pillar_weight = spacetime_config.get('annualPillarWeight', 1.2)
    
    year_stem_node = GraphNode(...)
    year_stem_node.is_liunian = True  # 标记为流年节点
    year_stem_node.liunian_weight = annual_pillar_weight
```

#### 影响范围
- 节点初始化阶段: 流年节点作为动态引动层加入网络
- 能量传播阶段: 流年节点具有高初始能量但快速衰减
- 应期预测阶段: 流年触发特定事件的时间点

### 地理参数注入

#### 注入位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`
- 参数: `geo_modifiers: Dict[str, float]`

#### 注入方式
```python
# 地理修正系数
geo_config = spacetime_config.get('geo', {})
geo_modifiers = geo_modifiers or {}

# 融合时代修正：九运离火加持火
era_element = era_config.get('eraElement')
if era_element and era_element.lower() == 'fire':
    geo_modifiers['fire'] = geo_modifiers.get('fire', 1.0) * (1.0 + era_bonus)
    geo_modifiers['water'] = geo_modifiers.get('water', 1.0) * (1.0 - era_bonus * 0.5)

# 在地支藏干能量计算中应用
branch_node.hidden_stems_energy = self._calculate_hidden_stems_energy(
    branch_char, physics_config, geo_modifiers
)
```

#### 影响范围
- 节点初始化阶段: 地理修正影响地支藏干能量
- 能量传播阶段: 地理修正影响整体能量分布
- 格局判定阶段: 地理修正影响格局判定结果

### 时代参数注入

#### 注入位置
- `core/engine_graph/phase1_initialization.py`: `NodeInitializer.initialize_nodes()`
- 参数: `era_context: Dict[str, Any]`

#### 注入方式
```python
# 时代宏观修正
era_config = spacetime_config.get('era', {})
era_bonus = era_config.get('eraBonus', 0.2)
era_element = era_config.get('eraElement')

# 九紫离火运加持
if era_element and era_element.lower() == 'fire':
    geo_modifiers['fire'] *= (1.0 + era_bonus)
    geo_modifiers['water'] *= (1.0 - era_bonus * 0.5)
```

#### 影响范围
- 全局能量修正: 时代元素影响全局能量分布
- 格局判定: 时代元素影响格局判定结果

---

## 输入输出规范

### 统一输入接口

#### GraphNetworkEngine.initialize_nodes()
```python
def initialize_nodes(
    self,
    bazi: List[str],              # 八字列表 [年柱, 月柱, 日柱, 时柱]
    day_master: str,              # 日主天干
    luck_pillar: str = None,      # 大运干支 (可选)
    year_pillar: str = None,      # 流年干支 (可选)
    geo_modifiers: Dict[str, float] = None  # 地理修正 (可选)
) -> np.ndarray
```

#### GraphNetworkEngine.calculate_strength_score()
```python
def calculate_strength_score(
    self,
    day_master: str,              # 日主天干
    bazi: List[str] = None,        # 八字列表 (可选)
    luck_pillar: str = None,      # 大运干支 (可选)
    year_pillar: str = None,      # 流年干支 (可选)
    geo_context: Dict[str, Any] = None,  # 地理上下文 (可选)
    era_context: Dict[str, Any] = None   # 时代上下文 (可选)
) -> Dict[str, Any]
```

### 统一输出格式

#### 旺衰判定输出
```python
{
    'strength_score': float,        # 旺衰分数 (0-100)
    'strength_label': str,         # 旺衰标签 (Strong/Weak/Balanced/Follower/Special_Strong)
    'self_team_energy': float,     # 己方能量
    'total_energy': float,         # 总能量
    'dm_element': str,             # 日主元素
    'resource_element': str,       # 印星元素
    'special_pattern': str,         # 特殊格局
    'uncertainty': Dict[str, Any],  # 不确定性信息
    'net_force': Dict[str, float],  # 净力分析
    'svm_prediction': bool          # 是否使用SVM预测
}
```

#### 能量计算输出
```python
{
    'graph_data': {
        'nodes': List[Dict],           # 节点列表
        'adjacency_matrix': List[List[float]],  # 邻接矩阵
        'initial_energy': List[float],  # 初始能量
        'final_energy': List[float]     # 最终能量
    },
    'strength_score': float,
    'strength_label': str,
    'dm_element': str
}
```

---

## 总结与建议

### 系统优势

1. **模块化架构**: 所有算法以模块形式注册，便于管理和扩展
2. **规则驱动**: 物理规则以规则ID形式注册，支持动态加载
3. **参数可配置**: 所有参数通过配置文件管理，支持热加载
4. **三阶段架构**: 清晰的Phase 1/2/3分离，便于理解和维护
5. **参数注入机制**: 完善的大运/流年/地理/时代参数注入机制

### 发现的问题

1. **规则冲突处理**: 部分规则存在冲突关系（如PH_SAN_HE与PH_CHONG），需要明确冲突处理逻辑
2. **参数重复**: 部分参数在不同模块中重复定义，需要统一管理
3. **文档不完整**: 部分算法的详细实现文档缺失
4. **测试覆盖**: 部分模块的测试覆盖不足

### 改进建议

1. **统一参数管理**: 建立统一的参数管理机制，避免重复定义
2. **规则冲突处理**: 明确规则冲突的处理逻辑和优先级
3. **完善文档**: 为所有模块和规则补充详细的算法文档
4. **增强测试**: 为所有模块和规则编写单元测试和集成测试
5. **性能优化**: 对高频调用的算法进行性能优化

---

**报告生成时间**: 2025-01-XX  
**审查人员**: AI Assistant  
**版本**: 1.0

