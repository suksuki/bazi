#!/usr/bin/env python3
"""
V31.0 Wealth Module Demo
演示新的"统一价值捕获协议"财富计算
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.calculator import BaziCalculator
from core.flux import FluxEngine
from core.meaning import MeaningEngine
import datetime

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def demo_wealth_calculation(name, year, month, day, hour):
    """演示财富计算"""
    print_section(f"📊 {name} 的财富分析")
    
    # 1. 计算八字
    calc = BaziCalculator(year, month, day, hour, 0)
    chart = calc.get_chart()
    
    print("八字排盘:")
    for pillar in ['year', 'month', 'day', 'hour']:
        stem = chart[pillar]['stem']
        branch = chart[pillar]['branch']
        print(f"  {pillar.capitalize()}: {stem}{branch}")
    
    # 2. 运行能量引擎
    flux_engine = FluxEngine(chart)
    flux_result = flux_engine.calculate_flux()
    
    # 3. 运行意义引擎
    meaning_engine = MeaningEngine(chart, flux_result)
    wealth_analysis = meaning_engine._calculate_wealth()
    
    # 4. 显示结果
    print_section("💰 财富统一场 V31.0 分析结果")
    
    print(f"净财富得分: {wealth_analysis['score']:.1f} eV")
    print(f"财富评级: {wealth_analysis['rating']}")
    print(f"获利模式: {wealth_analysis['mode']}")
    
    # 组件分析
    print("\n📊 能量组件:")
    comp = wealth_analysis['components']
    print(f"  总捕获能量: {comp['total_captured']:.1f} eV")
    print(f"  固化财富: {comp['solidified']:.1f} eV (可积累)")
    print(f"  耗散财富: {comp['dissipated']:.1f} eV (过路财)")
    print(f"  总损耗: {comp['friction']:.1f} eV")
    print(f"  净财富: {comp['net']:.1f} eV")
    
    # 矿源分析
    print("\n⛏️ 高能矿源 (Energy > 40):")
    sources = wealth_analysis['sources']
    
    if sources['wealth_ore']:
        print(f"  💎 财星: {len(sources['wealth_ore'])} 个")
        for ore in sources['wealth_ore']:
            print(f"     - {ore['id']}: {ore['energy']:.1f} eV")
    
    if sources['power_ore']:
        print(f"  ⚔️ 七杀: {len(sources['power_ore'])} 个")
        for ore in sources['power_ore']:
            print(f"     - {ore['id']}: {ore['energy']:.1f} eV")
    
    if sources['tech_ore']:
        print(f"  🔧 食伤: {len(sources['tech_ore'])} 个")
        for ore in sources['tech_ore']:
            print(f"     - {ore['id']}: {ore['energy']:.1f} eV")
    
    if sources['asset_ore']:
        print(f"  📚 印星: {len(sources['asset_ore'])} 个")
        for ore in sources['asset_ore']:
            print(f"     - {ore['id']}: {ore['energy']:.1f} eV")
    
    # 杠杆分析
    print("\n⚙️ 杠杆计算:")
    leverage_details = wealth_analysis.get('leverage_details', [])
    if leverage_details:
        for detail in leverage_details:
            mode_emoji = "💪" if "Labor" in detail['mode'] else "🔧" if "Technology" in detail['mode'] else "⚡" if "Power" in detail['mode'] else "💰"
            print(f"  {mode_emoji} {detail['mode']}")
            print(f"     {detail['source']} × {detail['leverage']} = {detail['captured']:.1f} eV")
    else:
        print("  无有效杠杆")
    
    # 损耗分析
    print("\n⚠️ 损耗分析:")
    friction_details = wealth_analysis.get('friction_details', [])
    if friction_details:
        for detail in friction_details:
            print(f"  {detail['type']}")
            print(f"     {detail['source']} - 损耗率 {detail['rate']*100:.0f}% = -{detail['loss']:.1f} eV")
    else:
        print("  ✅ 无显著损耗")
    
    # 存储分析
    print("\n🏦 存储容器:")
    storage = wealth_analysis['storage']
    vault_icon = "✅" if storage['has_vault'] else "❌"
    root_icon = "✅" if storage['has_root'] else "❌"
    print(f"  库 (Vault): {vault_icon}")
    print(f"  根 (Root): {root_icon}")
    print(f"  存储容量: {storage['capacity']:.1f}")
    print(f"  固化率: {storage['solidification_rate']*100:.0f}%")
    print(f"  状态: {storage['status']}")
    
    # 智能推断
    print("\n💡 智能推断:")
    if wealth_analysis.get('inferences'):
        for inf in wealth_analysis['inferences']:
            print(f"  {inf}")
    else:
        print("  无特殊推断")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     Antigravity Wealth Module V31.0 Demo                    ║
║     统一价值捕获协议 (Unified Value Capture Protocol)          ║
║                                                              ║
║     "Wealth = Net Mass of High-Energy Particles             ║
║      Successfully CAPTURED and COLLAPSED by the Self"       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 案例 1: 七杀格 + 食神制杀 (风投型)
    demo_wealth_calculation(
        name="案例1: 风投型",
        year=1985,
        month=3,
        day=15,
        hour=10
    )
    
    # 案例 2: 身旺财旺 (资产型)
    demo_wealth_calculation(
        name="案例2: 资产型",
        year=1990,
        month=6,
        day=20,
        hour=14
    )
    
    # 案例 3: 食伤生财 (技术型)
    demo_wealth_calculation(
        name="案例3: 技术型",
        year=1995,
        month=9,
        day=10,
        hour=8
    )
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     Demo Complete! 演示完成！                                 ║
║                                                              ║
║     查看详细文档: docs/WEALTH_V31_PROTOCOL.md                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
