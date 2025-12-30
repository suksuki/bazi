# 八字基础规则主题对齐 HOLOGRAPHIC_PATTERN 重构指南

**重构日期**: 2025-12-30  
**对齐目标**: HOLOGRAPHIC_PATTERN (张量全息格局主题)  
**重构标准**: QGA-HR V2.0

---

## 一、重构目标

将 **BAZI_FUNDAMENTAL** (八字基础规则主题) 的所有模块重构为与 **HOLOGRAPHIC_PATTERN** 相同的注册表结构，包括：

1. ✅ **注册表结构**: 创建独立的 `core/subjects/bazi_fundamental/registry.json`
2. ✅ **语义种子**: 为每个模块添加 `semantic_seed` 字段
3. ✅ **物理内核**: 为每个模块添加 `physics_kernel` 字段
4. ✅ **特征锚点**: 为每个模块添加 `feature_anchors` 字段
5. ✅ **动态状态**: 为每个模块添加 `dynamic_states` 字段
6. ✅ **张量算子**: 为每个模块添加 `tensor_operator` 字段
7. ✅ **算法实现**: 为每个模块添加 `algorithm_implementation` 字段（包含所有引擎函数路径）
8. ✅ **动力学演化**: 为每个模块添加 `kinetic_evolution` 字段
9. ✅ **审计轨迹**: 为每个模块添加 `audit_trail` 字段

---

## 二、已完成工作

### 2.1 基础结构

- ✅ 创建 `core/subjects/bazi_fundamental/registry.json`
- ✅ 添加 metadata 和 theme 定义
- ✅ 完成第一个模块 `MOD_00_SUBSTRATE` 的完整重构（作为示例）

### 2.2 系统集成

- ✅ 更新 `core/logic_manifest.json`，添加 `registry_path` 引用
- ✅ 更新 `core/registry_loader.py`，支持通过 `theme_id` 加载 bazi_fundamental 注册表

---

## 三、模块结构模板

每个模块应包含以下完整结构（参考 `MOD_00_SUBSTRATE`）：

```json
{
  "MOD_XX_NAME": {
    "id": "MOD_XX_NAME",
    "name": "模块中文名称",
    "name_cn": "模块中文名称",
    "name_en": "Module English Name",
    "category": "CATEGORY",
    "subject_id": "MOD_XX_NAME",
    "icon": "图标",
    "version": "版本号",
    "active": true,
    "created_at": "2025-12-30",
    "description": "模块描述",
    
    "semantic_seed": {
      "description": "语义种子描述",
      "physical_image": "物理图像描述",
      "source": "来源",
      "updated_at": "2025-12-30",
      "classical_meaning": {
        "关键概念1": "解释1",
        "关键概念2": "解释2"
      }
    },
    
    "physics_kernel": {
      "description": "核心物理参数与计算逻辑",
      "核心公式1": {
        "formula": "公式",
        "description": "描述",
        "parameters": {
          "参数1": 值1
        }
      }
    },
    
    "feature_anchors": {
      "description": "基于物理模型的特征锚点",
      "standard_centroid": {
        "description": "标准稳定态",
        "vector": {
          "指标1": 值1,
          "指标2": 值2
        },
        "match_threshold": 0.7,
        "perfect_threshold": 0.85
      },
      "singularity_centroids": [
        {
          "sub_id": "MOD_XX_VARIANT",
          "description": "变体描述",
          "vector": {...},
          "match_threshold": 0.8,
          "risk_level": "CRITICAL"
        }
      ]
    },
    
    "dynamic_states": {
      "description": "动态相变规则",
      "collapse_rules": [
        {
          "trigger": "触发条件",
          "action": "动作",
          "description": "描述"
        }
      ],
      "crystallization_rules": [
        {
          "condition": "条件",
          "action": "动作",
          "description": "描述"
        }
      ]
    },
    
    "tensor_operator": {
      "weights": {
        "指标1": 权重1,
        "指标2": 权重2
      },
      "activation_function": {
        "type": "函数类型",
        "description": "描述",
        "parameters": {...}
      },
      "normalized": true,
      "core_equation": "核心公式",
      "equation_description": "公式描述"
    },
    
    "algorithm_implementation": {
      "算法1": {
        "function": "core.模块.函数路径",
        "description": "算法描述",
        "parameters": {...}
      },
      "算法2": {...},
      "registry_loader": {
        "class": "core.registry_loader.RegistryLoader",
        "description": "读取本 JSON 配置并驱动上述引擎"
      },
      "paths": {
        "算法1": "core.模块.函数路径",
        "算法2": "core.模块.函数路径"
      }
    },
    
    "kinetic_evolution": {
      "trigger_operators": [...],
      "gain_operators": [...],
      "geo_damping": 1.0,
      "dynamic_simulation": {
        "scenario": "场景描述",
        "description": "描述",
        "simulation_samples": 数量
      }
    },
    
    "audit_trail": {
      "coverage_rate": 覆盖率,
      "hit_rate": 命中率,
      "data_selection_criteria": {...},
      "version_history": [...],
      "fds_fitting": {
        "status": "completed",
        "completed_at": "日期",
        "version": "版本"
      }
    },
    
    "linked_rules": ["规则ID1", "规则ID2"],
    "linked_metrics": ["指标1", "指标2"],
    "goal": "目标描述",
    "outcome": "成果描述",
    "layer": "层级",
    "priority": 优先级,
    "status": "ACTIVE",
    "origin_trace": ["来源1"],
    "fusion_type": "类型",
    "class": "实现类路径"
  }
}
```

