#!/usr/bin/env python3
"""
Antigravity V8.8 自动化全面测试套件
====================================
运行方式: python3 scripts/run_full_tests.py

此脚本执行:
1. V8.8 综合测试 (核心功能)
2. 相变协议测试
3. 混合引擎回归测试
4. 烟雾测试 (端到端验证)
5. 生成测试报告
"""

import subprocess
import sys
import os
from datetime import datetime

# 切换到项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.append(PROJECT_ROOT)


def run_pytest_suite():
    """运行核心测试套件 (Using unittest)"""
    print("\n" + "=" * 70)
    print("🧪 阶段 1: 核心测试套件 (Core Test Suite)")
    print("=" * 70)
    
    # Files to test
    test_files = [
        "tests/test_v88_comprehensive.py",
        "tests/test_controller_architecture.py",
        "tests/test_v88_hybrid.py"
    ]
    
    cmd = [sys.executable, "-m", "unittest", "-v"] + test_files
    
    result = subprocess.run(
        cmd,
        capture_output=False
    )
    
    return result.returncode == 0


def run_smoke_test():
    """运行端到端烟雾测试"""
    print("\n" + "=" * 70)
    print("🔥 阶段 2: 端到端烟雾测试 (Smoke Test)")
    print("=" * 70)
    
    try:
        from core.engine_v88 import EngineV88
        from core.bazi_profile import BaziProfile
        
        engine = EngineV88()
        
        # 测试1: 创建 BaziProfile
        birth_date = datetime(1990, 5, 15, 12)
        profile = BaziProfile(birth_date, gender=1)
        assert profile.day_master is not None
        assert len(profile.pillars) == 4
        print(f"  ✅ BaziProfile 创建成功: DM={profile.day_master}")
        
        # 测试2: 旺衰判定
        bazi_list = [profile.pillars['year'], profile.pillars['month'],
                     profile.pillars['day'], profile.pillars['hour']]
        verdict, score = engine.evaluate_strength(profile.day_master, bazi_list)
        assert verdict in ['Strong', 'Weak', 'Moderate']
        print(f"  ✅ 旺衰判定成功: {verdict} ({score:.1f})")
        
        # 测试3: 流年推演
        ctx = engine.calculate_year_context(profile, 2024)
        assert ctx.year == 2024
        assert ctx.pillar is not None
        assert ctx.icon is not None
        print(f"  ✅ 流年推演成功: {ctx.year} {ctx.pillar} {ctx.icon}")
        
        # 测试4: 大运时间轴
        timeline = engine.get_luck_timeline(profile, 2024, 5)
        assert len(timeline) == 5
        print(f"  ✅ 大运时间轴成功: {len(timeline)} 年")
        
        # 测试5: 能量计算
        case_data = {
            'day_master': profile.day_master,
            'year': profile.pillars['year'],
            'month': profile.pillars['month'],
            'day': profile.pillars['day'],
            'hour': profile.pillars['hour'],
            'gender': 1
        }
        energy = engine.calculate_energy(case_data)
        assert 'wang_shuai' in energy
        assert 'career' in energy
        print(f"  ✅ 能量计算成功: career={energy['career']:.1f}, wealth={energy['wealth']:.1f}")
        
        print("\n  🎉 所有烟雾测试通过！")
        return True
        
    except Exception as e:
        import traceback
        print(f"\n  ❌ 烟雾测试失败: {e}")
        traceback.print_exc()
        return False


def run_sub_engine_test():
    """测试子引擎"""
    print("\n" + "=" * 70)
    print("⚙️ 阶段 3: 子引擎验证 (Sub-Engine Verification)")
    print("=" * 70)
    
    try:
        from core.engine_v88 import EngineV88
        
        engine = EngineV88()
        
        # 验证所有子引擎存在
        assert engine.treasury_engine is not None
        print("  ✅ TreasuryEngine 初始化")
        
        assert engine.skull_engine is not None
        print("  ✅ SkullEngine 初始化")
        
        assert engine.harmony_engine is not None
        print("  ✅ HarmonyEngine 初始化")
        
        assert engine.luck_engine is not None
        print("  ✅ LuckEngine 初始化")
        
        # 测试骷髅协议
        branches = ['丑', '未', '戌']
        result = engine.skull_engine.evaluate(branches)
        assert result['icon'] == '💀'
        assert result['score'] <= -40
        print(f"  ✅ 骷髅协议触发: score={result['score']}, icon={result['icon']}")
        
        print("\n  🎉 所有子引擎验证通过！")
        return True
        
    except Exception as e:
        print(f"\n  ❌ 子引擎验证失败: {e}")
        return False


def generate_report(results):
    """生成测试报告"""
    print("\n" + "=" * 70)
    print("📊 测试报告 (Test Report)")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\n  日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  版本: V8.8 Modular Genesis Edition")
    print(f"\n  测试结果:")
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"    {name}: {status}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED - SYSTEM PRODUCTION READY!")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        print("=" * 70)
        return 1


def main():
    """主入口"""
    print("\n" + "=" * 70)
    print("🚀 ANTIGRAVITY V8.8 自动化全面测试")
    print("=" * 70)
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  工作目录: {os.getcwd()}")
    
    results = {}
    
    # 运行各阶段测试
    results['Core Test Suite'] = run_pytest_suite()
    results['Smoke Test'] = run_smoke_test()
    results['Sub-Engine Verification'] = run_sub_engine_test()
    
    # 生成报告
    exit_code = generate_report(results)
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
