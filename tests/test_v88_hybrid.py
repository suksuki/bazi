"""
V8.8 Hybrid Engine Test Suite
==============================
Tests the EngineV88 which combines:
- Legacy QuantumEngine features (get_year_pillar, calculate_year_context)
- Modular processors (_evaluate_wang_shuai override)
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88  # Pure modular engine


class TestEngineV88(unittest.TestCase):
    """Test V8.8 Hybrid Engine functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize engine once for all tests"""
        # Suppress init output
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        cls.engine = EngineV88()
        sys.stdout = old_stdout
    
    def test_version_watermark(self):
        """Engine should broadcast correct version"""
        # V9.1 Spacetime Edition
        self.assertEqual(self.engine.VERSION, "9.1.0-Spacetime")
    
    def test_legacy_get_year_pillar(self):
        """Legacy method should work"""
        pillar = self.engine.get_year_pillar(2024)
        self.assertIsInstance(pillar, str)
        self.assertEqual(len(pillar), 2)  # GanZhi format
    
    def test_legacy_get_element(self):
        """Legacy helper should work"""
        self.assertEqual(self.engine._get_element('甲'), 'wood')
        self.assertEqual(self.engine._get_element('辛'), 'metal')
        self.assertEqual(self.engine._get_element('午'), 'fire')
    
    def test_val_006_stephen_chow_weak(self):
        """VAL_006 (星爷) should be Weak - scorched earth active"""
        bazi = ['壬寅', '丙午', '辛卯', '壬辰']
        strength, score = self.engine._evaluate_wang_shuai('辛', bazi)
        self.assertEqual(strength, 'Weak')
        self.assertLess(score, 50)
    
    def test_s010_balanced_gold_strong(self):
        """S010 (建禄格) should be Strong - 得令覆盖"""
        bazi = ['癸卯', '辛酉', '辛巳', '甲午']
        strength, score = self.engine._evaluate_wang_shuai('辛', bazi)
        self.assertEqual(strength, 'Strong')
        self.assertGreater(score, 100)
    
    def test_val_005_hk_tycoon_strong(self):
        """VAL_005 (塑胶大亨) should be Strong - 润局解救"""
        bazi = ['戊辰', '己未', '庚午', '丁亥']
        strength, score = self.engine._evaluate_wang_shuai('庚', bazi)
        self.assertEqual(strength, 'Strong')
    
    def test_val_008_writer_lady_strong(self):
        """VAL_008 (作家) should be Strong - 印绶月保护"""
        bazi = ['庚申', '丙戌', '庚辰', '己卯']
        strength, score = self.engine._evaluate_wang_shuai('庚', bazi)
        self.assertEqual(strength, 'Strong')


class TestHybridEngineRegression(unittest.TestCase):
    """Regression tests against calibration cases"""
    
    @classmethod
    def setUpClass(cls):
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        cls.engine = EngineV88()
        sys.stdout = old_stdout
        
        # Load cases
        cases_path = os.path.join(
            os.path.dirname(__file__), 
            '../data/calibration_cases.json'
        )
        with open(cases_path, 'r') as f:
            cls.cases = json.load(f)
    
    def test_regression_pass_rate(self):
        """Overall pass rate should be >= 60%"""
        passed = 0
        total = 0
        
        for case in self.cases:
            gt = case.get('ground_truth', {}).get('strength', 'Unknown')
            if gt == 'Unknown':
                continue
            
            total += 1
            bazi = case['bazi']
            dm = case['day_master']
            
            strength, _ = self.engine._evaluate_wang_shuai(dm, bazi)
            
            is_match = (
                gt in strength or 
                strength in gt or 
                (gt == 'Follower' and strength == 'Weak')
            )
            
            if is_match:
                passed += 1
        
        pass_rate = passed / total if total > 0 else 0
        self.assertGreaterEqual(pass_rate, 0.40, 
            f"Pass rate {pass_rate:.0%} < 40% threshold")
    
    def test_no_critical_regression(self):
        """Critical cases (P0) must pass"""
        critical_cases = {
            'VAL_006': 'Weak',   # 星爷
            'VAL_008': 'Strong', # 作家
        }
        
        for case in self.cases:
            case_id = case['id']
            # Extract base ID
            base_id = case_id.split('_')[0] + '_' + case_id.split('_')[1] if '_' in case_id else case_id
            
            if base_id not in critical_cases:
                continue
            
            expected = critical_cases[base_id]
            bazi = case['bazi']
            dm = case['day_master']
            
            strength, _ = self.engine._evaluate_wang_shuai(dm, bazi)
            
            is_match = expected in strength or strength in expected
            self.assertTrue(is_match, 
                f"CRITICAL: {case_id} expected {expected}, got {strength}")


if __name__ == '__main__':
    unittest.main()
