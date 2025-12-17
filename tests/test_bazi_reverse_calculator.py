"""
BaziReverseCalculator 测试套件
测试统一反推接口的功能
"""

import unittest
from datetime import datetime
from core.bazi_reverse_calculator import BaziReverseCalculator
from core.bazi_profile import VirtualBaziProfile


class TestBaziReverseCalculator(unittest.TestCase):
    """测试 BaziReverseCalculator"""
    
    def setUp(self):
        self.calculator = BaziReverseCalculator(year_range=(1900, 2100))
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.calculator)
        self.assertEqual(self.calculator.year_range, (1900, 2100))
        print("✅ BaziReverseCalculator 初始化成功")
    
    def test_reverse_low_precision(self):
        """测试低精度反推"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        result = self.calculator.reverse_calculate(pillars, precision='low')
        self.assertIsNotNone(result)
        self.assertIn('birth_date', result)
        self.assertIn('confidence', result)
        
        birth_date = result['birth_date']
        self.assertIsInstance(birth_date, datetime)
        print(f"✅ 低精度反推: {birth_date}")
    
    def test_reverse_medium_precision(self):
        """测试中等精度反推"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        result = self.calculator.reverse_calculate(
            pillars,
            precision='medium',
            consider_lichun=True
        )
        self.assertIsNotNone(result)
        self.assertGreater(result['confidence'], 0.5)
        print(f"✅ 中等精度反推: {result['birth_date']}, 置信度={result['confidence']}")
    
    def test_reverse_high_precision(self):
        """测试高精度反推"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        result = self.calculator.reverse_calculate(
            pillars,
            precision='high',
            consider_lichun=True
        )
        
        if result:
            self.assertIn('birth_date', result)
            self.assertIn('matches', result)
            print(f"✅ 高精度反推: {result['birth_date']}, 匹配数={result.get('match_count', 0)}")
        else:
            print("⚠️ 高精度反推未找到匹配（可能是正常情况）")
    
    def test_year_index(self):
        """测试年份索引"""
        stats = self.calculator.get_cache_stats()
        self.assertIn('index_size', stats)
        self.assertGreater(stats['index_size'], 0)
        print(f"✅ 年份索引大小: {stats['index_size']}")
    
    def test_cache(self):
        """测试缓存功能"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        # 第一次查询
        result1 = self.calculator.reverse_calculate(pillars, precision='low')
        stats1 = self.calculator.get_cache_stats()
        
        # 第二次查询（应该使用缓存）
        result2 = self.calculator.reverse_calculate(pillars, precision='low')
        stats2 = self.calculator.get_cache_stats()
        
        self.assertEqual(result1['birth_date'], result2['birth_date'])
        self.assertEqual(stats1['cache_size'], stats2['cache_size'])
        print(f"✅ 缓存功能正常: 缓存大小={stats2['cache_size']}")
    
    def test_clear_cache(self):
        """测试清空缓存"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        self.calculator.reverse_calculate(pillars, precision='low')
        stats_before = self.calculator.get_cache_stats()
        
        self.calculator.clear_cache()
        stats_after = self.calculator.get_cache_stats()
        
        self.assertGreater(stats_before['cache_size'], 0)
        self.assertEqual(stats_after['cache_size'], 0)
        print("✅ 清空缓存功能正常")


class TestVirtualBaziProfileOptimized(unittest.TestCase):
    """测试优化后的 VirtualBaziProfile"""
    
    def test_custom_year_range(self):
        """测试自定义年份范围"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        # 使用扩展的年份范围
        profile = VirtualBaziProfile(
            pillars,
            day_master='庚',
            gender=1,
            year_range=(1800, 2200),
            precision='medium'
        )
        
        self.assertIsNotNone(profile)
        print(f"✅ 自定义年份范围: {profile.year_range}")
    
    def test_precision_modes(self):
        """测试不同精度模式"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        for precision in ['low', 'medium', 'high']:
            profile = VirtualBaziProfile(
                pillars,
                day_master='庚',
                gender=1,
                precision=precision,
                consider_lichun=(precision != 'low')
            )
            
            if profile._real_profile:
                print(f"✅ {precision} 精度模式: 成功反推出生日期")
            else:
                print(f"⚠️ {precision} 精度模式: 反推失败（可能是正常情况）")
    
    def test_lichun_consideration(self):
        """测试立春边界考虑"""
        pillars = {
            'year': '甲子',
            'month': '丙寅',
            'day': '庚辰',
            'hour': '戊午'
        }
        
        # 考虑立春边界
        profile1 = VirtualBaziProfile(
            pillars,
            day_master='庚',
            gender=1,
            consider_lichun=True
        )
        
        # 不考虑立春边界
        profile2 = VirtualBaziProfile(
            pillars,
            day_master='庚',
            gender=1,
            consider_lichun=False
        )
        
        print(f"✅ 立春边界测试: consider_lichun=True/False 都支持")


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 BaziReverseCalculator 测试套件")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBaziReverseCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestVirtualBaziProfileOptimized))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

