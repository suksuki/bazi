# Engine Graph 模块化拆分策略

## 📋 当前状态分析

### 文件规模
- **文件**: `core/engine_graph.py`
- **行数**: 5905 行
- **类数**: 2 个（`GraphNode`, `GraphNetworkEngine`）
- **方法数**: 45+ 个公共/私有方法
- **复杂度**: 极高（单一文件包含所有 Phase 1-3 逻辑）

### 主要职责（按 Phase 划分）

#### Phase 1: 节点初始化 (~800 行)
- `initialize_nodes()` - 主入口
- `_apply_stem_transformation()` - 天干化气
- `_has_root()` - 通根检测
- `_calculate_hidden_stems_energy()` - 藏干能量
- `_calculate_node_initial_energy()` - 节点初始能量计算

#### Phase 2: 邻接矩阵构建 (~600 行)
- `build_adjacency_matrix()` - 主入口
- `_build_relation_types_matrix()` - 关系类型矩阵
- `_get_generation_weight()` - 生关系权重
- `_get_control_weight()` - 克关系权重
- `_find_mediator_element()` - 通关元素查找
- `_calculate_mediator_energy()` - 通关能量计算
- `_get_stem_combination_weight()` - 天干合权重
- `_get_branch_combo_weight()` - 地支合权重
- `_get_clash_weight()` - 冲刑权重

#### Phase 3: 能量传播 (~500 行)
- `propagate()` - 主传播循环
- `apply_logistic_potential()` - 势井调谐（V14.2）
- `apply_scattering_interaction()` - 散射调谐（V14.2）
- `apply_superconductivity()` - 超导调谐（V14.2）

#### 高级功能 (~4000 行)
- `calculate_strength_score()` - 强度计算
- `calculate_wealth_index()` - 财富指数
- `simulate_timeline()` - 时间线模拟
- `analyze()` - 综合分析
- `_apply_quantum_entanglement_once()` - 量子纠缠（合化/刑冲）
- `_is_in_combination()` - 合局检测
- 各种模式检测和特殊逻辑

---

## 🎯 模块化拆分方案

### 目标架构

```
core/engine_graph/
├── __init__.py                    # 导出主类，保持向后兼容
├── constants.py                   # 常量定义（十二长生表等）
├── graph_node.py                  # GraphNode 类
├── phase1_initialization.py       # Phase 1: 节点初始化
├── phase2_adjacency.py            # Phase 2: 邻接矩阵构建
├── phase3_propagation.py          # Phase 3: 能量传播
├── wave_functions.py              # 物理调谐波函数（V14.2）
├── quantum_entanglement.py        # 量子纠缠（合化/刑冲）
├── strength_calculator.py          # 强度计算
├── wealth_calculator.py           # 财富指数计算
├── pattern_detector.py            # 模式检测
└── timeline_simulator.py          # 时间线模拟
```

### 模块职责划分

#### 1. `constants.py` (~100 行)
**职责**: 存储常量定义
- `TWELVE_LIFE_STAGES` - 十二长生表
- `LIFE_STAGE_COEFFICIENTS` - 长生系数
- `STEM_ELEMENTS` - 天干元素映射
- `BRANCH_ELEMENTS` - 地支元素映射

**依赖**: 无

#### 2. `graph_node.py` (~50 行)
**职责**: 节点数据结构
- `GraphNode` 类定义
- 节点属性（energy, element, has_root 等）

**依赖**: `constants.py`, `prob_math.ProbValue`

#### 3. `phase1_initialization.py` (~800 行)
**职责**: Phase 1 节点初始化
- `NodeInitializer` 类
- `initialize_nodes()` - 主入口
- `_apply_stem_transformation()` - 化气
- `_has_root()` - 通根检测
- `_calculate_hidden_stems_energy()` - 藏干能量
- `_calculate_node_initial_energy()` - 初始能量计算

**依赖**: 
- `graph_node.GraphNode`
- `constants.py`
- `core.processors.physics.PhysicsProcessor`
- `core.prob_math.ProbValue`

