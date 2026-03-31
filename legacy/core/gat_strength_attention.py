#!/usr/bin/env python3
"""
GAT 旺衰动态注意力模块 (GAT Strength Dynamic Attention)
======================================================

V10.0 改进：基础参数的"解耦"调优
利用 GAT 动态注意力，针对不同命局结构学习专门的旺衰评估权重

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class GATStrengthAttention:
    """
    GAT 旺衰动态注意力
    针对不同命局结构（如"财库多"、"官印相生"）学习专门的旺衰评估权重
    """
    
    def __init__(self, n_heads: int = 4, hidden_dim: int = 64, dropout: float = 0.1):
        """
        初始化 GAT 旺衰注意力
        
        Args:
            n_heads: 注意力头数量
            hidden_dim: 隐藏层维度
            dropout: 注意力稀疏度（防止过度关注细微路径）
        """
        self.n_heads = n_heads
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        
        # 初始化权重矩阵（简化版，实际应使用 PyTorch/TensorFlow）
        self.W_q = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.W_k = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.W_v = np.random.randn(hidden_dim, hidden_dim) * 0.01
    
    def calculate_dynamic_strength_weights(
        self,
        bazi_features: Dict[str, float],
        pattern_type: str = 'unknown',
        config: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        计算动态旺衰权重
        
        根据命局特征（如"财库多"、"官印相生"）动态调整基础参数的权重
        
        Args:
            bazi_features: 八字特征字典，包含：
                - has_vault: 是否有财库
                - has_officer: 是否有官星
                - has_seal: 是否有印星
                - has_wealth: 是否有财星
                - clash_count: 冲的数量
                - combination_count: 合的数量
            pattern_type: 命局类型（'wealth_vault', 'officer_seal', 'unknown'）
            config: 配置参数（可选）
        
        Returns:
            动态权重字典，包含：
                - water_fire_weight: 水克火的权重
                - fire_metal_weight: 火克金的权重
                - metal_wood_weight: 金克木的权重
                - wood_earth_weight: 木克土的权重
                - earth_water_weight: 土克水的权重
        """
        if config is None:
            config = {}
        
        # 基础权重（全局默认值）
        base_weights = {
            'water_fire_weight': 0.5,
            'fire_metal_weight': 0.5,
            'metal_wood_weight': 0.5,
            'wood_earth_weight': 0.5,
            'earth_water_weight': 0.5
        }
        
        # 根据命局类型调整权重
        if pattern_type == 'wealth_vault':
            # 财库多的命局：增强土对水的抑制
            base_weights['earth_water_weight'] = 0.7
            base_weights['water_fire_weight'] = 0.4
        elif pattern_type == 'officer_seal':
            # 官印相生的命局：增强金对木的抑制
            base_weights['metal_wood_weight'] = 0.7
            base_weights['wood_earth_weight'] = 0.4
        
        # 根据特征动态调整
        if bazi_features.get('has_vault', False):
            # 有财库：增强土相关权重
            base_weights['earth_water_weight'] *= 1.2
            base_weights['wood_earth_weight'] *= 0.9
        
        if bazi_features.get('clash_count', 0) > 2:
            # 冲多：降低所有权重（增加不确定性）
            for key in base_weights:
                base_weights[key] *= 0.9
        
        # 应用 dropout（注意力稀疏度）
        if self.dropout > 0:
            for key in base_weights:
                if np.random.random() < self.dropout:
                    base_weights[key] *= 0.1  # 大幅降低权重
        
        # 归一化
        total = sum(base_weights.values())
        if total > 0:
            base_weights = {k: v / total * len(base_weights) for k, v in base_weights.items()}
        
        logger.debug(f"动态旺衰权重: pattern_type={pattern_type}, weights={base_weights}")
        
        return base_weights
    
    def identify_pattern_type(self, bazi: List[str], day_master: str) -> str:
        """
        识别命局类型
        
        Args:
            bazi: 八字列表
            day_master: 日主
        
        Returns:
            命局类型（'wealth_vault', 'officer_seal', 'unknown'）
        """
        # 简化的命局识别逻辑
        vault_count = 0
        officer_count = 0
        seal_count = 0
        
        vaults = ['丑', '辰', '未', '戌']
        officers = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        seals = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        
        for pillar in bazi:
            if len(pillar) >= 2:
                branch = pillar[1]
                if branch in vaults:
                    vault_count += 1
        
        # 判断命局类型
        if vault_count >= 2:
            return 'wealth_vault'
        elif officer_count > 0 and seal_count > 0:
            return 'officer_seal'
        else:
            return 'unknown'
    
    def calculate_attention_weights(
        self,
        node_features: np.ndarray,
        adjacency_matrix: np.ndarray
    ) -> np.ndarray:
        """
        计算注意力权重矩阵
        
        Args:
            node_features: 节点特征矩阵 [n_nodes, hidden_dim]
            adjacency_matrix: 邻接矩阵 [n_nodes, n_nodes]
        
        Returns:
            注意力权重矩阵 [n_nodes, n_nodes]
        """
        n_nodes = node_features.shape[0]
        
        # 计算 Query, Key, Value
        Q = node_features @ self.W_q
        K = node_features @ self.W_k
        V = node_features @ self.W_v
        
        # 计算注意力分数
        scores = Q @ K.T / np.sqrt(self.hidden_dim)
        
        # 应用邻接矩阵掩码
        scores = np.where(adjacency_matrix > 0, scores, -np.inf)
        
        # Softmax
        exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
        attention_weights = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
        
        # 应用 dropout
        if self.dropout > 0:
            dropout_mask = np.random.random(attention_weights.shape) > self.dropout
            attention_weights = attention_weights * dropout_mask
            attention_weights = attention_weights / np.sum(attention_weights, axis=1, keepdims=True)
        
        return attention_weights

