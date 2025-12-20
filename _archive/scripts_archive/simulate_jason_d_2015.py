#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jason D 案例 2015年模拟推演脚本
================================

针对 Jason D (财库连冲) 案例，执行 GraphNetworkEngine 的完整模拟推演，
重点展示 2015 乙未年如何通过三刑和冲开财库达到财富爆发值。

案例信息：
- 八字: 辛丑 丁酉 庚辰 丙戌
- 日主: 庚金
- 性别: 男
- 2015年流年: 乙未
- 关键机制: 丑未冲触发财库开启 (Open Vault)
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def print_subsection(title: str):
    """打印子节标题"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")

def main():
    """主函数：执行 Jason D 2015 年模拟推演"""
    
    print_section("🚀 Jason D 案例 2015年模拟推演", "=")
    print("案例: Jason D (财库连冲)")
    print("八字: 辛丑 丁酉 庚辰 丙戌")
    print("日主: 庚金")
    print("性别: 男")
    print("目标年份: 2015年 (乙未)")
    print("真实财富指数: 100.0 (重大资产重组，财富暴增)")
    
    # ========== 步骤 1: 初始化八字档案 ==========
    print_section("📋 步骤 1: 初始化八字档案", "=")
    
    # Jason D 出生信息: 1961年10月10日 20:00
    birth_date = datetime(1961, 10, 10, 20, 0)
    gender = 1  # 男
    
    profile = BaziProfile(birth_date, gender)
    bazi = ['辛丑', '丁酉', '庚辰', '丙戌']
    day_master = '庚'
    
    print(f"✅ 出生日期: {birth_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"✅ 八字四柱: {' '.join(bazi)}")
    print(f"✅ 日主: {day_master}金")
    print(f"✅ 性别: {'男' if gender == 1 else '女'}")
    
    # ========== 步骤 2: 计算大运和流年 ==========
    print_section("📅 步骤 2: 计算大运和流年", "=")
    
    target_year = 2015
    luck_pillar = profile.get_luck_pillar_at(target_year)
    # 2015年是乙未年（已知）
    year_pillar = "乙未"
    
    print(f"✅ 目标年份: {target_year}")
    print(f"✅ 大运: {luck_pillar}")
    print(f"✅ 流年: {year_pillar}")
    
    # ========== 步骤 3: 初始化图网络引擎 ==========
    print_section("⚛️ 步骤 3: 初始化图网络引擎", "=")
    
    engine = GraphNetworkEngine()
    print(f"✅ 引擎版本: {engine.VERSION}")
    print(f"✅ 引擎初始化完成")
    
    # ========== 步骤 4: 执行完整分析 (analyze) ==========
    print_section("🔬 步骤 4: 执行完整分析 (analyze)", "=")
    
    print("正在执行 GraphNetworkEngine.analyze()...")
    print("   - Phase 1: 节点初始化 (Node Initialization)")
    print("   - Phase 2: 邻接矩阵构建 (Adjacency Matrix Construction)")
    print("   - Phase 3: 传播迭代 (Propagation)")
    
    result = engine.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    strength_score = result.get('strength_score', 50.0)
    strength_normalized = strength_score / 100.0
    strength_label = result.get('strength_label', 'Balanced')
    
    print_subsection("身强分析结果")
    print(f"  身强分数: {strength_score:.2f} / 100.0")
    print(f"  归一化值: {strength_normalized:.4f}")
    print(f"  身强标签: {strength_label}")
    
    if strength_normalized > 0.5:
        print(f"  ✅ 判定: 身强 (strength_normalized = {strength_normalized:.4f} > 0.5)")
        print(f"  📌 关键: 身强遇冲开财库 = 财富爆发 (+100.0)")
    else:
        print(f"  ⚠️  判定: 身弱 (strength_normalized = {strength_normalized:.4f} <= 0.5)")
        print(f"  📌 关键: 身弱遇冲开财库 = 库塌损失 (-120.0)")
    
    # ========== 步骤 5: 计算财富指数 ==========
    print_section("💰 步骤 5: 计算财富指数 (calculate_wealth_index)", "=")
    
    print("正在执行 GraphNetworkEngine.calculate_wealth_index()...")
    print("  核心机制检测:")
    print("    1. 基础财气计算 (天干透财、地支食伤生财、地支坐财)")
    print("    2. 墓库隧穿机制 (冲开财库、合开财库、三合局引动库)")
    print("    3. 帮身机制检测 (强根、印星、比劫)")
    print("    4. 承载力与极性反转 (身弱财变债)")
    print("    5. 特殊机制检测 (冲提纲、七杀攻身、截脚结构)")
    
    wealth_result = engine.calculate_wealth_index(
        bazi=bazi,
        day_master=day_master,
        gender='男',
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    wealth_index = wealth_result.get('wealth_index', 0.0)
    details = wealth_result.get('details', [])
    
    print_subsection("财富指数计算结果")
    print(f"  🎯 预测财富指数: {wealth_index:.2f}")
    print(f"  🎯 真实财富指数: 100.0")
    print(f"  📊 误差: {abs(wealth_index - 100.0):.2f}")
    
    if abs(wealth_index - 100.0) < 20.0:
        print(f"  ✅ 预测准确 (误差 < 20.0)")
    else:
        print(f"  ⚠️  预测偏差较大 (误差 >= 20.0)")
    
    print_subsection("计算详情 (Details)")
    for i, detail in enumerate(details, 1):
        print(f"  {i}. {detail}")
    
    # ========== 步骤 6: 关键机制分析 ==========
    print_section("🔍 步骤 6: 关键机制深度分析", "=")
    
    print_subsection("1. 财库检测")
    print("  原局财库:")
    vaults = {'辰', '戌', '丑', '未'}
    vault_elements = {'辰': '水', '戌': '火', '丑': '金', '未': '木'}
    
    # 庚金日主，我克为财（木），所以财库是未（木库）
    print(f"    - 年柱: {bazi[0]} (丑 = 金库)")
    print(f"    - 日柱: {bazi[2]} (辰 = 水库)")
    print(f"    - 时柱: {bazi[3]} (戌 = 火库)")
    print(f"    - 流年: {year_pillar} (未 = 木库 = 财库)")
    
    print(f"\n  ✅ 关键发现: 流年乙未的'未'是庚金日主的财库（木库）")
    
    print_subsection("2. 冲库机制")
    clashes = {'子': '午', '午': '子', '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
               '辰': '戌', '戌': '辰', '丑': '未', '未': '丑'}
    
    print("  冲库关系:")
    print(f"    - 丑 ↔ 未 (对冲)")
    print(f"    - 辰 ↔ 戌 (对冲)")
    
    # 检查原局是否有丑
    has_chou = any('丑' in pillar for pillar in bazi)
    year_branch = year_pillar[1] if len(year_pillar) >= 2 else None
    
    if has_chou and year_branch == '未':
        print(f"\n  ✅ 触发条件: 原局有'丑'，流年'未'来冲")
        print(f"  ✅ 冲库结果: 丑未冲 → 财库开启")
        if strength_normalized > 0.5:
            print(f"  ✅ 身强判定: 身强遇冲 = 财富爆发 (+100.0)")
        else:
            print(f"  ⚠️  身弱判定: 身弱遇冲 = 库塌损失 (-120.0)")
    
    print_subsection("3. 三刑机制")
    print("  丑未戌三刑:")
    has_chou = '丑' in bazi[0]
    has_wei = year_branch == '未'
    has_xu = '戌' in bazi[3]
    
    print(f"    - 原局年柱: {bazi[0]} (丑) {'✅' if has_chou else '❌'}")
    print(f"    - 流年地支: {year_branch} (未) {'✅' if has_wei else '❌'}")
    print(f"    - 原局时柱: {bazi[3]} (戌) {'✅' if has_xu else '❌'}")
    
    if has_chou and has_wei and has_xu:
        print(f"\n  ✅ 三刑齐备: 丑未戌三刑形成")
        print(f"  📌 三刑效应: 增强冲库的破坏力/爆发力")
    
    print_subsection("4. 能量流转路径")
    print("  图神经网络能量传播:")
    print(f"    H^(t+1) = damping × A × H^(t) + (1 - damping) × H^(0)")
    print(f"    ")
    print(f"  关键节点:")
    print(f"    - 节点 0-3: 原局四柱 (辛丑、丁酉、庚辰、丙戌)")
    print(f"    - 节点 8-9: 大运 ({luck_pillar})")
    print(f"    - 节点 10-11: 流年 ({year_pillar})")
    print(f"    ")
    print(f"  能量传导:")
    print(f"    1. 流年'未'节点 (节点11) 激活")
    print(f"    2. 通过冲关系矩阵 A[11][0] 传导到原局'丑'节点 (节点1)")
    print(f"    3. 触发财库开启机制")
    print(f"    4. 根据身强/身弱判定，应用 +100.0 或 -120.0 修正")
    
    # ========== 步骤 7: 最终结果总结 ==========
    print_section("📊 最终结果总结", "=")
    
    print(f"案例: Jason D (财库连冲)")
    print(f"目标年份: {target_year} ({year_pillar})")
    print(f"")
    print(f"【输入参数】")
    print(f"  八字: {' '.join(bazi)}")
    print(f"  日主: {day_master}金")
    print(f"  大运: {luck_pillar}")
    print(f"  流年: {year_pillar}")
    print(f"")
    print(f"【计算结果】")
    print(f"  身强分数: {strength_score:.2f} / 100.0")
    print(f"  身强判定: {strength_label} (归一化: {strength_normalized:.4f})")
    print(f"  预测财富指数: {wealth_index:.2f}")
    print(f"  真实财富指数: 100.0")
    print(f"  误差: {abs(wealth_index - 100.0):.2f}")
    print(f"")
    print(f"【关键机制】")
    for detail in details:
        if '财库' in detail or '冲' in detail or '三刑' in detail:
            print(f"  ⭐ {detail}")
    print(f"")
    
    if abs(wealth_index - 100.0) < 20.0:
        print(f"✅ 模拟推演成功！预测值与真实值高度吻合。")
        print(f"✅ 系统成功识别了'丑未冲开财库'机制，并根据身强判定应用了正确的财富爆发加成。")
    else:
        print(f"⚠️  模拟推演存在偏差，需要进一步调优算法参数。")
    
    print_section("推演完成", "=")
    
    return {
        'wealth_index': wealth_index,
        'strength_score': strength_score,
        'strength_label': strength_label,
        'details': details,
        'luck_pillar': luck_pillar,
        'year_pillar': year_pillar
    }

if __name__ == '__main__':
    try:
        result = main()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

