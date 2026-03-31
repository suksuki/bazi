"""
强化学习反馈模块 (Reinforcement Learning from Human Feedback - RLHF)
================================================================

V10.0 优化：基于真实案例反馈的自适应进化

核心功能：
1. 奖励模型 (Reward Model)
2. 自适应参数调优
3. 案例反馈学习
4. 持续进化机制

作者: Antigravity Team
版本: V10.0
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path


class RewardModel:
    """奖励模型，用于强化学习"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化奖励模型
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        
        # 奖励权重
        self.accuracy_weight = config.get('accuracy_weight', 1.0)
        self.error_penalty_weight = config.get('error_penalty_weight', -0.5)
        self.hit_rate_bonus = config.get('hit_rate_bonus', 10.0)
    
    def calculate_reward(
        self,
        predicted: float,
        real: float,
        error_threshold: float = 20.0
    ) -> float:
        """
        计算奖励
        
        基于预测值和真实值的差异计算奖励。
        
        Args:
            predicted: 预测值
            real: 真实值
            error_threshold: 误差阈值（默认 20.0）
        
        Returns:
            奖励值（正数表示好，负数表示差）
        """
        error = abs(predicted - real)
        
        if error < error_threshold:
            # 预测准确：正奖励
            reward = self.accuracy_weight * (error_threshold - error) / error_threshold
        else:
            # 预测偏差大：负奖励
            reward = self.error_penalty_weight * (error - error_threshold) / error_threshold
        
        return reward
    
    def calculate_batch_reward(
        self,
        predictions: List[float],
        reals: List[float],
        error_threshold: float = 20.0
    ) -> Dict[str, float]:
        """
        计算批量奖励
        
        Args:
            predictions: 预测值列表
            reals: 真实值列表
            error_threshold: 误差阈值
        
        Returns:
            包含总奖励、平均奖励、命中率等的字典
        """
        if len(predictions) != len(reals):
            raise ValueError("预测值和真实值数量不匹配")
        
        rewards = []
        correct_count = 0
        
        for pred, real in zip(predictions, reals):
            reward = self.calculate_reward(pred, real, error_threshold)
            rewards.append(reward)
            
            if abs(pred - real) < error_threshold:
                correct_count += 1
        
        total_reward = sum(rewards)
        avg_reward = total_reward / len(rewards) if rewards else 0.0
        hit_rate = correct_count / len(rewards) if rewards else 0.0
        
        # 命中率加成
        hit_rate_bonus = self.hit_rate_bonus * hit_rate
        
        return {
            'total_reward': total_reward,
            'avg_reward': avg_reward,
            'hit_rate': hit_rate,
            'hit_rate_bonus': hit_rate_bonus,
            'final_reward': total_reward + hit_rate_bonus,
            'correct_count': correct_count,
            'total_count': len(rewards)
        }


