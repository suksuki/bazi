"""
ProbValue 类型安全测试 (V13.0 - 全程概率分布)
============================================

测试所有 ProbValue 相关的类型转换、比较和序列化问题。

V13.0 更新：
- 全程使用 ProbValue（概率分布），不再转换为 float
- Graph 网络引擎完全基于概率分布运行
- 所有能量计算保留不确定性信息

这个测试套件确保：
1. ProbValue 与数值类型的比较不会出错（使用 .mean 属性）
2. ProbValue 的 JSON 序列化正常工作
3. 所有使用 ProbValue 的地方都能正确处理类型转换
4. Graph 网络引擎全程使用 ProbValue，不转换为 float
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json
import numpy as np
from typing import List, Dict, Any

from core.prob_math import ProbValue, prob_compare


class TestProbValueTypeSafety(unittest.TestCase):
    """测试 ProbValue 类型安全性"""
    
    def setUp(self):
        """测试前准备"""
        self.prob_value = ProbValue(50.0, std_dev_percent=0.1)
        self.float_value = 50.0
        self.int_value = 50
    
    def test_float_conversion(self):
        """测试 ProbValue 转换为 float"""
        result = float(self.prob_value)
        self.assertIsInstance(result, float)
        self.assertEqual(result, 50.0)
        print("✅ ProbValue 转 float 测试通过")
    
    def test_comparison_with_int(self):
        """测试 ProbValue 与整数比较（通过 float 转换）"""
        prob_val = float(self.prob_value)
        self.assertGreater(prob_val, 0)
        self.assertGreater(prob_val, -10)
        self.assertLess(prob_val, 100)
        print("✅ ProbValue 与整数比较测试通过")
    
    def test_comparison_with_float(self):
        """测试 ProbValue 与浮点数比较（通过 float 转换）"""
        prob_val = float(self.prob_value)
        self.assertGreater(prob_val, 0.0)
        self.assertGreaterEqual(prob_val, 50.0)
        self.assertLessEqual(prob_val, 50.0)
        print("✅ ProbValue 与浮点数比较测试通过")
    
    def test_arithmetic_operations(self):
        """测试 ProbValue 的算术运算"""
        # 加法
        result_add = self.prob_value + 10.0
        self.assertIsInstance(result_add, ProbValue)
        
        # 减法
        result_sub = self.prob_value - 10.0
        self.assertIsInstance(result_sub, ProbValue)
        
        # 乘法
        result_mul = self.prob_value * 2.0
        self.assertIsInstance(result_mul, ProbValue)
        
        # 除法
        result_div = self.prob_value / 2.0
        self.assertIsInstance(result_div, ProbValue)
        
        print("✅ ProbValue 算术运算测试通过")
    
    def test_json_serialization(self):
        """测试 ProbValue 的 JSON 序列化（通过 float 转换）"""
        # 直接序列化 ProbValue 会失败，需要先转换
        data = {
            'energy': float(self.prob_value),
            'mean': self.prob_value.mean,
            'std': self.prob_value.std
        }
        
        json_str = json.dumps(data)
        self.assertIsInstance(json_str, str)
        
        # 反序列化
        loaded_data = json.loads(json_str)
        self.assertEqual(loaded_data['energy'], 50.0)
        
        print("✅ ProbValue JSON 序列化测试通过")
    
    def test_list_conversion(self):
        """测试 ProbValue 列表转换为 float 列表"""
        prob_list = [
            ProbValue(10.0, std_dev_percent=0.1),
            ProbValue(20.0, std_dev_percent=0.1),
            ProbValue(30.0, std_dev_percent=0.1)
        ]
        
        float_list = [float(pv) for pv in prob_list]
        self.assertEqual(len(float_list), 3)
        self.assertEqual(float_list, [10.0, 20.0, 30.0])
        
        print("✅ ProbValue 列表转换测试通过")
    
    def test_mixed_list_conversion(self):
        """测试混合类型列表转换（ProbValue 和 float）"""
        mixed_list = [
            ProbValue(10.0, std_dev_percent=0.1),
            20.0,
            ProbValue(30.0, std_dev_percent=0.1),
            40.0
        ]
        
        def convert_to_float(val):
            return float(val) if isinstance(val, ProbValue) else float(val)
        
        float_list = [convert_to_float(v) for v in mixed_list]
        self.assertEqual(float_list, [10.0, 20.0, 30.0, 40.0])
        
        print("✅ 混合类型列表转换测试通过")


class TestEngineGraphProbValueIntegration(unittest.TestCase):
    """测试 engine_graph.py 中 ProbValue 的集成"""
    
    def setUp(self):
        """测试前准备"""
        from core.engine_graph import GraphNetworkEngine
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        
        self.engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        
        # 创建测试八字
        self.bazi_list = ['甲', '子', '乙', '丑', '丙', '寅', '丁', '卯']
        self.day_master = '乙'
    
    def test_node_energy_comparison(self):
        """测试节点能量比较（V13.0: 使用 ProbValue.mean 进行比较）"""
        self.engine.initialize_nodes(self.bazi_list, self.day_master)
        
        # V13.0: 节点能量始终是 ProbValue
        from core.prob_math import ProbValue
        
        for node in self.engine.nodes:
            # V13.0: 验证能量是 ProbValue
            self.assertIsInstance(node.initial_energy, ProbValue)
            
            if hasattr(node, 'current_energy'):
                current_energy = node.current_energy
                # V13.0: 使用 .mean 属性进行比较，保留概率分布
                self.assertIsInstance(current_energy, ProbValue)
                comparison_result = current_energy.mean > 0
                self.assertIsInstance(comparison_result, bool)
        
        print("✅ 节点能量比较测试通过（使用 ProbValue.mean）")
    
    def test_energy_list_conversion(self):
        """测试能量列表（V13.0: 保留 ProbValue，仅在可视化时转换）"""
        self.engine.initialize_nodes(self.bazi_list, self.day_master)
        
        from core.prob_math import ProbValue
        
        # V13.0: 获取初始能量列表（保留 ProbValue）
        initial_energy = []
        for node in self.engine.nodes:
            energy = node.initial_energy
            # V13.0: 验证是 ProbValue
            self.assertIsInstance(energy, ProbValue)
            initial_energy.append(energy)
        
        # 验证所有值都是 ProbValue
        self.assertTrue(all(isinstance(e, ProbValue) for e in initial_energy))
        self.assertEqual(len(initial_energy), len(self.engine.nodes))
        
        # 仅在可视化时转换为 float
        initial_energy_float = [float(e) for e in initial_energy]
        self.assertTrue(all(isinstance(e, (int, float)) for e in initial_energy_float))
        
        print("✅ 能量列表测试通过（保留 ProbValue，可视化时转换）")
    
    def test_adjacency_matrix_conversion(self):
        """测试邻接矩阵转换（模拟热图）"""
        self.engine.initialize_nodes(self.bazi_list, self.day_master)
        self.engine.build_adjacency_matrix()
        
        if self.engine.adjacency_matrix is not None:
            # 转换为 float 矩阵
            matrix = self.engine.adjacency_matrix
            matrix_float = np.array([[float(matrix[i][j]) 
                                   for j in range(matrix.shape[1])]
                                  for i in range(matrix.shape[0])], dtype=float)
            
            # 验证矩阵类型
            self.assertEqual(matrix_float.dtype, float)
            
            print("✅ 邻接矩阵转换测试通过")


class TestPhase1CalibratorProbValue(unittest.TestCase):
    """测试 phase1_auto_calibrator.py 中 ProbValue 的处理"""
    
    def test_self_team_energy_prob_initialization(self):
        """测试 self_team_energy_prob 的初始化（V13.0: 全程使用 ProbValue）"""
        from core.prob_math import ProbValue
        
        # V13.0: 模拟 Group A 的逻辑（全程使用 ProbValue）
        self_team_energy_prob = ProbValue(0.0, std_dev_percent=0.1)
        
        # 添加节点能量
        node_energy_1 = ProbValue(10.0, std_dev_percent=0.1)
        node_energy_2 = ProbValue(20.0, std_dev_percent=0.1)
        
        self_team_energy_prob = self_team_energy_prob + node_energy_1
        self_team_energy_prob = self_team_energy_prob + node_energy_2
        
        # V13.0: 验证结果是 ProbValue（不转换为 float）
        self.assertIsInstance(self_team_energy_prob, ProbValue)
        self.assertGreater(self_team_energy_prob.mean, 0)
        self.assertGreater(self_team_energy_prob.std, 0)  # 验证保留了不确定性
        
        print("✅ self_team_energy_prob 初始化测试通过（全程使用 ProbValue）")
    
    def test_prob_compare_function(self):
        """测试 prob_compare 函数"""
        from core.prob_math import prob_compare
        
        val_a = ProbValue(50.0, std_dev_percent=0.1)
        val_b = ProbValue(40.0, std_dev_percent=0.1)
        
        passed, prob = prob_compare(val_a, val_b, threshold=0.85)
        
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        
        print("✅ prob_compare 函数测试通过")


class TestGraphVisualizerProbValue(unittest.TestCase):
    """测试 graph_visualizer.py 中 ProbValue 的处理"""
    
    def test_energy_list_conversion_for_plotly(self):
        """测试能量列表转换用于 Plotly"""
        from ui.components.graph_visualizer import _convert_energy_list
        from core.prob_math import ProbValue
        
        # 创建包含 ProbValue 的能量列表
        energy_list = [
            ProbValue(10.0, std_dev_percent=0.1),
            ProbValue(20.0, std_dev_percent=0.1),
            30.0,  # 普通 float
            ProbValue(40.0, std_dev_percent=0.1)
        ]
        
        # 转换
        float_list = _convert_energy_list(energy_list)
        
        # 验证
        self.assertEqual(len(float_list), 4)
        self.assertTrue(all(isinstance(e, (int, float)) for e in float_list))
        self.assertEqual(float_list, [10.0, 20.0, 30.0, 40.0])
        
        print("✅ Plotly 能量列表转换测试通过")
    
    def test_json_serialization_for_plotly(self):
        """测试 Plotly 图表的 JSON 序列化"""
        import plotly.graph_objects as go
        from core.prob_math import ProbValue
        
        # 创建包含转换后数据的图表
        node_labels = ['Node1', 'Node2', 'Node3']
        initial_energy = [float(ProbValue(10.0, std_dev_percent=0.1)),
                          float(ProbValue(20.0, std_dev_percent=0.1)),
                          float(ProbValue(30.0, std_dev_percent=0.1))]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=node_labels,
            y=initial_energy,
            name='初始能量'
        ))
        
        # 尝试序列化（这应该不会出错）
        try:
            json_str = fig.to_json()
            self.assertIsInstance(json_str, str)
            print("✅ Plotly JSON 序列化测试通过")
        except TypeError as e:
            self.fail(f"Plotly JSON 序列化失败: {e}")


class TestComprehensiveProbValueScenarios(unittest.TestCase):
    """综合测试场景"""
    
    def test_real_world_scenario(self):
        """测试真实场景：完整的能量计算流程（V13.0: 全程使用 ProbValue）"""
        from core.engine_graph import GraphNetworkEngine
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        from core.prob_math import ProbValue
        
        # 初始化引擎
        engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        
        # 创建测试八字
        bazi_list = ['甲', '子', '乙', '丑', '丙', '寅', '丁', '卯']
        day_master = '乙'
        
        # 初始化节点
        engine.initialize_nodes(bazi_list, day_master)
        
        # V13.0: 验证 H0 存储的是 ProbValue
        if engine.H0 is not None:
            for i, h0_val in enumerate(engine.H0):
                if h0_val is not None:
                    self.assertIsInstance(h0_val, ProbValue, 
                                         f"H0[{i}] 应该是 ProbValue，但得到 {type(h0_val)}")
        
        # 构建邻接矩阵（V13.0: 全程使用 ProbValue）
        try:
            engine.build_adjacency_matrix()
            print("✅ 邻接矩阵构建成功")
        except TypeError as e:
            self.fail(f"构建邻接矩阵时出现类型错误: {e}")
        
        # V13.0: 获取能量数据（保留 ProbValue）
        initial_energy = []
        final_energy = []
        
        for node in engine.nodes:
            init_e = node.initial_energy
            final_e = getattr(node, 'current_energy', node.initial_energy)
            
            # V13.0: 验证能量是 ProbValue
            self.assertIsInstance(init_e, ProbValue, 
                                 f"节点 {node.node_id} 的 initial_energy 应该是 ProbValue")
            self.assertIsInstance(final_e, ProbValue, 
                                 f"节点 {node.node_id} 的 current_energy 应该是 ProbValue")
            
            # 保留 ProbValue（用于可视化时才转换为 float）
            initial_energy.append(init_e)
            final_energy.append(final_e)
        
        # 验证数据
        self.assertEqual(len(initial_energy), len(engine.nodes))
        self.assertEqual(len(final_energy), len(engine.nodes))
        self.assertTrue(all(isinstance(e, ProbValue) for e in initial_energy))
        self.assertTrue(all(isinstance(e, ProbValue) for e in final_energy))
        
        print("✅ 真实场景测试通过（全程使用 ProbValue）")


def run_all_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestProbValueTypeSafety))
    suite.addTests(loader.loadTestsFromTestCase(TestEngineGraphProbValueIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase1CalibratorProbValue))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphVisualizerProbValue))
    suite.addTests(loader.loadTestsFromTestCase(TestComprehensiveProbValueScenarios))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 60)
    print("ProbValue 类型安全测试套件")
    print("=" * 60)
    print()
    
    success = run_all_tests()
    
    print()
    print("=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查输出")
    print("=" * 60)
    
    exit(0 if success else 1)

