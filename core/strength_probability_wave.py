#!/usr/bin/env python3
"""
旺衰概率波模块 (Strength Probability Wave)
==========================================

V10.0 改进：废除"二元论"，引入"旺衰概率波"
将旺衰判定从硬性的 0/1 标签转换为动态的、连续的能量场概率分布

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class StrengthProbabilityWave:
    """
    旺衰概率波
    使用 Soft-thresholding 将旺衰判定从二元转换为连续概率分布
    """
    
    @staticmethod
    def calculate_strength_probability(
        energy_sum: float,
        threshold_center: float = 3.0,
        phase_transition_width: float = 10.0,
        config: Optional[Dict] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        计算旺衰概率（连续值 [0, 1]）
        
        使用 Sigmoid 函数替代硬编码的 if/else，实现平滑过渡
        
        Args:
            energy_sum: 能量总和（原始值）
            threshold_center: 激活函数中心点（中性点）
            phase_transition_width: 相变宽度（Softplus 的 β 参数，控制过渡的陡峭程度）
            config: 配置参数（可选）
        
        Returns:
            (strength_probability, details_dict)
            - strength_probability: 旺衰概率 [0, 1]，0 表示极弱，1 表示极强
            - details_dict: 详细分解字典
        """
        if config is None:
            config = {}
        
        # 从配置读取参数，或使用默认值
        threshold_center = config.get('energy_threshold_center', threshold_center)
        phase_transition_width = config.get('phase_transition_width', 
                                            config.get('strength_beta', phase_transition_width))
        
        details = {}
        
        # 1. 计算能量差值（相对于中心点）
        energy_diff = energy_sum - threshold_center
        details['energy_sum'] = energy_sum
        details['threshold_center'] = threshold_center
        details['energy_diff'] = energy_diff
        
        # 2. 使用 Sigmoid 函数计算旺衰概率
        # P(strong) = 1 / (1 + exp(-k * (energy - threshold)))
        # 其中 k 是相变宽度参数
        k = phase_transition_width
        strength_probability = 1.0 / (1.0 + np.exp(-k * energy_diff))
        details['strength_probability'] = strength_probability
        
        # 3. 计算置信度（基于能量差值的大小）
        # 能量差值越大，置信度越高
        confidence = min(1.0, abs(energy_diff) / threshold_center)
        details['confidence'] = confidence
        
        # 4. 计算概率分布（用于不确定性量化）
        # 假设能量值服从正态分布，计算概率密度
        std = threshold_center * 0.2  # 标准差（可配置）
        probability_density = np.exp(-0.5 * (energy_diff / std) ** 2) / (std * np.sqrt(2 * np.pi))
        details['probability_density'] = probability_density
        details['std'] = std
        
        # 5. 分类标签（用于向后兼容）
        if strength_probability > 0.7:
            strength_label = 'strong'
        elif strength_probability < 0.3:
            strength_label = 'weak'
        else:
            strength_label = 'neutral'
        details['strength_label'] = strength_label
        
        logger.debug(f"旺衰概率计算: energy_sum={energy_sum:.2f}, "
                    f"threshold_center={threshold_center:.2f}, "
                    f"strength_probability={strength_probability:.4f}, "
                    f"label={strength_label}")
        
        return strength_probability, details
    
    @staticmethod
    def calculate_strength_distribution(
        energy_sum: float,
        threshold_center: float = 3.0,
        phase_transition_width: float = 10.0,
        n_samples: int = 1000,
        config: Optional[Dict] = None
    ) -> Dict[str, np.ndarray]:
        """
        计算旺衰概率分布（蒙特卡洛模拟）
        
        Args:
            energy_sum: 能量总和（原始值）
            threshold_center: 激活函数中心点
            phase_transition_width: 相变宽度
            n_samples: 采样数量
            config: 配置参数（可选）
        
        Returns:
            概率分布字典，包含：
            - probabilities: 旺衰概率样本
            - mean: 均值
            - std: 标准差
            - percentiles: 百分位数 (p25, p50, p75)
        """
        if config is None:
            config = {}
        
        threshold_center = config.get('energy_threshold_center', threshold_center)
        phase_transition_width = config.get('phase_transition_width', 
                                            config.get('strength_beta', phase_transition_width))
        
        # 假设能量值有不确定性（标准差）
        std = threshold_center * 0.2
        energy_samples = np.random.normal(energy_sum, std, n_samples)
        
        # 计算每个样本的旺衰概率
        probabilities = []
        for energy in energy_samples:
            k = phase_transition_width
            energy_diff = energy - threshold_center
            prob = 1.0 / (1.0 + np.exp(-k * energy_diff))
            probabilities.append(prob)
        
        probabilities = np.array(probabilities)
        
        return {
            'probabilities': probabilities,
            'mean': np.mean(probabilities),
            'std': np.std(probabilities),
            'p25': np.percentile(probabilities, 25),
            'p50': np.percentile(probabilities, 50),
            'p75': np.percentile(probabilities, 75)
        }
    
    @staticmethod
    def optimize_threshold_center(
        case_data_list: list,
        objective_func: callable,
        search_range: Tuple[float, float] = (1.0, 5.0),
        n_iterations: int = 50
    ) -> float:
        """
        优化激活函数中心点
        
        通过贝叶斯优化或网格搜索，寻找大多数案例的能量中枢
        
        Args:
            case_data_list: 案例数据列表
            objective_func: 目标函数（接受 threshold_center，返回损失值）
            search_range: 搜索范围
            n_iterations: 迭代次数
        
        Returns:
            最优的 threshold_center 值
        """
        logger.info(f"开始优化激活函数中心点，搜索范围: {search_range}")
        
        # 简单的网格搜索（可以替换为贝叶斯优化）
        best_threshold = None
        best_loss = float('inf')
        
        threshold_values = np.linspace(search_range[0], search_range[1], n_iterations)
        
        for threshold in threshold_values:
            loss = objective_func(threshold)
            if loss < best_loss:
                best_loss = loss
                best_threshold = threshold
        
        logger.info(f"✅ 最优激活函数中心点: {best_threshold:.4f}, 最优损失: {best_loss:.4f}")
        return best_threshold

