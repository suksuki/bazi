#!/usr/bin/env python3
"""
贝叶斯旺衰自校准模块 (Bayesian Strength Self-Calibration)
========================================================

V10.0 改进：旺衰判定的"贝叶斯自校准"
如果第二阶段的"财富预测"与实际值偏差巨大，自动反向推导第一阶段的旺衰判定是否错误

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BayesianStrengthCalibration:
    """
    贝叶斯旺衰自校准
    通过财富预测误差自动反向推导旺衰判定是否正确
    """
    
    @staticmethod
    def calculate_strength_confidence(
        strength_probability: float,
        energy_sum: float,
        threshold_center: float = 3.0,
        config: Optional[Dict] = None
    ) -> float:
        """
        计算旺衰置信度
        
        Args:
            strength_probability: 旺衰概率 [0, 1]
            energy_sum: 能量总和
            threshold_center: 激活函数中心点
            config: 配置参数（可选）
        
        Returns:
            置信度 [0, 1]，0 表示完全不置信，1 表示完全置信
        """
        if config is None:
            config = {}
        
        threshold_center = config.get('energy_threshold_center', threshold_center)
        
        # 计算能量差值
        energy_diff = abs(energy_sum - threshold_center)
        
        # 置信度基于：
        # 1. 能量差值的大小（差值越大，置信度越高）
        # 2. 旺衰概率的极端程度（接近 0 或 1 时置信度更高）
        
        # 能量差值贡献
        energy_confidence = min(1.0, energy_diff / threshold_center)
        
        # 概率极端程度贡献
        probability_confidence = abs(strength_probability - 0.5) * 2  # [0, 1]
        
        # 综合置信度
        confidence = (energy_confidence + probability_confidence) / 2.0
        
        return confidence
    
    @staticmethod
    def reverse_infer_strength_error(
        predicted_wealth: float,
        real_wealth: float,
        strength_probability: float,
        wealth_error_threshold: float = 50.0
    ) -> Tuple[bool, float]:
        """
        反向推断旺衰判定错误
        
        如果财富预测误差巨大，可能是旺衰判定错误
        
        Args:
            predicted_wealth: 预测的财富值
            real_wealth: 真实的财富值
            strength_probability: 当前的旺衰概率
            wealth_error_threshold: 财富误差阈值
        
        Returns:
            (is_error, suggested_strength_probability)
            - is_error: 是否判定为错误
            - suggested_strength_probability: 建议的旺衰概率
        """
        error = abs(predicted_wealth - real_wealth)
        
        # 如果误差超过阈值，可能是旺衰判定错误
        if error > wealth_error_threshold:
            # 反向推断：如果预测值远小于真实值，可能是身强判定为身弱
            # 如果预测值远大于真实值，可能是身弱判定为身强
            
            if predicted_wealth < real_wealth:
                # 预测值偏小，可能是身强判定为身弱
                # 建议增加旺衰概率
                suggested_probability = min(1.0, strength_probability + 0.2)
                is_error = True
            elif predicted_wealth > real_wealth:
                # 预测值偏大，可能是身弱判定为身强
                # 建议降低旺衰概率
                suggested_probability = max(0.0, strength_probability - 0.2)
                is_error = True
            else:
                suggested_probability = strength_probability
                is_error = False
        else:
            suggested_probability = strength_probability
            is_error = False
        
        logger.debug(f"反向推断旺衰错误: error={error:.2f}, "
                    f"is_error={is_error}, "
                    f"current_prob={strength_probability:.4f}, "
                    f"suggested_prob={suggested_probability:.4f}")
        
        return is_error, suggested_probability
    
    @staticmethod
    def auto_adjust_threshold_center(
        case_results: List[Dict],
        current_threshold: float = 3.0,
        learning_rate: float = 0.01
    ) -> float:
        """
        自动调整激活函数中心点
        
        基于多个案例的预测误差，自动调整全局基准
        
        Args:
            case_results: 案例结果列表，每个结果包含：
                - predicted_wealth: 预测财富值
                - real_wealth: 真实财富值
                - strength_probability: 旺衰概率
                - energy_sum: 能量总和
            current_threshold: 当前的阈值中心点
            learning_rate: 学习率
        
        Returns:
            调整后的阈值中心点
        """
        logger.info(f"开始自动调整激活函数中心点，当前值: {current_threshold:.4f}")
        
        total_adjustment = 0.0
        adjustment_count = 0
        
        for result in case_results:
            predicted = result.get('predicted_wealth', 0.0)
            real = result.get('real_wealth', 0.0)
            strength_prob = result.get('strength_probability', 0.5)
            energy_sum = result.get('energy_sum', current_threshold)
            
            error = abs(predicted - real)
            
            # 如果误差较大，调整阈值
            if error > 30.0:  # 误差阈值
                # 计算调整方向
                if predicted < real:
                    # 预测偏小，可能是阈值太高，需要降低
                    adjustment = -learning_rate * error / 100.0
                else:
                    # 预测偏大，可能是阈值太低，需要提高
                    adjustment = learning_rate * error / 100.0
                
                total_adjustment += adjustment
                adjustment_count += 1
        
        if adjustment_count > 0:
            avg_adjustment = total_adjustment / adjustment_count
            new_threshold = current_threshold + avg_adjustment
            
            # 限制阈值范围
            new_threshold = max(1.0, min(5.0, new_threshold))
            
            logger.info(f"✅ 调整激活函数中心点: {current_threshold:.4f} -> {new_threshold:.4f}")
            return new_threshold
        else:
            logger.info("无需调整激活函数中心点")
            return current_threshold
    
    @staticmethod
    def calculate_uncertainty_factors(
        strength_probability: float,
        energy_sum: float,
        threshold_center: float = 3.0,
        config: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        计算不确定性因子
        
        用于量化旺衰判定的不确定性
        
        Args:
            strength_probability: 旺衰概率
            energy_sum: 能量总和
            threshold_center: 激活函数中心点
            config: 配置参数（可选）
        
        Returns:
            不确定性因子字典
        """
        if config is None:
            config = {}
        
        threshold_center = config.get('energy_threshold_center', threshold_center)
        
        # 1. 能量差值不确定性
        energy_diff = abs(energy_sum - threshold_center)
        energy_uncertainty = 1.0 / (1.0 + energy_diff / threshold_center)
        
        # 2. 概率极端程度不确定性
        # 接近 0.5 时不确定性最高
        probability_uncertainty = 1.0 - abs(strength_probability - 0.5) * 2
        
        # 3. 综合不确定性
        total_uncertainty = (energy_uncertainty + probability_uncertainty) / 2.0
        
        return {
            'energy_uncertainty': energy_uncertainty,
            'probability_uncertainty': probability_uncertainty,
            'total_uncertainty': total_uncertainty
        }