#### 4. `phase2_adjacency.py` (~600 行)
**职责**: Phase 2 邻接矩阵构建
- `AdjacencyMatrixBuilder` 类
- `build_adjacency_matrix()` - 主入口
- `_build_relation_types_matrix()` - 关系矩阵
- `_get_generation_weight()` - 生权重
- `_get_control_weight()` - 克权重
- `_find_mediator_element()` - 通关查找
- `_calculate_mediator_energy()` - 通关能量
- `_get_stem_combination_weight()` - 天干合
- `_get_branch_combo_weight()` - 地支合
- `_get_clash_weight()` - 冲刑

**依赖**:
- `graph_node.GraphNode`
- `constants.py`
- `core.processors.physics.GENERATION, CONTROL`
- `core.prob_math.ProbValue`

#### 5. `phase3_propagation.py` (~500 行)
**职责**: Phase 3 能量传播
- `EnergyPropagator` 类
- `propagate()` - 主传播循环
- 迭代逻辑、阻尼、能量更新

**依赖**:
- `graph_node.GraphNode`
- `wave_functions.py` (物理调谐)
- `quantum_entanglement.py` (合化检测)

#### 6. `wave_functions.py` (~200 行)
**职责**: V14.2 物理调谐波函数
- `apply_logistic_potential()` - 势井调谐
- `apply_scattering_interaction()` - 散射调谐
- `apply_superconductivity()` - 超导调谐

**依赖**:
- `core.prob_math.ProbValue`
- `core.math_utils`

#### 7. `quantum_entanglement.py` (~400 行)
**职责**: 量子纠缠（合化/刑冲）
- `QuantumEntanglement` 类
- `_apply_quantum_entanglement_once()` - 一次性应用
- `_is_in_combination()` - 合局检测
- 元素转化逻辑

**依赖**:
- `graph_node.GraphNode`
- `constants.py`
- `core.config_schema`

#### 8. `strength_calculator.py` (~800 行)
**职责**: 强度计算
- `StrengthCalculator` 类
- `calculate_strength_score()` - 主入口
- `_calculate_pattern_uncertainty()` - 模式不确定性
- `_calculate_net_force()` - 净力计算
- `_detect_special_pattern()` - 特殊模式检测
- `_apply_self_punishment_damping()` - 自刑阻尼
- `_apply_mediation_logic()` - 通关逻辑

**依赖**:
- `graph_node.GraphNode`
- `core.bayesian_inference`
- `core.nonlinear_activation`

#### 9. `wealth_calculator.py` (~1200 行)
**职责**: 财富指数计算
- `WealthCalculator` 类
- `calculate_wealth_index()` - 主入口
- 财富能量计算
- 冲提纲检测
- 非线性阻尼

**依赖**:
- `graph_node.GraphNode`
- `strength_calculator.StrengthCalculator`
- `core.bayesian_inference`

#### 10. `pattern_detector.py` (~600 行)
**职责**: 模式检测
- `PatternDetector` 类
- `_detect_follower_grid()` - 从格检测
- `_detect_officer_resource_mediation()` - 官杀通关
- `_apply_relative_suppression()` - 相对抑制
- `calculate_domain_scores()` - 领域评分

**依赖**:
- `graph_node.GraphNode`
- `strength_calculator.StrengthCalculator`

#### 11. `timeline_simulator.py` (~400 行)
**职责**: 时间线模拟
- `TimelineSimulator` 类
- `simulate_timeline()` - 主入口
- `_calculate_dynamic_score()` - 动态评分
- `_calculate_dayun_impact()` - 大运影响
- `_calculate_liunian_impact()` - 流年影响
- `_collect_trigger_events()` - 触发事件收集

**依赖**:
- `graph_node.GraphNode`
- `strength_calculator.StrengthCalculator`
- `pattern_detector.PatternDetector`

---

## 🔧 拆分实施步骤

### 阶段 1: 准备阶段（向后兼容）
1. ✅ 创建 `core/engine_graph/` 目录
2. ✅ 创建 `__init__.py`，导出 `GraphNetworkEngine`
3. ✅ 移动常量到 `constants.py`
4. ✅ 移动 `GraphNode` 到 `graph_node.py`
5. ✅ 更新 `engine_graph.py` 导入，保持向后兼容

