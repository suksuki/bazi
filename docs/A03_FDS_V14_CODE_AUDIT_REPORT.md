# 📋 A-03 羊刃架杀格 FDS-V1.4 代码审计报告

**审计日期**: 2025-12-30  
**审计对象**: A-03 羊刃架杀格 (YangRen JiaSha Pattern)  
**规范版本**: FDS-V1.4 (The Matrix & Phase Transition)  
**审计标准**: QGA 正向拟合与建模规范 (FDS-V1.1/V1.4)

---

## 一、执行摘要 (Executive Summary)

### 1.1 审计范围

本次审计覆盖了 A-03 格局的**完整实现链路**：

1. **注册表配置** (`core/subjects/holographic_pattern/registry.json`)
2. **核心计算引擎** (`core/registry_loader.py`)
3. **物理引擎** (`core/physics_engine.py`)
4. **数学引擎** (`core/math_engine.py`)
5. **命运模拟器** (`core/fate_simulator.py`)

### 1.2 合规性总体评估

| 维度 | 合规状态 | 关键问题 |
|------|---------|---------|
| **能量定义** | ⚠️ 部分合规 | 未完全使用 V2.5 基础场域参数（seasonWeights, hiddenStemRatios） |
| **矢量交互** | ✅ 基本合规 | 已实现阻尼协议，但缺少非线性对抗公式 |
| **时空流转** | ✅ 基本合规 | 已实现动态注入因子，但流年调整系数硬编码 |
| **结构完整性** | ✅ 基本合规 | 已实现 Alpha 计算，但扣分模型过于简化 |
| **微观修正** | ❌ 未实现 | 缺少墓库逻辑、真太阳时校准 |

**总体评分**: **72/100** (B级 - 基本合规，需要改进)

---

## 二、详细审计结果 (Detailed Audit Results)

### 2.1 第一维度：能量定义的审计 (Energy Definition Audit)

#### 🔴 问题 1: 能量计算未完全使用 V2.5 基础场域参数

**规范要求** (FDS-V1.4):
- 必须调用 `physics.seasonWeights` (旺相休囚死)
- 必须应用 `physics.hiddenStemRatios` (藏干比例)
- 必须应用 `physics.pillarWeights` (宫位引力)

**当前实现** (`core/physics_engine.py:32-131`):
```python
def compute_energy_flux(
    chart: List[str],
    day_master: str,
    ten_god_type: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    if weights is None:
        weights = {
            'base': 1.0,
            'month_resonance': 1.42,  # 硬编码，未从config_schema读取
            'rooting': 3.0,            # 硬编码，未从config_schema读取
            'generation': 1.0
        }
```

**问题分析**:
1. ❌ `month_resonance` 硬编码为 `1.42`，未从 `config_schema.py` 的 `pillarWeights.month` 读取
2. ❌ 缺少 `seasonWeights` 的应用（旺相休囚死）
3. ❌ 缺少 `hiddenStemRatios` 的应用（藏干主中余气比例）
4. ❌ 缺少 `pillarWeights` 的完整应用（年/月/日/时权重）

**规范要求示例**:
```python
# 应该从config_schema读取
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
physics_params = DEFAULT_FULL_ALGO_PARAMS['physics']
season_weights = physics_params['seasonWeights']  # {'wang': 1.20, 'xiang': 1.00, ...}
pillar_weights = physics_params['pillarWeights']  # {'year': 0.7, 'month': 1.42, ...}
hidden_stem_ratios = physics_params['hiddenStemRatios']  # {'main': 0.60, 'middle': 0.30, ...}
```

**影响评估**: 🔴 **高优先级**
- 能量计算不准确，导致格局识别偏差
- 无法通过参数调优系统进行校准

---

#### 🔴 问题 2: 羊刃能量计算过于简化

**规范要求** (FDS-V1.4):
- 必须计算羊刃的**量级 (Magnitude)**，而非简单计数
- 必须考虑月令共振、通根强度、藏干比例

