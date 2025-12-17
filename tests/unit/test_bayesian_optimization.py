"""
贝叶斯优化模块单元测试
====================

测试覆盖:
1. 高斯过程代理模型
2. 贝叶斯优化器
3. 超参数敏感度分析器
4. 边界条件和错误处理

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.bayesian_optimization import (
    GaussianProcess,
    BayesianOptimizer,
    HyperparameterSensitivityAnalyzer
)


class TestGaussianProcess(unittest.TestCase):
    """测试高斯过程代理模型"""
    
    def setUp(self):
        """测试前准备"""
        self.gp = GaussianProcess(kernel='rbf', length_scale=1.0, noise_level=0.1)
        # 创建简单的训练数据
        self.X_train = np.array([[0.0], [1.0], [2.0]])
        self.y_train = np.array([0.0, 1.0, 2.0])
    
    def test_fit(self):
        """测试拟合高斯过程"""
        self.gp.fit(self.X_train, self.y_train)
        self.assertIsNotNone(self.gp.K)
        self.assertIsNotNone(self.gp.K_inv)
        self.assertEqual(self.gp.K.shape, (3, 3))
        print("✅ 高斯过程拟合测试通过")
    
    def test_predict(self):
        """测试预测功能"""
        self.gp.fit(self.X_train, self.y_train)
        X_test = np.array([[0.5], [1.5]])
        mean, std = self.gp.predict(X_test)
        
        self.assertEqual(len(mean), 2)
        self.assertEqual(len(std), 2)
        self.assertTrue(np.all(std >= 0))  # 标准差应该非负
        print("✅ 高斯过程预测测试通过")
    
    def test_predict_without_fit(self):
        """测试未拟合时的预测（应该返回默认值）"""
        X_test = np.array([[0.5]])
        mean, std = self.gp.predict(X_test)
        
        self.assertEqual(len(mean), 1)
        self.assertEqual(len(std), 1)
        print("✅ 未拟合时的预测测试通过")
    
    def test_kernel_rbf(self):
        """测试 RBF 核函数"""
        X1 = np.array([[0.0], [1.0]])
        X2 = np.array([[0.0], [1.0]])
        K = self.gp._compute_kernel(X1, X2)
        
        self.assertEqual(K.shape, (2, 2))
        self.assertAlmostEqual(K[0, 0], 1.0, places=5)  # 相同点应该为 1
        print("✅ RBF 核函数测试通过")
    
    def test_kernel_matern(self):
        """测试 Matern 核函数"""
        gp = GaussianProcess(kernel='matern', length_scale=1.0)
        X1 = np.array([[0.0], [1.0]])
        X2 = np.array([[0.0], [1.0]])
        K = gp._compute_kernel(X1, X2)
        
        self.assertEqual(K.shape, (2, 2))
        self.assertAlmostEqual(K[0, 0], 1.0, places=5)
        print("✅ Matern 核函数测试通过")
    
    def test_kernel_invalid(self):
        """测试无效核函数"""
        gp = GaussianProcess(kernel='invalid')
        X1 = np.array([[0.0]])
        X2 = np.array([[0.0]])
        
        with self.assertRaises(ValueError):
            gp._compute_kernel(X1, X2)
        print("✅ 无效核函数错误处理测试通过")


class TestBayesianOptimizer(unittest.TestCase):
    """测试贝叶斯优化器"""
    
    def setUp(self):
        """测试前准备"""
        self.parameter_bounds = {
            'param1': (0.0, 1.0),
            'param2': (0.0, 1.0)
        }
        self.optimizer = BayesianOptimizer(
            parameter_bounds=self.parameter_bounds,
            acquisition_func='ei',
            n_initial_samples=5
        )
    
    def test_random_sample(self):
        """测试随机采样"""
        params = self.optimizer._random_sample()
        
        self.assertIn('param1', params)
        self.assertIn('param2', params)
        self.assertGreaterEqual(params['param1'], 0.0)
        self.assertLessEqual(params['param1'], 1.0)
        self.assertGreaterEqual(params['param2'], 0.0)
        self.assertLessEqual(params['param2'], 1.0)
        print("✅ 随机采样测试通过")
    
    def test_params_to_vector(self):
        """测试参数字典转向量"""
        params = {'param1': 0.5, 'param2': 0.7}
        vector = self.optimizer._params_to_vector(params)
        
        self.assertEqual(len(vector), 2)
        self.assertAlmostEqual(vector[0], 0.5, places=5)
        self.assertAlmostEqual(vector[1], 0.7, places=5)
        print("✅ 参数字典转向量测试通过")
    
    def test_vector_to_params(self):
        """测试向量转参数字典"""
        vector = np.array([0.5, 0.7])
        params = self.optimizer._vector_to_params(vector)
        
        self.assertIn('param1', params)
        self.assertIn('param2', params)
        self.assertAlmostEqual(params['param1'], 0.5, places=5)
        self.assertAlmostEqual(params['param2'], 0.7, places=5)
        print("✅ 向量转参数字典测试通过")
    
    def test_optimize_simple_objective(self):
        """测试简单目标函数的优化"""
        def objective(params):
            # 简单的二次函数，最小值在 (0.5, 0.5)
            return (params['param1'] - 0.5) ** 2 + (params['param2'] - 0.5) ** 2
        
        optimal_params = self.optimizer.optimize(objective, n_iterations=10)
        
        self.assertIn('param1', optimal_params)
        self.assertIn('param2', optimal_params)
        # 验证优化结果在合理范围内
        self.assertGreaterEqual(optimal_params['param1'], 0.0)
        self.assertLessEqual(optimal_params['param1'], 1.0)
        print("✅ 简单目标函数优化测试通过")
    
    def test_get_optimization_history(self):
        """测试获取优化历史"""
        def objective(params):
            return (params['param1'] - 0.5) ** 2
        
        self.optimizer.optimize(objective, n_iterations=5)
        params_history, loss_history = self.optimizer.get_optimization_history()
        
        self.assertGreater(len(params_history), 0)
        self.assertGreater(len(loss_history), 0)
        self.assertEqual(len(params_history), len(loss_history))
        print("✅ 优化历史获取测试通过")
    
    def test_acquisition_function_ei(self):
        """测试期望改进采集函数"""
        optimizer = BayesianOptimizer(
            parameter_bounds=self.parameter_bounds,
            acquisition_func='ei',
            n_initial_samples=3
        )
        
        def objective(params):
            return (params['param1'] - 0.5) ** 2
        
        # 先进行初始采样
        for _ in range(3):
            params = optimizer._random_sample()
            value = objective(params)
            optimizer.X_history.append(optimizer._params_to_vector(params))
            optimizer.y_history.append(value)
        
        # 拟合高斯过程
        X = np.array(optimizer.X_history)
        y = np.array(optimizer.y_history)
        optimizer.gp.fit(X, y)
        optimizer.best_value = min(y)
        
        # 选择下一个采样点
        next_params = optimizer._select_next_sample()
        
        self.assertIn('param1', next_params)
        self.assertIn('param2', next_params)
        print("✅ 期望改进采集函数测试通过")
    
    def test_acquisition_function_ucb(self):
        """测试上置信界采集函数"""
        optimizer = BayesianOptimizer(
            parameter_bounds=self.parameter_bounds,
            acquisition_func='ucb',
            n_initial_samples=3
        )
        
        def objective(params):
            return (params['param1'] - 0.5) ** 2
        
        # 先进行初始采样
        for _ in range(3):
            params = optimizer._random_sample()
            value = objective(params)
            optimizer.X_history.append(optimizer._params_to_vector(params))
            optimizer.y_history.append(value)
        
        # 拟合高斯过程
        X = np.array(optimizer.X_history)
        y = np.array(optimizer.y_history)
        optimizer.gp.fit(X, y)
        optimizer.best_value = min(y)
        
        # 选择下一个采样点
        next_params = optimizer._select_next_sample()
        
        self.assertIn('param1', next_params)
        print("✅ 上置信界采集函数测试通过")
    
    def test_acquisition_function_pi(self):
        """测试改进概率采集函数"""
        optimizer = BayesianOptimizer(
            parameter_bounds=self.parameter_bounds,
            acquisition_func='pi',
            n_initial_samples=3
        )
        
        def objective(params):
            return (params['param1'] - 0.5) ** 2
        
        # 先进行初始采样
        for _ in range(3):
            params = optimizer._random_sample()
            value = objective(params)
            optimizer.X_history.append(optimizer._params_to_vector(params))
            optimizer.y_history.append(value)
        
        # 拟合高斯过程
        X = np.array(optimizer.X_history)
        y = np.array(optimizer.y_history)
        optimizer.gp.fit(X, y)
        optimizer.best_value = min(y)
        
        # 选择下一个采样点
        next_params = optimizer._select_next_sample()
        
        self.assertIn('param1', next_params)
        print("✅ 改进概率采集函数测试通过")


class TestHyperparameterSensitivityAnalyzer(unittest.TestCase):
    """测试超参数敏感度分析器"""
    
    def setUp(self):
        """测试前准备"""
        self.base_params = {
            'param1': 0.5,
            'param2': 0.5
        }
        self.analyzer = HyperparameterSensitivityAnalyzer(self.base_params)
    
    def test_analyze_single_parameter(self):
        """测试单个参数的敏感度分析"""
        def objective(params):
            # 简单的线性函数
            return params['param1'] * 2.0
        
        range_values = np.linspace(0.0, 1.0, 10)
        result = self.analyzer.analyze(
            objective_func=objective,
            parameter_name='param1',
            range_values=range_values
        )
        
        self.assertIn('parameter_values', result)
        self.assertIn('losses', result)
        self.assertIn('sensitivity', result)
        self.assertIn('optimal_value', result)
        self.assertEqual(len(result['losses']), 10)
        self.assertEqual(len(result['sensitivity']), 10)
        print("✅ 单个参数敏感度分析测试通过")
    
    def test_analyze_all_parameters(self):
        """测试所有参数的敏感度分析"""
        def objective(params):
            return params['param1'] ** 2 + params['param2'] ** 2
        
        parameter_ranges = {
            'param1': np.linspace(0.0, 1.0, 5),
            'param2': np.linspace(0.0, 1.0, 5)
        }
        
        results = self.analyzer.analyze_all(objective, parameter_ranges)
        
        self.assertIn('param1', results)
        self.assertIn('param2', results)
        self.assertIn('optimal_value', results['param1'])
        self.assertIn('optimal_value', results['param2'])
        print("✅ 所有参数敏感度分析测试通过")
    
    def test_analyze_edge_case(self):
        """测试边界情况"""
        def objective(params):
            return 1.0  # 常数函数
        
        range_values = np.linspace(0.0, 1.0, 5)
        result = self.analyzer.analyze(
            objective_func=objective,
            parameter_name='param1',
            range_values=range_values
        )
        
        # 常数函数的敏感度应该接近 0
        self.assertTrue(np.allclose(result['sensitivity'], 0.0, atol=0.1))
        print("✅ 边界情况测试通过")


class TestBayesianOptimizationEdgeCases(unittest.TestCase):
    """测试边界情况和错误处理"""
    
    def test_empty_parameter_bounds(self):
        """测试空参数边界"""
        with self.assertRaises(ValueError):
            BayesianOptimizer(parameter_bounds={})
        print("✅ 空参数边界错误处理测试通过")
    
    def test_invalid_acquisition_function(self):
        """测试无效的采集函数"""
        parameter_bounds = {'param1': (0.0, 1.0)}
        optimizer = BayesianOptimizer(
            parameter_bounds=parameter_bounds,
            acquisition_func='invalid'
        )
        
        def objective(params):
            return params['param1'] ** 2
        
        # 初始采样
        for _ in range(3):
            params = optimizer._random_sample()
            value = objective(params)
            optimizer.X_history.append(optimizer._params_to_vector(params))
            optimizer.y_history.append(value)
        
        # 拟合高斯过程
        X = np.array(optimizer.X_history)
        y = np.array(optimizer.y_history)
        optimizer.gp.fit(X, y)
        optimizer.best_value = min(y)
        
        # 选择下一个采样点（应该回退到随机采样）
        next_params = optimizer._select_next_sample()
        self.assertIn('param1', next_params)
        print("✅ 无效采集函数错误处理测试通过")
    
    def test_optimize_with_exception(self):
        """测试目标函数抛出异常的情况"""
        parameter_bounds = {'param1': (0.0, 1.0)}
        optimizer = BayesianOptimizer(
            parameter_bounds=parameter_bounds,
            n_initial_samples=3
        )
        
        def objective(params):
            if params['param1'] > 0.5:
                raise ValueError("测试异常")
            return params['param1'] ** 2
        
        # 优化应该能够处理异常（返回很大的损失值）
        optimal_params = optimizer.optimize(objective, n_iterations=5)
        
        # 验证优化结果在合理范围内
        self.assertIn('param1', optimal_params)
        print("✅ 目标函数异常处理测试通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)