class AdaptiveParameterTuner:
    """自适应参数调优器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化自适应参数调优器
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        
        # 学习率
        self.learning_rate = config.get('learning_rate', 0.01)
        
        # 参数历史记录
        self.parameter_history: List[Dict] = []
        self.reward_history: List[float] = []
    
    def tune_parameters(
        self,
        current_params: Dict[str, float],
        reward: float,
        parameter_ranges: Dict[str, Tuple[float, float]]
    ) -> Dict[str, float]:
        """
        调优参数
        
        基于奖励信号调整参数。
        
        Args:
            current_params: 当前参数值
            reward: 奖励值
            parameter_ranges: 参数范围字典 {param_name: (min, max)}
        
        Returns:
            调整后的参数值
        """
        tuned_params = current_params.copy()
        
        # 如果奖励为正，说明当前参数较好，微调
        # 如果奖励为负，说明需要较大调整
        adjustment_factor = self.learning_rate * (1.0 if reward > 0 else -1.0)
        
        for param_name, (min_val, max_val) in parameter_ranges.items():
            if param_name in tuned_params:
                # 调整参数
                new_val = tuned_params[param_name] + adjustment_factor * (max_val - min_val) * 0.1
                
                # 限制在范围内
                new_val = max(min_val, min(max_val, new_val))
                tuned_params[param_name] = new_val
        
        # 记录历史
        self.parameter_history.append(tuned_params.copy())
        self.reward_history.append(reward)
        
        return tuned_params
    
    def get_best_parameters(self) -> Optional[Dict[str, float]]:
        """
        获取历史最佳参数
        
        Returns:
            历史最佳参数值（基于最高奖励）
        """
        if not self.reward_history:
            return None
        
        best_idx = np.argmax(self.reward_history)
        return self.parameter_history[best_idx]


class RLHFTrainer:
    """RLHF 训练器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 RLHF 训练器
        
        Args:
            config: 配置参数
        """
        if config is None:
            config = {}
        
        self.config = config
        self.reward_model = RewardModel(config.get('reward', {}))
        self.parameter_tuner = AdaptiveParameterTuner(config.get('tuner', {}))
        
        # 案例反馈历史
        self.feedback_history: List[Dict] = []
    
    def learn_from_feedback(
        self,
        case_id: str,
        predictions: List[Dict],
        reals: List[Dict]
    ) -> Dict[str, any]:
        """
        从案例反馈中学习
        
        Args:
            case_id: 案例 ID
            predictions: 预测结果列表
            reals: 真实结果列表
        
        Returns:
            学习结果字典
        """
        # 提取预测值和真实值
        pred_values = [p.get('wealth_index', 0.0) for p in predictions]
        real_values = [r.get('real_magnitude', 0.0) for r in reals]
        
        # 计算奖励
        batch_reward = self.reward_model.calculate_batch_reward(
            predictions=pred_values,
            reals=real_values
        )
        
        # 记录反馈
        feedback = {
            'case_id': case_id,
            'predictions': predictions,
            'reals': reals,
            'reward': batch_reward,
            'timestamp': str(np.datetime64('now'))
        }
        self.feedback_history.append(feedback)
        
        return batch_reward
    
    def optimize_parameters(
        self,
        current_config: Dict,
        feedback_history: List[Dict]
    ) -> Dict:
        """
        优化参数
        
        基于反馈历史优化配置参数。
        
        Args:
            current_config: 当前配置
            feedback_history: 反馈历史
        
        Returns:
            优化后的配置
        """
        # 计算总体奖励
        total_reward = sum(f.get('reward', {}).get('final_reward', 0.0) for f in feedback_history)
        avg_reward = total_reward / len(feedback_history) if feedback_history else 0.0
        
        # 定义可调优的参数范围
        parameter_ranges = {
            'nonlinear.threshold': (0.4, 0.6),
            'nonlinear.scale': (5.0, 15.0),
            'nonlinear.phase_point': (0.4, 0.6),
            'gat.gat_mix_ratio': (0.3, 0.7),
            'transformer.d_model': (32, 128),
            'transformer.num_heads': (2, 8)
        }
        
        # 调优参数
        optimized_config = current_config.copy()
        
        # 简化版：基于平均奖励调整关键参数
        if avg_reward > 0:
            # 奖励为正，微调参数
            if 'nonlinear' in optimized_config:
                threshold = optimized_config['nonlinear'].get('threshold', 0.5)
                optimized_config['nonlinear']['threshold'] = threshold + 0.01
        else:
            # 奖励为负，较大调整
            if 'nonlinear' in optimized_config:
                threshold = optimized_config['nonlinear'].get('threshold', 0.5)
                optimized_config['nonlinear']['threshold'] = threshold - 0.02
        
        return optimized_config
    
    def save_feedback(self, file_path: str):
        """保存反馈历史到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_history, f, ensure_ascii=False, indent=2)
    
    def load_feedback(self, file_path: str):
        """从文件加载反馈历史"""
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                self.feedback_history = json.load(f)