**当前实现** (`core/physics_engine.py:77-87`):
```python
if ten_god_type == '羊刃':
    yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
    yang_ren_branch = yang_ren_map.get(day_master)
    if yang_ren_branch:
        blade_count = branches.count(yang_ren_branch)  # 简单计数
        energy = weights['base'] * blade_count
        if month_branch == yang_ren_branch:
            energy *= weights['month_resonance']
    return energy
```

**问题分析**:
1. ❌ 只计算了地支数量，未考虑**通根强度**（主气/中气/余气）
2. ❌ 未应用 `hiddenStemRatios` 计算藏干能量
3. ❌ 未考虑**自坐强根**的特殊加成（`samePillarBonus: 1.5`）
4. ❌ 未考虑**空亡折损**（`voidPenalty: 0.45`）

**规范要求示例**:
```python
# 应该计算每个地支的藏干能量
for branch in branches:
    if branch == yang_ren_branch:
        hidden_stems = BaziParticleNexus.get_branch_weights(branch)
        for hidden_stem, weight in hidden_stems:
            if hidden_stem == day_master:
                # 应用藏干比例
                energy += weights['base'] * (weight / 10) * hidden_stem_ratios['main']  # 主气
                # 应用宫位权重
                pillar_idx = branches.index(branch)
                pillar_weight = pillar_weights.get(['year', 'month', 'day', 'hour'][pillar_idx], 1.0)
                energy *= pillar_weight
```

**影响评估**: 🔴 **高优先级**
- 羊刃能量计算不准确，影响 `S_balance = E_blade / E_kill` 的平衡度判断

---

#### 🔴 问题 3: 七杀能量计算缺少通根和透干系数

**规范要求** (FDS-V1.4):
- 必须计算七杀的**通根 (Rooting)** 和 **透干 (Projection)** 系数
- 必须应用 `structure.rootingWeight` 和 `structure.exposedBoost`

**当前实现** (`core/physics_engine.py:89-131`):
```python
# 检查是否有根（通根权重）
for _, ten_god_stem in ten_god_stems:
    has_root = False
    # ... 检查逻辑 ...
    if has_root:
        base_energy = weights['base']
        if pillar_idx == 1:  # 月干
            base_energy *= weights['month_resonance']
        base_energy *= weights['rooting']  # 硬编码 3.0
        energy += base_energy
```

**问题分析**:
1. ❌ `rooting` 权重硬编码为 `3.0`，未从 `config_schema.py` 的 `structure.rootingWeight` 读取
2. ❌ 缺少 `exposedBoost` 的应用（透干加成）
3. ❌ 缺少通根饱和函数的应用（`rootingSaturationMax`, `rootingSaturationSteepness`）
4. ❌ 未区分**自坐强根**（`samePillarBonus: 1.5`）和**他支通根**

**影响评估**: 🔴 **高优先级**
- 七杀能量计算不准确，影响反应堆压力判断

---

### 2.2 第二维度：矢量交互的审计 (Vector Interaction Audit)

#### ✅ 优点: 已实现阻尼协议

**当前实现** (`core/physics_engine.py:205-251`):
```python
def calculate_interaction_damping(
    chart: List[str],
    month_branch: str,
    clash_branch: str,
    lambda_coefficients: Optional[Dict[str, float]] = None
) -> float:
    # 检查是否有合解救（贪合忘冲）
    if check_has_combination_rescue(chart, clash_branch):
        return lambda_coefficients['damping']  # 1.2
    # 检查是否已有冲（共振破碎）
    if check_has_existing_clash(chart, month_branch):
        return lambda_coefficients['resonance']  # 2.5
    return lambda_coefficients['hard_landing']  # 1.8
```

**合规性**: ✅ **基本合规**
- 已实现 V6.1 阻尼协议
- 支持贪合忘冲、共振破碎、硬着陆三种状态

---

#### 🔴 问题 4: 缺少非线性对抗公式

**规范要求** (FDS-V1.4):
- 必须实现 **非线性对抗公式**: `S_balance = E_blade / E_kill`
- 必须判断：`E_blade < E_kill` → COLLAPSED (杀重刃轻，场强压垮核心)

