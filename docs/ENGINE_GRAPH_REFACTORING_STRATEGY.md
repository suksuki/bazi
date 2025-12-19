# Engine Graph 模块拆分策略文档

## 📋 概述

`engine_graph.py` 文件过大（5905行），需要拆分为多个小模块以提高可维护性和可测试性。本文档提供安全的拆分策略。

**文件统计**:
- 总行数: 5905 行
- 主类: `GraphNetworkEngine` (5772 行)
- 辅助类: `GraphNode` (34 行)
- 常量: `TWELVE_LIFE_STAGES`, `LIFE_STAGE_COEFFICIENTS`

## 🎯 拆分原则

1. **功能内聚**: 每个模块负责单一职责
2. **依赖最小化**: 减少模块间的循环依赖
3. **向后兼容**: 保持公共接口不变
4. **渐进式重构**: 分阶段实施，确保每一步都可测试
5. **遵循 MVC 架构**: 符合项目的架构约束

## 📦 模块拆分方案

### 方案一：按三阶段架构拆分（推荐）

基于引擎的三阶段架构（Phase 1/2/3）进行拆分，这是最自然的拆分方式。

#### 模块结构

```
core/
├── engine_graph/
│   ├── __init__.py              # 导出主类和公共接口
│   ├── graph_node.py            # GraphNode 类定义
│   ├── engine.py                # GraphNetworkEngine 主类（精简版）
│   ├── phase1_initialization.py # Phase 1: 节点初始化
│   ├── phase2_adjacency.py      # Phase 2: 邻接矩阵构建
│   ├── phase3_propagation.py    # Phase 3: 传播迭代
│   ├── strength_calculator.py    # 强度计算相关方法
│   ├── wealth_calculator.py     # 财富指数计算
│   ├── special_logic.py         # 特殊逻辑（通关、自刑、从格等）
│   ├── timeline_simulator.py     # 时间线模拟
│   └── constants.py             # 常量定义（十二长生表等）
```

#### 详细拆分

##### 1. `graph_node.py` (约 50 行)
```python
"""图网络节点定义"""
class GraphNode:
    """图网络节点，表示一个八字粒子"""
    # 从 engine_graph.py 第 97-131 行迁移
```

**依赖**: 无（基础数据结构）

##### 2. `constants.py` (约 100 行)
```python
"""图网络引擎常量定义"""
# TWELVE_LIFE_STAGES (第 36-77 行)
# LIFE_STAGE_COEFFICIENTS (第 81-94 行)
```

**依赖**: 无

##### 3. `phase1_initialization.py` (约 500 行)
```python
"""Phase 1: 节点初始化模块"""
class NodeInitializer:
    """负责节点初始化和初始能量计算"""
    
    def __init__(self, engine: 'GraphNetworkEngine'):
        """接收 engine 引用以访问共享状态"""
        self.engine = engine
        self.config = engine.config
    
    def initialize_nodes(self, ...) -> np.ndarray:
        """主初始化方法"""
        # 通过 self.engine.nodes, self.engine.H0 访问状态
        # 通过 self.engine.bazi 访问八字信息
        # ...
    
    def _apply_stem_transformation(self, ...):
        """化气逻辑"""
    
    def _has_root(self, ...) -> bool:
        """通根检测"""
    
    def _calculate_hidden_stems_energy(self, ...):
        """藏干能量计算"""
    
    def _calculate_node_initial_energy(self, ...):
        """节点初始能量计算"""
```

**依赖**: 
- `graph_node.py` (GraphNode)
- `constants.py` (TWELVE_LIFE_STAGES)
- `core.processors.physics` (PhysicsProcessor)
- `engine` 引用（用于访问共享状态）

**方法列表**:
- `initialize_nodes` (197-495行)
- `_apply_stem_transformation` (496-581行)
- `_has_root` (582-587行)
- `_calculate_hidden_stems_energy` (588-613行)
- `_calculate_node_initial_energy` (614-776行)

