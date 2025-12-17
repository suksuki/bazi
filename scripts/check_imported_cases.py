#!/usr/bin/env python3
"""
检查已导入的案例
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController

def main():
    """主函数"""
    print("=" * 80)
    print("🔍 检查已导入的案例")
    print("=" * 80)
    print()
    
    controller = WealthVerificationController()
    
    # 获取所有案例
    cases = controller.get_all_cases()
    
    print(f"📊 找到 {len(cases)} 个案例")
    print()
    
    if cases:
        print("案例列表：")
        for i, case in enumerate(cases, 1):
            print(f"\n{i}. {case.name} ({case.id})")
            print(f"   八字: {' '.join(case.bazi)}")
            print(f"   日主: {case.day_master}")
            print(f"   性别: {case.gender}")
            print(f"   事件数: {len(case.timeline) if case.timeline else 0}")
            if case.timeline:
                print(f"   事件年份: {[e.year for e in case.timeline]}")
    else:
        print("⚠️ 没有找到任何案例")
        print()
        print("可能的原因：")
        print("1. 转换脚本尚未运行")
        print("2. 数据目录不存在或路径错误")
        print("3. 文件格式不正确")
        print()
        print("💡 建议：运行转换脚本导入案例")
        print("   python3 scripts/convert_gemini_to_jason.py")
    
    # 检查数据目录
    data_dir = project_root / 'data'
    print()
    print("=" * 80)
    print("📁 数据目录检查")
    print("=" * 80)
    print(f"数据目录: {data_dir}")
    print(f"目录存在: {data_dir.exists()}")
    
    if data_dir.exists():
        timeline_files = list(data_dir.glob('*_timeline.json'))
        print(f"找到 {len(timeline_files)} 个timeline文件：")
        for f in timeline_files:
            print(f"  - {f.name}")
    else:
        print("⚠️ 数据目录不存在，将自动创建")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

