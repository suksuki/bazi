#!/usr/bin/env python3
"""
对比学习 RLHF 模块 (Contrastive RLHF)
=====================================

升级的 RLHF 系统，使用对比学习来学习偏好奖励模型
不仅告诉系统"预测错了"，还提供"路径 A vs 路径 B"的对比
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PredictionPath:
    """
    预测路径数据类
    表示一条完整的预测路径（包含多个年份的预测）
    """
    years: List[int]
    predictions: List[float]
    attention_weights: Dict[str, float]  # GAT 注意力权重
    energy_paths: List[Dict[str, float]]  # 能量传播路径
    details: List[str]  # 触发机制详情


@dataclass
class ContrastivePair:
    """
    对比学习对
    包含两条预测路径和真实偏好
    """
    path_a: PredictionPath
    path_b: PredictionPath
    preferred_path: str  # 'a' 或 'b'
    ground_truth: List[float]  # 真实值


class ContrastiveRewardModel:
    """
    对比奖励模型
    学习哪种预测路径更符合真实事件
    """
    
    def __init__(self, hidden_dim: int = 64):
        """
        初始化奖励模型
        
        Args:
            hidden_dim: 隐藏层维度
        """
        self.hidden_dim = hidden_dim
        # 简化的神经网络权重（实际应使用 PyTorch/TensorFlow）
        self.W1 = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.W2 = np.random.randn(1, hidden_dim) * 0.01
        self.b1 = np.zeros(hidden_dim)
        self.b2 = np.zeros(1)
    
    def encode_path(self, path: PredictionPath) -> np.ndarray:
        """
        编码预测路径为特征向量
        
        Args:
            path: 预测路径
            
        Returns:
            特征向量
        """
        # 特征提取
        features = []
        
        # 1. 预测准确性（与真实值的平均误差）
        # 注意：这里假设有真实值，实际使用时需要传入
        features.append(np.mean(path.predictions))
        features.append(np.std(path.predictions))
        
        # 2. 注意力权重特征
        if path.attention_weights:
            features.append(np.mean(list(path.attention_weights.values())))
            features.append(np.std(list(path.attention_weights.values())))
        else:
            features.extend([0.0, 0.0])
        
        # 3. 能量路径特征
        if path.energy_paths:
            path_strengths = [sum(p.values()) for p in path.energy_paths]
            features.append(np.mean(path_strengths))
            features.append(np.std(path_strengths))
        else:
            features.extend([0.0, 0.0])
        
        # 4. 路径长度
        features.append(len(path.years))
        
        return np.array(features)
    
    def predict_reward(self, path: PredictionPath) -> float:
        """
        预测路径的奖励值
        
        Args:
            path: 预测路径
            
        Returns:
            奖励值（越高越好）
        """
        # 编码路径
        x = self.encode_path(path)
        
        # 扩展维度
        if x.ndim == 1:
            x = x.reshape(1, -1)
        
        # 确保维度匹配
        if x.shape[1] != self.hidden_dim:
            # 如果特征维度不匹配，进行填充或截断
            if x.shape[1] < self.hidden_dim:
                x = np.pad(x, ((0, 0), (0, self.hidden_dim - x.shape[1])))
            else:
                x = x[:, :self.hidden_dim]
        
        # 前向传播
        h = np.tanh(x @ self.W1.T + self.b1)
        reward = (h @ self.W2.T + self.b2)[0, 0]
        
        return reward
    
    def train(self, contrastive_pairs: List[ContrastivePair], 
              n_epochs: int = 100, learning_rate: float = 0.001):
        """
        训练奖励模型
        
        Args:
            contrastive_pairs: 对比学习对列表
            n_epochs: 训练轮数
            learning_rate: 学习率
        """
        logger.info(f"开始训练对比奖励模型，样本数: {len(contrastive_pairs)}")
        
        for epoch in range(n_epochs):
            total_loss = 0.0
            
            for pair in contrastive_pairs:
                # 计算两条路径的奖励
                reward_a = self.predict_reward(pair.path_a)
                reward_b = self.predict_reward(pair.path_b)
                
                # 对比学习损失（Bradley-Terry 模型）
                if pair.preferred_path == 'a':
                    # 路径 A 更优，reward_a 应该 > reward_b
                    logit = reward_a - reward_b
                    loss = -np.log(1 / (1 + np.exp(-logit)))  # 负对数似然
                else:
                    # 路径 B 更优，reward_b 应该 > reward_a
                    logit = reward_b - reward_a
                    loss = -np.log(1 / (1 + np.exp(-logit)))
                
                total_loss += loss
                
                # 梯度更新（简化版，实际应使用反向传播）
                # 这里使用数值梯度近似
                self._update_weights(pair, learning_rate)
            
            avg_loss = total_loss / len(contrastive_pairs)
            if epoch % 10 == 0:
                logger.info(f"  Epoch {epoch}/{n_epochs}: 平均损失 = {avg_loss:.4f}")
        
        logger.info("✅ 奖励模型训练完成")
    
    def _update_weights(self, pair: ContrastivePair, learning_rate: float):
        """更新权重（简化版梯度更新）"""
        # 这里使用简化的更新规则
        # 实际应使用反向传播计算精确梯度
        reward_a = self.predict_reward(pair.path_a)
        reward_b = self.predict_reward(pair.path_b)
        
        # 根据偏好调整权重
        if pair.preferred_path == 'a' and reward_a < reward_b:
            # 路径 A 更优但奖励更低，需要增加路径 A 的奖励
            # 简化：增加权重
            self.W2 += learning_rate * 0.01
        elif pair.preferred_path == 'b' and reward_b < reward_a:
            # 路径 B 更优但奖励更低，需要增加路径 B 的奖励
            self.W2 += learning_rate * 0.01


class ContrastiveRLHFTrainer:
    """
    对比学习 RLHF 训练器
    使用对比学习来优化 GAT 注意力权重和能量传播路径
    """
    
    def __init__(self, reward_model: ContrastiveRewardModel):
        """
        初始化训练器
        
        Args:
            reward_model: 奖励模型
        """
        self.reward_model = reward_model
    
    def generate_contrastive_pairs(self, 
                                  case_data: Dict,
                                  engine_a: 'GraphNetworkEngine',
                                  engine_b: 'GraphNetworkEngine',
                                  target_years: List[int]) -> List[ContrastivePair]:
        """
        生成对比学习对
        
        Args:
            case_data: 案例数据
            engine_a: 引擎 A（不同参数配置）
            engine_b: 引擎 B（不同参数配置）
            target_years: 目标年份列表
            
        Returns:
            对比学习对列表
        """
        pairs = []
        
        # 使用两个不同的引擎配置生成预测路径
        path_a = self._generate_path(engine_a, case_data, target_years)
        path_b = self._generate_path(engine_b, case_data, target_years)
        
        # 获取真实值
        ground_truth = self._get_ground_truth(case_data, target_years)
        
        # 计算哪条路径更优（基于与真实值的误差）
        error_a = np.mean([abs(p - t) for p, t in zip(path_a.predictions, ground_truth)])
        error_b = np.mean([abs(p - t) for p, t in zip(path_b.predictions, ground_truth)])
        
        preferred_path = 'a' if error_a < error_b else 'b'
        
        pairs.append(ContrastivePair(
            path_a=path_a,
            path_b=path_b,
            preferred_path=preferred_path,
            ground_truth=ground_truth
        ))
        
        return pairs
    
    def _generate_path(self, engine: 'GraphNetworkEngine', 
                      case_data: Dict, target_years: List[int]) -> PredictionPath:
        """生成预测路径"""
        # 这里需要调用引擎进行预测
        # 简化实现
        predictions = []
        attention_weights = {}
        energy_paths = []
        details = []
        
        for year in target_years:
            # 调用引擎预测（简化）
            result = engine.calculate_wealth_index(
                bazi=case_data['bazi'],
                day_master=case_data['day_master'],
                gender=case_data['gender'],
                luck_pillar='',  # 需要从案例数据获取
                year_pillar=''   # 需要从案例数据获取
            )
            
            if isinstance(result, dict):
                predictions.append(result.get('wealth_index', 0.0))
                attention_weights.update(result.get('attention_weights', {}))
            else:
                predictions.append(float(result))
        
        return PredictionPath(
            years=target_years,
            predictions=predictions,
            attention_weights=attention_weights,
            energy_paths=energy_paths,
            details=details
        )
    
    def _get_ground_truth(self, case_data: Dict, target_years: List[int]) -> List[float]:
        """获取真实值"""
        timeline = case_data.get('timeline', [])
        ground_truth = []
        
        for year in target_years:
            event = next((e for e in timeline if e.get('year') == year), None)
            if event:
                ground_truth.append(event.get('real_magnitude', 0.0))
            else:
                ground_truth.append(0.0)
        
        return ground_truth