##### 4. `phase2_adjacency.py` (约 800 行)
```python
"""Phase 2: 邻接矩阵构建模块"""
class AdjacencyMatrixBuilder:
    """负责构建图网络的邻接矩阵"""
    
    def build_adjacency_matrix(self) -> np.ndarray:
        """主构建方法"""
    
    def _build_relation_types_matrix(self) -> np.ndarray:
        """关系类型矩阵"""
    
    def _get_generation_weight(self, ...) -> float:
        """生关系权重"""
    
    def _get_control_weight(self, ...) -> float:
        """克关系权重"""
    
    # ... 其他权重计算方法
```

**依赖**:
- `graph_node.py` (GraphNode)
- `core.processors.physics` (GENERATION, CONTROL)
- `core.interactions` (BRANCH_CLASHES, etc.)

**方法列表**:
- `build_adjacency_matrix` (777-935行)
- `_build_relation_types_matrix` (936-1008行)
- `_get_generation_weight` (1009-1087行)
- `_get_control_weight` (1088-1153行)
- `_find_mediator_element` (1154-1185行)
- `_calculate_mediator_energy` (1186-1213行)
- `_get_node_energy_by_element` (1214-1236行)
- `_get_stem_combination_weight` (1237-1251行)
- `_get_branch_combo_weight` (1252-1339行)
- `_get_clash_weight` (1340-1386行)

##### 5. `phase3_propagation.py` (约 600 行)
```python
"""Phase 3: 传播迭代模块"""
class EnergyPropagator:
    """负责能量传播迭代"""
    
    def propagate(self, ...) -> np.ndarray:
        """主传播方法"""
    
    def apply_logistic_potential(self, ...):
        """势井调谐算子"""
    
    def apply_scattering_interaction(self, ...):
        """散射调谐算子"""
    
    def apply_superconductivity(self, ...):
        """超导调谐算子"""
```

**依赖**:
- `graph_node.py` (GraphNode)
- `core.prob_math` (ProbValue)
- `core.processors.physics` (GENERATION, CONTROL)

**方法列表**:
- `propagate` (1516-2034行)
- `apply_logistic_potential` (1387-1430行)
- `apply_scattering_interaction` (1431-1469行)
- `apply_superconductivity` (1470-1515行)

##### 6. `strength_calculator.py` (约 900 行)
```python
"""强度计算模块"""
class StrengthCalculator:
    """负责身强分数计算和格局判定"""
    
    def extract_svm_features(self, ...) -> Tuple:
        """SVM特征提取"""
    
    def calculate_strength_score(self, ...) -> Dict:
        """强度计算主方法"""
    
    def _calculate_pattern_uncertainty(self, ...) -> Dict:
        """格局不确定性计算"""
    
    def _calculate_net_force(self, ...) -> Dict:
        """净作用力计算"""
    
    def _detect_special_pattern(self, ...) -> Optional[str]:
        """特殊格局检测"""
```

**依赖**:
- `graph_node.py` (GraphNode)
- `constants.py` (TWELVE_LIFE_STAGES)
- `core.processors.physics` (GENERATION, CONTROL)

**方法列表**:
- `extract_svm_features` (2040-2174行)
- `calculate_strength_score` (2175-2510行)
- `_calculate_pattern_uncertainty` (2511-2587行)
- `_calculate_net_force` (2588-2738行)
- `_detect_special_pattern` (2740-2871行)

##### 7. `special_logic.py` (约 1500 行)
```python
"""特殊逻辑模块"""
class SpecialLogicProcessor:
    """负责各种特殊逻辑处理"""
    
    def _apply_self_punishment_damping(self, ...):
        """自刑惩罚"""
    
    def _apply_mediation_logic(self, ...):
        """通关逻辑"""
    
    def _detect_officer_resource_mediation(self, ...):
        """官印相生检测"""
    
    def _add_dayun_support_links(self, ...):
        """大运支持链接"""
    
    def _add_liunian_trigger_links(self, ...):
        """流年触发链接"""
    
    def _detect_follower_grid(self, ...) -> Optional[Dict]:
        """从格检测"""
    
    def _calculate_dynamic_score(self, ...) -> float:
        """动态评分"""
    
    def _apply_quantum_entanglement_once(self):
        """量子纠缠（合化/刑冲）"""
    
    def _is_in_combination(self, ...):
        """合局检测"""
    
    def _apply_relative_suppression(self, ...):
        """相对抑制"""
```

