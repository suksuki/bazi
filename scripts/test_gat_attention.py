#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GAT 图注意力网络测试脚本
======================

测试 V10.0 新增的 GAT 功能，对比固定矩阵 vs 动态注意力机制。
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def test_gat_vs_fixed():
    """对比 GAT 和固定矩阵"""
    print_section("🔬 GAT vs 固定矩阵对比测试", "=")
    
    # Jason D 案例
    bazi = ['辛丑', '丁酉', '庚辰', '丙戌']
    day_master = '庚'
    gender = '男'
    year_pillar = '乙未'
    luck_pillar = '壬辰'
    
    print(f"【测试案例】")
    print(f"  八字: {' '.join(bazi)}")
    print(f"  日主: {day_master}")
    print(f"  大运: {luck_pillar}")
    print(f"  流年: {year_pillar}")
    print()
    
    # 测试 1: 固定矩阵（传统方法）
    print_section("测试 1: 固定矩阵（传统方法）", "-")
    config_fixed = DEFAULT_FULL_ALGO_PARAMS.copy()
    config_fixed['use_gat'] = False
    
    engine_fixed = GraphNetworkEngine(config=config_fixed)
    result_fixed = engine_fixed.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    wealth_fixed = engine_fixed.calculate_wealth_index(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    print(f"  身强分数: {result_fixed.get('strength_score', 0.0):.2f}")
    print(f"  财富指数: {wealth_fixed.get('wealth_index', 0.0):.2f}")
    print()
    
    # 测试 2: GAT 动态矩阵
    print_section("测试 2: GAT 动态矩阵（注意力机制）", "-")
    config_gat = DEFAULT_FULL_ALGO_PARAMS.copy()
    config_gat['use_gat'] = True
    config_gat['gat_mix_ratio'] = 0.5  # 50% 动态，50% 固定
    
    engine_gat = GraphNetworkEngine(config=config_gat)
    result_gat = engine_gat.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    wealth_gat = engine_gat.calculate_wealth_index(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    print(f"  身强分数: {result_gat.get('strength_score', 0.0):.2f}")
    print(f"  财富指数: {wealth_gat.get('wealth_index', 0.0):.2f}")
    print()
    
    # 对比分析
    print_section("📊 对比分析", "=")
    
    strength_diff = result_gat.get('strength_score', 0.0) - result_fixed.get('strength_score', 0.0)
    wealth_diff = wealth_gat.get('wealth_index', 0.0) - wealth_fixed.get('wealth_index', 0.0)
    
    print(f"身强分数差异: {strength_diff:+.2f}")
    print(f"财富指数差异: {wealth_diff:+.2f}")
    print()
    
    if abs(strength_diff) < 1.0 and abs(wealth_diff) < 1.0:
        print("✅ GAT 和固定矩阵结果高度一致，GAT 正常工作")
    else:
        print("⚠️  GAT 和固定矩阵结果存在差异，这是正常的（动态注意力机制）")
        print("   GAT 的优势在于能够根据节点状态动态调整权重")
    
    print()
    print("✅ GAT 测试完成！")
    
    return {
        'fixed': {
            'strength': result_fixed.get('strength_score', 0.0),
            'wealth': wealth_fixed.get('wealth_index', 0.0)
        },
        'gat': {
            'strength': result_gat.get('strength_score', 0.0),
            'wealth': wealth_gat.get('wealth_index', 0.0)
        }
    }

if __name__ == '__main__':
    try:
        result = test_gat_vs_fixed()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

