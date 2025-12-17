#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贝叶斯推理功能测试脚本
====================

测试 V10.0 新增的贝叶斯推理功能，验证置信区间的计算。
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from core.bayesian_inference import BayesianInference

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def test_bayesian_inference():
    """测试贝叶斯推理功能"""
    print_section("🔬 贝叶斯推理功能测试", "=")
    
    # Jason D 案例
    bazi = ['辛丑', '丁酉', '庚辰', '丙戌']
    day_master = '庚'
    gender = '男'
    year_pillar = '乙未'
    luck_pillar = '壬辰'
    
    engine = GraphNetworkEngine()
    
    print(f"【测试案例】")
    print(f"  八字: {' '.join(bazi)}")
    print(f"  日主: {day_master}")
    print(f"  大运: {luck_pillar}")
    print(f"  流年: {year_pillar}")
    print()
    
    # 计算财富指数（包含置信区间）
    result = engine.calculate_wealth_index(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    wealth_index = result.get('wealth_index', 0.0)
    confidence_interval = result.get('confidence_interval', {})
    uncertainty_factors = result.get('uncertainty_factors', {})
    
    print(f"【计算结果】")
    print(f"  点估计 (Point Estimate): {wealth_index:.2f}")
    print()
    
    if confidence_interval:
        print(f"【置信区间 (95% Confidence Interval)】")
        print(f"  下界 (Lower Bound): {confidence_interval.get('lower_bound', 0.0):.2f}")
        print(f"  上界 (Upper Bound): {confidence_interval.get('upper_bound', 0.0):.2f}")
        print(f"  不确定性 (Uncertainty): {confidence_interval.get('uncertainty', 0.0):.2f}")
        print(f"  置信水平 (Confidence Level): {confidence_interval.get('confidence_level', 0.95) * 100:.0f}%")
        print()
        
        # 格式化输出
        formatted = BayesianInference.format_confidence_interval(confidence_interval)
        print(f"【格式化输出】")
        print(f"  {formatted}")
        print()
    
    if uncertainty_factors:
        print(f"【不确定性因子】")
        for factor_name, factor_value in uncertainty_factors.items():
            print(f"  {factor_name}: {factor_value:.2f}")
        print()
    
    print("✅ 贝叶斯推理功能测试完成！")
    
    return result

if __name__ == '__main__':
    try:
        result = test_bayesian_inference()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

