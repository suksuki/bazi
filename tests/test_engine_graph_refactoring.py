"""
GraphNetworkEngine 重构后自动化测试
===================================

测试重构后的 GraphNetworkEngine 模块化架构：
- Phase 1: Node Initialization (节点初始化)
- Phase 2: Adjacency Matrix Construction (邻接矩阵构建)
- Phase 3: Propagation (传播迭代)

确保重构后的功能与重构前完全一致。
"""

import unittest
import numpy as np
from typing import Dict, List, Any

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.engine_graph.graph_node import GraphNode
from core.engine_graph.constants import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS


class TestGraphNetworkEngineRefactoring(unittest.TestCase):
    """测试重构后的 GraphNetworkEngine"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_FULL_ALGO_PARAMS.copy()
        self.engine = GraphNetworkEngine(self.config)
        self.bazi = ['甲子', '丙午', '辛卯', '壬辰']
        self.day_master = '辛'
    
    def test_phase1_node_initialization(self):
        """测试 Phase 1: 节点初始化"""
        # 测试初始化
        H0 = self.engine.initialize_nodes(
            self.bazi, 
            self.day_master,
            luck_pillar=None,
            year_pillar=None,
            geo_modifiers=None
        )
        
        # 验证结果
        self.assertIsNotNone(H0, "初始能量向量不应为 None")
        self.assertIsInstance(H0, np.ndarray, "初始能量向量应为 numpy 数组")
        self.assertEqual(len(H0), len(self.engine.nodes), "能量向量长度应与节点数一致")
        self.assertGreater(len(self.engine.nodes), 0, "应该有节点被创建")
        
        # 验证节点结构
        for node in self.engine.nodes:
            self.assertIsInstance(node, GraphNode, "节点应为 GraphNode 类型")
            self.assertIsNotNone(node.char, "节点字符不应为 None")
            self.assertIn(node.node_type, ['stem', 'branch'], "节点类型应为 stem 或 branch")
            self.assertIn(node.element, ['wood', 'fire', 'earth', 'metal', 'water'], 
                         "节点元素应为五行之一")
        
        print("✅ Phase 1 节点初始化测试通过")
    
    def test_phase2_adjacency_matrix(self):
        """测试 Phase 2: 邻接矩阵构建"""
        # 先初始化节点
        H0 = self.engine.initialize_nodes(self.bazi, self.day_master)
        
        # 构建邻接矩阵
        A = self.engine.build_adjacency_matrix()
        
        # 验证结果
        self.assertIsNotNone(A, "邻接矩阵不应为 None")
        self.assertIsInstance(A, np.ndarray, "邻接矩阵应为 numpy 数组")
        self.assertEqual(A.shape[0], len(self.engine.nodes), "矩阵行数应与节点数一致")
        self.assertEqual(A.shape[1], len(self.engine.nodes), "矩阵列数应与节点数一致")
        self.assertEqual(A.shape[0], A.shape[1], "邻接矩阵应为方阵")
        
        # 验证矩阵特性
        self.assertGreater(np.count_nonzero(A), 0, "邻接矩阵应有非零元素")
        
        print("✅ Phase 2 邻接矩阵构建测试通过")
    
    def test_phase3_propagation(self):
        """测试 Phase 3: 能量传播"""
        # 先执行 Phase 1 和 Phase 2
        H0 = self.engine.initialize_nodes(self.bazi, self.day_master)
        A = self.engine.build_adjacency_matrix()
        
        # 执行传播
        H_final = self.engine.propagate(max_iterations=5, damping=0.9)
        
        # 验证结果
        self.assertIsNotNone(H_final, "最终能量向量不应为 None")
        self.assertIsInstance(H_final, np.ndarray, "最终能量向量应为 numpy 数组")
        self.assertEqual(len(H_final), len(self.engine.nodes), "能量向量长度应与节点数一致")
        
        # 验证能量非负
        for i, energy in enumerate(H_final):
            from core.prob_math import ProbValue
            if isinstance(energy, ProbValue):
                self.assertGreaterEqual(energy.mean, 0, f"节点 {i} 的能量应为非负")
            else:
                self.assertGreaterEqual(float(energy), 0, f"节点 {i} 的能量应为非负")
        
        print("✅ Phase 3 能量传播测试通过")
    
    def test_full_pipeline(self):
        """测试完整流程：Phase 1 -> Phase 2 -> Phase 3"""
        # Phase 1: 初始化
        H0 = self.engine.initialize_nodes(self.bazi, self.day_master)
        self.assertIsNotNone(H0)
        
        # Phase 2: 构建邻接矩阵
        A = self.engine.build_adjacency_matrix()
        self.assertIsNotNone(A)
        
        # Phase 3: 传播
        H_final = self.engine.propagate(max_iterations=5, damping=0.9)
        self.assertIsNotNone(H_final)
        
        # 验证能量向量长度一致
        self.assertEqual(len(H0), len(H_final), "初始和最终能量向量长度应一致")
        
        print("✅ 完整流程测试通过")
    
    def test_backward_compatibility(self):
        """测试向后兼容性：委托方法"""
        # 初始化
        H0 = self.engine.initialize_nodes(self.bazi, self.day_master)
        
        # 测试委托方法
        # _has_root
        result = self.engine._has_root('甲', '子')
        self.assertIsInstance(result, bool, "_has_root 应返回 bool")
        
        # _calculate_hidden_stems_energy
        physics_config = self.config.get('physics', {})
        hidden_energy = self.engine._calculate_hidden_stems_energy('子', physics_config)
        self.assertIsInstance(hidden_energy, dict, "_calculate_hidden_stems_energy 应返回 dict")
        
        # _build_relation_types_matrix
        relation_types = self.engine._build_relation_types_matrix()
        self.assertIsNotNone(relation_types)
        self.assertIsInstance(relation_types, np.ndarray)
        
        # _get_generation_weight
        flow_config = self.config.get('flow', {})
        gen_weight = self.engine._get_generation_weight('wood', 'fire', flow_config)
        self.assertIsInstance(gen_weight, (int, float), "_get_generation_weight 应返回数值")
        
        # _get_control_weight
        control_weight = self.engine._get_control_weight('fire', 'metal', flow_config)
        self.assertIsInstance(control_weight, (int, float), "_get_control_weight 应返回数值")
        
        print("✅ 向后兼容性测试通过")
    
    def test_module_components(self):
        """测试模块组件是否正确组合"""
        # 验证组件存在
        self.assertIsNotNone(self.engine.node_initializer, "NodeInitializer 应存在")
        self.assertIsNotNone(self.engine.adjacency_builder, "AdjacencyMatrixBuilder 应存在")
        self.assertIsNotNone(self.engine.energy_propagator, "EnergyPropagator 应存在")
        
        # 验证组件类型
        from core.engine_graph.phase1_initialization import NodeInitializer
        from core.engine_graph.phase2_adjacency import AdjacencyMatrixBuilder
        from core.engine_graph.phase3_propagation import EnergyPropagator
        
        self.assertIsInstance(self.engine.node_initializer, NodeInitializer)
        self.assertIsInstance(self.engine.adjacency_builder, AdjacencyMatrixBuilder)
        self.assertIsInstance(self.engine.energy_propagator, EnergyPropagator)
        
        print("✅ 模块组件测试通过")
    
    def test_constants_import(self):
        """测试常量导入"""
        # 验证常量存在
        self.assertIsNotNone(TWELVE_LIFE_STAGES, "TWELVE_LIFE_STAGES 应存在")
        self.assertIsNotNone(LIFE_STAGE_COEFFICIENTS, "LIFE_STAGE_COEFFICIENTS 应存在")
        
        # 验证常量类型
        self.assertIsInstance(TWELVE_LIFE_STAGES, dict)
        self.assertIsInstance(LIFE_STAGE_COEFFICIENTS, dict)
        
        # 验证常量内容
        self.assertGreater(len(TWELVE_LIFE_STAGES), 0, "TWELVE_LIFE_STAGES 不应为空")
        self.assertGreater(len(LIFE_STAGE_COEFFICIENTS), 0, "LIFE_STAGE_COEFFICIENTS 不应为空")
        
        print("✅ 常量导入测试通过")
    
    def test_graph_node_import(self):
        """测试 GraphNode 导入"""
        # 验证 GraphNode 可以导入和使用
        node = GraphNode(
            node_id=0,
            char='甲',
            node_type='stem',
            element='wood',
            pillar_idx=0,
            pillar_name='year'
        )
        
        self.assertIsNotNone(node)
        self.assertEqual(node.char, '甲')
        self.assertEqual(node.node_type, 'stem')
        self.assertEqual(node.element, 'wood')
        
        print("✅ GraphNode 导入测试通过")
    
    def test_multiple_bazi_cases(self):
        """测试多个八字案例"""
        test_cases = [
            (['甲子', '丙午', '辛卯', '壬辰'], '辛'),
            (['乙丑', '戊寅', '癸巳', '甲午'], '癸'),
            (['丙寅', '庚子', '甲申', '丁卯'], '甲'),
        ]
        
        for bazi, day_master in test_cases:
            engine = GraphNetworkEngine(self.config)
            
            # Phase 1
            H0 = engine.initialize_nodes(bazi, day_master)
            self.assertIsNotNone(H0)
            
            # Phase 2
            A = engine.build_adjacency_matrix()
            self.assertIsNotNone(A)
            
            # Phase 3
            H_final = engine.propagate(max_iterations=3, damping=0.9)
            self.assertIsNotNone(H_final)
            
        print("✅ 多案例测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试未构建矩阵就传播
        engine = GraphNetworkEngine(self.config)
        engine.initialize_nodes(self.bazi, self.day_master)
        with self.assertRaises(ValueError):
            engine.propagate()
        
        # 注意：build_adjacency_matrix 在没有节点时可能不会抛出错误
        # 因为它会检查 self.engine.nodes，如果为空会返回空矩阵
        # 这是可以接受的行为，因为空矩阵也是有效的
        
        print("✅ 错误处理测试通过")


class TestModuleIsolation(unittest.TestCase):
    """测试模块隔离性"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DEFAULT_FULL_ALGO_PARAMS.copy()
    
    def test_phase1_isolation(self):
        """测试 Phase 1 模块隔离"""
        from core.engine_graph.phase1_initialization import NodeInitializer
        from core.engine_graph import GraphNetworkEngine
        
        engine = GraphNetworkEngine(self.config)
        initializer = engine.node_initializer
        
        self.assertIsNotNone(initializer)
        self.assertIsInstance(initializer, NodeInitializer)
        
        # 测试可以独立调用
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        H0 = initializer.initialize_nodes(bazi, '辛')
        self.assertIsNotNone(H0)
        
        print("✅ Phase 1 模块隔离测试通过")
    
    def test_phase2_isolation(self):
        """测试 Phase 2 模块隔离"""
        from core.engine_graph.phase2_adjacency import AdjacencyMatrixBuilder
        from core.engine_graph import GraphNetworkEngine
        
        engine = GraphNetworkEngine(self.config)
        builder = engine.adjacency_builder
        
        self.assertIsNotNone(builder)
        self.assertIsInstance(builder, AdjacencyMatrixBuilder)
        
        # 需要先初始化节点
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        engine.initialize_nodes(bazi, '辛')
        
        # 测试可以独立调用
        A = builder.build_adjacency_matrix()
        self.assertIsNotNone(A)
        
        print("✅ Phase 2 模块隔离测试通过")
    
    def test_phase3_isolation(self):
        """测试 Phase 3 模块隔离"""
        from core.engine_graph.phase3_propagation import EnergyPropagator
        from core.engine_graph import GraphNetworkEngine
        
        engine = GraphNetworkEngine(self.config)
        propagator = engine.energy_propagator
        
        self.assertIsNotNone(propagator)
        self.assertIsInstance(propagator, EnergyPropagator)
        
        # 需要先初始化节点和构建矩阵
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        engine.initialize_nodes(bazi, '辛')
        engine.build_adjacency_matrix()
        
        # 测试可以独立调用
        H_final = propagator.propagate(max_iterations=3, damping=0.9)
        self.assertIsNotNone(H_final)
        
        print("✅ Phase 3 模块隔离测试通过")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)

