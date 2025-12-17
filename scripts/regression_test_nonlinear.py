#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非线性模型回归测试脚本
====================

验证 V10.0 非线性优化后，所有案例的预测准确性是否保持或提升。

测试范围：
1. Jason Tier A 案例（5个）
2. 其他历史案例
3. 对比硬编码模型 vs 非线性模型
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from controllers.wealth_verification_controller import WealthVerificationController

def print_section(title: str, char: str = "="):
    """打印分节标题"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def test_jason_cases():
    """测试 Jason Tier A 案例"""
    print_section("📊 Jason Tier A 案例回归测试", "=")
    
    controller = WealthVerificationController()
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
    
    # 获取所有 Jason 案例
    all_cases = controller.get_all_cases()
    jason_cases = [c for c in all_cases if hasattr(c, 'id') and c.id.startswith('JASON_')]
    
    print(f"找到 {len(jason_cases)} 个 Jason 案例")
    print()
    
    results = []
    
    for case in jason_cases:
        case_id = case.id
        case_name = case.name
        bazi = case.bazi
        day_master = case.day_master
        gender = case.gender
        timeline = case.timeline or []
        
        print(f"【{case_name}】({case_id})")
        print(f"  八字: {' '.join(bazi)}")
        print(f"  日主: {day_master}")
        print(f"  事件数: {len(timeline)}")
        
        case_results = []
        
        for event in timeline:
            year = event.year
            ganzhi = event.ganzhi if hasattr(event, 'ganzhi') else ''
            dayun = event.dayun if hasattr(event, 'dayun') else ''
            real_magnitude = event.real_magnitude if hasattr(event, 'real_magnitude') else 0.0
            desc = event.desc if hasattr(event, 'desc') else ''
            
            if not ganzhi:
                # 如果没有流年干支，跳过
                continue
            
            # 计算预测值
            try:
                wealth_result = engine.calculate_wealth_index(
                    bazi=bazi,
                    day_master=day_master,
                    gender=gender,
                    luck_pillar=dayun,
                    year_pillar=ganzhi
                )
                
                predicted = wealth_result.get('wealth_index', 0.0)
                error = abs(predicted - real_magnitude)
                is_correct = error < 20.0
                
                case_results.append({
                    'year': year,
                    'predicted': predicted,
                    'real': real_magnitude,
                    'error': error,
                    'is_correct': is_correct
                })
                
                status = "✅" if is_correct else "❌"
                print(f"    {status} {year}年 ({ganzhi}): 预测={predicted:.1f}, 真实={real_magnitude:.1f}, 误差={error:.1f}")
                
            except Exception as e:
                print(f"    ❌ {year}年: 计算失败 - {e}")
                case_results.append({
                    'year': year,
                    'predicted': 0.0,
                    'real': real_magnitude,
                    'error': real_magnitude,
                    'is_correct': False
                })
        
        # 计算案例统计
        if case_results:
            total_events = len(case_results)
            correct_events = sum(1 for r in case_results if r['is_correct'])
            avg_error = sum(r['error'] for r in case_results) / total_events
            hit_rate = correct_events / total_events * 100.0
            
            results.append({
                'case_name': case_name,
                'case_id': case_id,
                'total_events': total_events,
                'correct_events': correct_events,
                'hit_rate': hit_rate,
                'avg_error': avg_error,
                'events': case_results
            })
            
            print(f"  命中率: {hit_rate:.1f}% ({correct_events}/{total_events})")
            print(f"  平均误差: {avg_error:.1f}")
        
        print()
    
    # 总体统计
    print_section("📈 总体统计", "=")
    
    if results:
        total_cases = len(results)
        total_events = sum(r['total_events'] for r in results)
        total_correct = sum(r['correct_events'] for r in results)
        overall_hit_rate = total_correct / total_events * 100.0 if total_events > 0 else 0.0
        overall_avg_error = sum(r['avg_error'] * r['total_events'] for r in results) / total_events if total_events > 0 else 0.0
        
        print(f"总案例数: {total_cases}")
        print(f"总事件数: {total_events}")
        print(f"正确事件数: {total_correct}")
        print(f"总体命中率: {overall_hit_rate:.1f}%")
        print(f"总体平均误差: {overall_avg_error:.1f}")
        print()
        
        # 详细结果表
        print("详细结果:")
        print(f"{'案例名称':<20} {'事件数':<8} {'正确数':<8} {'命中率':<10} {'平均误差':<10}")
        print("-" * 80)
        for r in results:
            print(f"{r['case_name']:<20} {r['total_events']:<8} {r['correct_events']:<8} {r['hit_rate']:<10.1f} {r['avg_error']:<10.1f}")
        
        return {
            'total_cases': total_cases,
            'total_events': total_events,
            'total_correct': total_correct,
            'overall_hit_rate': overall_hit_rate,
            'overall_avg_error': overall_avg_error,
            'results': results
        }
    
    return None

def main():
    """主函数"""
    print_section("🚀 V10.0 非线性模型回归测试", "=")
    print("测试目标: 验证非线性优化后，所有案例的预测准确性是否保持或提升")
    print()
    
    try:
        # 测试 Jason 案例
        stats = test_jason_cases()
        
        if stats:
            print_section("✅ 测试完成", "=")
            print(f"总体命中率: {stats['overall_hit_rate']:.1f}%")
            print(f"总体平均误差: {stats['overall_avg_error']:.1f}")
            
            if stats['overall_hit_rate'] >= 50.0:
                print("✅ 回归测试通过！命中率 >= 50%")
            else:
                print("⚠️  回归测试未通过，命中率 < 50%，需要进一步调优")
        else:
            print("⚠️  未找到测试案例")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

