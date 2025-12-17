#!/usr/bin/env python3
"""
验证 Jason 案例的财富预测准确性
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

def verify_jason_timeline():
    """
    验证 Jason 案例的财富预测
    """
    print("=" * 80)
    print("💰 Jason 案例财富引擎验证")
    print("=" * 80)
    print()
    
    # 加载数据
    data_path = project_root / 'data' / 'jason_timeline.json'
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("❌ 数据文件未找到，正在自动创建...")
        from scripts.create_jason_timeline import create_jason_timeline
        create_jason_timeline()
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        print("✅ 数据文件已创建并加载")
        print()
    
    jason = cases[0]
    
    print(f"👤 案例: {jason['name']}")
    print(f"   八字: {' '.join(jason['bazi'])}")
    print(f"   日主: {jason['day_master']}水")
    print(f"   财库: {', '.join(jason.get('wealth_vaults', []))}")
    print("-" * 80)
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
    
    # 验证每个事件
    results = []
    for event in jason['timeline']:
        year = event['year']
        ganzhi = event['ganzhi']
        dayun = event.get('dayun', '甲子')  # 默认大运，实际需要计算
        real_magnitude = event.get('real_magnitude', 0.0)
        desc = event.get('desc', '')
        
        print(f"{year} ({ganzhi}) | 运: {dayun}")
        print(f"   真实财富: {real_magnitude:>6.1f} | {desc}")
        
        try:
            result = engine.calculate_wealth_index(
                bazi=jason['bazi'],
                day_master=jason['day_master'],
                gender=jason['gender'],
                luck_pillar=dayun,
                year_pillar=ganzhi
            )
            
            if isinstance(result, dict):
                wealth_index = result.get('wealth_index', 0.0)
                details = result.get('details', [])
                strength_score = result.get('strength_score', 0.0)
                strength_label = result.get('strength_label', 'Unknown')
            else:
                wealth_index = result
                details = []
                strength_score = 0.0
                strength_label = 'Unknown'
            
            error = abs(wealth_index - real_magnitude)
            is_correct = error <= 20.0  # 允许20分误差
            
            results.append({
                'year': year,
                'real': real_magnitude,
                'predicted': wealth_index,
                'error': error,
                'is_correct': is_correct
            })
            
            print(f"   AI 预测 : {wealth_index:>6.1f} | 误差: {error:.1f}")
            print(f"   身强分数: {strength_score:.1f} ({strength_label})")
            
            # 检查关键事件
            vault_opened = any('冲开财库' in d or '🏆' in d for d in details)
            vault_collapsed = any('冲提纲' in d or '灾难' in d or '💀' in d for d in details)
            
            if vault_opened:
                print(f"   财库状态: 🏆 已冲开")
            elif vault_collapsed:
                print(f"   财库状态: 💀 财库坍塌")
            else:
                print(f"   财库状态: 🔒 未变化")
            
            if details:
                print(f"   触发机制: {', '.join(details[:3])}")
            
            print(f"   结果: {'✅' if is_correct else '❌'}")
            print("-" * 40)
            print()
            
        except Exception as e:
            print(f"⚠️ {year}年财富计算失败: {e}")
            import traceback
            traceback.print_exc()
            print("-" * 40)
            print()
    
    # 统计结果
    if results:
        correct_count = sum(1 for r in results if r['is_correct'])
        total_count = len(results)
        avg_error = sum(r['error'] for r in results) / total_count
        
        print("=" * 80)
        print("📊 最终统计")
        print("=" * 80)
        print(f"   命中率: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)")
        print(f"   平均误差: {avg_error:.1f}分")
        
        if correct_count == total_count:
            print("🚀 完美！财富引擎验证通过！")
        else:
            print("⚠️ 部分事件预测偏差较大，需要进一步调优")
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    verify_jason_timeline()

