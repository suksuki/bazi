#!/usr/bin/env python3
"""
贝叶斯优化模块 (Bayesian Optimization)
=====================================

针对 V10.0 非线性架构的参数调优系统
使用代理模型（Surrogate Model）和期望改进（Expected Improvement）来寻找全局最优解
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from scipy.optimize import minimize
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)


class GaussianProcess:
    """
    高斯过程（代理模型）
    用于建模参数空间到目标函数的映射
    """
    
    def __init__(self, kernel='rbf', length_scale=1.0, noise_level=0.1):
        """
        初始化高斯过程
        
        Args:
            kernel: 核函数类型（'rbf', 'matern', 'rational_quadratic'）
            length_scale: 长度尺度参数
            noise_level: 噪声水平
        """
        self.kernel = kernel
        self.length_scale = length_scale
        self.noise_level = noise_level
        self.X_train = None
        self.y_train = None
        self.K = None
        self.K_inv = None
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        拟合高斯过程
        
        Args:
            X: 训练输入（参数组合）
            y: 训练输出（目标函数值）
        """
        self.X_train = X
        self.y_train = y
        
        # 计算协方差矩阵
        self.K = self._compute_kernel(X, X)
        self.K += self.noise_level ** 2 * np.eye(len(X))
        self.K_inv = np.linalg.inv(self.K)
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测均值和方差
        
        Args:
            X: 预测输入
            
        Returns:
            (mean, std): 预测均值和标准差
        """
        if self.X_train is None:
            return np.zeros(len(X)), np.ones(len(X))
        
        # 计算训练-测试协方差
        K_star = self._compute_kernel(self.X_train, X)
        # 计算测试-测试协方差
        K_star_star = self._compute_kernel(X, X)
        
        # 预测均值
        mean = K_star.T @ self.K_inv @ self.y_train
        
        # 预测方差
        var = np.diag(K_star_star) - np.diag(K_star.T @ self.K_inv @ K_star)
        var = np.maximum(var, 0)  # 确保非负
        std = np.sqrt(var)
        
        return mean, std
    
    def _compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """
        计算核函数矩阵
        
        Args:
            X1: 输入1
            X2: 输入2
            
        Returns:
            核函数矩阵
        """
        if self.kernel == 'rbf':
            # RBF 核
            dist_sq = np.sum((X1[:, np.newaxis] - X2) ** 2, axis=2)
            return np.exp(-0.5 * dist_sq / self.length_scale ** 2)
        elif self.kernel == 'matern':
            # Matern 3/2 核
            dist = np.sqrt(np.sum((X1[:, np.newaxis] - X2) ** 2, axis=2))
            return (1 + np.sqrt(3) * dist / self.length_scale) * \
                   np.exp(-np.sqrt(3) * dist / self.length_scale)
        else:
            raise ValueError(f"Unknown kernel: {self.kernel}")


class BayesianOptimizer:
    """
    贝叶斯优化器
    使用高斯过程作为代理模型，通过期望改进（EI）来寻找最优参数
    """
    
    def __init__(self, parameter_bounds: Dict[str, Tuple[float, float]], 
                 acquisition_func: str = 'ei', n_initial_samples: int = 10):
        """
        初始化贝叶斯优化器
        
        Args:
            parameter_bounds: 参数边界字典，例如 {'beta': (5.0, 15.0), 'k': (3.0, 7.0)}
            acquisition_func: 采集函数类型（'ei', 'ucb', 'pi'）
            n_initial_samples: 初始随机采样数量
        """
        self.parameter_bounds = parameter_bounds
        self.parameter_names = list(parameter_bounds.keys())
        self.acquisition_func = acquisition_func
        self.n_initial_samples = n_initial_samples
        
        self.gp = GaussianProcess()
        self.X_history = []
        self.y_history = []
        self.best_params = None
        self.best_value = float('inf')
    
    def optimize(self, objective_func: Callable, n_iterations: int = 50) -> Dict[str, float]:
        """
        执行贝叶斯优化
        
        Args:
            objective_func: 目标函数，接受参数字典，返回损失值
            n_iterations: 优化迭代次数
            
        Returns:
            最优参数字典
        """
        logger.info(f"开始贝叶斯优化，参数空间: {self.parameter_names}")
        
        # 1. 初始随机采样
        logger.info(f"步骤1: 初始随机采样 ({self.n_initial_samples} 个样本)")
        for _ in range(self.n_initial_samples):
            params = self._random_sample()
            value = objective_func(params)
            self.X_history.append(self._params_to_vector(params))
            self.y_history.append(value)
            logger.debug(f"  采样: {params} -> 损失: {value:.4f}")
        
        # 2. 迭代优化
        logger.info(f"步骤2: 贝叶斯优化迭代 ({n_iterations} 次)")
        for i in range(n_iterations):
            # 拟合高斯过程
            X = np.array(self.X_history)
            y = np.array(self.y_history)
            self.gp.fit(X, y)
            
            # 找到当前最优
            best_idx = np.argmin(y)
            if y[best_idx] < self.best_value:
                self.best_value = y[best_idx]
                self.best_params = self._vector_to_params(X[best_idx])
            
            # 通过采集函数选择下一个采样点
            next_params = self._select_next_sample()
            next_value = objective_func(next_params)
            
            self.X_history.append(self._params_to_vector(next_params))
            self.y_history.append(next_value)
            
            logger.info(f"  迭代 {i+1}/{n_iterations}: {next_params} -> 损失: {next_value:.4f} "
                       f"(当前最优: {self.best_value:.4f})")
        
        logger.info(f"✅ 优化完成！最优参数: {self.best_params}, 最优值: {self.best_value:.4f}")
        return self.best_params
    
    def _random_sample(self) -> Dict[str, float]:
        """随机采样参数"""
        params = {}
        for name, (low, high) in self.parameter_bounds.items():
            params[name] = np.random.uniform(low, high)
        return params
    
    def _params_to_vector(self, params: Dict[str, float]) -> np.ndarray:
        """将参数字典转换为向量"""
        return np.array([params[name] for name in self.parameter_names])
    
    def _vector_to_params(self, vector: np.ndarray) -> Dict[str, float]:
        """将向量转换为参数字典"""
        return {name: vector[i] for i, name in enumerate(self.parameter_names)}
    
    def _select_next_sample(self) -> Dict[str, float]:
        """通过采集函数选择下一个采样点"""
        # 定义搜索空间
        bounds = [self.parameter_bounds[name] for name in self.parameter_names]
        
        # 使用采集函数优化
        def acquisition(x):
            x_dict = self._vector_to_params(x)
            mean, std = self.gp.predict(x.reshape(1, -1))
            mean = mean[0]
            std = std[0]
            
            if self.acquisition_func == 'ei':
                # 期望改进（Expected Improvement）
                if std == 0:
                    return 0
                z = (self.best_value - mean) / std
                return std * (z * norm.cdf(z) + norm.pdf(z))
            elif self.acquisition_func == 'ucb':
                # 上置信界（Upper Confidence Bound）
                beta = 2.0  # 探索-利用平衡参数
                return -(mean - beta * std)  # 负号因为 minimize
            elif self.acquisition_func == 'pi':
                # 改进概率（Probability of Improvement）
                if std == 0:
                    return 0
                z = (self.best_value - mean) / std
                return norm.cdf(z)
            else:
                raise ValueError(f"Unknown acquisition function: {self.acquisition_func}")
        
        # 多起点优化
        best_x = None
        best_acq = -float('inf')
        
        for _ in range(10):  # 10 个随机起点
            x0 = self._random_sample()
            x0_vec = self._params_to_vector(x0)
            
            result = minimize(
                acquisition,
                x0_vec,
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            if result.success and -result.fun > best_acq:
                best_acq = -result.fun
                best_x = result.x
        
        if best_x is None:
            # 如果优化失败，随机采样
            return self._random_sample()
        
        return self._vector_to_params(best_x)
    
    def get_optimization_history(self) -> Tuple[List[Dict[str, float]], List[float]]:
        """
        获取优化历史
        
        Returns:
            (参数历史, 损失历史)
        """
        params_history = [self._vector_to_params(x) for x in self.X_history]
        return params_history, self.y_history


class HyperparameterSensitivityAnalyzer:
    """
    超参数敏感度分析器
    分析非线性激活函数参数对预测结果的影响
    """
    
    def __init__(self, base_params: Dict[str, float]):
        """
        初始化敏感度分析器
        
        Args:
            base_params: 基础参数字典
        """
        self.base_params = base_params
    
    def analyze(self, objective_func: Callable, 
                parameter_name: str, 
                range_values: np.ndarray) -> Dict[str, np.ndarray]:
        """
        分析单个参数的敏感度
        
        Args:
            objective_func: 目标函数
            parameter_name: 参数名称
            range_values: 参数取值范围
            
        Returns:
            敏感度分析结果
        """
        logger.info(f"分析参数 {parameter_name} 的敏感度")
        
        losses = []
        for value in range_values:
            params = self.base_params.copy()
            params[parameter_name] = value
            loss = objective_func(params)
            losses.append(loss)
        
        # 计算敏感度（损失的变化率）
        sensitivity = np.gradient(losses, range_values)
        
        return {
            'parameter_values': range_values,
            'losses': np.array(losses),
            'sensitivity': sensitivity,
            'optimal_value': range_values[np.argmin(losses)]
        }
    
    def analyze_all(self, objective_func: Callable, 
                   parameter_ranges: Dict[str, np.ndarray]) -> Dict[str, Dict]:
        """
        分析所有参数的敏感度
        
        Args:
            objective_func: 目标函数
            parameter_ranges: 参数范围字典
            
        Returns:
            所有参数的敏感度分析结果
        """
        results = {}
        for param_name, range_values in parameter_ranges.items():
            results[param_name] = self.analyze(objective_func, param_name, range_values)
        return results

