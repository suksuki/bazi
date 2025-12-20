#!/usr/bin/env python3
"""
深入分析单个财富验证案例
提供详细的预测分析和优化建议
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

def analyze_single_case(case_id: str):
    """深入分析单个案例"""
    print("=" * 80)
    print(f"🔍 深入分析案例: {case_id}")
    print("=" * 80)
    print()
    
    # 初始化控制器
    controller = WealthVerificationController()
    
    # 获取案例
    case = controller.get_case_by_id(case_id)
    if not case:
        print(f"❌ 未找到案例: {case_id}")
        return
    
    print(f"📋 案例信息:")
    print(f"   名称: {case.name}")
    print(f"   八字: {' '.join(case.bazi)}")
    print(f"   日主: {case.day_master}")
    print(f"   性别: {case.gender}")
    print(f"   描述: {case.description}")
    print()
    
    # 初始化引擎（用于详细分析）
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
    
    # 验证案例
    results = controller.verify_case(case)
    
    if not results:
        print("❌ 无验证结果")
        return
    
    print("=" * 80)
    print("📊 事件详细分析")
    print("=" * 80)
    print()
    
    for r in results:
        year = r['year']
        ganzhi = r['ganzhi']
        dayun = r.get('dayun', 'N/A')
        real = r['real']
        predicted = r.get('predicted')
        error = r.get('error')
        is_correct = r.get('is_correct', False)
        details = r.get('details', [])
        strength_score = r.get('strength_score', 0.0)
        strength_label = r.get('strength_label', 'Unknown')
        opportunity = r.get('opportunity', 0.0)
        
        print("-" * 80)
        print(f"📅 {year}年 ({ganzhi}) | 大运: {dayun}")
        print(f"   真实值: {real:>6.1f} | 预测值: {predicted if predicted is not None else '计算失败':>6.1f}")
        print(f"   误差: {error if error is not None else 'N/A':>5.1f} | 状态: {'✅ 正确' if is_correct else '❌ 错误'}")
        print(f"   描述: {r.get('desc', 'N/A')}")
        print()
        
        if predicted is not None:
            # 方向分析
            direction_match = (real > 0 and predicted > 0) or (real < 0 and predicted < 0)
            print(f"   📈 方向分析:")
            print(f"      真实方向: {'正' if real > 0 else '负'}")
            print(f"      预测方向: {'正' if predicted > 0 else '负'}")
            print(f"      方向匹配: {'✅ 是' if direction_match else '❌ 否'}")
            print()
            
            # 强度分析
            print(f"   💪 强度分析:")
            print(f"      身强分数: {strength_score:.1f} ({strength_label})")
            print(f"      机会指数: {opportunity:.1f}")
            print()
            
            # 机制分析
            print(f"   ⚙️ 触发机制:")
            if details:
                for i, detail in enumerate(details, 1):
                    print(f"      {i}. {detail}")
            else:
                print(f"      无触发机制")
            print()
            
            # 关键机制检查
            print(f"   🔑 关键机制:")
            print(f"      强根: {'✅' if r.get('strong_root') else '❌'}")
            print(f"      开库: {'✅' if r.get('vault_opened') else '❌'}")
            print(f"      库塌: {'✅' if r.get('vault_collapsed') else '❌'}")
            print()
            
            # 问题诊断
            print(f"   🔍 问题诊断:")
            if not is_correct:
                if abs(error) > 50:
                    print(f"      ⚠️ 误差过大 ({error:.1f}分)")
                    if abs(real) > 80 and abs(predicted) < 30:
                        print(f"      💡 可能原因: 遗漏了关键机制（如开库、强根、官印相生等）")
                        print(f"      💡 建议: 检查财富引擎是否正确识别了以下机制:")
                        if real > 0:
                            print(f"         - 强根帮身（长生、帝旺、临官）")
                            print(f"         - 财库开启（冲开财库）")
                            print(f"         - 官印相生")
                            print(f"         - 创业加成（身弱得强根但无财透）")
                        else:
                            print(f"         - 冲提纲（月令被冲）")
                            print(f"         - 财库坍塌")
                            print(f"         - 七杀攻身")
                    elif abs(real) < 30 and abs(predicted) > 80:
                        print(f"      💡 可能原因: 过度触发了某些机制")
                        print(f"      💡 建议: 检查以下机制的权重是否过高:")
                        print(f"         - 强根加成")
                        print(f"         - 开库加成")
                        print(f"         - 官印相生加成")
                elif not direction_match:
                    print(f"      ⚠️ 方向错误")
                    print(f"      💡 可能原因: 关键机制的触发条件判断错误")
                    print(f"      💡 建议: 检查财富引擎的方向判断逻辑")
                else:
                    print(f"      ⚠️ 误差在可接受范围内，但仍有优化空间")
            else:
                print(f"      ✅ 预测准确，无需调整")
            print()
            
            # 详细计算（如果需要）
            if not is_correct and abs(error) > 30:
                print(f"   🔬 详细计算分析:")
                try:
                    # 重新计算，获取详细信息
                    result = engine.calculate_wealth_index(
                        bazi=case.bazi,
                        day_master=case.day_master,
                        gender=case.gender,
                        luck_pillar=dayun,
                        year_pillar=ganzhi
                    )
                    
                    if isinstance(result, dict):
                        wealth_index = result.get('wealth_index', 0.0)
                        wealth_energy = result.get('wealth_energy', 0.0)
                        base_wealth = result.get('base_wealth', 0.0)
                        strong_root_bonus = result.get('strong_root_bonus', 0.0)
                        vault_bonus = result.get('vault_bonus', 0.0)
                        clash_penalty = result.get('clash_penalty', 0.0)
                        
                        print(f"      财富指数: {wealth_index:.1f}")
                        print(f"      财富能量: {wealth_energy:.1f}")
                        print(f"      基础财富: {base_wealth:.1f}")
                        print(f"      强根加成: {strong_root_bonus:.1f}")
                        print(f"      开库加成: {vault_bonus:.1f}")
                        print(f"      冲克惩罚: {clash_penalty:.1f}")
                except Exception as e:
                    print(f"      ⚠️ 无法获取详细计算信息: {e}")
                print()
        else:
            print(f"   ❌ 计算失败: {r.get('error_msg', 'Unknown')}")
            print()
    
    # 总结
    print("=" * 80)
    print("📊 案例总结")
    print("=" * 80)
    print()
    
    total = len(results)
    correct = sum(1 for r in results if r.get('is_correct', False))
    errors = [r.get('error', 0) for r in results if r.get('error') is not None]
    avg_error = sum(errors) / len(errors) if errors else 0.0
    max_error = max(errors) if errors else 0.0
    
    print(f"总事件数: {total}")
    print(f"正确事件: {correct}")
    print(f"命中率: {correct/total*100:.1f}%")
    print(f"平均误差: {avg_error:.1f}分")
    print(f"最大误差: {max_error:.1f}分")
    print()
    
    # 优化建议
    print("=" * 80)
    print("💡 优化建议")
    print("=" * 80)
    print()
    
    if correct / total < 0.5:
        print("⚠️ 命中率低于50%，建议:")
        print("   1. 检查财富引擎的核心逻辑")
        print("   2. 调整各种机制的触发阈值")
        print("   3. 检查身强/身弱的判定准确性")
        print()
    
    if avg_error > 30:
        print("⚠️ 平均误差超过30分，建议:")
        print("   1. 调整财富能量的基础值")
        print("   2. 调整各种加成的权重")
        print("   3. 检查惩罚机制是否过重")
        print()
    
    # 找出最需要修复的事件
    failed_events = [r for r in results if not r.get('is_correct', False) and r.get('predicted') is not None]
    if failed_events:
        failed_events.sort(key=lambda x: abs(x.get('error', 0)), reverse=True)
        print("🔧 优先修复的事件:")
        for i, fe in enumerate(failed_events[:3], 1):
            print(f"   {i}. {fe['year']}年: 误差={fe.get('error', 0):.1f}分")
        print()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='深入分析单个财富验证案例')
    parser.add_argument('case_id', help='案例ID (如: TIMELINE_MUSK_WEALTH)')
    args = parser.parse_args()
    
    analyze_single_case(args.case_id)

