#!/usr/bin/env python3
"""
修复Musk案例的real_magnitude值
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController

def main():
    """主函数"""
    print("=" * 80)
    print("🔧 修复Musk案例的real_magnitude值")
    print("=" * 80)
    print()
    
    controller = WealthVerificationController()
    
    # 1. 查找Musk案例
    all_cases = controller.get_all_cases()
    musk_case = None
    
    for case in all_cases:
        if 'musk' in case.name.lower() or 'elon' in case.name.lower() or case.id == 'TIMELINE_MUSK_WEALTH':
            musk_case = case
            break
    
    if not musk_case:
        print("❌ 未找到Musk案例，先导入...")
        # 尝试导入
        from scripts.import_musk_case import main as import_musk
        import_musk()
        # 重新查找
        all_cases = controller.get_all_cases()
        for case in all_cases:
            if 'musk' in case.name.lower() or 'elon' in case.name.lower() or case.id == 'TIMELINE_MUSK_WEALTH':
                musk_case = case
                break
    
    if not musk_case:
        print("❌ 仍然未找到Musk案例")
        return
    
    print(f"✅ 找到Musk案例: {musk_case.name} ({musk_case.id})")
    print()
    
    # 2. 正确的real_magnitude值（兼容旧格式和新格式）
    correct_values = {
        1995: 60.0,   # 创业起步（Zip2）
        1999: 60.0,   # Zip2获利
        2000: -50.0,  # 被踢出PayPal
        2002: 80.0,   # PayPal收购（如果存在）
        2008: -90.0,  # 破产危机
        2021: 100.0   # 登顶首富
    }
    
    # 3. 修复timeline
    print("🔧 修复real_magnitude值...")
    fixed = False
    
    if musk_case.timeline:
        for event in musk_case.timeline:
            year = event.year
            if year in correct_values:
                old_value = event.real_magnitude
                new_value = correct_values[year]
                if old_value != new_value:
                    event.real_magnitude = new_value
                    print(f"   ✅ {year}年: {old_value} → {new_value}")
                    fixed = True
                else:
                    print(f"   ✓ {year}年: 已经是正确值 {new_value}")
            else:
                print(f"   ⚠️ {year}年: 未找到对应的正确值")
    
    if not fixed:
        print("   ℹ️ 所有值都已经是正确的，无需修复")
        return
    
    # 4. 保存修复后的案例
    print()
    print("💾 保存修复后的案例...")
    
    from core.models.wealth_case_model import WealthCaseModel
    model = WealthCaseModel()
    
    if model.save_case(musk_case):
        print("✅ 案例已保存")
    else:
        print("❌ 保存失败")
        return
    
    # 5. 验证修复结果
    print()
    print("=" * 80)
    print("🔍 验证修复结果")
    print("=" * 80)
    
    # 重新加载
    fixed_case = controller.get_case_by_id(musk_case.id)
    if fixed_case:
        print(f"✅ 重新加载成功: {fixed_case.name}")
        print()
        print("修复后的real_magnitude值：")
        for event in fixed_case.timeline:
            print(f"   {event.year}年: {event.real_magnitude}")
        
        # 测试验证
        print()
        print("🧪 测试验证...")
        results = controller.verify_case(fixed_case)
        
        if results:
            print("✅ 验证完成")
            print()
            print("验证结果中的real值：")
            for r in results:
                year = r.get('year', 'N/A')
                real = r.get('real', 'N/A')
                print(f"   {year}年: {real}")
        else:
            print("❌ 验证结果为空")
    else:
        print("❌ 重新加载失败")
    
    print("=" * 80)
    print()
    print("🎉 修复完成！")
    print("💡 现在可以在UI中刷新页面查看正确的真实值了。")

if __name__ == "__main__":
    main()

