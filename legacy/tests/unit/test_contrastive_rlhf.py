"""
对比学习 RLHF 模块单元测试
==========================

测试覆盖:
1. 对比奖励模型
2. 对比学习训练器
3. 预测路径数据类
4. 边界条件和错误处理

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.contrastive_rlhf import (
    PredictionPath,
    ContrastivePair,
    ContrastiveRewardModel,
    ContrastiveRLHFTrainer
)


class TestPredictionPath(unittest.TestCase):
    """测试预测路径数据类"""
    
    def test_prediction_path_creation(self):
        """测试创建预测路径"""
        path = PredictionPath(
            years=[1999, 2015, 2021],
            predictions=[50.0, 100.0, 100.0],
            attention_weights={'path1': 0.5, 'path2': 0.3},
            energy_paths=[{'path1': 0.5}, {'path2': 0.3}],
            details=['detail1', 'detail2']
        )
        
        self.assertEqual(len(path.years), 3)
        self.assertEqual(len(path.predictions), 3)
        self.assertEqual(len(path.attention_weights), 2)
        print("✅ 预测路径创建测试通过")
    
    def test_prediction_path_empty(self):
        """测试空预测路径"""
        path = PredictionPath(
            years=[],
            predictions=[],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        
        self.assertEqual(len(path.years), 0)
        self.assertEqual(len(path.predictions), 0)
        print("✅ 空预测路径测试通过")


class TestContrastivePair(unittest.TestCase):
    """测试对比学习对"""
    
    def test_contrastive_pair_creation(self):
        """测试创建对比学习对"""
        path_a = PredictionPath(
            years=[1999, 2015],
            predictions=[50.0, 100.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        path_b = PredictionPath(
            years=[1999, 2015],
            predictions=[30.0, 80.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        
        pair = ContrastivePair(
            path_a=path_a,
            path_b=path_b,
            preferred_path='a',
            ground_truth=[50.0, 100.0]
        )
        
        self.assertEqual(pair.preferred_path, 'a')
        self.assertEqual(len(pair.ground_truth), 2)
        print("✅ 对比学习对创建测试通过")


class TestContrastiveRewardModel(unittest.TestCase):
    """测试对比奖励模型"""
    
    def setUp(self):
        """测试前准备"""
        self.reward_model = ContrastiveRewardModel(hidden_dim=64)
    
    def test_encode_path(self):
        """测试路径编码"""
        path = PredictionPath(
            years=[1999, 2015],
            predictions=[50.0, 100.0],
            attention_weights={'path1': 0.5},
            energy_paths=[{'path1': 0.5}],
            details=[]
        )
        
        features = self.reward_model.encode_path(path)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 0)
        print("✅ 路径编码测试通过")
    
    def test_encode_path_empty(self):
        """测试空路径编码"""
        path = PredictionPath(
            years=[],
            predictions=[],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        
        features = self.reward_model.encode_path(path)
        
        self.assertIsInstance(features, np.ndarray)
        print("✅ 空路径编码测试通过")
    
    def test_predict_reward(self):
        """测试预测奖励"""
        path = PredictionPath(
            years=[1999, 2015],
            predictions=[50.0, 100.0],
            attention_weights={'path1': 0.5},
            energy_paths=[{'path1': 0.5}],
            details=[]
        )
        
        reward = self.reward_model.predict_reward(path)
        
        self.assertIsInstance(reward, (int, float))
        print("✅ 预测奖励测试通过")
    
    def test_train(self):
        """测试训练奖励模型"""
        path_a = PredictionPath(
            years=[1999],
            predictions=[50.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        path_b = PredictionPath(
            years=[1999],
            predictions=[30.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        
        pair = ContrastivePair(
            path_a=path_a,
            path_b=path_b,
            preferred_path='a',
            ground_truth=[50.0]
        )
        
        # 训练（简化版，只测试不抛出异常）
        try:
            self.reward_model.train([pair], n_epochs=5, learning_rate=0.001)
            print("✅ 训练奖励模型测试通过")
        except Exception as e:
            self.fail(f"训练抛出异常: {e}")


class TestContrastiveRLHFTrainer(unittest.TestCase):
    """测试对比学习 RLHF 训练器"""
    
    def setUp(self):
        """测试前准备"""
        reward_model = ContrastiveRewardModel()
        self.trainer = ContrastiveRLHFTrainer(reward_model)
    
    def test_get_ground_truth(self):
        """测试获取真实值"""
        case_data = {
            'timeline': [
                {'year': 1999, 'real_magnitude': 50.0},
                {'year': 2015, 'real_magnitude': 100.0}
            ]
        }
        target_years = [1999, 2015]
        
        ground_truth = self.trainer._get_ground_truth(case_data, target_years)
        
        self.assertEqual(len(ground_truth), 2)
        self.assertEqual(ground_truth[0], 50.0)
        self.assertEqual(ground_truth[1], 100.0)
        print("✅ 获取真实值测试通过")
    
    def test_get_ground_truth_missing_year(self):
        """测试缺失年份的真实值"""
        case_data = {
            'timeline': [
                {'year': 1999, 'real_magnitude': 50.0}
            ]
        }
        target_years = [1999, 2015]  # 2015 年缺失
        
        ground_truth = self.trainer._get_ground_truth(case_data, target_years)
        
        self.assertEqual(len(ground_truth), 2)
        self.assertEqual(ground_truth[0], 50.0)
        self.assertEqual(ground_truth[1], 0.0)  # 缺失年份返回 0.0
        print("✅ 缺失年份真实值测试通过")
    
    def test_get_ground_truth_empty_timeline(self):
        """测试空时间线的真实值"""
        case_data = {'timeline': []}
        target_years = [1999, 2015]
        
        ground_truth = self.trainer._get_ground_truth(case_data, target_years)
        
        self.assertEqual(len(ground_truth), 2)
        self.assertEqual(ground_truth[0], 0.0)
        self.assertEqual(ground_truth[1], 0.0)
        print("✅ 空时间线真实值测试通过")


class TestContrastiveRLHFEdgeCases(unittest.TestCase):
    """测试边界情况和错误处理"""
    
    def test_reward_model_invalid_hidden_dim(self):
        """测试无效的隐藏层维度"""
        # 应该能够创建（使用默认值或处理异常）
        try:
            model = ContrastiveRewardModel(hidden_dim=0)
            # 如果创建成功，至少应该能够编码路径
            path = PredictionPath(
                years=[1999],
                predictions=[50.0],
                attention_weights={},
                energy_paths=[],
                details=[]
            )
            features = model.encode_path(path)
            self.assertIsNotNone(features)
            print("✅ 无效隐藏层维度处理测试通过")
        except Exception:
            # 如果抛出异常也是可以接受的
            pass
    
    def test_contrastive_pair_invalid_preferred(self):
        """测试无效的偏好路径"""
        path_a = PredictionPath(
            years=[1999],
            predictions=[50.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        path_b = PredictionPath(
            years=[1999],
            predictions=[30.0],
            attention_weights={},
            energy_paths=[],
            details=[]
        )
        
        # 使用无效的偏好路径（应该是 'a' 或 'b'）
        pair = ContrastivePair(
            path_a=path_a,
            path_b=path_b,
            preferred_path='invalid',
            ground_truth=[50.0]
        )
        
        # 训练时应该能够处理（或抛出异常）
        reward_model = ContrastiveRewardModel()
        try:
            reward_model.train([pair], n_epochs=1, learning_rate=0.001)
            print("✅ 无效偏好路径处理测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)

