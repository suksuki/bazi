"""
[QGA V25.0] 自动权重拟合模块 (AutoTuner)
RSS-V1.2规范：根据仿真偏差自动修正应力权重与坍缩阈值
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class AutoTuner:
    """
    自动权重拟合器（RSS-V1.1规范）
    
    根据Step B仿真结果与预期偏差，自动拟合最优参数：
    - stress_tensor_weight: 应力张量权重
    - collapse_threshold: 坍缩阈值
    """
    
    def __init__(self, 
                 initial_stress_weight: float = 1.0,
                 initial_collapse_threshold: float = 0.6):
        """
        初始化自动拟合器
        
        Args:
            initial_stress_weight: 初始应力权重
            initial_collapse_threshold: 初始坍缩阈值
        """
        self.initial_stress_weight = initial_stress_weight
        self.initial_collapse_threshold = initial_collapse_threshold
        logger.info("✅ AutoTuner 初始化完成（RSS-V1.2规范）")
    
    def calculate_deviation(self, 
                           predicted_stability: float,
                           actual_stability: float) -> float:
        """
        计算预测稳定性与实际稳定性的偏差
        
        Args:
            predicted_stability: 预测的稳定性
            actual_stability: 实际的稳定性（来自Step B仿真）
        
        Returns:
            偏差值（绝对值）
        """
        return abs(predicted_stability - actual_stability)
    
    def fit_optimal_parameters(self,
                              simulation_results: List[Dict[str, Any]],
                              target_stability_range: Tuple[float, float] = (0.3, 0.5)) -> Dict[str, Any]:
        """
        根据仿真结果自动拟合最优参数
        
        Args:
            simulation_results: Step B仿真结果列表
            target_stability_range: 目标稳定性范围（min, max）
        
        Returns:
            拟合结果，包含：
            - optimized_stress_weight: 优化后的应力权重
            - optimized_collapse_threshold: 优化后的坍缩阈值
            - parameter_diff: 参数变化
            - fitting_metrics: 拟合指标
        """
        logger.info("🔧 开始自动权重拟合...")
        
        if not simulation_results:
            logger.warning("⚠️  仿真结果为空，返回初始参数")
            return {
                "optimized_stress_weight": self.initial_stress_weight,
                "optimized_collapse_threshold": self.initial_collapse_threshold,
                "parameter_diff": {
                    "stress_weight": 0.0,
                    "collapse_threshold": 0.0
                },
                "fitting_metrics": {
                    "total_samples": 0,
                    "average_deviation": 0.0
                }
            }
        
        # 提取关键数据
        deviations = []
        stress_tensors = []
        actual_stabilities = []
        
        for sim in simulation_results:
            sample = sim.get('sample', {})
            actual_stability = sim.get('system_stability', 0.0)
            stress_tensor = sample.get('stress_tensor', 0.0)
            
            # 计算预测稳定性（基于初始参数）
            predicted_stability = self._predict_stability(
                stress_tensor=stress_tensor,
                stress_weight=self.initial_stress_weight,
                collapse_threshold=self.initial_collapse_threshold
            )
            
            deviation = self.calculate_deviation(predicted_stability, actual_stability)
            deviations.append(deviation)
            stress_tensors.append(stress_tensor)
            actual_stabilities.append(actual_stability)
        
        # 计算平均偏差
        avg_deviation = np.mean(deviations) if deviations else 0.0
        
        # 简单的拟合策略：根据偏差调整参数
        # 如果实际稳定性普遍低于预测，降低collapse_threshold
        # 如果偏差较大，调整stress_weight
        
        avg_actual_stability = np.mean(actual_stabilities) if actual_stabilities else 0.5
        avg_stress_tensor = np.mean(stress_tensors) if stress_tensors else 0.5
        
        # 拟合逻辑：
        # 1. 如果平均实际稳定性 < 目标范围下限，说明collapse_threshold太高，需要降低
        # 2. 如果平均偏差 > 0.1，说明stress_weight需要调整
        
        optimized_collapse_threshold = self.initial_collapse_threshold
        optimized_stress_weight = self.initial_stress_weight
        
        if avg_actual_stability < target_stability_range[0]:
            # 实际稳定性偏低，降低collapse_threshold
            optimized_collapse_threshold = max(0.15, avg_actual_stability + 0.1)
            logger.info(f"📉 实际稳定性偏低，降低collapse_threshold: {self.initial_collapse_threshold:.3f} -> {optimized_collapse_threshold:.3f}")
        
        if avg_deviation > 0.1:
            # 偏差较大，调整stress_weight
            # 如果实际稳定性普遍低于预测，增加stress_weight的影响
            if avg_actual_stability < 0.4:
                optimized_stress_weight = min(1.5, self.initial_stress_weight * 1.25)
            else:
                optimized_stress_weight = max(0.5, self.initial_stress_weight * 0.9)
            logger.info(f"🔧 偏差较大，调整stress_weight: {self.initial_stress_weight:.3f} -> {optimized_stress_weight:.3f}")
        
        parameter_diff = {
            "stress_weight": optimized_stress_weight - self.initial_stress_weight,
            "collapse_threshold": optimized_collapse_threshold - self.initial_collapse_threshold
        }
        
        fitting_metrics = {
            "total_samples": len(simulation_results),
            "average_deviation": avg_deviation,
            "average_actual_stability": avg_actual_stability,
            "average_stress_tensor": avg_stress_tensor
        }
        
        logger.info(f"✅ 自动权重拟合完成: stress_weight={optimized_stress_weight:.3f}, collapse_threshold={optimized_collapse_threshold:.3f}")
        
        return {
            "optimized_stress_weight": optimized_stress_weight,
            "optimized_collapse_threshold": optimized_collapse_threshold,
            "parameter_diff": parameter_diff,
            "fitting_metrics": fitting_metrics
        }
    
    def _predict_stability(self,
                          stress_tensor: float,
                          stress_weight: float,
                          collapse_threshold: float) -> float:
        """
        基于参数预测稳定性
        
        Args:
            stress_tensor: 应力张量
            stress_weight: 应力权重
            collapse_threshold: 坍缩阈值
        
        Returns:
            预测的稳定性
        """
        # 简化的预测模型：稳定性 = 1 - (stress_tensor * stress_weight - collapse_threshold)
        predicted = 1.0 - max(0.0, (stress_tensor * stress_weight - collapse_threshold))
        return max(0.0, min(1.0, predicted))

