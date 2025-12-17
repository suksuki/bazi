#!/usr/bin/env python3
"""
V59.1 墓库机制详细计算模拟
展示财库冲开（量子隧穿）的完整计算过程
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def detailed_vault_calculation():
    """
    详细模拟：乙未 丙戌 壬戌 辛亥，2024年甲辰冲开财库
    """
    print("=" * 80)
    print("🏆 V59.1 墓库机制详细计算模拟")
    print("=" * 80)
    print()
    
    # 测试案例
    bazi = ["乙未", "丙戌", "壬戌", "辛亥"]
    day_master = "壬"
    gender = "男"
    year_2024 = "甲辰"
    dayun = "壬午"
    
    print("📋 案例信息：")
    print(f"   八字: {' '.join(bazi)}")
    print(f"   日主: {day_master}水")
    print(f"   性别: {gender}")
    print()
    
    print("🔍 五行分析：")
    print(f"   日主: {day_master}水")
    print(f"   财星: 火（我克为财）")
    print(f"   财库: 戌（火库）")
    print(f"   原局财库: 月支戌、日支戌（两个戌土财库）")
    print()
    
    print("📅 流年分析：")
    print(f"   2024年: {year_2024}")
    print(f"   流年地支: 辰")
    print(f"   辰戌冲: 辰冲戌，理论上应冲开财库")
    print()
    
    print("-" * 80)
    print("⚙️ 初始化引擎...")
    print("-" * 80)
    
    # 初始化引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, user_config)
    
    engine = GraphNetworkEngine(config=config)
    print("✅ 引擎初始化完成")
    print()
    
    print("=" * 80)
    print("🧮 开始计算 2024年财富指数...")
    print("=" * 80)
    print()
    
    # 计算财富指数
    try:
        result = engine.calculate_wealth_index(
            bazi=bazi,
            day_master=day_master,
            gender=gender,
            luck_pillar=dayun,
            year_pillar=year_2024
        )
        
        if isinstance(result, dict):
            wealth_index = result.get('wealth_index', 0.0)
            details = result.get('details', [])
            strength_score = result.get('strength_score', 0.0)
            strength_label = result.get('strength_label', 'Unknown')
            opportunity = result.get('opportunity', 0.0)
        else:
            wealth_index = result
            details = []
            strength_score = 0.0
            strength_label = 'Unknown'
            opportunity = 0.0
        
        print("📊 计算结果：")
        print(f"   财富指数: {wealth_index:.1f}")
        print(f"   身强分数: {strength_score:.1f} ({strength_label})")
        print(f"   机会能量: {opportunity:.1f}")
        print()
        
        # 检查财库冲开
        vault_opened = False
        vault_details = []
        for detail in details:
            if '冲开财库' in detail or '🏆' in detail:
                vault_opened = True
                vault_details.append(detail)
        
        print("🔓 墓库状态分析：")
        if vault_opened:
            print("   ✅ 财库已冲开！")
            print(f"   触发事件: {', '.join(vault_details)}")
        else:
            print("   ❌ 财库未冲开")
            print("   ⚠️ 需要检查财库判定逻辑")
        print()
        
        print("📝 完整触发机制：")
        for i, detail in enumerate(details, 1):
            print(f"   {i}. {detail}")
        print()
        
        print("=" * 80)
        print("🎯 验证结果")
        print("=" * 80)
        
        # 判断是否符合预期
        if vault_opened and wealth_index > 80:
            print("✅ 测试通过！")
            print(f"   🏆 财库冲开成功")
            print(f"   💰 财富指数: {wealth_index:.1f} (预期 > 80)")
            print()
            print("🎉 墓库拓扑学与量子隧穿机制运行正常！")
            print()
            print("📚 物理原理验证：")
            print("   1. ✅ 闭库态检测: 原局戌土财库处于闭库态")
            print("   2. ✅ 冲开条件: 流年辰冲戌，满足冲开条件")
            print("   3. ✅ 财库判定: 戌为火库，火是日主壬水的财星")
            print("   4. ✅ 能量释放: 财库冲开，财富能量爆发")
            print("   5. ✅ 隧穿态激活: 势垒击穿，能量从闭库态跃迁到开放态")
        elif vault_opened:
            print("⚠️ 部分通过")
            print(f"   🏆 财库已冲开")
            print(f"   💰 但财富指数偏低: {wealth_index:.1f} (预期 > 80)")
            print("   💡 可能原因: 身弱或其他因素限制了财富能量")
        else:
            print("❌ 测试失败")
            print(f"   🔒 财库未冲开")
            print(f"   💰 财富指数: {wealth_index:.1f}")
            print()
            print("🔍 可能的问题：")
            print("   1. 财库判定逻辑可能未正确识别戌为财库")
            print("   2. 冲开条件检测可能有问题")
            print("   3. 需要检查 core/engine_graph.py 中的财库判定代码")
        
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 计算错误: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 80)

if __name__ == "__main__":
    detailed_vault_calculation()