**依赖**:
- `graph_node.py` (GraphNode)
- `constants.py` (TWELVE_LIFE_STAGES)
- `core.processors.physics` (GENERATION, CONTROL)
- `core.interactions` (BRANCH_CLASHES, etc.)

**方法列表**:
- `_apply_self_punishment_damping` (2873-2936行)
- `_apply_mediation_logic` (2937-3124行)
- `_detect_officer_resource_mediation` (3125-3180行)
- `_add_dayun_support_links` (3181-3230行)
- `_add_liunian_trigger_links` (3231-3456行)
- `_detect_follower_grid` (3457-3708行)
- `_calculate_dynamic_score` (3709-3742行)
- `_calculate_dayun_impact` (3743-3776行)
- `_calculate_liunian_impact` (3777-3827行)
- `_get_dynamic_label` (3829-3840行)
- `_apply_quantum_entanglement_once` (3941-4324行)
- `_is_in_combination` (4325-4363行)
- `_apply_relative_suppression` (4364-4504行)

##### 8. `wealth_calculator.py` (约 1300 行)
```python
"""财富指数计算模块"""
class WealthIndexCalculator:
    """负责财富指数计算"""
    
    def calculate_wealth_index(self, ...) -> Dict:
        """财富指数计算主方法"""
```

**依赖**:
- `graph_node.py` (GraphNode)
- `core.processors.physics` (GENERATION, CONTROL)
- `core.bayesian_inference` (BayesianInference)

**方法列表**:
- `calculate_wealth_index` (4643-5905行)

##### 9. `timeline_simulator.py` (约 100 行)
```python
"""时间线模拟模块"""
class TimelineSimulator:
    """负责时间线推演"""
    
    def simulate_timeline(self, ...) -> List[Dict]:
        """时间线模拟主方法"""
    
    def _collect_trigger_events(self) -> List[str]:
        """收集触发事件"""
```

**依赖**:
- `graph_node.py` (GraphNode)
- `core.transformer_temporal` (TemporalTransformer)

**方法列表**:
- `simulate_timeline` (3842-3931行)
- `_collect_trigger_events` (3933-3939行)

##### 10. `engine.py` (约 300 行)
```python
"""图网络引擎主类（精简版）"""
class GraphNetworkEngine:
    """图网络引擎 - 物理初始化的图神经网络模型"""
    
    # 类常量
    CAPACITY = 2000.0
    VERSION = "10.0-Graph"
    
    def __init__(self, config: Dict = None):
        """初始化引擎，组合各个模块"""
        # 初始化共享状态
        self.config = config or DEFAULT_FULL_ALGO_PARAMS
        self.nodes: List[GraphNode] = []
        self.H0: np.ndarray = None
        self.adjacency_matrix: np.ndarray = None
        self.bazi: List[str] = []
        self.day_master_element: str = None
        
        # 初始化处理器
        self.physics_processor = PhysicsProcessor()
        self.use_gat = config.get('use_gat', False)
        if self.use_gat:
            self.gat_builder = GATAdjacencyBuilder(config)
        else:
            self.gat_builder = None
        
        # 元素映射
        self.STEM_ELEMENTS = {...}
        self.BRANCH_ELEMENTS = {...}
        
        # 组合各个模块（传递 self 引用）
        self.node_initializer = NodeInitializer(self)
        self.adjacency_builder = AdjacencyMatrixBuilder(self)
        self.propagator = EnergyPropagator(self)
        self.strength_calculator = StrengthCalculator(self)
        self.wealth_calculator = WealthIndexCalculator(self)
        self.special_logic = SpecialLogicProcessor(self)
        self.timeline_simulator = TimelineSimulator(self)
    
    def analyze(self, ...) -> Dict:
        """完整的图网络分析流程"""
        # Phase 1
        H0 = self.node_initializer.initialize_nodes(...)
        # Phase 2
        A = self.adjacency_builder.build_adjacency_matrix()
        # Phase 3
        H_final = self.propagator.propagate(...)
        # 计算强度
        strength_data = self.strength_calculator.calculate_strength_score(...)
        # ...
    
    def calculate_wealth_index(self, ...) -> Dict:
        """财富指数计算（委托给 wealth_calculator）"""
        return self.wealth_calculator.calculate_wealth_index(...)
    
    def simulate_timeline(self, ...) -> List[Dict]:
        """时间线模拟（委托给 timeline_simulator）"""
        return self.timeline_simulator.simulate_timeline(...)
    
    # 保留一些辅助方法
    def calculate_domain_scores(self, ...) -> Dict:
        """领域得分计算"""
    
    def _get_element_str(self, ...) -> str:
        """获取元素字符串"""
```

