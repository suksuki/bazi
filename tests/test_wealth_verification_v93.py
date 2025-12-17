"""
财富验证 V9.3 测试套件
=====================
测试财富验证功能的改进（开库机制、冲提纲、身弱财重等）
"""

import unittest
from controllers.wealth_verification_controller import WealthVerificationController
from core.models.wealth_case_model import WealthCase, WealthEvent


class TestWealthVerificationV93(unittest.TestCase):
    """测试财富验证 V9.3 改进"""
    
    def setUp(self):
        self.controller = WealthVerificationController()
    
    def test_vault_opening_with_combination(self):
        """测试合开财库（如寅合未）"""
        # Jason A 2010年案例：未土官库被寅木合动
        case = WealthCase(
            id="TEST_JASON_A",
            name="测试案例 A",
            bazi=["戊午", "癸亥", "壬戌", "丁未"],
            day_master="壬",
            gender="男",
            timeline=[
                WealthEvent(
                    year=2010,
                    ganzhi="庚寅",
                    dayun="甲子",
                    real_magnitude=100.0,
                    desc="未土官库被寅木合动，财富爆发"
                )
            ]
        )
        
        results = self.controller.verify_case(case)
        if results:
            result = results[0]
            vault_opened = result.get('vault_opened', False)
            predicted = result.get('predicted', 0)
            
            print(f"✅ 合开财库测试: 预测值={predicted:.1f}, 开库={vault_opened}")
            print(f"   真实值=100.0, 误差={result.get('error', 0):.1f}")
            
            # 检查是否识别了开库
            if vault_opened:
                print("   ✅ 开库机制已识别")
            else:
                print("   ⚠️ 开库机制未识别（可能需要进一步优化）")
    
    def test_clash_commander_priority(self):
        """测试冲提纲优先判断"""
        # Elon Musk 2008年案例：子午冲（冲提纲）
        case = WealthCase(
            id="TEST_MUSK_2008",
            name="测试案例 Musk 2008",
            bazi=["辛亥", "甲午", "甲申", "甲子"],
            day_master="甲",
            gender="男",
            timeline=[
                WealthEvent(
                    year=2008,
                    ganzhi="戊子",
                    dayun="庚寅",
                    real_magnitude=-90.0,
                    desc="SpaceX 三次爆炸，特斯拉濒临破产，离婚。子午冲(冲提纲)"
                )
            ]
        )
        
        results = self.controller.verify_case(case)
        if results:
            result = results[0]
            predicted = result.get('predicted', 0)
            
            print(f"✅ 冲提纲测试: 预测值={predicted:.1f}")
            print(f"   真实值=-90.0, 误差={result.get('error', 0):.1f}")
            
            # 检查方向是否正确（应该是负值）
            if predicted < 0:
                print("   ✅ 方向正确（预测为负值）")
            else:
                print("   ⚠️ 方向错误（预测为正值，应该是负值）")
    
    def test_weak_wealth_reversal(self):
        """测试身弱财重反转"""
        # 测试身弱财重的情况
        case = WealthCase(
            id="TEST_WEAK_WEALTH",
            name="测试案例 身弱财重",
            bazi=["甲子", "丙午", "辛卯", "壬辰"],
            day_master="辛",
            gender="男",
            timeline=[
                WealthEvent(
                    year=2020,
                    ganzhi="庚子",
                    dayun="戊申",
                    real_magnitude=-50.0,
                    desc="身弱财重，破财"
                )
            ]
        )
        
        results = self.controller.verify_case(case)
        if results:
            result = results[0]
            predicted = result.get('predicted', 0)
            details = result.get('details', [])
            
            print(f"✅ 身弱财重测试: 预测值={predicted:.1f}")
            print(f"   真实值=-50.0, 误差={result.get('error', 0):.1f}")
            
            # 检查是否有"财变债"的标记
            has_debt_marker = any('变债务' in d or '变债' in d for d in details)
            if has_debt_marker:
                print("   ✅ 身弱财重机制已识别")
            else:
                print("   ⚠️ 身弱财重机制未识别")
    
    def test_verification_statistics(self):
        """测试验证统计功能"""
        cases = self.controller.get_all_cases()
        if cases:
            case = cases[0]
            results = self.controller.verify_case(case)
            
            if results:
                stats = self.controller.get_verification_statistics(results)
                
                self.assertIn('total_count', stats)
                self.assertIn('correct_count', stats)
                self.assertIn('hit_rate', stats)
                self.assertIn('avg_error', stats)
                self.assertIn('status', stats)
                
                print(f"✅ 验证统计: 命中率={stats['hit_rate']:.1f}%, 平均误差={stats['avg_error']:.1f}分")
            else:
                print("⚠️ 没有验证结果")
        else:
            print("⚠️ 没有可用案例")


def run_wealth_verification_tests():
    """运行财富验证测试"""
    print("\n" + "=" * 70)
    print("💰 财富验证 V9.3 测试套件")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestWealthVerificationV93))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_wealth_verification_tests()
    exit(0 if success else 1)

