#!/usr/bin/env python3
"""
调试所有财富验证案例
分析预测结果，找出需要调整的参数
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def analyze_all_cases():
    """分析所有案例的预测结果"""
    print("=" * 80)
    print("🔍 财富验证案例调试分析")
    print("=" * 80)
    print()
    
    # 初始化控制器
    controller = WealthVerificationController()
    
    # 获取所有案例
    all_cases = controller.get_all_cases()
    print(f"📋 找到 {len(all_cases)} 个案例")
    print()
    
    # 统计信息
    total_events = 0
    correct_events = 0
    total_error = 0.0
    
    # 按案例分析
    case_results = []
    
    for case in all_cases:
        print("=" * 80)
        print(f"📊 案例: {case.name} ({case.id})")
        print(f"   八字: {' '.join(case.bazi)}")
        print(f"   日主: {case.day_master} | 性别: {case.gender}")
        print(f"   事件数: {len(case.timeline) if case.timeline else 0}")
        print("-" * 80)
        
        # 验证案例
        results = controller.verify_case(case)
        
        if not results:
            print("   ⚠️ 无验证结果")
            continue
        
        # 统计
        case_correct = 0
        case_total = len(results)
        case_errors = []
        
        for r in results:
            year = r['year']
            real = r['real']
            predicted = r.get('predicted')
            error = r.get('error')
            is_correct = r.get('is_correct', False)
            
            if predicted is not None and error is not None:
                total_events += 1
                total_error += error
                case_errors.append(error)
                
                if is_correct:
                    correct_events += 1
                    case_correct += 1
                
                status = "✅" if is_correct else "❌"
                print(f"   {status} {year}年 ({r['ganzhi']}): 真实={real:>6.1f}, 预测={predicted:>6.1f}, 误差={error:>5.1f}")
                
                # 显示关键机制
                details = r.get('details', [])
                if details:
                    key_mechs = []
                    if r.get('strong_root'):
                        key_mechs.append("强根")
                    if r.get('vault_opened'):
                        key_mechs.append("开库")
                    if r.get('vault_collapsed'):
                        key_mechs.append("库塌")
                    if key_mechs:
                        print(f"      机制: {', '.join(key_mechs)}")
                    # 显示前3个details
                    if len(details) > 0:
                        print(f"      详情: {', '.join(details[:3])}")
            else:
                print(f"   ❌ {year}年: 计算失败 - {r.get('error_msg', 'Unknown')}")
        
        # 案例统计
        case_avg_error = sum(case_errors) / len(case_errors) if case_errors else 0.0
        case_hit_rate = (case_correct / case_total * 100) if case_total > 0 else 0.0
        
        print(f"\n   📈 案例统计: 命中率={case_hit_rate:.1f}% ({case_correct}/{case_total}), 平均误差={case_avg_error:.1f}")
        
        case_results.append({
            'case_id': case.id,
            'case_name': case.name,
            'total': case_total,
            'correct': case_correct,
            'hit_rate': case_hit_rate,
            'avg_error': case_avg_error,
            'errors': case_errors
        })
        
        print()
    
    # 总体统计
    print("=" * 80)
    print("📊 总体统计")
    print("=" * 80)
    print()
    
    overall_hit_rate = (correct_events / total_events * 100) if total_events > 0 else 0.0
    overall_avg_error = (total_error / total_events) if total_events > 0 else 0.0
    
    print(f"总事件数: {total_events}")
    print(f"正确事件: {correct_events}")
    print(f"总体命中率: {overall_hit_rate:.1f}%")
    print(f"平均误差: {overall_avg_error:.1f}分")
    print()
    
    # 问题分析
    print("=" * 80)
    print("🔍 问题分析")
    print("=" * 80)
    print()
    
    # 找出误差最大的案例
    case_results.sort(key=lambda x: x['avg_error'], reverse=True)
    
    print("❌ 误差最大的案例 (需要优先修复):")
    for i, cr in enumerate(case_results[:3], 1):
        print(f"   {i}. {cr['case_name']} ({cr['case_id']})")
        print(f"      命中率: {cr['hit_rate']:.1f}%, 平均误差: {cr['avg_error']:.1f}分")
        if cr['errors']:
            max_error = max(cr['errors'])
            print(f"      最大误差: {max_error:.1f}分")
        print()
    
    # 找出命中率最低的案例
    case_results.sort(key=lambda x: x['hit_rate'])
    
    print("⚠️ 命中率最低的案例 (需要重点关注):")
    for i, cr in enumerate(case_results[:3], 1):
        print(f"   {i}. {cr['case_name']} ({cr['case_id']})")
        print(f"      命中率: {cr['hit_rate']:.1f}%, 平均误差: {cr['avg_error']:.1f}分")
        print()
    
    # 建议
    print("=" * 80)
    print("💡 优化建议")
    print("=" * 80)
    print()
    
    if overall_hit_rate < 50:
        print("⚠️ 总体命中率低于50%，建议:")
        print("   1. 检查财富指数计算逻辑（calculate_wealth_index）")
        print("   2. 检查强根、开库、库塌等关键机制的触发条件")
        print("   3. 检查身强/身弱的判定是否准确")
        print()
    
    if overall_avg_error > 30:
        print("⚠️ 平均误差超过30分，建议:")
        print("   1. 调整财富能量的基础值")
        print("   2. 调整各种加成的权重（强根加成、开库加成等）")
        print("   3. 检查惩罚机制是否过重（如冲提纲惩罚）")
        print()
    
    # 详细分析每个失败的事件
    print("=" * 80)
    print("📋 详细失败事件分析")
    print("=" * 80)
    print()
    
    for case in all_cases:
        results = controller.verify_case(case)
        failed_events = [r for r in results if not r.get('is_correct', False) and r.get('predicted') is not None]
        
        if failed_events:
            print(f"📌 {case.name} ({case.id}):")
            for fe in failed_events:
                year = fe['year']
                real = fe['real']
                predicted = fe['predicted']
                error = fe['error']
                details = fe.get('details', [])
                
                print(f"   ❌ {year}年: 真实={real:.1f}, 预测={predicted:.1f}, 误差={error:.1f}")
                print(f"      描述: {fe.get('desc', 'N/A')}")
                
                # 分析方向
                direction_match = (real > 0 and predicted > 0) or (real < 0 and predicted < 0)
                if not direction_match:
                    print(f"      ⚠️ 方向错误: 真实{'正' if real > 0 else '负'}, 预测{'正' if predicted > 0 else '负'}")
                
                # 分析误差类型
                if abs(error) > 50:
                    print(f"      ⚠️ 误差过大: {error:.1f}分")
                    if abs(real) > 80 and abs(predicted) < 30:
                        print(f"      💡 建议: 检查是否遗漏了关键机制（如开库、强根等）")
                    elif abs(real) < 30 and abs(predicted) > 80:
                        print(f"      💡 建议: 检查是否过度触发了某些机制")
                
                if details:
                    print(f"      触发机制: {', '.join(details[:5])}")
                print()
    
    print("=" * 80)
    print("✅ 分析完成")
    print("=" * 80)

if __name__ == "__main__":
    analyze_all_cases()

