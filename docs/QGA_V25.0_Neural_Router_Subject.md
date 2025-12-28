# QGA V25.0 神经网络路由专题 (LLM Neural Router Subject)

## 概述

**神经网络路由专题**是QGA V25.0的核心创新，它将原本散落在各处的路由逻辑，转化为QGA标准化的"算子矩阵"，实现了**元编程 (Meta-Programming)**级别的架构升级。

## 专题定位

**中央处理中枢 (Central Processing Kernel)**

- **作用**: 将八字物理指纹（五行、应力、相位）投射到LLM的逻辑潜空间，实现格局智能路由
- **特性**: 可生长、可审计的"逻辑生命体"
- **优势**: 即使未来增加第100个格局，也只需要在注册表中增加一行配置，神经网络会自动学习如何将其与其他格局进行耦合

## 目录结构

```
core/subjects/neural_router/
├── __init__.py              # 专题模块导出
├── registry.json            # 专题注册表（路由参数、物理模型、格局定义）
├── registry.py              # 注册表管理类
└── execution_kernel.py      # 执行内核
```

## 核心组件

### 1. 路由参数 (Routing Parameters)

在`registry.json`中定义：

- **field_strength_threshold** (0.6): 场强探测阈值，定义AI启动特定逻辑分衬的敏感度
- **coherence_weight** (0.75): 相干性权重，定义多格局叠加时的相干干涉系数
- **entropy_damping** (0.3): 熵值阻尼，防止AI在处理矛盾格局时逻辑崩溃的保护参数

所有参数都支持运行时调优（`tunable: true`）。

### 2. 物理模型与算法 (Physics Models)

#### Feature_to_Latent算子

- **作用**: 将八字物理指纹投射到LLM的逻辑潜空间
- **输入特征**:
  - `five_elements_field_strength`: 五行场强分布
  - `stress_tensor`: 应力张量
  - `phase_relationships`: 相位关系
  - `synthesized_field`: 合成场强信息
- **输出维度**: 256（可配置）

#### SAI_Collapse算子

- **作用**: 全量格局扫描后的综合SAI（应变张量）动态结算
- **聚合方法**: weighted_sum（加权求和）
- **坍缩阈值**: 0.7（可配置）

### 3. 格局定义 (Pattern Definitions)

专题注册表中包含了7个格局的公理化定义：

1. **SHANG_GUAN_JIAN_GUAN** (伤官见官) - Conflict类型
2. **HUA_HUO_GE** (化火格) - Special类型
3. **XIAO_SHEN_DUO_SHI** (枭神夺食) - Conflict类型
4. **JIAN_LU_YUE_JIE** (建禄月劫) - Special类型
5. **GUAN_YIN_XIANG_SHENG** (官印相生) - Normal类型
6. **YANG_REN_JIA_SHA** (羊刃架杀) - Special类型
7. **CONG_ER_GE** (从儿格) - Special类型

每个格局定义包含：
- `core_conflict`: 核心矛盾点
- `force_characteristics`: 受力特征（五行场强分布）
- `semantic_keywords`: 语义关键词
- `priority_rank`: 优先级
- `base_strength`: 基础强度

### 4. 优化机制 (Optimization)

#### 逻辑自愈 (Self-Healing)

当LLM输出违背物理守恒定律时，触发重读算子进行逻辑强制校准。

检查项：
- `energy_conservation_check`: 能量守恒检查
- `element_balance_check`: 元素平衡检查
- `semantic_coherence_check`: 语义一致性检查

#### 离群审计接口 (Outlier Audit)

专门用于记录神经网络路由在处理"从未见过"的八字结构时的决策路径，作为后续微调的Dataset。

- **存储路径**: `logs/neural_router_outliers`
- **日志格式**: JSON

## 使用方式

### 基本使用

```python
from core.subjects.neural_router import NeuralRouterKernel

# 创建执行内核
kernel = NeuralRouterKernel()

# 处理八字档案
result = kernel.process_bazi_profile(
    active_patterns=active_patterns,
    synthesized_field=synthesized_field,
    profile_name="测试档案",
    day_master="丁",
    force_vectors={"fire": 10.0, "water": -5.0},
    geo_info="北方/北京"
)

# 获取结果
persona = result.get("persona")
metadata = result.get("neural_router_metadata")
```

### 访问注册表

```python
from core.subjects.neural_router.registry import get_neural_router_registry

registry = get_neural_router_registry()

# 获取路由参数
threshold = registry.get_routing_parameter("field_strength_threshold")

# 获取格局定义
pattern_def = registry.get_pattern_definition("SHANG_GUAN_JIAN_GUAN")

# 更新路由参数（运行时调优）
registry.update_routing_parameter("field_strength_threshold", 0.7)
registry.save_registry()
```

## 与Phase 1的集成

神经网络路由专题与Phase 1的逻辑真空化完美配合：

1. **格局引擎**不再包含硬编码判定逻辑，而是从`PatternDefinitionRegistry`读取定义
2. **专题执行内核**从`NeuralRouterRegistry`读取格局定义和路由参数
3. **LLM合成器**保持不变，但被封装在专题执行内核中，作为执行管道的一部分

## 架构优势

1. **元编程**: 不是在写如何路由，而是在写一个"如何路由"的物理模型
2. **可扩展性**: 新增格局只需在注册表中添加配置
3. **可审计性**: 所有路由决策都有可追溯的路径
4. **可调优性**: 所有参数支持运行时调优
5. **可生长性**: 通过离群审计接口，系统可以不断学习和改进

## 下一步工作

1. **Phase 2**: 特征向量提取器开发
2. **神经网络训练**: 使用离群审计数据训练神经网络路由模型
3. **参数优化**: 通过实际使用数据优化路由参数

## 参考资料

- `core/subjects/neural_router/registry.json` - 专题注册表
- `core/subjects/neural_router/execution_kernel.py` - 执行内核实现
- `core/models/pattern_definition_registry.py` - 格局定义注册表（Phase 1）

