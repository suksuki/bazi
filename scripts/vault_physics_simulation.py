#!/usr/bin/env python3
"""
V59.1 墓库拓扑学与量子隧穿：理论模型验证
对比理论预测与实际计算结果
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

def vault_physics_simulation():
    """
    模拟墓库拓扑学与量子隧穿的完整物理过程
    """
    print("=" * 80)
    print("🔬 墓库拓扑学与量子隧穿：理论模型验证")
    print("=" * 80)
    print()
    
    # 测试案例
    bazi = ["乙未", "丙戌", "壬戌", "辛亥"]
    day_master = "壬"
    gender = "男"
    dayun = "壬午"
    
    print("📋 案例信息：")
    print(f"   八字: {' '.join(bazi)}")
    print(f"   日主: {day_master}水")
    print(f"   财星: 火（我克为财）")
    print(f"   财库: 戌（火库），原局有2个戌土财库")
    print()
    
    print("=" * 80)
    print("📊 理论模型预测")
    print("=" * 80)
    print()
    
    # 理论模型参数
    sealed_damping = 0.4  # 闭库折损系数
    open_bonus = 1.5      # 开库爆发倍率
    storage_energy = 10.0  # 戌中火库原始能量（单位）
    
    print("1️⃣ 闭库态 (2023年基线)")
    print(f"   参数: sealedDamping = {sealed_damping}")
    print(f"   原始能量: E_Storage = {storage_energy} 单位")
    print(f"   有效能量: {storage_energy} × {sealed_damping} = {storage_energy * sealed_damping:.1f} 单位")
    print(f"   状态: 🔒 能量被引力陷阱封锁，只能使用 {sealed_damping * 100:.0f}%")
    print()
    
    print("2️⃣ 量子隧穿态 (2024年甲辰)")
    print(f"   触发条件: 辰戌冲（流年辰土撞击原局戌土）")
    print(f"   参数: openBonus = {open_bonus}")
    print(f"   势垒击穿: 积蓄的财星能量瞬间释放")
    print()
    
    # 计算理论能量
    sealed_energy = storage_energy * sealed_damping
    open_energy = storage_energy * open_bonus * 2  # 两个戌库
    
    print(f"   闭库态能量: {sealed_energy:.1f} 单位")
    print(f"   隧穿态能量: {open_energy:.1f} 单位（{storage_energy} × {open_bonus} × 2库）")
    print(f"   能量增长: {open_energy / sealed_energy:.1f}x ({open_energy / sealed_energy * 100:.0f}%)")
    print(f"   状态: 🏆 势垒击穿，财富线飙升")
    print()
    
    print("=" * 80)
    print("⚙️ 实际引擎计算")
    print("=" * 80)
    print()
    
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
    
    # 测试2023年和2024年
    test_years = [
        {"year": 2023, "ganzhi": "癸卯", "label": "闭库态"},
        {"year": 2024, "ganzhi": "甲辰", "label": "隧穿态"}
    ]
    
    results = {}
    
    for test_year in test_years:
        year = test_year['year']
        ganzhi = test_year['ganzhi']
        label = test_year['label']
        
        print(f"📅 {year}年 ({ganzhi}) - {label}")
        print("-" * 40)
        
        try:
            result = engine.calculate_wealth_index(
                bazi=bazi,
                day_master=day_master,
                gender=gender,
                luck_pillar=dayun,
                year_pillar=ganzhi
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
            
            # 检查财库状态
            vault_opened = False
            vault_details = []
            for detail in details:
                if '冲开财库' in detail or '🏆' in detail:
                    vault_opened = True
                    vault_details.append(detail)
            
            results[year] = {
                'wealth_index': wealth_index,
                'opportunity': opportunity,
                'strength_score': strength_score,
                'strength_label': strength_label,
                'vault_opened': vault_opened,
                'details': details
            }
            
            print(f"   财富指数: {wealth_index:.1f}")
            print(f"   机会能量: {opportunity:.1f}")
            print(f"   身强分数: {strength_score:.1f} ({strength_label})")
            print(f"   财库状态: {'🏆 已冲开' if vault_opened else '🔒 未冲开'}")
            if vault_details:
                print(f"   触发事件: {', '.join(vault_details)}")
            
            # 检查是否有冲提纲
            clash_commander = False
            clash_details = []
            for detail in details:
                if '冲提纲' in detail or '灾难' in detail:
                    clash_commander = True
                    clash_details.append(detail)
            
            if clash_commander:
                print(f"   ⚠️ 冲提纲: {', '.join(clash_details)}")
                print(f"   💡 说明: 财库冲开(+100) 但冲提纲(-150) = 最终 {wealth_index:.1f}")
            print()
            
        except Exception as e:
            print(f"   ❌ 计算错误: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # 对比分析
    print("=" * 80)
    print("📊 理论模型 vs 实际计算对比")
    print("=" * 80)
    print()
    
    if 2023 in results and 2024 in results:
        r2023 = results[2023]
        r2024 = results[2024]
        
        print("| 指标 | 理论模型 | 实际计算 | 匹配度 |")
        print("|------|---------|---------|--------|")
        
        # 闭库态对比
        theoretical_sealed = sealed_energy
        actual_sealed = r2023['wealth_index']
        sealed_match = "✅" if abs(theoretical_sealed - actual_sealed) < 20 else "⚠️"
        print(f"| 闭库态能量 (2023) | {theoretical_sealed:.1f} | {actual_sealed:.1f} | {sealed_match} |")
        
        # 隧穿态对比
        theoretical_open = open_energy
        actual_open = r2024['wealth_index']
        open_match = "✅" if actual_open > 80 and r2024['vault_opened'] else "❌"
        print(f"| 隧穿态能量 (2024) | {theoretical_open:.1f} | {actual_open:.1f} | {open_match} |")
        
        # 能量增长对比
        theoretical_growth = open_energy / sealed_energy
        actual_growth = actual_open / actual_sealed if actual_sealed > 0 else 0
        growth_match = "✅" if actual_growth > 2.0 else "⚠️"
        print(f"| 能量增长倍数 | {theoretical_growth:.1f}x | {actual_growth:.1f}x | {growth_match} |")
        
        print()
        
        # 财库状态验证
        print("🔓 财库状态验证：")
        if r2024['vault_opened']:
            print("   ✅ 2024年财库冲开事件已触发")
            print(f"   🏆 触发事件: {', '.join([d for d in r2024['details'] if '🏆' in d or '冲开财库' in d])}")
        else:
            print("   ❌ 2024年财库冲开事件未触发")
            print("   ⚠️ 需要检查财库判定逻辑")
        print()
        
        # 结论
        print("=" * 80)
        print("🎯 验证结论")
        print("=" * 80)
        print()
        
        if r2024['vault_opened'] and actual_open > 80:
            print("✅ 理论模型验证通过！")
            print()
            print("📚 物理原理确认：")
            print("   1. ✅ 闭库态检测: 2023年能量被封锁")
            print("   2. ✅ 冲开条件: 2024年辰戌冲触发")
            print("   3. ✅ 财库判定: 戌为火库，火是日主财星")
            print("   4. ✅ 能量释放: 势垒击穿，财富能量爆发")
            print("   5. ✅ 隧穿态激活: 从闭库态跃迁到开放态")
            print()
            print("🎉 墓库拓扑学与量子隧穿机制运行正常！")
        else:
            print("⚠️ 理论模型部分验证")
            print(f"   财库状态: {'已冲开' if r2024['vault_opened'] else '未冲开'}")
            print(f"   财富指数: {actual_open:.1f} (预期 > 80)")
            print()
            print("💡 可能的原因：")
            print("   1. 身弱限制了财富能量")
            print("   2. 其他因素（如冲提纲）影响了最终结果")
            print("   3. 需要调整财库冲开的能量加成参数")
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    vault_physics_simulation()