**依赖**: 所有其他模块

## 🔄 拆分实施步骤

### 阶段 1: 准备阶段（低风险）
1. ✅ 创建 `core/engine_graph/` 目录
2. ✅ 创建 `__init__.py`，保持向后兼容
3. ✅ 提取常量到 `constants.py`
4. ✅ 提取 `GraphNode` 到 `graph_node.py`
5. ✅ 运行测试，确保无破坏性变更

### 阶段 2: Phase 1 拆分（中等风险）
1. ✅ 创建 `phase1_initialization.py`
2. ✅ 将 Phase 1 相关方法迁移到 `NodeInitializer` 类
3. ✅ 在 `GraphNetworkEngine` 中组合 `NodeInitializer`
4. ✅ 运行测试，确保 Phase 1 功能正常

### 阶段 3: Phase 2 拆分（中等风险）
1. ✅ 创建 `phase2_adjacency.py`
2. ✅ 将 Phase 2 相关方法迁移到 `AdjacencyMatrixBuilder` 类
3. ✅ 在 `GraphNetworkEngine` 中组合 `AdjacencyMatrixBuilder`
4. ✅ 运行测试，确保 Phase 2 功能正常

### 阶段 4: Phase 3 拆分（中等风险）
1. ✅ 创建 `phase3_propagation.py`
2. ✅ 将 Phase 3 相关方法迁移到 `EnergyPropagator` 类
3. ✅ 在 `GraphNetworkEngine` 中组合 `EnergyPropagator`
4. ✅ 运行测试，确保 Phase 3 功能正常

### 阶段 5: 辅助模块拆分（低风险）
1. ✅ 创建 `strength_calculator.py`
2. ✅ 创建 `special_logic.py`
3. ✅ 创建 `timeline_simulator.py`
4. ✅ 创建 `wealth_calculator.py`
5. ✅ 逐步迁移方法，每次迁移后运行测试

### 阶段 6: 主类精简（低风险）
1. ✅ 精简 `engine.py`，只保留组合逻辑和公共接口
2. ✅ 确保所有公共接口保持不变
3. ✅ 运行完整测试套件

### 阶段 7: 清理和优化（低风险）
1. ✅ 删除旧的 `engine_graph.py` 文件
2. ✅ 更新导入路径（如果需要）
3. ✅ 更新文档
4. ✅ 代码审查

## 🔒 安全保证措施

### 1. 向后兼容性
- 保持 `GraphNetworkEngine` 类的公共接口不变
- 保持所有公共方法的签名不变
- 保持返回值结构不变
- 保持类级别的常量（如 `CAPACITY`, `VERSION`）不变

### 2. 测试覆盖
- 每个阶段迁移后，运行完整测试套件
- 特别关注：
  - `scripts/run_full_check_v93.py` 中的 `GraphNetworkEngine` 测试
  - `test_wealth_verification.py` (使用 `WealthVerificationController`)
  - `test_bazi_controller.py` (使用 `BaziController`)
  - 回归测试用例
  - 端到端集成测试

### 3. 依赖管理
- 使用组合而非继承，减少耦合
- 通过 `config` 参数传递配置
- 通过方法参数传递状态，避免隐式状态依赖
- 使用依赖注入模式，各模块接收 `engine` 引用访问共享状态

### 4. 状态管理（关键）

**共享状态对象**:
```python
class EngineState:
    """引擎状态容器，用于在各模块间共享状态"""
    def __init__(self):
        self.nodes: List[GraphNode] = []
        self.H0: np.ndarray = None
        self.adjacency_matrix: np.ndarray = None
        self.bazi: List[str] = []
        self.day_master_element: str = None
        self.config: Dict = None
        self.physics_processor: PhysicsProcessor = None
        self.gat_builder: Optional[GATAdjacencyBuilder] = None
        self.STEM_ELEMENTS: Dict = {}
        self.BRANCH_ELEMENTS: Dict = {}
```

