"""
Transformer 时序建模模块 (Transformer Temporal Modeling)
==========================================================

V10.0 优化：时序建模，捕捉长程依赖

核心功能：
1. Self-Attention 机制捕捉时序相关性
2. 多尺度时序融合（流年、流月、流日）
3. 长程依赖建模（十年前的因，今日的果）
4. 位置编码（Positional Encoding）

作者: Antigravity Team
版本: V10.0
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import math


class PositionalEncoding:
    """位置编码，用于 Transformer 时序建模"""
    
    def __init__(self, d_model: int, max_len: int = 100):
        """
        初始化位置编码
        
        Args:
            d_model: 模型维度
            max_len: 最大序列长度
        """
        self.d_model = d_model
        self.max_len = max_len
        
        # 创建位置编码矩阵
        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len, dtype=np.float32).reshape(-1, 1)
        div_term = np.exp(np.arange(0, d_model, 2).astype(np.float32) * 
                         -(math.log(10000.0) / d_model))
        
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        self.pe = pe
    
    def __call__(self, seq_len: int) -> np.ndarray:
        """
        获取位置编码
        
        Args:
            seq_len: 序列长度
        
        Returns:
            位置编码矩阵 [seq_len x d_model]
        """
        return self.pe[:seq_len, :]


class TemporalTransformer:
    """时序 Transformer，用于捕捉长程依赖"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化时序 Transformer
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        self.d_model = config.get('d_model', 64)  # 模型维度
        self.num_heads = config.get('num_heads', 4)  # 注意力头数
        self.num_layers = config.get('num_layers', 2)  # Transformer 层数
        self.dropout = config.get('dropout', 0.1)
        
        # 位置编码
        self.pos_encoder = PositionalEncoding(self.d_model, max_len=100)
        
        # 多头注意力参数（简化版）
        self.W_q = np.random.randn(self.d_model, self.d_model) * 0.1
        self.W_k = np.random.randn(self.d_model, self.d_model) * 0.1
        self.W_v = np.random.randn(self.d_model, self.d_model) * 0.1
        self.W_o = np.random.randn(self.d_model, self.d_model) * 0.1
    
    def multi_head_attention(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Multi-head Self-Attention
        
        捕捉时序中的长程依赖关系。
        
        Args:
            query: 查询矩阵 [seq_len x d_model]
            key: 键矩阵 [seq_len x d_model]
            value: 值矩阵 [seq_len x d_model]
            mask: 掩码矩阵 [seq_len x seq_len]
        
        Returns:
            注意力输出 [seq_len x d_model]
        """
        seq_len, d_model = query.shape
        d_k = d_model // self.num_heads
        
        # 分割为多个头
        Q = query.reshape(seq_len, self.num_heads, d_k)
        K = key.reshape(seq_len, self.num_heads, d_k)
        V = value.reshape(seq_len, self.num_heads, d_k)
        
        # 计算注意力分数 [seq_len x seq_len x num_heads]
        scores = np.einsum('qhd,khd->qkh', Q, K) / np.sqrt(d_k)
        
        # 应用掩码
        if mask is not None:
            # 扩展掩码维度以匹配 scores 的形状
            if mask.ndim == 2:
                mask_expanded = mask[:, :, np.newaxis]  # [seq_len x seq_len x 1]
            else:
                mask_expanded = mask
            scores = np.where(mask_expanded, scores, -np.inf)
        
        # Softmax（对最后一个维度，即 key 维度）
        attention_weights = np.exp(scores - np.max(scores, axis=1, keepdims=True))
        attention_weights = attention_weights / (np.sum(attention_weights, axis=1, keepdims=True) + 1e-8)
        
        # 应用注意力权重
        output = np.einsum('qkh,khd->qhd', attention_weights, V)
        
        # 合并多个头
        output = output.reshape(seq_len, d_model)
        
        return output
    
    def encode_temporal_features(
        self,
        timeline_data: List[Dict[str, any]]
    ) -> np.ndarray:
        """
        编码时序特征
        
        将时序数据转换为特征矩阵。
        
        Args:
            timeline_data: 时序数据列表，每个元素包含：
                - year: 年份
                - strength_score: 身强分数
                - wealth_index: 财富指数
                - luck_pillar: 大运
                - year_pillar: 流年
                - ... 其他特征
        
        Returns:
            特征矩阵 [seq_len x d_model]
        """
        seq_len = len(timeline_data)
        features = np.zeros((seq_len, self.d_model))
        
        for i, data in enumerate(timeline_data):
            # 特征编码（简化版，实际应该更复杂）
            feature_vec = np.zeros(self.d_model)
            
            # 1. 身强分数（归一化到 0-1）
            strength = data.get('strength_score', 50.0) / 100.0
            feature_vec[0] = strength
            
            # 2. 财富指数（归一化到 -1 到 1）
            wealth = data.get('wealth_index', 0.0) / 100.0
            feature_vec[1] = wealth
            
            # 3. 大运特征（简化编码）
            luck_pillar = data.get('luck_pillar', '')
            if luck_pillar:
                # 简单的哈希编码
                luck_hash = hash(luck_pillar) % 1000 / 1000.0
                feature_vec[2] = luck_hash
            
            # 4. 流年特征（简化编码）
            year_pillar = data.get('year_pillar', '')
            if year_pillar:
                year_hash = hash(year_pillar) % 1000 / 1000.0
                feature_vec[3] = year_hash
            
            # 5. 年份特征（相对位置）
            year = data.get('year', 0)
            year_offset = (year - 2000) / 100.0  # 归一化
            feature_vec[4] = year_offset
            
            # 6. 其他特征（可以扩展）
            # ... 更多特征编码
            
            features[i] = feature_vec
        
        return features
    
    def forward(
        self,
        timeline_data: List[Dict[str, any]],
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Transformer 前向传播
        
        捕捉时序中的长程依赖关系。
        
        Args:
            timeline_data: 时序数据列表
            return_attention: 是否返回注意力权重
        
        Returns:
            (输出特征 [seq_len x d_model], 注意力权重 [可选])
        """
        # 1. 编码时序特征
        x = self.encode_temporal_features(timeline_data)
        seq_len = x.shape[0]
        
        # 2. 添加位置编码
        pos_encoding = self.pos_encoder(seq_len)
        x = x + pos_encoding
        
        # 3. Multi-head Self-Attention
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        # 创建因果掩码（只能看到过去的信息）
        causal_mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype(bool)
        
        # 应用注意力
        attention_output = self.multi_head_attention(Q, K, V, mask=~causal_mask)
        
        # 4. 残差连接和层归一化（简化版）
        x = x + attention_output
        
        # 5. 前馈网络（简化版）
        # 这里可以添加 Feed-Forward Network
        
        return x, None
    
    def predict_future(
        self,
        historical_data: List[Dict[str, any]],
        future_years: int = 5
    ) -> List[Dict[str, float]]:
        """
        预测未来
        
        基于历史数据预测未来 N 年的运势。
        
        Args:
            historical_data: 历史时序数据
            future_years: 预测年数
        
        Returns:
            预测结果列表
        """
        # 1. 编码历史数据
        historical_features = self.encode_temporal_features(historical_data)
        
        # 2. 使用 Transformer 提取时序特征
        encoded_features, _ = self.forward(historical_data)
        
        # 3. 预测未来（简化版，使用线性外推）
        # 实际应该使用更复杂的预测模型
        predictions = []
        
        # 获取最后几年的趋势
        if len(encoded_features) >= 3:
            trend = encoded_features[-1] - encoded_features[-3]
        else:
            trend = np.zeros(self.d_model)
        
        # 外推未来
        for i in range(future_years):
            future_feature = encoded_features[-1] + trend * (i + 1)
            
            # 解码特征（简化版）
            predicted_strength = future_feature[0] * 100.0
            predicted_wealth = future_feature[1] * 100.0
            
            predictions.append({
                'year': historical_data[-1]['year'] + i + 1,
                'predicted_strength': predicted_strength,
                'predicted_wealth': predicted_wealth
            })
        
        return predictions


class MultiScaleTemporalFusion:
    """多尺度时序融合"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化多尺度时序融合
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        
        # 不同时间尺度的权重
        self.year_weight = config.get('year_weight', 1.0)
        self.month_weight = config.get('month_weight', 0.3)
        self.day_weight = config.get('day_weight', 0.1)
    
    def fuse_multi_scale(
        self,
        year_data: List[Dict],
        month_data: Optional[List[Dict]] = None,
        day_data: Optional[List[Dict]] = None
    ) -> np.ndarray:
        """
        融合多尺度时序数据
        
        将流年、流月、流日的数据融合为统一的时序表示。
        
        Args:
            year_data: 流年数据
            month_data: 流月数据（可选）
            day_data: 流日数据（可选）
        
        Returns:
            融合后的特征矩阵
        """
        # 1. 编码流年数据
        year_features = self._encode_scale(year_data, self.year_weight)
        
        # 2. 编码流月数据（如果有）
        if month_data:
            month_features = self._encode_scale(month_data, self.month_weight)
            # 融合流年和流月
            year_features = self._merge_scales(year_features, month_features)
        
        # 3. 编码流日数据（如果有）
        if day_data:
            day_features = self._encode_scale(day_data, self.day_weight)
            # 融合所有尺度
            year_features = self._merge_scales(year_features, day_features)
        
        return year_features
    
    def _encode_scale(self, data: List[Dict], weight: float) -> np.ndarray:
        """编码单个时间尺度的数据"""
        # 简化版编码
        features = []
        for item in data:
            feature = [
                item.get('strength_score', 50.0) / 100.0,
                item.get('wealth_index', 0.0) / 100.0
            ]
            features.append(feature)
        
        return np.array(features) * weight
    
    def _merge_scales(
        self,
        scale1: np.ndarray,
        scale2: np.ndarray
    ) -> np.ndarray:
        """合并两个时间尺度的特征"""
        # 简化版：加权平均
        # 实际应该使用更复杂的融合方法
        if scale1.shape[0] != scale2.shape[0]:
            # 如果长度不同，需要对齐
            min_len = min(scale1.shape[0], scale2.shape[0])
            scale1 = scale1[:min_len]
            scale2 = scale2[:min_len]
        
        return (scale1 + scale2) / 2.0

