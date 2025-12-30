# A-03 羊刃架杀格依赖关系分析报告

**分析日期**: 2025-12-30  
**分析目标**: 检查A-03格局使用的物理模块和算法，确认是否需要BAZI_FUNDAMENTAL和FRAMEWORK_UTILITIES的模块

---

## 📋 执行摘要

经过代码审查，发现A-03羊刃架杀格**已经隐式依赖**了BAZI_FUNDAMENTAL和FRAMEWORK_UTILITIES的模块，但**依赖关系未明确声明**，且部分实现使用了硬编码值而非配置参数。

### 核心发现

1. ✅ **已使用但未声明**：A-03使用了FRAMEWORK_UTILITIES的MOD_19（BaziParticleNexus）
2. ⚠️ **硬编码问题**：`compute_energy_flux`使用了硬编码权重，应该从`config_schema.py`读取
3. ⚠️ **缺少依赖声明**：A-03的`algorithm_implementation`未明确声明依赖的模块
4. ✅ **潜在依赖**：A-03可能需要BAZI_FUNDAMENTAL的合化动力学模块（MOD_05）

---

## 🔍 详细分析

### 1. A-03使用的算法实现路径

从`core/subjects/holographic_pattern/registry.json`的A-03定义：

```json
"algorithm_implementation": {
  "energy_calculation": {
    "function": "core.physics_engine.compute_energy_flux",
    "description": "读取任意十神的物理场强（支持月令加权）",
    "weights": {
      "base": 1.0,
      "month_resonance": 1.42,
      "rooting": 3.0,
      "generation": 1.0
    }
  },
  "interaction_damping": {
    "function": "core.physics_engine.calculate_interaction_damping",
    "description": "计算刑冲合害的拓扑结构与阻尼系数 lambda"
  },
  "integrity_alpha": {
    "function": "core.physics_engine.calculate_integrity_alpha",
    "description": "计算结构完整性alpha值（扣分制模型）"
  },
  "event_trigger": {
    "function": "core.physics_engine.check_trigger",
    "description": "检查事件触发条件（Day_Branch_Clash等）"
  }
}
```

### 2. 实际代码依赖分析

#### 2.1 `compute_energy_flux` 函数

**文件**: `core/physics_engine.py`

**当前实现**:
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
            'month_resonance': 1.42,  # 从config_schema.py获取
            'rooting': 3.0,
            'generation': 1.0
        }
    # ...
    # 使用 BaziParticleNexus.get_shi_shen()  # 来自FRAMEWORK_UTILITIES
    # 使用 SymbolicStarsEngine.YANG_REN_MAP  # 来自BAZI_FUNDAMENTAL或PATTERN_PHYSICS