---

## 四、待重构模块列表

### 4.1 核心模块（高优先级）

| 模块ID | 模块名称 | 状态 | 说明 |
|--------|---------|------|------|
| `MOD_00_SUBSTRATE` | 晶格基底与因果涌现 | ✅ | 已完成（示例） |
| `MOD_01_TRIPLE` | 大一统三元动力 | ⏳ | 待重构 |
| `MOD_02_SUPER` | 极高位格局共振 | ⏳ | 待重构 |
| `MOD_03_TRANSFORM` | 合化动力学 | ⏳ | 待重构 |
| `MOD_04_STABILITY` | 刑害干涉动力学 | ⏳ | 待重构 |

### 4.2 时空模块

| 模块ID | 模块名称 | 状态 | 说明 |
|--------|---------|------|------|
| `MOD_14_TIME_SPACE_INTERFERENCE` | 多维时空场耦合 | ⏳ | 待重构 |
| `MOD_15_STRUCTURAL_VIBRATION` | 结构振动传导 | ⏳ | 待重构 |
| `MOD_16_TEMPORAL_SHUNTING` | 应期预测与行为干预 | ⏳ | 待重构 |

### 4.3 应用模块

| 模块ID | 模块名称 | 状态 | 说明 |
|--------|---------|------|------|
| `MOD_05_WEALTH` | 财富流体力学 | ⏳ | 待重构 |
| `MOD_06_RELATIONSHIP` | 情感引力场 | ⏳ | 待重构 |
| `MOD_07_LIFEPATH` | 个人生命轨道仪 | ⏳ | 待重构 |

### 4.4 基础模块

| 模块ID | 模块名称 | 状态 | 说明 |
|--------|---------|------|------|
| `MOD_09_COMBINATION` | 天干合化相位 | ⏳ | 待重构 |
| `MOD_10_RESONANCE` | 干支通根增益 | ⏳ | 待重构 |
| `MOD_11_GRAVITY` | 宫位引力场 | ⏳ | 待重构 |
| `MOD_12_INERTIA` | 时空场惯性 | ⏳ | 待重构 |
| `MOD_17_STELLAR_INTERACTION` | 星辰相干与喜剧真言 | ⏳ | 待重构 |
| `MOD_18_BASE_APP` | 基础应用与全局工具 | ⏳ | 待重构 |

---

## 五、算法实现路径映射

### 5.1 核心引擎函数

| 功能 | 函数路径 | 说明 |
|------|---------|------|
| 能量计算 | `core.physics_engine.compute_energy_flux` | 计算十神能量 |
| 交互阻尼 | `core.physics_engine.calculate_interaction_damping` | 计算刑冲合害阻尼 |
| 张量投影 | `core.math_engine.project_tensor_with_matrix` | 5x5矩阵投影 |
| 余弦相似度 | `core.math_engine.calculate_cosine_similarity` | 格局识别 |
| 完整性Alpha | `core.physics_engine.calculate_integrity_alpha` | 结构完整性 |
| 触发检查 | `core.physics_engine.check_trigger` | 事件触发条件 |

### 5.2 专用引擎类

