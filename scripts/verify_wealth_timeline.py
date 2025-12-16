#!/usr/bin/env python3
"""
V56.0 Step 3: Wealth Timeline Backtester
验证财富引擎：测试马斯克的财富曲线
"""

import json
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def run_backtest():
    print("=" * 80)
    print("💰 V56.0 财富引擎回测：马斯克专场")
    print("=" * 80)
    print()

    # 1. Initialize Engine
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 尝试加载用户配置（如果有）
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            # 合并配置
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, user_config)
    
    engine = GraphNetworkEngine(config=config)
    
    # 2. Load Data
    try:
        with open('data/golden_timeline.json', 'r', encoding='utf-8') as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("❌ 数据文件未找到，请先运行 scripts/create_wealth_timeline.py")
        return

    musk = cases[0]
    print(f"👤 案例: {musk['name']} ({musk['day_master']}日主)")
    print(f"   八字: {' '.join(musk['bazi'])}")
    print("-" * 80)

    total_error = 0
    hit_count = 0
    event_count = len(musk['timeline'])

    for evt in musk['timeline']:
        year = evt['year']
        ganzhi = evt['ganzhi']
        dayun = evt.get('dayun', '')
        # 兼容两种数据格式：real_magnitude 或 result
        if 'real_magnitude' in evt:
            real_mag = evt['real_magnitude']
        elif 'result' in evt:
            # 将 result 转换为数值
            result_map = {
                "TERRIBLE": -90.0,
                "BAD": -50.0,
                "GOOD": 60.0,
                "GREAT": 100.0
            }
            real_mag = result_map.get(evt['result'], 0.0)
        else:
            print(f"⚠️ 警告：事件 {year} 缺少财富数据，跳过")
            continue
        desc = evt.get('desc', '')
        
        # 3. Call Engine
        if hasattr(engine, 'calculate_wealth_index'):
            result = engine.calculate_wealth_index(
                bazi=musk['bazi'],
                day_master=musk['day_master'],
                gender=musk['gender'],
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            # 处理返回结果（可能是字典或浮点数）
            if isinstance(result, dict):
                ai_score = result.get('wealth_index', 0.0)
                details = result.get('details', [])
            else:
                ai_score = result
                details = []
        else:
            print("⚠️ 警告：引擎尚未实现 calculate_wealth_index，使用基础 analyze 模拟")
            res = engine.analyze(musk['bazi'], musk['day_master'], musk['gender'])
            ai_score = res.get('strength_score', 50.0)  # 仅作占位
            details = []

        # 4. Compare
        diff = abs(real_mag - ai_score)
        total_error += diff
        
        # 判定 Match: 方向一致 且 误差 < 40
        direction_match = (real_mag > 0 and ai_score > 0) or (real_mag < 0 and ai_score < 0)
        is_hit = direction_match and (diff < 40 or (abs(real_mag) > 80 and abs(ai_score) > 80))
        
        if is_hit: 
            hit_count += 1
        
        mark = "✅" if is_hit else "❌"
        
        print(f"{year} ({ganzhi}) | 运: {dayun}")
        print(f"   真实财富: {real_mag:>6.1f} | {desc.split('。')[0]}")
        print(f"   AI 预测 : {ai_score:>6.1f} | 误差: {diff:.1f}")
        if details:
            print(f"   触发机制: {', '.join(details)}")
        print(f"   结果: {mark}")
        print("-" * 40)

    print(f"📊 最终统计: 命中率 {hit_count}/{event_count} ({hit_count/event_count*100:.1f}%)")
    print(f"   平均误差: {total_error/event_count:.1f}分")
    
    if hit_count == event_count:
        print("🚀 完美！财富引擎验证通过！")
    elif hit_count >= event_count - 1:
        print("✨ 优秀。模型基本抓住了财富趋势。")
    else:
        print("🔧 模型仍需调优。请检查冲库逻辑或身弱担财判定。")

if __name__ == "__main__":
    run_backtest()
