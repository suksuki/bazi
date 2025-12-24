"""
[V13.7] REAL_01 案例验证：通根增益回归测试
===========================================

核心任务：检查通根增益是否锁定在实证值 2.229

验证步骤：
1. 加载 REAL_01 案例数据（癸水日主）
2. 注入实证大运与地理参数
3. 提取 MOD_10 计算出的 rooting_gain 原始数值
4. 对比实证标尺 2.229

预期结果：
- base_gain = 2.0 (Main 本气通根)
- geo_correction = ε_geo * K_geo²
- corrected_gain = 2.0 * (1 + geo_correction) ≈ 2.229
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.assets.resonance_booster import ResonanceBooster
from core.trinity.core.middleware.influence_bus import InfluenceBus, InfluenceFactor, ExpectationVector, PhysicsTensor, NonlinearType
from typing import Dict, Any, Optional


class REAL_01_Verification:
    """
    REAL_01 案例验证器
    
    案例信息：
    - 日主：癸水
    - 目标：通根增益 = 2.229
    - 验证：地理二阶修正是否正确应用
    """
    
    # 实证值
    TARGET_GAIN = 2.229
    TOLERANCE = 0.01  # 允许误差 ±0.01
    
    def __init__(self):
        self.results = {}
    
    def create_real_01_case(self) -> Dict[str, Any]:
        """
        创建 REAL_01 案例数据
        
        根据文档，这是一个癸水日主的案例，需要：
        - 本气通根（Main）：基础增益 2.0
        - 地理修正：通过 InfluenceBus 注入
        """
        # 假设的八字（需要根据实际案例调整）
        # 癸水日主，需要水元素的地支通根
        case = {
            "name": "REAL_01",
            "day_master": "癸",
            "day_master_element": "water",
            "bazi": ["甲子", "丙寅", "癸亥", "壬子"],  # 假设八字，包含子、亥水根
            "stem": "癸",
            "branches": ["子", "亥"],  # 水元素的地支
            "geo_element": "water",  # 假设地理环境为水区
            "geo_factor": 1.5,  # 地理修正系数（需要调整以达到 2.229）
        }
        return case
    
    def create_influence_bus(self, case: Dict[str, Any]) -> InfluenceBus:
        """
        创建并配置 InfluenceBus，注入地理参数
        """
        bus = InfluenceBus()
        
        # 创建地理修正因子（地域作为介质阻尼系数）
        geo_factor = InfluenceFactor(
            name="GeoBias/地域",
            nonlinear_type=NonlinearType.GAUSSIAN_DAMPING,  # 使用现有的类型
            weight=1.0,
            enabled=True,
            metadata={
                "geo_factor": case["geo_factor"],
                "geo_element": case["geo_element"]
            }
        )
        
        # 注册地理因子
        bus.register(geo_factor)
        
        return bus
    
    def calculate_expected_geo_correction(self, base_gain: float, target_gain: float) -> float:
        """
        根据目标增益反推地理修正系数
        
        公式：G_res = G_base * (1 + ε_geo * K_geo²)
        如果 G_base = 2.0, G_res = 2.229
        则：2.229 = 2.0 * (1 + ε_geo * K_geo²)
        即：ε_geo * K_geo² = (2.229 / 2.0) - 1 = 0.1145
        """
        if base_gain <= 0:
            return 0.0
        
        correction_ratio = (target_gain / base_gain) - 1.0
        return correction_ratio
    
    def verify_rooting_gain(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证通根增益
        
        返回详细的验证报告
        """
        print(f"\n{'='*60}")
        print(f"REAL_01 案例验证：通根增益回归测试")
        print(f"{'='*60}\n")
        
        # 1. 创建 InfluenceBus 并注入地理参数
        influence_bus = self.create_influence_bus(case)
        
        # 2. 计算通根增益
        result = ResonanceBooster.calculate_resonance_gain(
            stem=case["stem"],
            branches=case["branches"],
            influence_bus=influence_bus
        )
        
        actual_gain = result.get("gain", 0.0)
        best_root = result.get("best_root", "unknown")
        root_type = result.get("root_type", "unknown")
        status = result.get("status", "unknown")
        
        # 3. 提取调试信息
        debug_info = result.get("debug_info", {})
        detected_matches = debug_info.get("detected_matches", [])
        
        # 4. 计算误差
        error = abs(actual_gain - self.TARGET_GAIN)
        relative_error = (error / self.TARGET_GAIN) * 100 if self.TARGET_GAIN > 0 else 0
        
        # 5. 判断是否通过
        passed = error <= self.TOLERANCE
        
        # 6. 反推地理修正系数（用于调试）
        base_gain = 2.0  # Main 本气通根
        expected_correction = self.calculate_expected_geo_correction(base_gain, self.TARGET_GAIN)
        
        # 7. 生成报告
        report = {
            "case_name": case["name"],
            "day_master": case["day_master"],
            "day_master_element": case["day_master_element"],
            "stem": case["stem"],
            "branches": case["branches"],
            "geo_element": case["geo_element"],
            "geo_factor": case["geo_factor"],
            "target_gain": self.TARGET_GAIN,
            "actual_gain": actual_gain,
            "error": error,
            "relative_error": relative_error,
            "tolerance": self.TOLERANCE,
            "passed": passed,
            "best_root": best_root,
            "root_type": root_type,
            "status": status,
            "base_gain": base_gain,
            "expected_correction": expected_correction,
            "detected_matches": detected_matches,
            "debug_info": debug_info
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """
        打印验证报告
        """
        print(f"\n{'='*60}")
        print(f"通根增益验证报告")
        print(f"{'='*60}\n")
        
        print(f"案例信息：")
        print(f"  名称: {report['case_name']}")
        print(f"  日主: {report['day_master']} ({report['day_master_element']})")
        print(f"  天干: {report['stem']}")
        print(f"  地支: {report['branches']}")
        print(f"  地理环境: {report['geo_element']} (系数: {report['geo_factor']})")
        
        print(f"\n计算结果：")
        print(f"  目标增益: {report['target_gain']:.4f}")
        print(f"  实际增益: {report['actual_gain']:.4f}")
        print(f"  绝对误差: {report['error']:.4f}")
        print(f"  相对误差: {report['relative_error']:.2f}%")
        print(f"  允许误差: ±{report['tolerance']:.4f}")
        
        print(f"\n通根信息：")
        print(f"  最佳通根: {report['best_root']}")
        print(f"  通根类型: {report['root_type']}")
        print(f"  状态: {report['status']}")
        print(f"  基础增益: {report['base_gain']:.2f} (Main)")
        print(f"  预期修正: {report['expected_correction']:.4f}")
        
        if report['detected_matches']:
            print(f"\n检测到的匹配：")
            for match in report['detected_matches']:
                print(f"  - {match}")
        
        print(f"\n验证结果：")
        if report['passed']:
            print(f"  ✅ 通过！实际增益 {report['actual_gain']:.4f} 符合目标值 {report['target_gain']:.4f}")
        else:
            print(f"  ❌ 未通过！实际增益 {report['actual_gain']:.4f} 与目标值 {report['target_gain']:.4f} 差异过大")
            print(f"     需要调整地理修正系数或算法参数")
        
        print(f"\n{'='*60}\n")
    
    def run_verification(self) -> Dict[str, Any]:
        """
        运行完整验证流程
        """
        # 1. 创建案例
        case = self.create_real_01_case()
        
        # 2. 执行验证
        report = self.verify_rooting_gain(case)
        
        # 3. 打印报告
        self.print_report(report)
        
        # 4. 如果未通过，尝试调整地理系数
        if not report['passed']:
            print(f"\n{'='*60}")
            print(f"参数调整建议")
            print(f"{'='*60}\n")
            
            # 反推所需的地理系数
            base_gain = report['base_gain']
            target_gain = report['target_gain']
            current_geo_factor = case['geo_factor']
            
            # 假设 K_geo = geo_factor，则 ε_geo * K_geo² = ε_geo * geo_factor²
            # 如果 geo_factor = 1.5，则 ε_geo = 0.1145 / (1.5²) = 0.0509
            # 或者，如果 ε_geo = geo_factor - 1.0 = 0.5，则 K_geo² = 0.1145 / 0.5 = 0.229
            # 即 K_geo = sqrt(0.229) = 0.478
            
            # 更简单的方法：如果 geo_factor = 1.5，则修正应该是：
            # correction = (geo_factor - 1.0) * geo_factor² = 0.5 * 2.25 = 1.125
            # 但这样太大了，不符合预期
            
            # 根据公式 G_res = G_base * (1 + ε_geo * K_geo²)
            # 如果 geo_factor 代表 ε_geo，K_geo 代表地理影响强度
            # 则：2.229 = 2.0 * (1 + geo_factor * K_geo²)
            # 即：geo_factor * K_geo² = 0.1145
            
            # 如果 geo_factor = 1.5，则 K_geo² = 0.1145 / 1.5 = 0.0763
            # 即 K_geo = sqrt(0.0763) = 0.276
            
            # 或者，如果 K_geo = geo_factor = 1.5，则 ε_geo = 0.1145 / (1.5²) = 0.0509
            
            print(f"当前地理系数: {current_geo_factor}")
            print(f"目标修正比例: {report['expected_correction']:.4f}")
            print(f"\n建议调整方案：")
            print(f"  方案1: 调整 geo_factor 为 {current_geo_factor * (1 + report['expected_correction']):.2f}")
            print(f"  方案2: 检查算法中 ε_geo 和 K_geo 的计算逻辑")
            print(f"  方案3: 验证地理修正公式是否正确应用")
        
        return report


def main():
    """
    主函数：执行 REAL_01 案例验证
    """
    verifier = REAL_01_Verification()
    report = verifier.run_verification()
    
    # 返回验证结果（用于自动化测试）
    return report['passed']


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