### 阶段 2: Phase 1 拆分
1. 创建 `phase1_initialization.py`
2. 创建 `NodeInitializer` 类
3. 移动 Phase 1 相关方法
4. 在 `GraphNetworkEngine` 中委托给 `NodeInitializer`
5. 运行测试确保功能正常

### 阶段 3: Phase 2 拆分
1. 创建 `phase2_adjacency.py`
2. 创建 `AdjacencyMatrixBuilder` 类
3. 移动 Phase 2 相关方法
4. 在 `GraphNetworkEngine` 中委托给 `AdjacencyMatrixBuilder`
5. 运行测试确保功能正常

### 阶段 4: Phase 3 拆分
1. 创建 `wave_functions.py`（先拆分物理调谐函数）
2. 创建 `phase3_propagation.py`
3. 创建 `EnergyPropagator` 类
4. 移动 Phase 3 相关方法
5. 在 `GraphNetworkEngine` 中委托给 `EnergyPropagator`
6. 运行测试确保功能正常

### 阶段 5: 量子纠缠拆分
1. 创建 `quantum_entanglement.py`
2. 创建 `QuantumEntanglement` 类
3. 移动合化/刑冲相关方法
4. 在 `GraphNetworkEngine` 中委托给 `QuantumEntanglement`
5. 运行测试确保功能正常

### 阶段 6: 高级功能拆分
1. 创建 `strength_calculator.py`
2. 创建 `wealth_calculator.py`
3. 创建 `pattern_detector.py`
4. 创建 `timeline_simulator.py`
5. 逐步移动相关方法
6. 每个模块拆分后运行测试

### 阶段 7: 清理和优化
1. 移除 `engine_graph.py` 中的冗余代码
2. 优化导入路径
3. 更新文档
4. 运行完整测试套件

---

## 🔗 依赖关系图

```
GraphNetworkEngine (主类)
    │
    ├── NodeInitializer (Phase 1)
    │   ├── GraphNode
    │   ├── constants
    │   └── PhysicsProcessor
    │
    ├── AdjacencyMatrixBuilder (Phase 2)
    │   ├── GraphNode
    │   ├── constants
    │   └── PhysicsProcessor
    │
    ├── EnergyPropagator (Phase 3)
    │   ├── GraphNode
    │   ├── wave_functions
    │   └── QuantumEntanglement
    │
    ├── QuantumEntanglement
    │   ├── GraphNode
    │   └── constants
    │
    ├── StrengthCalculator
    │   ├── GraphNode
    │   └── BayesianInference
    │
    ├── WealthCalculator
    │   ├── GraphNode
    │   └── StrengthCalculator
    │
    ├── PatternDetector
    │   ├── GraphNode
    │   └── StrengthCalculator
    │
    └── TimelineSimulator
        ├── GraphNode
        ├── StrengthCalculator
        └── PatternDetector
```

---

## ✅ 向后兼容性保证

### 策略
1. **保持主类接口不变**: `GraphNetworkEngine` 的所有公共方法签名保持不变
2. **委托模式**: 主类方法委托给子模块，不改变调用方式
3. **渐进式迁移**: 分阶段进行，每阶段都保持功能完整
4. **导入兼容**: `from core.engine_graph import GraphNetworkEngine` 仍然有效

### 示例代码结构

```python
# core/engine_graph/__init__.py
from core.engine_graph.engine_main import GraphNetworkEngine
__all__ = ['GraphNetworkEngine']

# core/engine_graph/engine_main.py
class GraphNetworkEngine:
    def __init__(self, config=None):
        self.node_initializer = NodeInitializer(self)
        self.adjacency_builder = AdjacencyMatrixBuilder(self)
        self.energy_propagator = EnergyPropagator(self)
        # ...
    
    def initialize_nodes(self, bazi, day_master, ...):
        """委托给 NodeInitializer"""
        return self.node_initializer.initialize_nodes(bazi, day_master, ...)
    
    def build_adjacency_matrix(self):
        """委托给 AdjacencyMatrixBuilder"""
        return self.adjacency_builder.build_adjacency_matrix()
    
    def propagate(self, max_iterations=10, damping=0.9):
        """委托给 EnergyPropagator"""
        return self.energy_propagator.propagate(max_iterations, damping)
```