```

**问题**:
- ⚠️ **硬编码权重**：`month_resonance: 1.42`和`rooting: 3.0`是硬编码的
- ⚠️ **应该使用**：`DEFAULT_FULL_ALGO_PARAMS['physics']['pillarWeights']['month']` (1.42)
- ⚠️ **应该使用**：`DEFAULT_FULL_ALGO_PARAMS['structure']['rootingWeight']` (1.0，但需要乘以饱和函数)
- ✅ **已使用**：`BaziParticleNexus`（来自FRAMEWORK_UTILITIES的MOD_19）
- ✅ **已使用**：`SymbolicStarsEngine`（来自BAZI_FUNDAMENTAL或PATTERN_PHYSICS）

#### 2.2 `check_clash` 和 `check_combination` 函数

**文件**: `core/physics_engine.py`

**当前实现**:
```python
CLASH_PAIRS = [
    ('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
    ('辰', '戌'), ('巳', '亥')
]

COMBINATION_PAIRS = [
    ('子', '丑'), ('寅', '亥'), ('卯', '戌'), ('辰', '酉'),
    ('巳', '申'), ('午', '未')
]

def check_clash(branch1: str, branch2: str) -> bool:
    """检查两个地支是否对冲"""
    return (branch1, branch2) in CLASH_PAIRS or (branch2, branch1) in CLASH_PAIRS

def check_combination(branch1: str, branch2: str) -> bool:
    """检查两个地支是否相合"""
    return (branch1, branch2) in COMBINATION_PAIRS or (branch2, branch1) in COMBINATION_PAIRS
```

**问题**:
- ⚠️ **硬编码关系表**：冲合关系是硬编码的
- ✅ **应该使用**：BAZI_FUNDAMENTAL的MOD_05（合化动力学）模块，它定义了完整的合化规则
- ⚠️ **缺少参数化**：没有使用`DEFAULT_FULL_ALGO_PARAMS['interactions']['branchEvents']`中的参数

#### 2.3 `calculate_interaction_damping` 函数

**文件**: `core/physics_engine.py`

**当前实现**:
```python
def calculate_interaction_damping(
    chart: List[str],
    month_branch: str,
    clash_branch: str,
    lambda_coefficients: Optional[Dict[str, float]] = None
) -> float:
    if lambda_coefficients is None:
        lambda_coefficients = {
            'resonance': 2.5,  # 硬编码
            'hard_landing': 1.8,  # 硬编码
            'damping': 1.2  # 硬编码
        }
    # ...
    # 使用 check_clash() 和 check_combination()
```

**问题**:
- ⚠️ **硬编码Lambda系数**：阻尼系数是硬编码的
- ⚠️ **应该使用**：BAZI_FUNDAMENTAL的MOD_05（合化动力学）模块中的阻尼参数
- ⚠️ **应该使用**：`DEFAULT_FULL_ALGO_PARAMS['interactions']['branchEvents']['clashDamping']` (0.4)

#### 2.4 `calculate_integrity_alpha` 函数

**文件**: `core/physics_engine.py`

**当前实现**:
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
    # 使用扣分制模型
    # 硬编码的扣分规则
```

**问题**:
- ⚠️ **硬编码扣分规则**：扣分项是硬编码的
- ⚠️ **应该使用**：BAZI_FUNDAMENTAL的MOD_06（微观应力）模块中的损伤模型
- ⚠️ **应该使用**：`DEFAULT_FULL_ALGO_PARAMS`中的相关参数

### 3. RegistryLoader 依赖

**文件**: `core/registry_loader.py`

**当前实现**:
```python
class RegistryLoader:
    def _calculate_with_transfer_matrix(self, ...):
        # 使用 BaziParticleNexus.get_shi_shen()  # 来自FRAMEWORK_UTILITIES
        # 使用 check_clash() 和 check_combination()  # 来自physics_engine
```

**问题**:
- ✅ **已使用**：`BaziParticleNexus`（来自FRAMEWORK_UTILITIES的MOD_19）
- ⚠️ **应该使用**：`BaziProfile`（来自FRAMEWORK_UTILITIES的MOD_19）来获取大运流年
- ⚠️ **应该使用**：`ConfigManager`（来自FRAMEWORK_UTILITIES的MOD_20）来读取配置参数

---

## 📊 依赖关系矩阵

| A-03使用的函数 | 当前依赖 | 应该依赖 | 状态 |
|--------------|---------|---------|------|
| `compute_energy_flux` | `BaziParticleNexus` (MOD_19) | ✅ 已使用 | ✅ |
| `compute_energy_flux` | `SymbolicStarsEngine` | ✅ 已使用 | ✅ |
| `compute_energy_flux` | `config_schema.py` 参数 | ⚠️ 硬编码 | ❌ |
| `check_clash` | 硬编码CLASH_PAIRS | MOD_05 (合化动力学) | ❌ |
| `check_combination` | 硬编码COMBINATION_PAIRS | MOD_05 (合化动力学) | ❌ |
| `calculate_interaction_damping` | 硬编码lambda | MOD_05 + config参数 | ❌ |
| `calculate_integrity_alpha` | 硬编码扣分规则 | MOD_06 (微观应力) | ❌ |
| `RegistryLoader` | `BaziParticleNexus` | ✅ 已使用 | ✅ |
| `RegistryLoader` | `BaziProfile` | ⚠️ 未使用 | ❌ |
| `RegistryLoader` | `ConfigManager` | ⚠️ 未使用 | ❌ |

---

## 🎯 建议改进

### 1. 明确声明依赖关系

在A-03的`algorithm_implementation`中添加`dependencies`字段：

```json
"algorithm_implementation": {
  "dependencies": {
    "FRAMEWORK_UTILITIES": [
      "MOD_19_BAZI_UTILITIES",  // BaziParticleNexus, BaziProfile
      "MOD_20_SYS_CONFIG"       // ConfigManager
    ],
    "BAZI_FUNDAMENTAL": [
      "MOD_05_TRIPLE",           // 合化动力学（冲合关系）
      "MOD_06_MICRO_STRESS"      // 微观应力（完整性alpha）
    ]
  },
  // ... 其他字段
}
```

### 2. 参数化硬编码值

#### 2.1 `compute_energy_flux` 改进

```python
def compute_energy_flux(
    chart: List[str],
    day_master: str,
    ten_god_type: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    from core.config_manager import ConfigManager
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    
    if weights is None:
        config = ConfigManager.load_config()
        physics_params = config.get('physics', DEFAULT_FULL_ALGO_PARAMS['physics'])
        structure_params = config.get('structure', DEFAULT_FULL_ALGO_PARAMS['structure'])
        
        weights = {
            'base': 1.0,
            'month_resonance': physics_params.get('pillarWeights', {}).get('month', 1.42),
            'rooting': structure_params.get('rootingWeight', 1.0),
            'generation': 1.0
        }
    # ... 其余逻辑
```

#### 2.2 `check_clash` 和 `check_combination` 改进

```python
def check_clash(branch1: str, branch2: str) -> bool:
    """检查两个地支是否对冲（从BAZI_FUNDAMENTAL的MOD_05获取）"""
    from core.logic_registry import LogicRegistry
    
    registry = LogicRegistry()
    mod_05 = registry.get_module_by_id("MOD_05_TRIPLE", theme_id="BAZI_FUNDAMENTAL")
    if mod_05:
        clash_rules = mod_05.get('pattern_data', {}).get('physics_kernel', {}).get('clash_rules', [])
        # 使用MOD_05定义的冲合规则
    else:
        # 回退到硬编码
        return (branch1, branch2) in CLASH_PAIRS or (branch2, branch1) in CLASH_PAIRS
```

#### 2.3 `calculate_interaction_damping` 改进

```python
def calculate_interaction_damping(
    chart: List[str],
    month_branch: str,
    clash_branch: str,
    lambda_coefficients: Optional[Dict[str, float]] = None
) -> float:
    from core.config_manager import ConfigManager
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    
    if lambda_coefficients is None:
        config = ConfigManager.load_config()
        interactions = config.get('interactions', DEFAULT_FULL_ALGO_PARAMS['interactions'])
        branch_events = interactions.get('branchEvents', {})
        
        lambda_coefficients = {
            'resonance': branch_events.get('clashPhase', 2.618),
            'hard_landing': branch_events.get('clashDamping', 0.4),
            'damping': branch_events.get('harmDamping', 0.2)
        }
    # ... 其余逻辑
```

### 3. 使用BaziProfile获取大运流年

在`RegistryLoader._calculate_with_transfer_matrix`中：

```python
def _calculate_with_transfer_matrix(self, ...):
    # 如果context中没有提供大运流年，尝试从BaziProfile获取
    from core.bazi_profile import BaziProfile
    
    if context and 'bazi_profile' in context:
        profile = context['bazi_profile']
        luck_pillar = profile.get_luck_pillar_at(year)
        year_pillar = profile.get_year_pillar_at(year)
    # ... 其余逻辑
```

---

## 📝 总结

### 当前状态（已更新）

1. ✅ **依赖关系已声明**：A-03的`algorithm_implementation`中已添加`dependencies`字段
2. ✅ **配置参数化**：`compute_energy_flux`已改为从`config_schema.py`读取参数
3. ✅ **模块化冲合关系**：`check_clash`和`check_combination`已改为使用MOD_03_TRANSFORM模块
4. ✅ **已使用FRAMEWORK_UTILITIES**：A-03已使用MOD_19（BaziParticleNexus）和MOD_20（ConfigManager）
5. ✅ **已使用BAZI_FUNDAMENTAL**：A-03已声明依赖MOD_03_TRANSFORM和MOD_06_MICRO_STRESS

### 已完成的改进

1. ✅ **依赖关系声明**（2025-12-30）：
   - 在A-03的`algorithm_implementation`中添加了`dependencies`字段
   - 声明了FRAMEWORK_UTILITIES依赖：MOD_19_BAZI_UTILITIES, MOD_20_SYS_CONFIG
   - 声明了BAZI_FUNDAMENTAL依赖：MOD_03_TRANSFORM, MOD_06_MICRO_STRESS

2. ✅ **配置参数化**（2025-12-30）：
   - `compute_energy_flux`已改为从`config_schema.py`的`DEFAULT_FULL_ALGO_PARAMS`读取参数
   - `month_resonance`从`physics.pillarWeights.month`读取
   - `rooting`从`structure.rootingWeight`读取，并应用饱和函数
   - 添加了配置读取失败时的回退机制

3. ✅ **模块化冲合关系**（2025-12-30）：
   - `check_clash`和`check_combination`已改为优先从MOD_03_TRANSFORM模块读取
   - 添加了`_get_clash_pairs_from_module()`和`_get_combination_pairs_from_module()`函数
   - 实现了模块加载失败时的回退机制

### 待改进项

1. **短期改进**：
   - 将`calculate_interaction_damping`改为使用配置参数
   - 将`calculate_integrity_alpha`改为使用BAZI_FUNDAMENTAL的MOD_06_MICRO_STRESS模块

2. **长期优化**：
   - 建立模块依赖关系图
   - 实现依赖注入机制
   - 添加依赖关系验证工具
   - 实现依赖关系的自动检查

---

**最后更新**: 2025-12-30  
**维护者**: Antigravity Core Team

