#!/usr/bin/env python3
"""
Antigravity V9.3 全检自动化测试套件
====================================
运行方式: python3 scripts/run_full_check_v93.py

此脚本执行:
1. MCP V9.3 功能测试
2. 财富验证改进测试
3. 核心引擎回归测试
4. 集成测试
5. 生成测试报告
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 切换到项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)


def run_test_suite(test_path: str, suite_name: str) -> bool:
    """运行测试套件"""
    print(f"\n{'=' * 70}")
    print(f"🧪 {suite_name}")
    print(f"{'=' * 70}")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode == 0


def run_mcp_tests() -> bool:
    """运行 MCP V9.3 测试"""
    print(f"\n{'=' * 70}")
    print("🌍 MCP V9.3 功能测试")
    print(f"{'=' * 70}")
    
    try:
        # 直接运行测试模块
        result = subprocess.run(
            [sys.executable, "tests/test_mcp_v93.py"],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ MCP 测试失败: {e}")
        return False


def run_wealth_verification_tests() -> bool:
    """运行财富验证测试"""
    print(f"\n{'=' * 70}")
    print("💰 财富验证 V9.3 测试")
    print(f"{'=' * 70}")
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/test_wealth_verification_v93.py"],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 财富验证测试失败: {e}")
        return False


def run_core_regression_tests() -> bool:
    """运行核心引擎回归测试"""
    print(f"\n{'=' * 70}")
    print("⚙️ 核心引擎回归测试")
    print(f"{'=' * 70}")
    
    test_files = [
        "tests/test_v88_comprehensive.py",
        "tests/test_flux_engine.py",
        "tests/test_controller_facade.py"
    ]
    
    all_passed = True
    for test_file in test_files:
        if os.path.exists(test_file):
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=False
            )
            if result.returncode != 0:
                all_passed = False
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
    
    return all_passed


def run_integration_tests() -> bool:
    """运行集成测试"""
    print(f"\n{'=' * 70}")
    print("🔗 集成测试")
    print(f"{'=' * 70}")
    
    test_files = [
        "tests/integration/test_controller_integration.py"
    ]
    
    all_passed = True
    for test_file in test_files:
        if os.path.exists(test_file):
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=False
            )
            if result.returncode != 0:
                all_passed = False
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
    
    return all_passed


def run_smoke_test() -> bool:
    """运行端到端烟雾测试"""
    print(f"\n{'=' * 70}")
    print("🔥 端到端烟雾测试")
    print(f"{'=' * 70}")
    
    try:
        from controllers.bazi_controller import BaziController
        from core.processors.geo import GeoProcessor
        from core.processors.hourly_context import HourlyContextProcessor
        from core.processors.era import EraProcessor
        from core.engine_graph import GraphNetworkEngine
        
        # 测试1: Controller 初始化
        controller = BaziController()
        assert controller is not None
        print("  ✅ BaziController 初始化成功")
        
        # 测试2: GeoProcessor
        geo = GeoProcessor()
        geo_result = geo.process("Beijing")
        assert isinstance(geo_result, dict)
        print(f"  ✅ GeoProcessor 测试成功: {geo_result.get('desc', 'N/A')}")
        
        # 测试3: HourlyContextProcessor
        hourly = HourlyContextProcessor()
        hourly_result = hourly.process({
            'day_master': '甲',
            'current_time': datetime.now(),
            'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
        })
        assert 'hourly_pillar' in hourly_result
        print(f"  ✅ HourlyContextProcessor 测试成功: {hourly_result['hourly_pillar']}")
        
        # 测试4: EraProcessor
        era = EraProcessor()
        era_result = era.process(2024)
        if era_result:
            print(f"  ✅ EraProcessor 测试成功: {era_result.get('desc', 'N/A')}")
        else:
            print("  ⚠️ EraProcessor 未找到当前时代数据")
        
        # 测试5: GraphNetworkEngine
        engine = GraphNetworkEngine()
        result = engine.analyze(['甲子', '丙午', '辛卯', '壬辰'], '辛', '男')
        assert 'strength_score' in result
        assert 'uncertainty' in result
        print(f"  ✅ GraphNetworkEngine 测试成功: 身强分数={result['strength_score']:.1f}")
        
        # 测试6: 不确定性计算
        uncertainty = result.get('uncertainty', {})
        if uncertainty.get('has_uncertainty'):
            print(f"  ✅ 不确定性检测: {uncertainty.get('pattern_type', 'Unknown')}")
        else:
            print("  ℹ️ 格局稳定，无不确定性")
        
        print("\n  🎉 所有烟雾测试通过！")
        return True
        
    except Exception as e:
        import traceback
        print(f"\n  ❌ 烟雾测试失败: {e}")
        traceback.print_exc()
        return False


def generate_test_report(results: dict) -> dict:
    """生成测试报告"""
    print(f"\n{'=' * 70}")
    print("📊 测试报告 (Test Report)")
    print(f"{'=' * 70}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': 'V9.3 MCP Improvements',
        'total_tests': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': (passed / total * 100) if total > 0 else 0,
        'results': results
    }
    
    print(f"\n  日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  版本: V9.3 MCP Improvements")
    print(f"\n  测试结果:")
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"    {name}: {status}")
    
    print(f"\n  总计: {passed}/{total} 通过 ({report['pass_rate']:.1f}%)")
    
    # 保存报告到文件
    report_file = PROJECT_ROOT / "test_report_v93.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n  报告已保存: {report_file}")
    
    if passed == total:
        print(f"\n{'=' * 70}")
        print("🎉 ALL TESTS PASSED - SYSTEM PRODUCTION READY!")
        print(f"{'=' * 70}")
        return report
    else:
        print(f"\n{'=' * 70}")
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        print(f"{'=' * 70}")
        return report


def main():
    """主入口"""
    print(f"\n{'=' * 70}")
    print("🚀 ANTIGRAVITY V9.3 全检自动化测试")
    print(f"{'=' * 70}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  工作目录: {os.getcwd()}")
    
    results = {}
    
    # 运行各阶段测试
    results['MCP V9.3 功能测试'] = run_mcp_tests()
    results['财富验证 V9.3 测试'] = run_wealth_verification_tests()
    results['核心引擎回归测试'] = run_core_regression_tests()
    results['集成测试'] = run_integration_tests()
    results['端到端烟雾测试'] = run_smoke_test()
    
    # 生成报告
    report = generate_test_report(results)
    
    # 返回退出码
    exit_code = 0 if report['passed'] == report['total_tests'] else 1
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