---

## 🧪 测试策略

### 单元测试
- 每个模块独立测试
- 测试文件: `tests/test_engine_graph_*.py`
- 覆盖所有公共方法

### 集成测试
- 测试模块间协作
- 测试完整流程（Phase 1 → 2 → 3）
- 回归测试确保结果一致

### 兼容性测试
- 确保现有代码无需修改
- 测试所有 Controller 和 UI 调用
- 验证 Phase 2 验证脚本

---

## 📝 实施检查清单

### 阶段 1: 准备
- [ ] 创建 `core/engine_graph/` 目录
- [ ] 创建 `__init__.py`
- [ ] 移动常量到 `constants.py`
- [ ] 移动 `GraphNode` 到 `graph_node.py`
- [ ] 更新导入，保持兼容
- [ ] 运行测试确保无破坏

### 阶段 2: Phase 1
- [ ] 创建 `phase1_initialization.py`
- [ ] 实现 `NodeInitializer` 类
- [ ] 移动 Phase 1 方法
- [ ] 更新 `GraphNetworkEngine` 委托
- [ ] 运行 Phase 1 测试

### 阶段 3: Phase 2
- [ ] 创建 `phase2_adjacency.py`
- [ ] 实现 `AdjacencyMatrixBuilder` 类
- [ ] 移动 Phase 2 方法
- [ ] 更新 `GraphNetworkEngine` 委托
- [ ] 运行 Phase 2 测试

### 阶段 4: Phase 3
- [ ] 创建 `wave_functions.py`
- [ ] 创建 `phase3_propagation.py`
- [ ] 实现 `EnergyPropagator` 类
- [ ] 移动 Phase 3 方法
- [ ] 更新 `GraphNetworkEngine` 委托
- [ ] 运行 Phase 3 测试

### 阶段 5: 量子纠缠
- [ ] 创建 `quantum_entanglement.py`
- [ ] 实现 `QuantumEntanglement` 类
- [ ] 移动合化/刑冲方法
- [ ] 更新 `GraphNetworkEngine` 委托
- [ ] 运行量子纠缠测试

### 阶段 6: 高级功能
- [ ] 创建 `strength_calculator.py`
- [ ] 创建 `wealth_calculator.py`
- [ ] 创建 `pattern_detector.py`
- [ ] 创建 `timeline_simulator.py`
- [ ] 逐步移动方法
- [ ] 运行完整测试套件

### 阶段 7: 清理
- [ ] 移除冗余代码
- [ ] 优化导入
- [ ] 更新文档
- [ ] 运行完整回归测试
- [ ] 代码审查

---

## 🚀 在新 Chat 中开始

### 快速开始指令

```
你好，我需要继续重构 `core/engine_graph.py` 文件。

当前状态：
- 文件有 5905 行，需要拆分为模块
- 已创建策略文档：`docs/ENGINE_GRAPH_MODULARIZATION_STRATEGY.md`

请按照策略文档执行阶段 X（指定阶段），确保：
1. 保持向后兼容性
2. 每个阶段完成后运行测试
3. 遵循 MVC 架构约束
```

### 关键文件位置
- 策略文档: `docs/ENGINE_GRAPH_MODULARIZATION_STRATEGY.md`
- 主文件: `core/engine_graph.py`
- 目标目录: `core/engine_graph/`
- 测试目录: `tests/test_engine_graph_*.py`

### 依赖检查
在开始前，运行以下命令检查当前状态：
```bash
# 检查文件大小
wc -l core/engine_graph.py

# 检查目录结构
ls -la core/engine_graph/ 2>/dev/null || echo "目录不存在，需要创建"

# 运行基础测试
python -m pytest tests/test_engine_graph*.py -v
```

---

## 📚 参考文档

- MVC 架构约束: 项目根目录的 `.cursorrules`
- 算法规范: `docs/ALGORITHM_CONSTITUTION_v2.6.md`
- Phase 2 验证: `core/phase2_verifier.py`
- 配置管理: `core/config_schema.py`

---

**最后更新**: 2025-01-XX  
**版本**: 1.0.0  
**状态**: 待实施

