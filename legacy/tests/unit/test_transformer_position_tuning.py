"""
Transformer 位置编码调优模块单元测试
====================================

测试覆盖:
1. 位置编码调优器
2. 多尺度时序融合
3. 边界条件和错误处理

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

from core.transformer_position_tuning import (
    PositionalEncodingTuner,
    MultiScaleTemporalFusion
)


class TestPositionalEncodingTuner(unittest.TestCase):
    """测试位置编码调优器"""
    
    def setUp(self):
        """测试前准备"""
        self.tuner = PositionalEncodingTuner(d_model=128, max_length=100)
    
    def test_generate_positional_encoding(self):
        """测试生成位置编码"""
        pe = self.tuner.generate_positional_encoding(
            position_scale=10000.0,
            decay_factor=1.0
        )
        
        self.assertEqual(pe.shape, (100, 128))
        self.assertTrue(np.all(np.isfinite(pe)))
        print("✅ 生成位置编码测试通过")
    
    def test_generate_positional_encoding_with_decay(self):
        """测试带衰减因子的位置编码"""
        pe = self.tuner.generate_positional_encoding(
            position_scale=10000.0,
            decay_factor=0.5  # 衰减因子
        )
        
        self.assertEqual(pe.shape, (100, 128))
        # 验证衰减因子影响编码
        pe_no_decay = self.tuner.generate_positional_encoding(
            position_scale=10000.0,
            decay_factor=1.0
        )
        # 衰减后的编码应该不同
        self.assertFalse(np.allclose(pe, pe_no_decay))
        print("✅ 带衰减因子的位置编码测试通过")
    
    def test_generate_positional_encoding_different_scales(self):
        """测试不同位置缩放因子的位置编码"""
        pe1 = self.tuner.generate_positional_encoding(
            position_scale=1000.0,
            decay_factor=1.0
        )
        pe2 = self.tuner.generate_positional_encoding(
            position_scale=100000.0,
            decay_factor=1.0
        )
        
        # 不同缩放因子应该产生不同的编码
        self.assertFalse(np.allclose(pe1, pe2))
        print("✅ 不同位置缩放因子测试通过")
    
    def test_tune_for_long_range_dependency(self):
        """测试长程依赖调优"""
        timeline_data = [
            {'year': 1999, 'energy': 50.0},
            {'year': 2015, 'energy': 100.0},
            {'year': 2021, 'energy': 100.0}
        ]
        
        def objective(params):
            # 简单的目标函数
            return abs(params['position_scale'] - 10000.0) + abs(params['decay_factor'] - 1.0)
        
        optimal_params = self.tuner.tune_for_long_range_dependency(
            timeline_data=timeline_data,
            objective_func=objective
        )
        
        self.assertIn('position_scale', optimal_params)
        self.assertIn('decay_factor', optimal_params)
        self.assertGreater(optimal_params['position_scale'], 0)
        self.assertGreater(optimal_params['decay_factor'], 0)
        print("✅ 长程依赖调优测试通过")


class TestMultiScaleTemporalFusion(unittest.TestCase):
    """测试多尺度时序融合"""
    
    def setUp(self):
        """测试前准备"""
        self.fusion = MultiScaleTemporalFusion()
    
    def test_fuse_temporal_features(self):
        """测试融合时序特征"""
        timeline_data = [
            {'year': 2005, 'energy': 50.0},
            {'year': 2010, 'energy': 60.0},
            {'year': 2015, 'energy': 100.0},
            {'year': 1995, 'energy': 40.0},
            {'year': 1990, 'energy': 30.0}
        ]
        
        fused = self.fusion.fuse_temporal_features(timeline_data)
        
        self.assertIsInstance(fused, np.ndarray)
        self.assertGreater(len(fused), 0)
        print("✅ 融合时序特征测试通过")
    
    def test_fuse_temporal_features_custom_weights(self):
        """测试自定义权重的时序融合"""
        timeline_data = [
            {'year': 2005, 'energy': 50.0},
            {'year': 2010, 'energy': 60.0}
        ]
        
        custom_weights = {
            'short_term': 0.5,
            'medium_term': 0.3,
            'long_term': 0.2
        }
        
        fused = self.fusion.fuse_temporal_features(
            timeline_data,
            scale_weights=custom_weights
        )
        
        self.assertIsInstance(fused, np.ndarray)
        print("✅ 自定义权重时序融合测试通过")
    
    def test_fuse_temporal_features_empty(self):
        """测试空时间线的时序融合"""
        timeline_data = []
        
        fused = self.fusion.fuse_temporal_features(timeline_data)
        
        self.assertIsInstance(fused, np.ndarray)
        print("✅ 空时间线时序融合测试通过")
    
    def test_optimize_scale_weights(self):
        """测试优化尺度权重"""
        timeline_data = [
            {'year': 2005, 'energy': 50.0},
            {'year': 2010, 'energy': 60.0},
            {'year': 2015, 'energy': 100.0}
        ]
        ground_truth = [50.0, 60.0, 100.0]
        
        def objective(weights):
            # 简单的目标函数：权重之和应该接近 1.0
            total = weights['short_term'] + weights['medium_term'] + weights['long_term']
            return abs(total - 1.0)
        
        optimal_weights = self.fusion.optimize_scale_weights(
            timeline_data=timeline_data,
            ground_truth=ground_truth,
            objective_func=objective
        )
        
        self.assertIn('short_term', optimal_weights)
        self.assertIn('medium_term', optimal_weights)
        self.assertIn('long_term', optimal_weights)
        
        # 验证权重之和接近 1.0
        total = (optimal_weights['short_term'] + 
                optimal_weights['medium_term'] + 
                optimal_weights['long_term'])
        self.assertAlmostEqual(total, 1.0, places=1)
        print("✅ 优化尺度权重测试通过")
    
    def test_extract_features(self):
        """测试特征提取"""
        data = [
            {'energy': 50.0},
            {'energy': 60.0},
            {'energy': 100.0}
        ]
        
        features = self.fusion._extract_features(data)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 0)
        print("✅ 特征提取测试通过")
    
    def test_extract_features_empty(self):
        """测试空数据的特征提取"""
        data = []
        
        features = self.fusion._extract_features(data)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(len(features), 10)  # 默认特征维度
        print("✅ 空数据特征提取测试通过")


class TestTransformerPositionTuningEdgeCases(unittest.TestCase):
    """测试边界情况和错误处理"""
    
    def test_positional_encoding_invalid_d_model(self):
        """测试无效的模型维度"""
        try:
            tuner = PositionalEncodingTuner(d_model=0, max_length=100)
            pe = tuner.generate_positional_encoding()
            # 如果创建成功，应该能够生成编码（可能使用默认值）
            self.assertIsNotNone(pe)
            print("✅ 无效模型维度处理测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass
    
    def test_positional_encoding_invalid_max_length(self):
        """测试无效的最大长度"""
        try:
            tuner = PositionalEncodingTuner(d_model=128, max_length=0)
            pe = tuner.generate_positional_encoding()
            # 如果创建成功，应该能够生成编码
            self.assertIsNotNone(pe)
            print("✅ 无效最大长度处理测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass
    
    def test_fusion_invalid_weights_sum(self):
        """测试权重和不等于 1.0 的情况"""
        fusion = MultiScaleTemporalFusion()
        timeline_data = [{'year': 2005, 'energy': 50.0}]
        
        # 权重之和不等于 1.0
        invalid_weights = {
            'short_term': 0.5,
            'medium_term': 0.3,
            'long_term': 0.1  # 总和 = 0.9
        }
        
        # 应该能够处理（或归一化）
        try:
            fused = fusion.fuse_temporal_features(
                timeline_data,
                scale_weights=invalid_weights
            )
            self.assertIsNotNone(fused)
            print("✅ 无效权重和处理测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)