**状态传递方式**:
- 方案 A（推荐）: 各模块接收 `engine_state` 对象，通过 `engine_state.nodes` 等访问
- 方案 B: 各模块接收 `engine` 引用，通过 `engine.nodes` 等访问
- 方案 C: 通过方法参数显式传递所需状态

**实施建议**:
- 使用方案 B（最简单，向后兼容性最好）
- 各模块类接收 `engine` 引用作为构造参数
- 通过 `self.engine.nodes`, `self.engine.H0` 等访问共享状态
- 避免在模块内部缓存状态，始终从 `engine` 读取最新状态

## 📊 拆分后的文件大小

| 模块 | 预估行数 | 复杂度 |
|------|---------|--------|
| `graph_node.py` | 50 | 低 |
| `constants.py` | 100 | 低 |
| `phase1_initialization.py` | 500 | 中 |
| `phase2_adjacency.py` | 800 | 中 |
| `phase3_propagation.py` | 600 | 高 |
| `strength_calculator.py` | 900 | 中 |
| `special_logic.py` | 1500 | 高 |
| `wealth_calculator.py` | 1300 | 高 |
| `timeline_simulator.py` | 100 | 低 |
| `engine.py` | 300 | 低 |
| **总计** | **5650** | - |

## ⚠️ 注意事项

1. **循环依赖**: 避免模块间的循环依赖，使用依赖注入
2. **状态共享**: 通过主类共享状态，避免模块间直接访问
3. **配置传递**: 所有模块共享同一个 `config` 对象
4. **测试覆盖**: 每个阶段都要有完整的测试验证
5. **文档更新**: 及时更新相关文档

## 🎯 预期收益

1. **可维护性**: 每个模块职责单一，易于理解和修改
2. **可测试性**: 可以单独测试每个模块
3. **可扩展性**: 新功能可以添加到对应模块，不影响其他模块
4. **代码复用**: 模块可以在其他场景复用
5. **团队协作**: 不同开发者可以并行开发不同模块

## 📝 实施检查清单

### 阶段 1 检查清单
- [ ] 创建 `core/engine_graph/` 目录
- [ ] 创建 `__init__.py`，导出 `GraphNetworkEngine`
- [ ] 提取常量到 `constants.py`
- [ ] 提取 `GraphNode` 到 `graph_node.py`
- [ ] 运行测试，确保无破坏性变更
- [ ] 更新导入路径（如果需要）

### 阶段 2-4 检查清单（每个阶段）
- [ ] 创建对应的模块文件
- [ ] 迁移相关方法到新类
- [ ] 在 `GraphNetworkEngine` 中组合新类
- [ ] 运行测试，确保功能正常
- [ ] 检查代码覆盖率

### 阶段 5 检查清单
- [ ] 创建所有辅助模块文件
- [ ] 逐步迁移方法
- [ ] 每次迁移后运行测试
- [ ] 检查依赖关系

### 阶段 6 检查清单
- [ ] 精简 `engine.py`
- [ ] 确保公共接口不变
- [ ] 运行完整测试套件
- [ ] 性能测试（确保无性能退化）

### 阶段 7 检查清单
- [ ] 删除旧的 `engine_graph.py`
- [ ] 更新所有导入路径
- [ ] 更新文档
- [ ] 代码审查
- [ ] 最终测试

## 🔍 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 破坏性变更 | 高 | 低 | 保持公共接口不变，完整测试覆盖 |
| 性能退化 | 中 | 低 | 性能测试，优化关键路径 |
| 循环依赖 | 中 | 中 | 使用依赖注入，避免循环导入 |
| 状态管理错误 | 高 | 中 | 明确的状态传递接口，单元测试 |
| 测试覆盖不足 | 高 | 中 | 每个阶段都要有测试验证 |

## 📚 参考文档

- [MVC 架构约束](../.cursorrules)
- [核心算法总纲](./ALGORITHM_CONSTITUTION_v2.6.md)
- [图网络引擎架构](./GRAPH_NETWORK_ENGINE_ARCHITECTURE.md)

---

**版本**: 1.0.0  
**创建日期**: 2025-01-XX  
**作者**: AI Assistant  
**审核状态**: 待审核

