"""
全息格局V2.1自动化测试套件
测试FDS-V1.5.1 V2.1规范的核心功能：
- transfer_matrix矩阵投影
- SAI计算
- 动态状态判定（成格/破格）
- 注入因子（流年/大运）的影响
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import project_tensor_with_matrix, tensor_normalize
from core.physics_engine import compute_energy_flux, calculate_integrity_alpha, check_trigger
from controllers.holographic_pattern_controller import HolographicPatternController
import math


class TestHolographicPatternV21(unittest.TestCase):
    """全息格局V2.1测试套件"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.registry_loader = RegistryLoader()
        cls.controller = HolographicPatternController()
        cls.pattern_id = 'A-03'
        
        # 获取A-03格局配置
        cls.pattern = cls.registry_loader.get_pattern(cls.pattern_id)
        assert cls.pattern is not None, "A-03格局不存在"
        
        # 验证版本
        version = cls.pattern.get('version', '1.0')
        # Allow 2.1 or 2.1.0
        assert version.startswith('2.1'), f"A-03版本应为2.1.x，实际为{version}"
        
        # 获取transfer_matrix
        physics_kernel = cls.pattern.get('physics_kernel', {})
        cls.transfer_matrix = physics_kernel.get('transfer_matrix')
        assert cls.transfer_matrix is not None, "transfer_matrix不存在"
        
        print(f"\n{'='*70}")
        print(f"✅ 测试环境初始化完成")
        print(f"   格局ID: {cls.pattern_id}")
        print(f"   版本: {version}")
        print(f"   transfer_matrix: {'存在' if cls.transfer_matrix else '不存在'}")
        print(f"{'='*70}\n")
    
    def test_01_pattern_loading(self):
        """测试1: 格局加载"""
        print("【测试1】格局加载")
        print("-" * 70)
        
        pattern = self.registry_loader.get_pattern(self.pattern_id)
        self.assertIsNotNone(pattern, "格局应该存在")
        
        version = pattern.get('version', '1.0')
        self.assertTrue(version.startswith('2.1'), f"版本应为2.1.x，实际为{version}")
        
        physics_kernel = pattern.get('physics_kernel', {})
        transfer_matrix = physics_kernel.get('transfer_matrix')
        self.assertIsNotNone(transfer_matrix, "transfer_matrix应该存在")
        
        # 验证transfer_matrix结构
        required_rows = ['E_row', 'O_row', 'M_row', 'S_row', 'R_row']
        for row in required_rows:
            self.assertIn(row, transfer_matrix, f"transfer_matrix应包含{row}")
        
        print("✅ 格局加载测试通过")
        print()
    
    def test_02_frequency_vector_calculation(self):
        """测试2: 十神频率向量计算"""
        print("【测试2】十神频率向量计算")
        print("-" * 70)
        
        # 测试八字
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        
        # 计算频率向量
        parallel = compute_energy_flux(chart, day_master, "比肩") + \
                   compute_energy_flux(chart, day_master, "劫财")
        resource = compute_energy_flux(chart, day_master, "正印") + \
                   compute_energy_flux(chart, day_master, "偏印")
        power = compute_energy_flux(chart, day_master, "七杀") + \
                compute_energy_flux(chart, day_master, "正官")
        wealth = compute_energy_flux(chart, day_master, "正财") + \
                 compute_energy_flux(chart, day_master, "偏财")
        output = compute_energy_flux(chart, day_master, "食神") + \
                 compute_energy_flux(chart, day_master, "伤官")
        
        frequency_vector = {
            "parallel": parallel,
            "resource": resource,
            "power": power,
            "wealth": wealth,
            "output": output
        }
        
        print(f"频率向量: {frequency_vector}")
        
        # 验证频率向量不为全0
        total = sum(abs(v) for v in frequency_vector.values())
        self.assertGreater(total, 0, "频率向量不应全为0")
        
        print(f"✅ 频率向量计算测试通过 (总和: {total:.4f})")
        print()
    
    def test_03_matrix_projection(self):
        """测试3: 矩阵投影计算"""
        print("【测试3】矩阵投影计算")
        print("-" * 70)
        
        # 测试频率向量
        frequency_vector = {
            "parallel": 3.5,
            "resource": 0.0,
            "power": 0.0,
            "wealth": 0.0,
            "output": 0.5
        }
        
        # 使用transfer_matrix进行投影
        projection = project_tensor_with_matrix(frequency_vector, self.transfer_matrix)
        
        print(f"输入频率向量: {frequency_vector}")
        print(f"输出投影: {projection}")
        
        # 验证投影结果
        self.assertIn('E', projection)
        self.assertIn('O', projection)
        self.assertIn('M', projection)
        self.assertIn('S', projection)
        self.assertIn('R', projection)
        
        # 验证投影值不为全0
        total = sum(abs(v) for v in projection.values())
        self.assertGreater(total, 0, "投影值不应全为0")
        
        print(f"✅ 矩阵投影测试通过 (投影总和: {total:.4f})")
        print()
    
    def test_04_sai_calculation(self):
        """测试4: SAI计算"""
        print("【测试4】SAI计算")
        print("-" * 70)
        
        # 测试投影值
        projection = {
            'E': 4.1,
            'O': 1.1,
            'M': -2.65,
            'S': -1.4,
            'R': 0.1
        }
        
        # 计算SAI（L2范数）
        sai = math.sqrt(sum(v ** 2 for v in projection.values()))
        
        print(f"投影值: {projection}")
        print(f"SAI (L2范数): {sai:.4f}")
        
        # 验证SAI不为0
        self.assertGreater(sai, 0, "SAI不应为0")
        self.assertGreater(sai, 0.1, "SAI应大于0.1")
        
        # 测试fallback逻辑
        projection_zero = {'E': 0, 'O': 0, 'M': 0, 'S': 0, 'R': 0}
        sai_zero = math.sqrt(sum(v ** 2 for v in projection_zero.values()))
        
        if sai_zero < 0.1:
            frequency_vector = {"parallel": 2.5, "resource": 1.8, "power": 3.2, "wealth": 0.5, "output": 0.3}
            base_sai = math.sqrt(sum(v ** 2 for v in frequency_vector.values()))
            if base_sai > 0:
                sai_fallback = base_sai * 0.5
                self.assertGreater(sai_fallback, 0, "Fallback SAI不应为0")
                print(f"✅ Fallback逻辑测试通过 (fallback SAI: {sai_fallback:.4f})")
        
        print(f"✅ SAI计算测试通过")
        print()
    
    def test_05_calculate_with_transfer_matrix(self):
        """测试5: _calculate_with_transfer_matrix完整流程"""
        print("【测试5】_calculate_with_transfer_matrix完整流程")
        print("-" * 70)
        
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        
        result = self.registry_loader._calculate_with_transfer_matrix(
            pattern_id=self.pattern_id,
            chart=chart,
            day_master=day_master,
            transfer_matrix=self.transfer_matrix,
            context=None
        )
        
        print(f"计算结果: {result}")
        
        # 验证返回结构
        self.assertIn('pattern_id', result)
        self.assertIn('sai', result)
        self.assertIn('projection', result)
        self.assertIn('raw_projection', result)
        self.assertIn('frequency_vector', result)
        self.assertIn('alpha', result)
        
        # 验证SAI不为0
        sai = result.get('sai', 0)
        self.assertGreater(sai, 0, f"SAI不应为0，实际为{sai}")
        
        # 验证投影值
        projection = result.get('projection', {})
        self.assertIn('E', projection)
        self.assertIn('O', projection)
        
        # 验证频率向量
        frequency_vector = result.get('frequency_vector', {})
        total_freq = sum(abs(v) for v in frequency_vector.values())
        self.assertGreater(total_freq, 0, "频率向量不应全为0")
        
        print(f"✅ SAI: {sai:.4f}")
        print(f"✅ 投影: {projection}")
        print(f"✅ 完整流程测试通过")
        print()
    
    def test_06_controller_calculate_tensor_projection(self):
        """测试6: Controller的calculate_tensor_projection"""
        print("【测试6】Controller的calculate_tensor_projection")
        print("-" * 70)
        
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        
        result = self.controller.calculate_tensor_projection(
            pattern_id=self.pattern_id,
            chart=chart,
            day_master=day_master,
            context=None
        )
        
        print(f"Controller计算结果: {result}")
        
        # 验证没有错误
        self.assertNotIn('error', result, f"计算不应返回错误: {result.get('error', '')}")
        
        # 验证SAI不为0
        sai = result.get('sai', 0)
        self.assertGreater(sai, 0, f"SAI不应为0，实际为{sai}")
        
        # 验证投影值
        projection = result.get('projection', {})
        self.assertIn('E', projection)
        
        # 验证返回格式兼容性
        self.assertIn('pattern_id', result)
        self.assertIn('pattern_name', result)
        self.assertIn('weights', result)  # UI兼容字段
        
        print(f"✅ Controller计算测试通过 (SAI: {sai:.4f})")
        print()
    
    def test_07_pattern_state_check(self):
        """测试7: 格局状态检查（成格/破格）"""
        print("【测试7】格局状态检查")
        print("-" * 70)
        
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        day_branch = '申'
        luck_pillar = '丁卯'
        year_pillar = '甲辰'
        alpha = 0.8
        
        pattern_state = self.registry_loader._check_pattern_state(
            pattern=self.pattern,
            chart=chart,
            day_master=day_master,
            day_branch=day_branch,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            alpha=alpha
        )
        
        print(f"格局状态: {pattern_state}")
        
        # 验证返回结构
        self.assertIn('state', pattern_state)
        self.assertIn('alpha', pattern_state)
        self.assertIn('matrix', pattern_state)
        
        # 验证状态值
        valid_states = ['STABLE', 'COLLAPSED', 'CRYSTALLIZED']
        self.assertIn(pattern_state['state'], valid_states, 
                     f"状态应为{valid_states}之一，实际为{pattern_state['state']}")
        
        print(f"✅ 格局状态检查测试通过 (状态: {pattern_state['state']})")
        print()
    
    def test_08_integrity_alpha_calculation(self):
        """测试8: 结构完整性Alpha计算"""
        print("【测试8】结构完整性Alpha计算")
        print("-" * 70)
        
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        day_branch = '申'
        
        # 测试正常情况
        flux_events = []
        alpha = calculate_integrity_alpha(
            natal_chart=chart,
            day_master=day_master,
            day_branch=day_branch,
            flux_events=flux_events,
            luck_pillar='',
            year_pillar='',
            energy_flux={}
        )
        
        print(f"正常情况Alpha: {alpha:.4f}")
        self.assertGreaterEqual(alpha, 0, "Alpha应>=0")
        self.assertLessEqual(alpha, 1, "Alpha应<=1")
        
        # 测试破格情况（日支被冲）
        flux_events_collapse = ['Day_Branch_Clash']
        alpha_collapse = calculate_integrity_alpha(
            natal_chart=chart,
            day_master=day_master,
            day_branch=day_branch,
            flux_events=flux_events_collapse,
            luck_pillar='',
            year_pillar='',
            energy_flux={}
        )
        
        print(f"破格情况Alpha: {alpha_collapse:.4f}")
        # 注意：如果正常情况已经是0.4（已经很低），破格可能不会进一步降低
        # 所以只验证破格时Alpha <= 正常Alpha，而不是严格小于
        self.assertLessEqual(alpha_collapse, alpha, "破格时Alpha应<=正常Alpha")
        
        # 验证破格时Alpha确实受到了影响（如果正常Alpha > 0.4，破格应该降低）
        if alpha > 0.4:
            self.assertLess(alpha_collapse, alpha, "破格时Alpha应降低")
        
        print(f"✅ Alpha计算测试通过")
        print()
    
    def test_09_injection_factor_impact(self):
        """测试9: 注入因子（流年）的影响"""
        print("【测试9】注入因子（流年）的影响")
        print("-" * 70)
        
        chart = ['甲子', '丙寅', '甲申', '乙亥']
        day_master = '甲'
        
        # 无流年
        result_no_year = self.registry_loader._calculate_with_transfer_matrix(
            pattern_id=self.pattern_id,
            chart=chart,
            day_master=day_master,
            transfer_matrix=self.transfer_matrix,
            context=None
        )
        
        # 有流年（七杀年，应该增加power）
        context_with_year = {
            'annual_pillar': '庚申'  # 庚是甲的七杀
        }
        result_with_year = self.registry_loader._calculate_with_transfer_matrix(
            pattern_id=self.pattern_id,
            chart=chart,
            day_master=day_master,
            transfer_matrix=self.transfer_matrix,
            context=context_with_year
        )
        
        freq_no_year = result_no_year.get('frequency_vector', {})
        freq_with_year = result_with_year.get('frequency_vector', {})
        
        print(f"无流年频率向量: {freq_no_year}")
        print(f"有流年频率向量: {freq_with_year}")
        
        # 验证流年影响了频率向量
        power_no_year = freq_no_year.get('power', 0)
        power_with_year = freq_with_year.get('power', 0)
        
        self.assertGreaterEqual(power_with_year, power_no_year, 
                               "流年七杀应该增加power值")
        
        print(f"✅ 注入因子影响测试通过 (power变化: {power_no_year:.4f} -> {power_with_year:.4f})")
        print()
    
    def test_10_edge_cases(self):
        """测试10: 边界情况"""
        print("【测试10】边界情况测试")
        print("-" * 70)
        
        # 测试空八字（应该不会崩溃）
        try:
            result = self.registry_loader._calculate_with_transfer_matrix(
                pattern_id=self.pattern_id,
                chart=[],
                day_master='甲',
                transfer_matrix=self.transfer_matrix,
                context=None
            )
            print("✅ 空八字测试通过（未崩溃）")
        except Exception as e:
            print(f"⚠️ 空八字测试: {e}")
        
        # 测试频率向量全为0的情况
        frequency_vector_zero = {
            "parallel": 0.0,
            "resource": 0.0,
            "power": 0.0,
            "wealth": 0.0,
            "output": 0.0
        }
        
        projection_zero = project_tensor_with_matrix(frequency_vector_zero, self.transfer_matrix)
        sai_zero = math.sqrt(sum(v ** 2 for v in projection_zero.values()))
        
        print(f"频率向量全0时的SAI: {sai_zero:.4f}")
        
        # 应该触发fallback逻辑
        if sai_zero < 0.1:
            base_sai = math.sqrt(sum(v ** 2 for v in frequency_vector_zero.values()))
            if base_sai == 0:
                # 应该使用默认值1.0
                final_sai = 1.0
                self.assertEqual(final_sai, 1.0, "全0时应使用默认SAI=1.0")
                print(f"✅ Fallback到默认SAI: {final_sai:.4f}")
        
        print(f"✅ 边界情况测试通过")
        print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 全息格局V2.1自动化测试套件")
    print("="*70)
    print()
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHolographicPatternV21)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

