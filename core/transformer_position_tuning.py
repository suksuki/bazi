#!/usr/bin/env python3
"""
Transformer 位置编码调优模块
============================

调优 Transformer 的位置编码参数，平衡"远期积压能量"与"近期突发能量"的权重
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PositionalEncodingTuner:
    """
    位置编码调优器
    调整位置编码的参数，影响系统对时间距离的感知
    """
    
    def __init__(self, d_model: int = 128, max_length: int = 100):
        """
        初始化位置编码调优器
        
        Args:
            d_model: 模型维度
            max_length: 最大序列长度
        """
        self.d_model = d_model
        self.max_length = max_length
    
    def generate_positional_encoding(self, 
                                     position_scale: float = 10000.0,
                                     decay_factor: float = 1.0) -> np.ndarray:
        """
        生成位置编码
        
        Args:
            position_scale: 位置缩放因子（影响位置编码的周期）
            decay_factor: 衰减因子（影响远期能量的权重）
            
        Returns:
            位置编码矩阵 [max_length, d_model]
        """
        pe = np.zeros((self.max_length, self.d_model))
        
        for pos in range(self.max_length):
            for i in range(0, self.d_model, 2):
                # 应用衰减因子（位置越远，衰减越大）
                effective_pos = pos * decay_factor
                
                # 正弦编码
                pe[pos, i] = np.sin(effective_pos / (position_scale ** (2 * i / self.d_model)))
                
                # 余弦编码
                if i + 1 < self.d_model:
                    pe[pos, i + 1] = np.cos(effective_pos / (position_scale ** (2 * (i + 1) / self.d_model)))
        
        return pe
    
    def tune_for_long_range_dependency(self, 
                                       timeline_data: List[Dict],
                                       objective_func: callable) -> Dict[str, float]:
        """
        针对长程依赖调优位置编码参数
        
        Args:
            timeline_data: 时间线数据
            objective_func: 目标函数（接受位置编码参数，返回损失值）
            
        Returns:
            最优参数字典
        """
        logger.info("开始调优位置编码参数（长程依赖）")
        
        # 参数搜索空间
        position_scales = np.logspace(3, 5, 10)  # 1000 到 100000
        decay_factors = np.linspace(0.5, 1.5, 10)  # 衰减因子
        
        best_params = None
        best_loss = float('inf')
        
        for pos_scale in position_scales:
            for decay in decay_factors:
                params = {
                    'position_scale': pos_scale,
                    'decay_factor': decay
                }
                loss = objective_func(params)
                
                if loss < best_loss:
                    best_loss = loss
                    best_params = params
        
        logger.info(f"✅ 最优参数: {best_params}, 最优损失: {best_loss:.4f}")
        return best_params


class MultiScaleTemporalFusion:
    """
    多尺度时序融合模块
    平衡不同时间尺度的能量贡献
    """
    
    def __init__(self):
        """初始化多尺度时序融合模块"""
        self.scales = ['short_term', 'medium_term', 'long_term']
        self.scale_weights = {
            'short_term': 0.3,   # 近期（0-10年）
            'medium_term': 0.4,  # 中期（10-30年）
            'long_term': 0.3     # 远期（30+年）
        }
    
    def fuse_temporal_features(self, 
                              timeline_data: List[Dict],
                              scale_weights: Optional[Dict[str, float]] = None) -> np.ndarray:
        """
        融合多尺度时序特征
        
        Args:
            timeline_data: 时间线数据
            scale_weights: 尺度权重（可选）
            
        Returns:
            融合后的特征向量
        """
        if scale_weights is None:
            scale_weights = self.scale_weights
        
        # 按时间尺度分组
        short_term = [d for d in timeline_data if d.get('year', 0) >= 2005]
        medium_term = [d for d in timeline_data if 1995 <= d.get('year', 0) < 2005]
        long_term = [d for d in timeline_data if d.get('year', 0) < 1995]
        
        # 计算各尺度的特征
        short_features = self._extract_features(short_term)
        medium_features = self._extract_features(medium_term)
        long_features = self._extract_features(long_term)
        
        # 加权融合
        fused = (scale_weights['short_term'] * short_features +
                scale_weights['medium_term'] * medium_features +
                scale_weights['long_term'] * long_features)
        
        return fused
    
    def _extract_features(self, data: List[Dict]) -> np.ndarray:
        """提取特征（简化版）"""
        if not data:
            return np.zeros(10)  # 默认特征维度
        
        # 提取能量特征
        energies = [d.get('energy', 0.0) for d in data]
        return np.array([
            np.mean(energies),
            np.std(energies),
            np.max(energies),
            np.min(energies),
            len(energies),
            # ... 更多特征
        ])
    
    def optimize_scale_weights(self, 
                               timeline_data: List[Dict],
                               ground_truth: List[float],
                               objective_func: callable) -> Dict[str, float]:
        """
        优化尺度权重
        
        Args:
            timeline_data: 时间线数据
            ground_truth: 真实值
            objective_func: 目标函数
            
        Returns:
            最优权重字典
        """
        logger.info("开始优化多尺度时序融合权重")
        
        # 网格搜索
        best_weights = None
        best_loss = float('inf')
        
        for w1 in np.linspace(0.1, 0.5, 10):
            for w2 in np.linspace(0.2, 0.6, 10):
                w3 = 1.0 - w1 - w2
                if w3 < 0.1 or w3 > 0.5:
                    continue
                
                weights = {
                    'short_term': w1,
                    'medium_term': w2,
                    'long_term': w3
                }
                
                loss = objective_func(weights)
                
                if loss < best_loss:
                    best_loss = loss
                    best_weights = weights
        
        logger.info(f"✅ 最优权重: {best_weights}, 最优损失: {best_loss:.4f}")
        return best_weights

