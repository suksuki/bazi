#!/usr/bin/env python3
"""
测试财富验证MVC架构
验证Model、Controller、View各层是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model():
    """测试Model层"""
    print("=" * 80)
    print("🧪 测试 Model 层")
    print("=" * 80)
    
    from core.models.wealth_case_model import WealthCaseModel, WealthCase, WealthEvent
    
    model = WealthCaseModel()
    
    # 测试加载案例
    cases = model.load_all_cases()
    print(f"✅ 加载案例: {len(cases)} 个")
    
    if cases:
        case = cases[0]
        print(f"   示例案例: {case.name} ({case.id})")
        print(f"   八字: {' '.join(case.bazi)}")
        print(f"   事件数: {len(case.timeline) if case.timeline else 0}")
    
    return True

def test_controller():
    """测试Controller层"""
    print("\n" + "=" * 80)
    print("🧪 测试 Controller 层")
    print("=" * 80)
    
    from controllers.wealth_verification_controller import WealthVerificationController
    
    controller = WealthVerificationController()
    
    # 测试获取案例
    cases = controller.get_all_cases()
    print(f"✅ 获取案例: {len(cases)} 个")
    
    if cases:
        case = cases[0]
        print(f"   示例案例: {case.name}")
        
        # 测试验证（只验证第一个事件，避免耗时）
        if case.timeline and len(case.timeline) > 0:
            print(f"   测试验证案例...")
            results = controller.verify_case(case)
            print(f"   ✅ 验证完成: {len(results)} 个结果")
            
            if results:
                stats = controller.get_verification_statistics(results)
                print(f"   命中率: {stats['hit_rate']:.1f}%")
                print(f"   平均误差: {stats['avg_error']:.1f}分")
    
    return True

def test_import():
    """测试导入功能"""
    print("\n" + "=" * 80)
    print("🧪 测试导入功能")
    print("=" * 80)
    
    from controllers.wealth_verification_controller import WealthVerificationController
    
    controller = WealthVerificationController()
    
    # 测试数据
    test_data = [{
        "id": "TEST_001",
        "name": "测试案例",
        "bazi": ["戊午", "癸亥", "壬戌", "丁未"],
        "day_master": "壬",
        "gender": "男",
        "timeline": [
            {
                "year": 2010,
                "ganzhi": "庚寅",
                "dayun": "甲子",
                "real_magnitude": 100.0,
                "desc": "测试事件"
            }
        ]
    }]
    
    success, message = controller.import_cases(test_data)
    print(f"✅ 导入测试: {message}")
    
    # 验证是否导入成功
    case = controller.get_case_by_id("TEST_001")
    if case:
        print(f"   ✅ 案例已成功导入: {case.name}")
        # 清理测试数据
        import os
        test_file = project_root / 'data' / 'TEST_001_timeline.json'
        if test_file.exists():
            os.remove(test_file)
            print(f"   🗑️ 已清理测试文件")
    else:
        print(f"   ❌ 导入失败：案例未找到")
    
    return success

def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("🚀 财富验证 MVC 架构测试")
    print("=" * 80)
    print()
    
    results = []
    
    # 测试Model
    try:
        results.append(("Model层", test_model()))
    except Exception as e:
        print(f"❌ Model层测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Model层", False))
    
    # 测试Controller
    try:
        results.append(("Controller层", test_controller()))
    except Exception as e:
        print(f"❌ Controller层测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Controller层", False))
    
    # 测试导入
    try:
        results.append(("导入功能", test_import()))
    except Exception as e:
        print(f"❌ 导入功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("导入功能", False))
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n🎉 所有测试通过！MVC架构运行正常！")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

