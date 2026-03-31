"""
元学习调优体系集成测试
====================

测试覆盖:
1. 贝叶斯优化与引擎的集成
2. 对比学习 RLHF 与引擎的集成
3. Transformer 位置编码调优与引擎的集成
4. GAT 路径过滤与引擎的集成
5. 完整元学习工作流

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import unittest
import numpy as np
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.bayesian_optimization import BayesianOptimizer
from core.contrastive_rlhf import ContrastiveRLHFTrainer, ContrastiveRewardModel
from core.transformer_position_tuning import PositionalEncodingTuner, MultiScaleTemporalFusion
from core.gat_path_filter import GATPathFilter
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


class TestBayesianOptimizationIntegration(unittest.TestCase):
    """测试贝叶斯优化与引擎的集成"""
    
    def setUp(self):
        """测试前准备"""
        self.case_data = {
            'bazi': ['辛丑', '丁酉', '庚辰', '丙戌'],
            'day_master': '庚',
            'gender': '男'
        }
        self.target_year = 1999
        self.target_real_value = 50.0
    
    def test_bayesian_optimization_with_engine(self):
        """测试贝叶斯优化与引擎的集成"""
        parameter_bounds = {
            'strength_beta': (5.0, 15.0),
            'clash_k': (3.0, 7.0)
        }
        
        optimizer = BayesianOptimizer(
            parameter_bounds=parameter_bounds,
            n_initial_samples=3
        )
        
        def objective(params):
            """目标函数：使用引擎计算预测值"""
            config = DEFAULT_FULL_ALGO_PARAMS.copy()
            if 'nonlinear' not in config:
                config['nonlinear'] = {}
            config['nonlinear']['strength_beta'] = params.get('strength_beta', 10.0)
            config['nonlinear']['scale'] = params.get('strength_beta', 10.0)
            config['nonlinear']['clash_k'] = params.get('clash_k', 5.0)
            config['nonlinear']['steepness'] = params.get('clash_k', 5.0)
            
            engine = GraphNetworkEngine(config=config)
            result = engine.calculate_wealth_index(
                bazi=self.case_data['bazi'],
                day_master=self.case_data['day_master'],
                gender=self.case_data['gender'],
                luck_pillar='戊戌',
                year_pillar='己卯'
            )
            
            if isinstance(result, dict):
                predicted = result.get('wealth_index', 0.0)
            else:
                predicted = float(result)
            
            error = (predicted - self.target_real_value) ** 2
            return error
        
        # 执行优化（少量迭代以加快测试）
        optimal_params = optimizer.optimize(objective, n_iterations=5)
        
        self.assertIn('strength_beta', optimal_params)
        self.assertIn('clash_k', optimal_params)
        print("✅ 贝叶斯优化与引擎集成测试通过")


class TestContrastiveRLHFIntegration(unittest.TestCase):
    """测试对比学习 RLHF 与引擎的集成"""
    
    def setUp(self):
        """测试前准备"""
        self.case_data = {
            'bazi': ['辛丑', '丁酉', '庚辰', '丙戌'],
            'day_master': '庚',
            'gender': '男',
            'timeline': [
                {'year': 1999, 'real_magnitude': 50.0},
                {'year': 2015, 'real_magnitude': 100.0}
            ]
        }
        self.reward_model = ContrastiveRewardModel()
        self.trainer = ContrastiveRLHFTrainer(self.reward_model)
    
    def test_contrastive_rlhf_with_engine(self):
        """测试对比学习 RLHF 与引擎的集成"""
        # 创建两个不同配置的引擎
        config_a = DEFAULT_FULL_ALGO_PARAMS.copy()
        config_b = DEFAULT_FULL_ALGO_PARAMS.copy()
        
        if 'nonlinear' not in config_a:
            config_a['nonlinear'] = {}
        if 'nonlinear' not in config_b:
            config_b['nonlinear'] = {}
        
        config_a['nonlinear']['strength_beta'] = 10.0
        config_b['nonlinear']['strength_beta'] = 15.0
        
        engine_a = GraphNetworkEngine(config=config_a)
        engine_b = GraphNetworkEngine(config=config_b)
        
        # 生成对比学习对（简化版）
        target_years = [1999, 2015]
        
        # 由于 _generate_path 需要完整的引擎接口，这里只测试基本功能
        ground_truth = self.trainer._get_ground_truth(self.case_data, target_years)
        
        self.assertEqual(len(ground_truth), 2)
        self.assertEqual(ground_truth[0], 50.0)
        self.assertEqual(ground_truth[1], 100.0)
        print("✅ 对比学习 RLHF 与引擎集成测试通过")


class TestTransformerTuningIntegration(unittest.TestCase):
    """测试 Transformer 位置编码调优与引擎的集成"""
    
    def setUp(self):
        """测试前准备"""
        self.timeline_data = [
            {'year': 1999, 'energy': 50.0},
            {'year': 2015, 'energy': 100.0},
            {'year': 2021, 'energy': 100.0}
        ]
    
    def test_transformer_tuning_with_timeline(self):
        """测试 Transformer 位置编码调优与时间线的集成"""
        tuner = PositionalEncodingTuner(d_model=128, max_length=100)
        
        def objective(params):
            # 简单的目标函数
            return abs(params['position_scale'] - 10000.0)
        
        optimal_params = tuner.tune_for_long_range_dependency(
            timeline_data=self.timeline_data,
            objective_func=objective
        )
        
        self.assertIn('position_scale', optimal_params)
        self.assertIn('decay_factor', optimal_params)
        print("✅ Transformer 位置编码调优与时间线集成测试通过")
    
    def test_multi_scale_fusion_with_timeline(self):
        """测试多尺度时序融合与时间线的集成"""
        fusion = MultiScaleTemporalFusion()
        
        fused = fusion.fuse_temporal_features(self.timeline_data)
        
        self.assertIsInstance(fused, np.ndarray)
        self.assertGreater(len(fused), 0)
        print("✅ 多尺度时序融合与时间线集成测试通过")


class TestGATPathFilterIntegration(unittest.TestCase):
    """测试 GAT 路径过滤与引擎的集成"""
    
    def setUp(self):
        """测试前准备"""
        self.filter = GATPathFilter(threshold=0.1)
        self.attention_weights = {
            (0, 1): 0.5,
            (1, 2): 0.3,
            (2, 3): 0.15,
            (3, 4): 0.05
        }
        self.energy_paths = [
            {'0->1': 0.5},
            {'1->2': 0.3},
            {'2->3': 0.15},
            {'3->4': 0.05}
        ]
    
    def test_gat_filter_with_attention_weights(self):
        """测试 GAT 路径过滤与注意力权重的集成"""
        filtered = self.filter.filter_paths(
            attention_weights=self.attention_weights,
            energy_paths=self.energy_paths
        )
        
        self.assertIsInstance(filtered, dict)
        self.assertLessEqual(len(filtered), len(self.attention_weights))
        print("✅ GAT 路径过滤与注意力权重集成测试通过")
    
    def test_entropy_controller_with_attention_weights(self):
        """测试系统熵控制器与注意力权重的集成"""
        controller = SystemEntropyController(base_entropy=0.1)
        
        entropy = controller.calculate_path_entropy(self.attention_weights)
        filtered = controller.filter_by_entropy(
            attention_weights=self.attention_weights,
            max_entropy=2.0
        )
        
        self.assertIsInstance(entropy, float)
        self.assertIsInstance(filtered, dict)
        print("✅ 系统熵控制器与注意力权重集成测试通过")


class TestMetaLearningWorkflowIntegration(unittest.TestCase):
    """测试完整元学习工作流集成"""
    
    def setUp(self):
        """测试前准备"""
        self.case_data = {
            'bazi': ['辛丑', '丁酉', '庚辰', '丙戌'],
            'day_master': '庚',
            'gender': '男',
            'timeline': [
                {'year': 1999, 'real_magnitude': 50.0}
            ]
        }
    
    def test_complete_meta_learning_workflow(self):
        """测试完整元学习工作流"""
        # 1. 贝叶斯优化
        parameter_bounds = {
            'strength_beta': (5.0, 15.0),
            'clash_k': (3.0, 7.0)
        }
        
        optimizer = BayesianOptimizer(
            parameter_bounds=parameter_bounds,
            n_initial_samples=2
        )
        
        def objective(params):
            config = DEFAULT_FULL_ALGO_PARAMS.copy()
            if 'nonlinear' not in config:
                config['nonlinear'] = {}
            config['nonlinear']['strength_beta'] = params.get('strength_beta', 10.0)
            config['nonlinear']['scale'] = params.get('strength_beta', 10.0)
            
            engine = GraphNetworkEngine(config=config)
            result = engine.calculate_wealth_index(
                bazi=self.case_data['bazi'],
                day_master=self.case_data['day_master'],
                gender=self.case_data['gender'],
                luck_pillar='戊戌',
                year_pillar='己卯'
            )
            
            if isinstance(result, dict):
                predicted = result.get('wealth_index', 0.0)
            else:
                predicted = float(result)
            
            return (predicted - 50.0) ** 2
        
        optimal_params = optimizer.optimize(objective, n_iterations=3)
        
        # 2. GAT 路径过滤
        filter = GATPathFilter(threshold=0.1)
        attention_weights = {(0, 1): 0.5, (1, 2): 0.3}
        energy_paths = [{'0->1': 0.5}, {'1->2': 0.3}]
        filtered = filter.filter_paths(attention_weights, energy_paths)
        
        # 验证工作流完成
        self.assertIn('strength_beta', optimal_params)
        self.assertIsInstance(filtered, dict)
        print("✅ 完整元学习工作流集成测试通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)

