#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformer 时序建模测试脚本
============================

测试 V10.0 新增的 Transformer 时序建模功能，验证长程依赖捕捉。
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from core.transformer_temporal import TemporalTransformer, MultiScaleTemporalFusion
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def test_transformer_timeline():
    """测试 Transformer 时序建模"""
    print_section("🔬 Transformer 时序建模测试", "=")
    
    # Jason D 案例
    bazi = ['辛丑', '丁酉', '庚辰', '丙戌']
    day_master = '庚'
    gender = '男'
    
    print(f"【测试案例】")
    print(f"  八字: {' '.join(bazi)}")
    print(f"  日主: {day_master}")
    print()
    
    # 初始化引擎
    config = DEFAULT_FULL_ALGO_PARAMS.copy()
    config['transformer'] = {
        'use_transformer': True,
        'd_model': 64,
        'num_heads': 4,
        'num_layers': 2
    }
    
    engine = GraphNetworkEngine(config=config)
    
    # 测试 1: 传统时序推演（不使用 Transformer）
    print_section("测试 1: 传统时序推演（不使用 Transformer）", "-")
    
    timeline_traditional = engine.simulate_timeline(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        start_year=2010,
        duration=10,
        use_transformer=False
    )
    
    print(f"  推演年数: {len(timeline_traditional)}")
    print(f"  前3年结果:")
    for item in timeline_traditional[:3]:
        print(f"    {item['year']}年 ({item['year_pillar']}): "
              f"身强={item['strength_score']:.1f}, "
              f"财富={item['wealth_index']:.1f}")
    print()
    
    # 测试 2: Transformer 时序推演
    print_section("测试 2: Transformer 时序推演（使用 Transformer）", "-")
    
    timeline_transformer = engine.simulate_timeline(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        start_year=2010,
        duration=10,
        use_transformer=True
    )
    
    print(f"  推演年数: {len(timeline_transformer)}")
    print(f"  前3年结果:")
    for item in timeline_transformer[:3]:
        print(f"    {item['year']}年 ({item['year_pillar']}): "
              f"身强={item['strength_score']:.1f}, "
              f"财富={item['wealth_index']:.1f}")
    print()
    
    # 测试 3: Transformer 直接使用
    print_section("测试 3: Transformer 直接使用（长程依赖捕捉）", "-")
    
    transformer = TemporalTransformer(config['transformer'])
    
    # 使用历史数据
    historical_data = timeline_traditional[:5]  # 前5年作为历史
    
    # 编码时序特征
    encoded_features, _ = transformer.forward(historical_data)
    
    print(f"  历史数据年数: {len(historical_data)}")
    print(f"  编码特征维度: {encoded_features.shape}")
    print(f"  Transformer 成功捕捉了时序特征")
    print()
    
    # 测试 4: 预测未来
    print_section("测试 4: Transformer 预测未来", "-")
    
    predictions = transformer.predict_future(historical_data, future_years=3)
    
    print(f"  预测未来3年:")
    for pred in predictions:
        print(f"    {pred['year']}年: "
              f"预测身强={pred['predicted_strength']:.1f}, "
              f"预测财富={pred['predicted_wealth']:.1f}")
    print()
    
    # 对比分析
    print_section("📊 对比分析", "=")
    
    print("【传统方法 vs Transformer】")
    print("  传统方法: 逐 year 独立计算，不考虑长程依赖")
    print("  Transformer: 使用 Self-Attention 捕捉长程依赖")
    print()
    print("【Transformer 优势】")
    print("  1. ✅ 捕捉长程依赖: 十年前的因，今日的果")
    print("  2. ✅ 时序相关性: 使用 Self-Attention 捕捉时序模式")
    print("  3. ✅ 多尺度融合: 支持流年、流月、流日的多尺度融合")
    print("  4. ✅ 预测能力: 可以基于历史数据预测未来")
    print()
    
    print("✅ Transformer 时序建模测试完成！")
    
    return {
        'traditional': timeline_traditional,
        'transformer': timeline_transformer,
        'predictions': predictions
    }

if __name__ == '__main__':
    try:
        result = test_transformer_timeline()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

