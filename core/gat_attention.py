"""
图注意力网络模块 (Graph Attention Network - GAT)
=================================================

V10.0 优化：从固定邻接矩阵转向动态注意力机制

核心功能：
1. 动态注意力权重计算
2. Multi-head Attention 支持多条路径
3. 非线性通关路径学习
4. 基于节点状态的动态权重调整

作者: Antigravity Team
版本: V10.0
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import math


class GraphAttentionLayer:
    """图注意力层，用于计算动态注意力权重"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化图注意力层
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        self.num_heads = config.get('num_heads', 4)  # Multi-head 数量
        self.attention_dropout = config.get('attention_dropout', 0.1)
        self.alpha = config.get('leaky_relu_alpha', 0.2)  # LeakyReLU 参数
        
        # 学习参数（简化版，实际应该使用可训练参数）
        self.W = np.eye(5)  # 特征变换矩阵 [5 x 5] (五行特征)
        self.a = np.ones((2 * 5, 1))  # 注意力参数 [10 x 1]
    
    def compute_attention_weights(
        self,
        node_features: np.ndarray,
        node_energies: np.ndarray,
        relation_types: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        计算注意力权重
        
        Args:
            node_features: 节点特征矩阵 [N x F]，F 是特征维度（五行）
            node_energies: 节点能量向量 [N x 1]
            relation_types: 关系类型矩阵 [N x N]，表示节点间的关系类型
                - 1: 生 (Generation)
                - -1: 克 (Control)
                - 2: 合 (Combination)
                - -2: 冲 (Clash)
                - 0: 无关系
            mask: 掩码矩阵 [N x N]，True 表示有效连接
        
        Returns:
            注意力权重矩阵 [N x N]
        """
        N = node_features.shape[0]
        
        # 1. 特征变换
        h = node_features @ self.W  # [N x F]
        
        # 2. 计算注意力分数（简化版，使用能量和关系类型）
        attention_scores = np.zeros((N, N))
        
        for i in range(N):
            for j in range(N):
                if i == j:
                    # 自连接
                    attention_scores[i, j] = 0.0
                    continue
                
                if mask is not None and not mask[i, j]:
                    # 被掩码的连接
                    attention_scores[i, j] = -np.inf
                    continue
                
                # 基础注意力分数 = 节点 j 的能量
                base_score = node_energies[j, 0]
                
                # 关系类型修正
                relation_type = relation_types[i, j]
                if relation_type == 1:  # 生
                    relation_multiplier = 1.5  # 生的权重更高
                elif relation_type == -1:  # 克
                    relation_multiplier = -0.8  # 克的权重为负
                elif relation_type == 2:  # 合
                    relation_multiplier = 1.2  # 合的权重较高
                elif relation_type == -2:  # 冲
                    relation_multiplier = -1.0  # 冲的权重为负
                else:  # 无关系
                    relation_multiplier = 0.0
                
                # 综合注意力分数
                attention_scores[i, j] = base_score * relation_multiplier
        
        # 3. 应用 LeakyReLU 激活
        attention_scores = np.where(
            attention_scores > 0,
            attention_scores,
            self.alpha * attention_scores
        )
        
        # 4. Softmax 归一化（对每一行）
        # 添加掩码处理
        if mask is not None:
            attention_scores = np.where(mask, attention_scores, -np.inf)
        
        # 计算 softmax
        exp_scores = np.exp(attention_scores - np.max(attention_scores, axis=1, keepdims=True))
        attention_weights = exp_scores / (np.sum(exp_scores, axis=1, keepdims=True) + 1e-8)
        
        # 5. Dropout（训练时使用，这里简化处理）
        if self.attention_dropout > 0:
            dropout_mask = np.random.binomial(1, 1 - self.attention_dropout, size=(N, N))
            attention_weights = attention_weights * dropout_mask
            # 重新归一化
            attention_weights = attention_weights / (np.sum(attention_weights, axis=1, keepdims=True) + 1e-8)
        
        return attention_weights
    
    def multi_head_attention(
        self,
        node_features: np.ndarray,
        node_energies: np.ndarray,
        relation_types: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Multi-head Attention
        
        使用多个注意力头，可以学习多条复杂的通关或合化路径。
        
        Args:
            node_features: 节点特征矩阵 [N x F]
            node_energies: 节点能量向量 [N x 1]
            relation_types: 关系类型矩阵 [N x N]
            mask: 掩码矩阵 [N x N]
        
        Returns:
            (综合注意力权重 [N x N], 各头注意力权重列表)
        """
        head_weights = []
        
        for head in range(self.num_heads):
            # 每个头使用不同的参数（简化版，实际应该使用不同的 W 和 a）
            head_weight = self.compute_attention_weights(
                node_features=node_features,
                node_energies=node_energies,
                relation_types=relation_types,
                mask=mask
            )
            head_weights.append(head_weight)
        
        # 平均所有头的权重
        combined_weights = np.mean(np.stack(head_weights), axis=0)
        
        return combined_weights, head_weights


class GATAdjacencyBuilder:
    """GAT 邻接矩阵构建器，替代固定的邻接矩阵"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 GAT 邻接矩阵构建器
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        self.attention_layer = GraphAttentionLayer(config.get('gat', {}))
        
        # 基础关系权重（作为先验知识）
        self.generation_efficiency = config.get('generation_efficiency', 0.3)
        self.control_impact = config.get('control_impact', 0.7)
        self.combination_weight = config.get('combination_weight', 0.5)
        self.clash_weight = config.get('clash_weight', -0.8)
    
    def build_dynamic_adjacency_matrix(
        self,
        nodes: List,
        node_energies: np.ndarray,
        relation_types: np.ndarray,
        base_adjacency: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        构建动态邻接矩阵
        
        使用注意力机制动态计算节点间的权重，而不是使用固定的生克关系。
        
        Args:
            nodes: 节点列表
            node_energies: 节点能量向量 [N x 1]
            relation_types: 关系类型矩阵 [N x N]
            base_adjacency: 基础邻接矩阵（可选，作为先验知识）
        
        Returns:
            动态邻接矩阵 [N x N]
        """
        N = len(nodes)
        
        # 1. 提取节点特征（五行特征）
        node_features = self._extract_node_features(nodes)
        
        # 2. 计算注意力权重
        attention_weights, head_weights = self.attention_layer.multi_head_attention(
            node_features=node_features,
            node_energies=node_energies,
            relation_types=relation_types
        )
        
        # 3. 结合基础邻接矩阵（如果有）
        if base_adjacency is not None:
            # 使用注意力权重对基础矩阵进行加权
            dynamic_adjacency = base_adjacency * attention_weights
        else:
            # 直接使用注意力权重作为邻接矩阵
            dynamic_adjacency = attention_weights
        
        # 4. 应用关系类型修正
        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                
                relation_type = relation_types[i, j]
                if relation_type == 1:  # 生
                    dynamic_adjacency[i, j] *= self.generation_efficiency
                elif relation_type == -1:  # 克
                    dynamic_adjacency[i, j] *= -self.control_impact
                elif relation_type == 2:  # 合
                    dynamic_adjacency[i, j] *= self.combination_weight
                elif relation_type == -2:  # 冲
                    dynamic_adjacency[i, j] *= self.clash_weight
        
        return dynamic_adjacency
    
    def _extract_node_features(self, nodes: List) -> np.ndarray:
        """
        提取节点特征
        
        将节点转换为特征向量（五行特征）。
        
        Args:
            nodes: 节点列表
        
        Returns:
            节点特征矩阵 [N x 5]，每行是节点的五行特征向量
        """
        N = len(nodes)
        features = np.zeros((N, 5))
        
        element_map = {'wood': 0, 'fire': 1, 'earth': 2, 'metal': 3, 'water': 4}
        
        for i, node in enumerate(nodes):
            element = node.element
            if element in element_map:
                idx = element_map[element]
                features[i, idx] = 1.0  # One-hot 编码
        
        return features
    
    def learn_mediation_paths(
        self,
        nodes: List,
        node_energies: np.ndarray,
        relation_types: np.ndarray,
        target_paths: List[Tuple[int, int, int]]  # (source, mediator, target)
    ) -> np.ndarray:
        """
        学习通关路径
        
        使用 Multi-head Attention 自动学习多条复杂的通关或合化路径。
        
        Args:
            nodes: 节点列表
            node_energies: 节点能量向量
            relation_types: 关系类型矩阵
            target_paths: 目标路径列表，每个路径是 (source, mediator, target)
        
        Returns:
            学习后的邻接矩阵
        """
        # 1. 构建基础动态邻接矩阵
        adjacency = self.build_dynamic_adjacency_matrix(
            nodes=nodes,
            node_energies=node_energies,
            relation_types=relation_types
        )
        
        # 2. 对目标路径进行强化学习（简化版）
        for source, mediator, target in target_paths:
            if (source < len(nodes) and mediator < len(nodes) and target < len(nodes)):
                # 强化通关路径的权重
                # source -> mediator -> target
                if adjacency[mediator, source] > 0 and adjacency[target, mediator] > 0:
                    # 如果存在通关路径，增强权重
                    adjacency[target, source] = (
                        adjacency[target, mediator] * adjacency[mediator, source] * 1.5
                    )
        
        return adjacency

