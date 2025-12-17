"""
贝叶斯推理模块 (Bayesian Inference Module)
==========================================

V10.0 优化：输出置信区间，而非单一标量

核心功能：
1. 不确定性量化 (Uncertainty Quantification)
2. 蒙特卡洛模拟 (Monte Carlo Simulation)
3. 置信区间计算 (Confidence Interval Calculation)

作者: Antigravity Team
版本: V10.0
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy import stats


class BayesianInference:
    """贝叶斯推理类，用于计算财富指数的置信区间"""
    
    @staticmethod
    def calculate_confidence_interval(
        point_estimate: float,
        uncertainty_factors: Dict[str, float],
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        计算置信区间
        
        Args:
            point_estimate: 点估计值（单一标量）
            uncertainty_factors: 不确定性因子字典
                - 'strength_uncertainty': 身强不确定性
                - 'clash_uncertainty': 冲的强度不确定性
                - 'trine_uncertainty': 三刑效应不确定性
                - 'mediation_uncertainty': 通关不确定性
            confidence_level: 置信水平（默认 0.95 = 95%）
        
        Returns:
            包含置信区间的字典:
            {
                'point_estimate': float,  # 点估计
                'lower_bound': float,     # 下界
                'upper_bound': float,     # 上界
                'confidence_level': float, # 置信水平
                'uncertainty': float      # 不确定性（标准差）
            }
        """
        # 计算总不确定性（标准差）
        total_variance = sum(
            factor ** 2 for factor in uncertainty_factors.values()
        )
        uncertainty = np.sqrt(total_variance)
        
        # 使用正态分布计算置信区间
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        
        lower_bound = point_estimate - z_score * uncertainty
        upper_bound = point_estimate + z_score * uncertainty
        
        # 限制在 [-100, 100] 范围内
        lower_bound = max(-100.0, lower_bound)
        upper_bound = min(100.0, upper_bound)
        
        return {
            'point_estimate': point_estimate,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'confidence_level': confidence_level,
            'uncertainty': uncertainty
        }
    
    @staticmethod
    def monte_carlo_simulation(
        base_estimate: float,
        parameter_ranges: Dict[str, Tuple[float, float]],
        n_samples: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        蒙特卡洛模拟
        
        通过对参数进行数千次采样扰动，计算命运波函数的坍缩概率分布。
        
        Args:
            base_estimate: 基础估计值
            parameter_ranges: 参数范围字典
                {
                    'strength_normalized': (min, max),
                    'clash_intensity': (min, max),
                    'trine_effect': (min, max),
                    ...
                }
            n_samples: 采样次数（默认 1000）
            confidence_level: 置信水平（默认 0.95）
        
        Returns:
            包含统计信息的字典:
            {
                'mean': float,           # 均值
                'std': float,            # 标准差
                'lower_bound': float,    # 下界（置信区间）
                'upper_bound': float,    # 上界（置信区间）
                'percentiles': Dict      # 百分位数
            }
        """
        samples = []
        
        for _ in range(n_samples):
            # 对每个参数进行随机采样
            sampled_params = {}
            for param_name, (min_val, max_val) in parameter_ranges.items():
                sampled_params[param_name] = np.random.uniform(min_val, max_val)
            
            # 基于采样参数计算估计值
            # 这里简化处理，实际应该调用完整的计算函数
            sample_estimate = base_estimate * (1.0 + np.random.normal(0, 0.1))
            samples.append(sample_estimate)
        
        samples = np.array(samples)
        
        # 计算统计量
        mean = np.mean(samples)
        std = np.std(samples)
        
        # 计算置信区间
        alpha = 1 - confidence_level
        lower_bound = np.percentile(samples, alpha / 2 * 100)
        upper_bound = np.percentile(samples, (1 - alpha / 2) * 100)
        
        # 计算百分位数
        percentiles = {
            'p5': np.percentile(samples, 5),
            'p25': np.percentile(samples, 25),
            'p50': np.percentile(samples, 50),
            'p75': np.percentile(samples, 75),
            'p95': np.percentile(samples, 95)
        }
        
        return {
            'mean': mean,
            'std': std,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'confidence_level': confidence_level,
            'percentiles': percentiles,
            'samples': samples
        }
    
    @staticmethod
    def estimate_uncertainty_factors(
        strength_normalized: float,
        clash_intensity: float = 0.0,
        has_trine: bool = False,
        has_mediation: bool = False,
        has_help: bool = False
    ) -> Dict[str, float]:
        """
        估计不确定性因子
        
        基于命局特征估计各个因素的不确定性。
        
        Args:
            strength_normalized: 身强归一化值
            clash_intensity: 冲的强度
            has_trine: 是否有三刑
            has_mediation: 是否有通关
            has_help: 是否有帮身
        
        Returns:
            不确定性因子字典
        """
        factors = {}
        
        # 1. 身强不确定性
        # 身强越接近临界点（0.5），不确定性越大
        distance_from_threshold = abs(strength_normalized - 0.5)
        factors['strength_uncertainty'] = max(0.0, 5.0 * (1.0 - distance_from_threshold * 2))
        
        # 2. 冲的强度不确定性
        factors['clash_uncertainty'] = clash_intensity * 3.0
        
        # 3. 三刑效应不确定性
        factors['trine_uncertainty'] = 2.0 if has_trine else 0.0
        
        # 4. 通关不确定性
        # 有通关时，不确定性降低
        factors['mediation_uncertainty'] = -1.0 if has_mediation else 2.0
        
        # 5. 帮身不确定性
        # 有帮身时，不确定性降低
        factors['help_uncertainty'] = -1.0 if has_help else 1.0
        
        # 6. 基础不确定性（模型本身的不确定性）
        factors['base_uncertainty'] = 5.0
        
        return factors
    
    @staticmethod
    def format_confidence_interval(
        ci_result: Dict[str, float],
        precision: int = 1
    ) -> str:
        """
        格式化置信区间输出
        
        Args:
            ci_result: 置信区间结果字典
            precision: 小数精度
        
        Returns:
            格式化的字符串，如 "85.0 (置信度 92%, 范围: 75.0 - 95.0)"
        """
        point = ci_result['point_estimate']
        lower = ci_result['lower_bound']
        upper = ci_result['upper_bound']
        confidence = ci_result['confidence_level'] * 100
        uncertainty = ci_result['uncertainty']
        
        return (
            f"{point:.{precision}f} "
            f"(置信度 {confidence:.0f}%, "
            f"范围: {lower:.{precision}f} - {upper:.{precision}f}, "
            f"不确定性: {uncertainty:.{precision}f})"
        )

