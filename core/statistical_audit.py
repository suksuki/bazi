"""
[QGA V25.0] 统计审计工具模块 (Statistical Audit Utilities)
RSS-V1.4规范：通用统计方法，供格局审计复用

功能：
- 离群值检测（Z-Score、IQR）
- 梯度消失判定
- 分布统计（均值、标准差、偏度）
- 奇点存在性验证（统计层面）

作者: Antigravity Team
版本: V1.4
日期: 2025-12-28
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class StatisticalAuditor:
    """
    统计审计器（RSS-V1.4规范）
    
    提供通用的统计方法，用于格局审计中的：
    - 离群值检测（动态奇点判定）
    - 梯度消失判定（逻辑平滑检测）
    - 分布统计（全量样本分析）
    """
    
    def __init__(self, z_score_threshold: float = 3.0, gradient_threshold: float = 0.05):
        """
        初始化统计审计器
        
        Args:
            z_score_threshold: Z-Score阈值（默认3.0，即3-Sigma规则）
            gradient_threshold: 梯度消失判定阈值（默认0.05，即5%差异）
        """
        self.z_score_threshold = z_score_threshold
        self.gradient_threshold = gradient_threshold
        logger.info(f"✅ 统计审计器初始化完成（Z-Score阈值={z_score_threshold}, 梯度阈值={gradient_threshold}）")
    
    def detect_outliers(self, 
                       values: List[float],
                       method: str = "combined") -> Dict[str, Any]:
        """
        离群值检测（RSS-V1.4规范：动态离群值检测）
        
        使用Z-Score（3-Sigma规则）和IQR方法检测统计学意义上的离群值。
        
        Args:
            values: 数值列表（如稳定性值）
            method: 检测方法（"z_score", "iqr", "combined"）
            
        Returns:
            包含离群值索引和统计信息的字典
        """
        if not values or len(values) < 2:
            return {
                "outlier_indices": [],
                "normal_indices": list(range(len(values))),
                "statistics": {},
                "has_outliers": False
            }
        
        values_array = np.array(values)
        
        # 计算统计量
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)
        median_val = np.median(values_array)
        min_val = np.min(values_array)
        max_val = np.max(values_array)
        
        # 计算偏度（Skewness）：用于判断是否存在长尾
        skewness = stats.skew(values_array) if len(values_array) > 2 else 0.0
        
        # 方法1：Z-Score检测（3-Sigma规则）
        z_scores = (values_array - mean_val) / (std_val + 1e-6)
        z_outlier_indices = [i for i, z in enumerate(z_scores) if z < -self.z_score_threshold]
        
        # 方法2：IQR检测（作为补充）
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        iqr_outlier_indices = [i for i, v in enumerate(values_array) 
                              if v < lower_bound or v > upper_bound]
        
        # 根据方法选择结果
        if method == "z_score":
            outlier_indices = z_outlier_indices
        elif method == "iqr":
            outlier_indices = iqr_outlier_indices
        else:  # combined
            outlier_indices = list(set(z_outlier_indices + iqr_outlier_indices))
        
        normal_indices = [i for i in range(len(values)) if i not in outlier_indices]
        
        logger.info(f"📊 离群值检测: 总样本={len(values)}, 离群样本={len(outlier_indices)}, "
                   f"均值={mean_val:.4f}, 标准差={std_val:.4f}, 偏度={skewness:.4f}, "
                   f"Z-Score离群={len(z_outlier_indices)}, IQR离群={len(iqr_outlier_indices)}")
        
        return {
            "outlier_indices": outlier_indices,
            "normal_indices": normal_indices,
            "statistics": {
                "mean": float(mean_val),
                "std": float(std_val),
                "median": float(median_val),
                "min": float(min_val),
                "max": float(max_val),
                "skewness": float(skewness),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            },
            "z_scores": [float(z) for z in z_scores],
            "detection_methods": {
                "z_score_outliers": len(z_outlier_indices),
                "iqr_outliers": len(iqr_outlier_indices),
                "combined_outliers": len(outlier_indices),
                "method_used": method
            },
            "has_outliers": len(outlier_indices) > 0
        }
    
    def check_gradient_vanishing(self,
                                 values: List[float],
                                 outlier_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        梯度消失判定（RSS-V1.4规范：逻辑平滑检测）
        
        如果最差样本和平均样本差异极小，判定为"逻辑平滑"，拒绝奇点注册。
        
        Args:
            values: 数值列表（如稳定性值）
            outlier_indices: 离群值索引列表（如果已检测）
            
        Returns:
            包含梯度信息和判定结果的字典
        """
        if not values:
            return {
                "has_gradient": False,
                "gradient": 0.0,
                "gradient_ratio": 0.0,
                "verdict": "no_data"
            }
        
        values_array = np.array(values)
        mean_val = np.mean(values_array)
        
        if outlier_indices:
            # 如果有离群值，使用离群值中的最小值
            outlier_values = [values[i] for i in outlier_indices]
            worst_val = min(outlier_values)
        else:
            # 否则使用全局最小值
            worst_val = np.min(values_array)
        
        gradient = mean_val - worst_val
        gradient_ratio = gradient / (mean_val + 1e-6)  # 相对差异百分比
        
        # RSS-V1.4规范：如果差异小于20%，判定为逻辑平滑
        has_gradient = gradient > self.gradient_threshold and gradient_ratio > 0.20
        
        verdict = "has_gradient" if has_gradient else "gradient_vanished"
        
        logger.info(f"🔍 梯度消失判定: 均值={mean_val:.4f}, 最差值={worst_val:.4f}, "
                   f"梯度={gradient:.4f}, 相对差异={gradient_ratio*100:.2f}%, "
                   f"判定={verdict}")
        
        return {
            "has_gradient": has_gradient,
            "gradient": float(gradient),
            "gradient_ratio": float(gradient_ratio),
            "mean": float(mean_val),
            "worst": float(worst_val),
            "verdict": verdict
        }
    
    def calculate_distribution_stats(self, values: List[float]) -> Dict[str, Any]:
        """
        计算分布统计量（RSS-V1.4规范：全量分布审计）
        
        Args:
            values: 数值列表
            
        Returns:
            包含完整统计信息的字典
        """
        if not values:
            return {}
        
        values_array = np.array(values)
        
        stats_dict = {
            "count": len(values),
            "mean": float(np.mean(values_array)),
            "std": float(np.std(values_array)),
            "median": float(np.median(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "q1": float(np.percentile(values_array, 25)),
            "q3": float(np.percentile(values_array, 75)),
            "iqr": float(np.percentile(values_array, 75) - np.percentile(values_array, 25)),
        }
        
        # 计算偏度（Skewness）
        if len(values_array) > 2:
            stats_dict["skewness"] = float(stats.skew(values_array))
            stats_dict["kurtosis"] = float(stats.kurtosis(values_array))
        else:
            stats_dict["skewness"] = 0.0
            stats_dict["kurtosis"] = 0.0
        
        # 计算动态离群红线（RSS-V1.4规范）
        mean_val = stats_dict["mean"]
        std_val = stats_dict["std"]
        dynamic_threshold = min(0.15, mean_val - 3 * std_val)
        stats_dict["dynamic_singularity_threshold"] = float(dynamic_threshold)
        
        return stats_dict
    
    def verify_singularity_existence(self,
                                    values: List[float],
                                    outlier_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        奇点存在性验证（RSS-V1.4规范：统计层面验证）
        
        结合离群值检测和梯度消失判定，验证是否存在真正的奇点。
        
        Args:
            values: 数值列表
            outlier_indices: 离群值索引列表（如果已检测）
            
        Returns:
            包含验证结果的字典
        """
        # 1. 离群值检测
        outlier_result = self.detect_outliers(values, method="combined")
        
        # 2. 梯度消失判定
        gradient_result = self.check_gradient_vanishing(
            values, 
            outlier_indices=outlier_result["outlier_indices"]
        )
        
        # 3. 综合判定
        has_outliers = outlier_result["has_outliers"]
        has_gradient = gradient_result["has_gradient"]
        
        # RSS-V1.4规范：只有同时满足"存在离群值"和"存在梯度"时，才判定为存在奇点
        singularity_exists = has_outliers and has_gradient
        
        verdict = "singularity_exists" if singularity_exists else "no_singularity"
        
        if not singularity_exists:
            if not has_outliers:
                reason = "no_statistical_outliers"
            elif not has_gradient:
                reason = "gradient_vanished"
            else:
                reason = "unknown"
        else:
            reason = "verified"
        
        logger.info(f"✅ 奇点存在性验证: 离群值={has_outliers}, 梯度={has_gradient}, "
                   f"综合判定={verdict}, 原因={reason}")
        
        return {
            "singularity_exists": singularity_exists,
            "verdict": verdict,
            "reason": reason,
            "outlier_detection": outlier_result,
            "gradient_check": gradient_result,
            "statistics": self.calculate_distribution_stats(values)
        }


# 全局单例实例
_global_auditor = None

def get_statistical_auditor(z_score_threshold: float = 3.0, 
                           gradient_threshold: float = 0.05) -> StatisticalAuditor:
    """
    获取全局统计审计器实例（单例模式）
    
    Args:
        z_score_threshold: Z-Score阈值
        gradient_threshold: 梯度阈值
        
    Returns:
        StatisticalAuditor实例
    """
    global _global_auditor
    if _global_auditor is None:
        _global_auditor = StatisticalAuditor(z_score_threshold, gradient_threshold)
    return _global_auditor