| 模块 | 引擎类路径 | 说明 |
|------|-----------|------|
| MOD_00_SUBSTRATE | `core.trinity.core.engines.quantum_dispersion.QuantumDispersionEngine` | 量子弥散引擎 |
| MOD_02_SUPER | `core.trinity.core.engines.super_structure_resonance_v13_7.SuperStructureResonanceEngineV13_7` | 极高位格局共振引擎 |
| MOD_05_WEALTH | `core.trinity.core.engines.wealth_fluid_v13_7.WealthFluidEngineV13_7` | 财富流体力学引擎 |
| MOD_06_RELATIONSHIP | `core.trinity.core.engines.relationship_gravity_v13_7.RelationshipGravityEngineV13_7` | 情感引力场引擎 |
| MOD_07_LIFEPATH | `core.trinity.core.engines.lifepath_resampling_v13_7.LifepathResamplingEngineV13_7` | 生命轨道引擎 |
| MOD_11_GRAVITY | `core.trinity.core.engines.pillar_gravity_v13_7.PillarGravityEngineV13_7` | 宫位引力场引擎 |
| MOD_12_INERTIA | `core.trinity.core.engines.spacetime_inertia_v13_7.SpacetimeInertiaEngineV13_7` | 时空场惯性引擎 |
| MOD_16_TEMPORAL_SHUNTING | `core.trinity.core.engines.temporal_prediction_v13_7.TemporalPredictionEngineV13_7` | 应期预测引擎 |
| MOD_17_STELLAR_INTERACTION | `core.trinity.core.engines.stellar_coherence_v13_7.StellarCoherenceEngineV13_7` | 星辰相干引擎 |
| MOD_18_BASE_APP | `core.trinity.core.engines.global_interference_v13_7.GlobalInterferenceEngineV13_7` | 全局干涉引擎 |

---

## 六、重构步骤

### 6.1 单个模块重构流程

1. **收集信息**
   - 从 `logic_manifest.json` 获取模块基本信息
   - 查找对应的引擎类路径
   - 确定核心算法函数路径

2. **创建语义种子**
   - 定义物理图像
   - 解释核心概念

3. **定义物理内核**
   - 列出核心公式
   - 定义参数

4. **设置特征锚点**
   - 定义标准质心
   - 定义奇点质心（如果有）

5. **定义动态状态**
   - 崩塌规则
   - 晶体化规则

6. **配置张量算子**
   - 权重分配
   - 激活函数
   - 核心公式

7. **映射算法实现**
   - 列出所有使用的引擎函数
   - 提供函数路径和参数

8. **添加动力学演化**
   - 触发算子
   - 增益算子
   - 动态仿真

9. **记录审计轨迹**
   - 版本历史
   - FDS拟合状态

---

## 七、验证检查清单

重构完成后，检查以下项目：

- [ ] JSON 语法正确（使用 `python3 -m json.tool` 验证）
- [ ] 所有必需字段都已填写
- [ ] `algorithm_implementation` 中的函数路径正确
- [ ] `feature_anchors` 的向量维度一致
- [ ] `linked_rules` 和 `linked_metrics` 与模块功能匹配
- [ ] `class` 字段指向正确的引擎类
- [ ] `audit_trail` 包含版本历史

---

## 八、使用示例

### 8.1 加载注册表

```python
from core.registry_loader import RegistryLoader

# 通过 theme_id 加载
loader = RegistryLoader(theme_id="BAZI_FUNDAMENTAL")

# 获取模块
module = loader.get_pattern("MOD_00_SUBSTRATE")

# 获取算法实现路径
algo_path = module["algorithm_implementation"]["quantum_dispersion"]["function"]
```

### 8.2 在 quantum_lab.py 中使用

```python
from core.logic_registry import LogicRegistry
from core.registry_loader import RegistryLoader

reg = LogicRegistry()
themes = reg.get_themes()

# 获取 BAZI_FUNDAMENTAL 主题
bazi_theme = themes.get("BAZI_FUNDAMENTAL")

# 加载独立注册表
if bazi_theme and "registry_path" in bazi_theme:
    loader = RegistryLoader(theme_id="BAZI_FUNDAMENTAL")
    patterns = loader.registry.get("patterns", {})
    # 显示所有模块
    for pattern_id, pattern_data in patterns.items():
        print(f"{pattern_id}: {pattern_data['name']}")
```

---

## 九、下一步工作

1. ⏳ 按照模板重构剩余14个模块
2. ⏳ 验证所有模块的算法实现路径正确
3. ⏳ 更新 `quantum_lab.py` 支持从新注册表加载模块
4. ⏳ 测试所有模块的计算功能

---

**重构进度**: 1/15 模块已完成 (6.7%)  
**下一步**: 继续重构剩余模块，建议按优先级顺序进行

