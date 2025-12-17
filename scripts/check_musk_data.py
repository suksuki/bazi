#!/usr/bin/env python3
"""
检查Musk案例的数据文件，诊断real_magnitude为0的问题
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
    print("🔍 检查Musk案例数据")
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
        print("❌ 未找到Musk案例")
        print("💡 请先运行: python3 scripts/import_musk_case.py")
        return
    
    print(f"✅ 找到Musk案例: {musk_case.name} ({musk_case.id})")
    print(f"   八字: {' '.join(musk_case.bazi)}")
    print()
    
    # 2. 检查timeline数据
    if not musk_case.timeline:
        print("❌ Timeline为空")
        return
    
    print(f"📋 Timeline事件数: {len(musk_case.timeline)}")
    print()
    print("事件详情：")
    for i, event in enumerate(musk_case.timeline, 1):
        print(f"\n{i}. {event.year}年")
        print(f"   流年: {event.ganzhi}")
        print(f"   大运: {event.dayun}")
        print(f"   真实值 (real_magnitude): {event.real_magnitude}")
        print(f"   描述: {event.desc}")
        
        # 检查real_magnitude是否为0
        if event.real_magnitude == 0.0:
            print(f"   ⚠️ 警告: real_magnitude为0，可能是数据问题！")
    
    # 3. 检查数据文件
    print()
    print("=" * 80)
    print("📁 检查数据文件")
    print("=" * 80)
    
    data_dir = project_root / 'data'
    data_file = data_dir / f"{musk_case.id}_timeline.json"
    
    if data_file.exists():
        print(f"✅ 数据文件存在: {data_file}")
        with open(data_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        print(f"   文件格式: {type(file_data)}")
        if isinstance(file_data, list) and len(file_data) > 0:
            case_data = file_data[0]
            print(f"   案例ID: {case_data.get('id', 'N/A')}")
            print(f"   案例名称: {case_data.get('name', 'N/A')}")
            
            timeline = case_data.get('timeline', [])
            print(f"   Timeline事件数: {len(timeline)}")
            
            print("\n   文件中的real_magnitude值：")
            for event in timeline:
                year = event.get('year', 'N/A')
                real_mag = event.get('real_magnitude', 'N/A')
                print(f"      {year}年: {real_mag}")
                
                if real_mag == 0.0 or real_mag == 'N/A':
                    print(f"      ⚠️ 警告: {year}年的real_magnitude为0或缺失！")
        else:
            print("   ⚠️ 文件格式不正确（应该是包含案例的数组）")
    else:
        print(f"❌ 数据文件不存在: {data_file}")
    
    # 4. 测试验证
    print()
    print("=" * 80)
    print("🧪 测试验证（查看实际使用的值）")
    print("=" * 80)
    
    results = controller.verify_case(musk_case)
    
    if results:
        print(f"✅ 验证完成，共 {len(results)} 个结果")
        print()
        print("验证结果中的real值：")
        for r in results:
            year = r.get('year', 'N/A')
            real = r.get('real', 'N/A')
            predicted = r.get('predicted', 'N/A')
            print(f"   {year}年: real={real}, predicted={predicted}")
            
            if real == 0.0 or real == 'N/A':
                print(f"   ⚠️ 警告: {year}年的real值为0或缺失！")
    else:
        print("❌ 验证结果为空")
    
    print("=" * 80)
    print()
    print("💡 如果real_magnitude都是0，请检查：")
    print("   1. 数据导入时是否正确设置了real_magnitude")
    print("   2. 数据文件中的real_magnitude字段是否正确")
    print("   3. 运行修复脚本: python3 scripts/fix_musk_real_magnitude.py")

if __name__ == "__main__":
    main()