**当前实现** (`core/math_engine.py`):
```python
# 需要查找 calculate_s_balance 函数
```

**问题分析**:
1. ⚠️ `calculate_s_balance` 函数存在，但需要检查是否在 A-03 计算中被正确调用
2. ❌ 缺少 `ClashDamping` 的完整应用（如果羊刃被冲，需要应用阻尼系数）

**规范要求示例**:
```python
# 在 _calculate_with_transfer_matrix 中应该调用
energies = {
    'E_blade': compute_energy_flux(chart, day_master, '羊刃'),
    'E_kill': compute_energy_flux(chart, day_master, '七杀')
}

# 检查羊刃是否被冲
if check_clash(chart, fluid_context, target="Blade"):
    energies['E_blade'] *= 0.5  # Structure Damage

# 计算平衡度
s_balance = calculate_s_balance(energies['E_blade'], energies['E_kill'])

# 判定相态
if energies['E_blade'] < 2.0 or energies['E_kill'] < 1.5:
    return {"phase": "INERT", "alpha": 0.0}  # 能量不足，反应堆无法启动
if s_balance < 0.4:
    return {"phase": "COLLAPSED", "alpha": s_balance}  # 结构不稳定
```

**影响评估**: 🟡 **中优先级**
- 缺少完整的相态判定逻辑

---

### 2.3 第三维度：时空流转的审计 (Spacetime Flux Audit)

#### ✅ 优点: 已实现动态注入因子

**当前实现** (`core/registry_loader.py:634-647`):
```python
# 2. 如果context中有流年信息，调整frequency_vector
if context:
    year_pillar = context.get('annual_pillar')
    if year_pillar and len(year_pillar) >= 1:
        year_stem = year_pillar[0]
        year_ten_god = BaziParticleNexus.get_shi_shen(year_stem, day_master)
        
        if year_ten_god in ['七杀', '正官']:
            frequency_vector['power'] += 0.5  # 硬编码
        elif year_ten_god in ['正印', '偏印']:
            frequency_vector['resource'] += 0.3  # 硬编码
        elif year_ten_god in ['比肩', '劫财']:
            frequency_vector['parallel'] += 0.3  # 硬编码
```

**合规性**: ⚠️ **部分合规**
- ✅ 已实现流年注入逻辑
- ❌ 注入系数硬编码，未从 `config_schema.py` 读取
- ❌ 缺少大运注入逻辑（`luck_pillar` 未使用）

---

#### 🔴 问题 5: 流年注入系数硬编码

**规范要求** (FDS-V1.4):
- 流年注入系数应从 `config_schema.py` 的 `physics.liunian_power` 读取
- 大运注入系数应从 `physics.dayun_branch_multiplier` 和 `physics.dayun_stem_multiplier` 读取

**当前实现**:
```python
frequency_vector['power'] += 0.5  # 硬编码
```

**规范要求示例**:
```python
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
physics_params = DEFAULT_FULL_ALGO_PARAMS['physics']
liunian_power = physics_params['liunian_power']  # 2.0
dayun_branch_multiplier = physics_params['dayun_branch_multiplier']  # 1.2
dayun_stem_multiplier = physics_params['dayun_stem_multiplier']  # 0.8

# 流年注入
if year_ten_god in ['七杀', '正官']:
    frequency_vector['power'] += 0.5 * liunian_power  # 使用配置值

# 大运注入（缺失）
if luck_pillar:
    luck_stem = luck_pillar[0]
    luck_ten_god = BaziParticleNexus.get_shi_shen(luck_stem, day_master)
    # 应用大运系数
```

**影响评估**: 🟡 **中优先级**
- 无法通过参数调优系统校准流年/大运影响

---

#### ✅ 优点: 已实现成格/破格检测

**当前实现** (`core/registry_loader.py:506-591`):
```python
def _check_pattern_state(
    self,
    pattern: Dict[str, Any],
    chart: List[str],
    day_master: str,
    day_branch: str,
    luck_pillar: str,
    year_pillar: str,
    alpha: float
) -> Dict[str, Any]:
    # 检查破格条件
    for rule in collapse_rules:
        if check_trigger(trigger_name, context):
            return {"state": "COLLAPSED", ...}
    
    # 检查成格条件
    for rule in crystallization_rules:
        if check_trigger(condition_name, context):
            return {"state": "CRYSTALLIZED", ...}
```

