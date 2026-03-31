#!/usr/bin/env python3
"""
GAT 路径过滤模块
================

过滤掉对财富指数贡献低于阈值的无效注意力路径
使核心路径（如"未→丑"）更加聚焦
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class GATPathFilter:
    """
    GAT 路径过滤器
    根据路径强度过滤注意力路径
    """
    
    def __init__(self, threshold: float = 0.1):
        """
        初始化路径过滤器
        
        Args:
            threshold: 路径过滤阈值（低于此值的路径将被过滤）
        """
        self.threshold = threshold
    
    def filter_paths(self, 
                    attention_weights: Dict[Tuple[int, int], float],
                    energy_paths: List[Dict[str, float]]) -> Dict[Tuple[int, int], float]:
        """
        过滤注意力路径
        
        Args:
            attention_weights: 注意力权重字典 {(节点i, 节点j): 权重}
            energy_paths: 能量路径列表
            
        Returns:
            过滤后的注意力权重字典
        """
        filtered_weights = {}
        
        for (i, j), weight in attention_weights.items():
            # 计算路径强度
            path_strength = self._calculate_path_strength(i, j, energy_paths)
            
            # 如果路径强度高于阈值，保留
            if path_strength >= self.threshold:
                filtered_weights[(i, j)] = weight
            else:
                logger.debug(f"过滤路径 ({i}, {j}): 强度 {path_strength:.4f} < 阈值 {self.threshold}")
        
        # 重新归一化
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            filtered_weights = {k: v / total_weight for k, v in filtered_weights.items()}
        
        logger.info(f"路径过滤: {len(attention_weights)} -> {len(filtered_weights)} "
                   f"(阈值: {self.threshold})")
        
        return filtered_weights
    
    def _calculate_path_strength(self, 
                                 node_i: int, 
                                 node_j: int,
                                 energy_paths: List[Dict[str, float]]) -> float:
        """
        计算路径强度
        
        Args:
            node_i: 起始节点
            node_j: 目标节点
            energy_paths: 能量路径列表
            
        Returns:
            路径强度（0-1）
        """
        # 查找包含此路径的能量路径
        for path in energy_paths:
            path_key = f"{node_i}->{node_j}"
            if path_key in path:
                return path[path_key]
        
        # 如果没有找到，返回默认值
        return 0.0
    
    def optimize_threshold(self,
                          attention_weights: Dict[Tuple[int, int], float],
                          energy_paths: List[Dict[str, float]],
                          objective_func: callable) -> float:
        """
        优化过滤阈值
        
        Args:
            attention_weights: 注意力权重字典
            energy_paths: 能量路径列表
            objective_func: 目标函数（接受阈值，返回损失值）
            
        Returns:
            最优阈值
        """
        logger.info("开始优化路径过滤阈值")
        
        # 搜索阈值范围
        thresholds = np.linspace(0.01, 0.5, 50)
        
        best_threshold = None
        best_loss = float('inf')
        
        for threshold in thresholds:
            self.threshold = threshold
            filtered = self.filter_paths(attention_weights, energy_paths)
            loss = objective_func(filtered)
            
            if loss < best_loss:
                best_loss = loss
                best_threshold = threshold
        
        logger.info(f"✅ 最优阈值: {best_threshold:.4f}, 最优损失: {best_loss:.4f}")
        return best_threshold


class SystemEntropyController:
    """
    系统熵控制器
    通过调整熵参数来过滤无效的注意力路径
    """
    
    def __init__(self, base_entropy: float = 0.1):
        """
        初始化熵控制器
        
        Args:
            base_entropy: 基础熵值
        """
        self.base_entropy = base_entropy
    
    def calculate_path_entropy(self, 
                              attention_weights: Dict[Tuple[int, int], float]) -> float:
        """
        计算路径熵
        
        Args:
            attention_weights: 注意力权重字典
            
        Returns:
            路径熵值
        """
        weights = np.array(list(attention_weights.values()))
        weights = weights / weights.sum()  # 归一化
        
        # 计算熵: H = -Σ p_i * log(p_i)
        entropy = -np.sum(weights * np.log(weights + 1e-10))
        
        return entropy
    
    def filter_by_entropy(self,
                         attention_weights: Dict[Tuple[int, int], float],
                         max_entropy: float = 2.0) -> Dict[Tuple[int, int], float]:
        """
        根据熵值过滤路径
        
        Args:
            attention_weights: 注意力权重字典
            max_entropy: 最大允许熵值
            
        Returns:
            过滤后的注意力权重字典
        """
        current_entropy = self.calculate_path_entropy(attention_weights)
        
        if current_entropy <= max_entropy:
            return attention_weights
        
        # 如果熵值过高，过滤掉权重较小的路径
        sorted_paths = sorted(attention_weights.items(), key=lambda x: x[1], reverse=True)
        
        filtered_weights = {}
        cumulative_weight = 0.0
        
        for (i, j), weight in sorted_paths:
            filtered_weights[(i, j)] = weight
            cumulative_weight += weight
            
            # 检查熵值
            temp_entropy = self.calculate_path_entropy(filtered_weights)
            if temp_entropy <= max_entropy:
                break
        
        # 重新归一化
        total_weight = sum(filtered_weights.values())
        if total_weight > 0:
            filtered_weights = {k: v / total_weight for k, v in filtered_weights.items()}
        
        logger.info(f"熵过滤: 原始熵 {current_entropy:.4f} -> 过滤后熵 {self.calculate_path_entropy(filtered_weights):.4f}")
        
        return filtered_weights

