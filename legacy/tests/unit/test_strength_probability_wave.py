"""
旺衰概率波模块单元测试
====================

测试覆盖:
1. 旺衰概率计算（连续值）
2. 概率分布计算（蒙特卡洛模拟）
3. 阈值中心点优化
4. 边界条件和错误处理

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import unittest
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.strength_probability_wave import StrengthProbabilityWave


class TestStrengthProbabilityWave(unittest.TestCase):
    """测试旺衰概率波"""
    
    def test_calculate_strength_probability_strong(self):
        """测试身强的概率计算"""
        energy_sum = 4.0  # 身强
        threshold_center = 3.0
        phase_transition_width = 10.0
        
        strength_prob, details = StrengthProbabilityWave.calculate_strength_probability(
            energy_sum=energy_sum,
            threshold_center=threshold_center,
            phase_transition_width=phase_transition_width
        )
        
        # 身强时概率应该 > 0.5
        self.assertGreater(strength_prob, 0.5)
        self.assertEqual(details['strength_label'], 'strong')
        print("✅ 身强概率计算测试通过")
    
    def test_calculate_strength_probability_weak(self):
        """测试身弱的概率计算"""
        energy_sum = 2.0  # 身弱
        threshold_center = 3.0
        phase_transition_width = 10.0
        
        strength_prob, details = StrengthProbabilityWave.calculate_strength_probability(
            energy_sum=energy_sum,
            threshold_center=threshold_center,
            phase_transition_width=phase_transition_width
        )
        
        # 身弱时概率应该 < 0.5
        self.assertLess(strength_prob, 0.5)
        self.assertEqual(details['strength_label'], 'weak')
        print("✅ 身弱概率计算测试通过")
    
    def test_calculate_strength_probability_neutral(self):
        """测试中性（临界点）的概率计算"""
        energy_sum = 3.0  # 中性
        threshold_center = 3.0
        phase_transition_width = 10.0
        
        strength_prob, details = StrengthProbabilityWave.calculate_strength_probability(
            energy_sum=energy_sum,
            threshold_center=threshold_center,
            phase_transition_width=phase_transition_width
        )
        
        # 中性时概率应该接近 0.5
        self.assertAlmostEqual(strength_prob, 0.5, places=1)
        self.assertEqual(details['strength_label'], 'neutral')
        print("✅ 中性概率计算测试通过")
    
    def test_calculate_strength_distribution(self):
        """测试概率分布计算"""
        energy_sum = 3.0
        threshold_center = 3.0
        phase_transition_width = 10.0
        
        distribution = StrengthProbabilityWave.calculate_strength_distribution(
            energy_sum=energy_sum,
            threshold_center=threshold_center,
            phase_transition_width=phase_transition_width,
            n_samples=100
        )
        
        self.assertIn('probabilities', distribution)
        self.assertIn('mean', distribution)
        self.assertIn('std', distribution)
        self.assertIn('p25', distribution)
        self.assertIn('p50', distribution)
        self.assertIn('p75', distribution)
        
        # 验证概率在 [0, 1] 范围内
        self.assertTrue(np.all(distribution['probabilities'] >= 0))
        self.assertTrue(np.all(distribution['probabilities'] <= 1))
        print("✅ 概率分布计算测试通过")
    
    def test_optimize_threshold_center(self):
        """测试阈值中心点优化"""
        case_data_list = [
            {'energy_sum': 2.5, 'real_wealth': 50.0},
            {'energy_sum': 3.5, 'real_wealth': 100.0},
            {'energy_sum': 3.0, 'real_wealth': 75.0}
        ]
        
        def objective(threshold):
            total_loss = 0.0
            for case in case_data_list:
                energy_sum = case['energy_sum']
                real_wealth = case['real_wealth']
                
                strength_prob, _ = StrengthProbabilityWave.calculate_strength_probability(
                    energy_sum=energy_sum,
                    threshold_center=threshold,
                    phase_transition_width=10.0
                )
                
                predicted_wealth = strength_prob * 100.0
                error = (predicted_wealth - real_wealth) ** 2
                total_loss += error
            
            return total_loss / len(case_data_list)
        
        optimal_threshold = StrengthProbabilityWave.optimize_threshold_center(
            case_data_list=case_data_list,
            objective_func=objective,
            search_range=(1.0, 5.0),
            n_iterations=10
        )
        
        self.assertIsNotNone(optimal_threshold)
        self.assertGreater(optimal_threshold, 1.0)
        self.assertLess(optimal_threshold, 5.0)
        print("✅ 阈值中心点优化测试通过")


if __name__ == '__main__':
    unittest.main(verbosity=2)