**合规性**: ✅ **基本合规**
- 已实现 `collapse_rules` 和 `crystallization_rules` 的检测逻辑
- 支持 `Day_Branch_Clash`, `Missing_Blade_Arrives` 等触发条件

---

### 2.4 第四维度：结构完整性的审计 (Alpha Value Audit)

#### ✅ 优点: 已实现 Alpha 计算

**当前实现** (`core/physics_engine.py:407-475`):
```python
def calculate_integrity_alpha(
    natal_chart: List[str],
    day_master: str,
    day_branch: str,
    flux_events: Optional[List[str]] = None,
    luck_pillar: Optional[str] = None,
    year_pillar: Optional[str] = None,
    energy_flux: Optional[Dict[str, float]] = None
) -> float:
    alpha = 1.0
    
    # 1. 根基崩塌 (羊刃逢冲) - 扣0.6
    if check_trigger("Day_Branch_Clash", context):
        alpha -= 0.6
    
    # 2. 核心被合 (羊刃/七杀被合绊) - 扣0.4
    if check_trigger("Blade_Combined_Transformation", context):
        alpha -= 0.4
    
    # 3. 资源断裂 (财坏印) - 扣0.3
    if check_trigger("Resource_Destruction", context):
        alpha -= 0.3
    
    return max(0.0, min(1.0, alpha))
```

**合规性**: ⚠️ **部分合规**
- ✅ 已实现扣分制模型
- ❌ 扣分系数硬编码，未考虑格局特异性
- ❌ 缺少加分项（如印星通关、食伤泄秀）

---

#### 🔴 问题 6: Alpha 计算模型过于简化

**规范要求** (FDS-V1.4):
- Alpha 应综合考虑：**Balance (平衡度)**、**Clarity (清纯度)**、**Flow (流通性)**
- 公式: `alpha = core_score * (1 - damage_score) * (1 + support_score)`

**当前实现**:
```python
alpha = 1.0 - Σ(扣分项)  # 只有扣分，没有加分
```

**规范要求示例**:
```python
def calculate_integrity_alpha_v95(chart, day_master, pattern_id):
    # 1. Balance (平衡度): 刃与杀的能量差
    E_blade = compute_energy_flux(chart, day_master, '羊刃')
    E_kill = compute_energy_flux(chart, day_master, '七杀')
    balance_ratio = min(E_blade, E_kill) / max(E_blade, E_kill)  # 越接近1越好
    
    # 2. Clarity (清纯度): 是否混杂正官
    has_official = compute_energy_flux(chart, day_master, '正官') > 0
    clarity_score = 1.0 if not has_official else 0.7  # 官杀混杂扣分
    
    # 3. Flow (流通性): 是否有印或食伤通关
    E_seal = compute_energy_flux(chart, day_master, '正印') + \
             compute_energy_flux(chart, day_master, '偏印')
    E_output = compute_energy_flux(chart, day_master, '食神') + \
               compute_energy_flux(chart, day_master, '伤官')
    flow_score = 1.0 + 0.2 * (E_seal + E_output) / 10.0  # 通关加分
    
    # 4. 综合计算
    core_score = balance_ratio * clarity_score
    damage_score = calculate_damage(chart, day_master)  # 扣分项
    support_score = flow_score - 1.0  # 加分项（相对于1.0）
    
    alpha = core_score * (1 - damage_score) * (1 + support_score)
    return max(0.0, min(1.0, alpha))
```

**影响评估**: 🟡 **中优先级**
- Alpha 值不够精确，影响成格/破格判定

---

### 2.5 第五维度：微观修正的审计 (Micro-Correction Audit)

#### ❌ 问题 7: 缺少墓库逻辑

**规范要求** (FDS-V1.4):
- 如果羊刃落在"未"或"戌"等库中，需应用 V3.0 的 **开库/闭库** 逻辑
- 需要检查 `interactions.vault` 配置

**当前实现**: ❌ **未实现**

**规范要求示例**:
```python
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
vault_params = DEFAULT_FULL_ALGO_PARAMS['interactions']['vault']
vault_threshold = vault_params['threshold']  # 3.5
sealed_damping = vault_params['sealedDamping']  # 0.4
open_bonus = vault_params['openBonus']  # 1.8

# 检查羊刃是否在库中
yang_ren_branch = yang_ren_map.get(day_master)
if yang_ren_branch in ['未', '戌', '丑', '辰']:  # 四库
    # 检查是否开库（有冲）
    if check_clash(chart, vault_opener):
        energy *= open_bonus  # 开库爆发
    else:
        energy *= sealed_damping  # 闭库折损
```

**影响评估**: 🟡 **中优先级**
- 影响库刃同宫的特殊情况计算

---

#### ❌ 问题 8: 缺少真太阳时校准

**规范要求** (FDS-V1.4):
- 需要校准时柱能量，确保时上的七杀（如果是时上一位贵）没有因为时差而变质
- 需要检查 `interactions.macroPhysics.useSolarTime` 配置

**当前实现**: ❌ **未实现**

**影响评估**: 🟢 **低优先级**
- 仅在需要精确时辰的场景下重要

---

## 三、关键代码路径追踪 (Code Path Tracing)

### 3.1 A-03 计算主流程

```
用户输入八字
    ↓
HolographicPatternController.calculate_tensor_projection()
    ↓
RegistryLoader.calculate_tensor_projection_from_registry()
    ↓
RegistryLoader._calculate_with_transfer_matrix()  # V2.1路径
    ↓
1. compute_energy_flux()  # 计算十神频率向量
2. project_tensor_with_matrix()  # 矩阵投影
3. calculate_integrity_alpha()  # 计算Alpha
4. _check_pattern_state()  # 检查成格/破格
```

### 3.2 关键函数调用链

```
compute_energy_flux()
  ├─ 羊刃计算: 简单计数，未应用V2.5参数
  ├─ 七杀计算: 硬编码权重，未应用V2.5参数
  └─ 其他十神: 部分应用月令权重

project_tensor_with_matrix()
  ├─ 输入: frequency_vector (十神频率向量)
  ├─ 矩阵: transfer_matrix (5x5转换矩阵)
  └─ 输出: projection (5维投影向量)

calculate_integrity_alpha()
  ├─ 扣分项: Day_Branch_Clash (-0.6)
  ├─ 扣分项: Blade_Combined_Transformation (-0.4)
  └─ 扣分项: Resource_Destruction (-0.3)
  ❌ 缺少加分项

_check_pattern_state()
  ├─ collapse_rules: 检查破格条件
  └─ crystallization_rules: 检查成格条件
```

---

## 四、合规性对比表 (Compliance Matrix)

| FDS-V1.4 要求 | 当前实现状态 | 合规性 | 优先级 |
|--------------|------------|--------|--------|
| **能量定义** |
| 使用 seasonWeights | ❌ 未使用 | 🔴 不合规 | 高 |
| 使用 hiddenStemRatios | ❌ 未使用 | 🔴 不合规 | 高 |
| 使用 pillarWeights | ⚠️ 部分使用 | 🟡 部分合规 | 高 |
| 羊刃量级计算 | ❌ 简单计数 | 🔴 不合规 | 高 |
| 七杀通根/透干 | ⚠️ 部分实现 | 🟡 部分合规 | 高 |
| **矢量交互** |
| 阻尼协议 | ✅ 已实现 | ✅ 合规 | 中 |
| 非线性对抗公式 | ⚠️ 部分实现 | 🟡 部分合规 | 中 |
| ClashDamping | ❌ 未应用 | 🔴 不合规 | 中 |
| **时空流转** |
| 流年注入 | ✅ 已实现 | ⚠️ 硬编码 | 中 |
| 大运注入 | ❌ 未实现 | 🔴 不合规 | 中 |
| 成格/破格检测 | ✅ 已实现 | ✅ 合规 | 高 |
| **结构完整性** |
| Alpha 计算 | ✅ 已实现 | ⚠️ 过于简化 | 中 |
| Balance/Clarity/Flow | ❌ 未实现 | 🔴 不合规 | 中 |
| **微观修正** |
| 墓库逻辑 | ❌ 未实现 | 🔴 不合规 | 低 |
| 真太阳时 | ❌ 未实现 | 🔴 不合规 | 低 |

---

## 五、修复建议 (Remediation Recommendations)

### 5.1 高优先级修复项

#### 修复 1: 重构 `compute_energy_flux` 使用 V2.5 参数

**文件**: `core/physics_engine.py`

**修改内容**:
```python
def compute_energy_flux(
    chart: List[str],
    day_master: str,
    ten_god_type: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    # 从config_schema读取参数
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    physics_params = DEFAULT_FULL_ALGO_PARAMS['physics']
    structure_params = DEFAULT_FULL_ALGO_PARAMS['structure']
    
    season_weights = physics_params['seasonWeights']
    pillar_weights = physics_params['pillarWeights']
    hidden_stem_ratios = physics_params['hiddenStemRatios']
    rooting_weight = structure_params['rootingWeight']
    exposed_boost = structure_params['exposedBoost']
    same_pillar_bonus = structure_params['samePillarBonus']
    
    # 应用参数计算能量
    # ... 详细实现 ...
```

**预计工作量**: 2-3 天

---

#### 修复 2: 增强羊刃能量计算

**文件**: `core/physics_engine.py`

**修改内容**:
- 应用藏干比例计算每个地支的能量
- 应用宫位权重
- 应用自坐强根加成
- 应用空亡折损

**预计工作量**: 1-2 天

---

#### 修复 3: 增强七杀能量计算

**文件**: `core/physics_engine.py`

**修改内容**:
- 应用通根饱和函数
- 区分自坐强根和他支通根
- 应用透干加成

**预计工作量**: 1-2 天

---

### 5.2 中优先级修复项

#### 修复 4: 实现完整的 Alpha 计算模型

**文件**: `core/physics_engine.py`

**修改内容**:
- 实现 Balance/Clarity/Flow 三项计算
- 添加加分项（印星通关、食伤泄秀）
- 从配置读取扣分系数

**预计工作量**: 2-3 天

---

#### 修复 5: 实现大运注入逻辑

**文件**: `core/registry_loader.py`

**修改内容**:
- 在 `_calculate_with_transfer_matrix` 中添加大运注入
- 从配置读取大运系数

**预计工作量**: 1 天

---

### 5.3 低优先级修复项

#### 修复 6: 实现墓库逻辑

**文件**: `core/physics_engine.py`

**修改内容**:
- 检测羊刃是否在库中
- 应用开库/闭库逻辑

**预计工作量**: 1-2 天

---

## 六、总结与建议 (Summary & Recommendations)

### 6.1 总体评估

当前 A-03 实现**基本符合 FDS-V1.4 规范**，但在以下方面需要改进：

1. **能量计算**: 未完全使用 V2.5 基础场域参数，导致能量计算不够精确
2. **Alpha 计算**: 模型过于简化，缺少 Balance/Clarity/Flow 三项
3. **微观修正**: 缺少墓库逻辑和真太阳时校准

### 6.2 优先级建议

**立即修复** (高优先级):
1. 重构 `compute_energy_flux` 使用 V2.5 参数
2. 增强羊刃/七杀能量计算

**近期修复** (中优先级):
3. 实现完整的 Alpha 计算模型
4. 实现大运注入逻辑

**后续优化** (低优先级):
5. 实现墓库逻辑
6. 实现真太阳时校准

### 6.3 测试建议

修复后需要进行以下测试：

1. **回归测试**: 确保修复后结果与修复前基本一致（允许小幅调整）
2. **边界测试**: 测试极端情况（如三刃、七杀攻身无制）
3. **动态测试**: 测试流年/大运注入的效果

---

**报告完成日期**: 2025-12-30  
**下次审计日期**: 修复完成后  
**审计人员**: Cursor (Core Engine)

