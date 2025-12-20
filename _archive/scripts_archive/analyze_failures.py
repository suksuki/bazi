#!/usr/bin/env python3
"""
Failure Analysis Script (V36.0)
================================

生成详细的失败案例分析和混淆矩阵，用于诊断系统误判方向。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import copy

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


def load_golden_cases(data_path: Path = None) -> List[Dict[str, Any]]:
    """加载测试案例"""
    if data_path is None:
        data_path = project_root / "data" / "golden_cases.json"
    
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            return cases
    return []


def predict_strength(strength_score: float, 
                     strong_threshold: float = 60.0,
                     weak_threshold: float = 40.0) -> str:
    """根据占比分数预测身强身弱"""
    if strength_score >= strong_threshold:
        return "Strong"
    elif strength_score >= weak_threshold:
        return "Balanced"
    else:
        return "Weak"


def analyze_weak_inflation_cases(cases: List[Dict[str, Any]], config: Dict):
    """
    [V42.0] 专门分析Weak案例被误判为Strong/Balanced的原因（能量通胀诊断）
    """
    print("=" * 80)
    print("🩺 Inflation Diagnosis (V42.0) - Weak Case Analysis")
    print("=" * 80)
    print()
    
    from core.engine_graph import GraphNetworkEngine
    from core.processors.physics import GENERATION, CONTROL
    
    engine = GraphNetworkEngine(config=config)
    
    weak_failures = []
    
    for case in cases:
        true_label = case.get('true_label')
        if true_label != 'Weak':
            continue
        
        try:
            result = engine.analyze(
                bazi=case['bazi'],
                day_master=case['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            strength_score = result.get('strength_score', 0.0)
            
            # 使用阈值判断
            grading_config = config.get('grading', {})
            strong_threshold = grading_config.get('strong_threshold', 60.0)
            weak_threshold = grading_config.get('weak_threshold', 40.0)
            
            if strength_score >= strong_threshold:
                pred_label = "Strong"
            elif strength_score >= weak_threshold:
                pred_label = "Balanced"
            else:
                pred_label = "Weak"
            
            if pred_label != "Weak":
                weak_failures.append({
                    'case': case,
                    'result': result,
                    'score': strength_score,
                    'pred_label': pred_label
                })
        except Exception as e:
            print(f"⚠️  案例 {case.get('id')} 出错: {e}")
            continue
    
    if not weak_failures:
        print("✅ 没有Weak案例被误判")
        return
    
    print(f"📊 发现 {len(weak_failures)} 个Weak案例被误判为Strong/Balanced\n")
    
    for i, failure in enumerate(weak_failures, 1):
        case = failure['case']
        result = failure['result']
        score = failure['score']
        pred_label = failure['pred_label']
        
        print("=" * 80)
        print(f"🔬 案例 {i}: {case.get('id')} (True: Weak, Pred: {pred_label}, Score: {score:.1f}%)")
        print("=" * 80)
        print(f"Bazi: {case['bazi']}")
        print(f"日主: {case['day_master']}")
        print(f"描述: {case.get('description', '')}")
        print()
        
        # 重新初始化引擎以获取详细状态
        engine_detail = GraphNetworkEngine(config=config)
        detail_result = engine_detail.analyze(
            bazi=case['bazi'],
            day_master=case['day_master'],
            luck_pillar=None,
            year_pillar=None,
            geo_modifiers=None
        )
        
        nodes = engine_detail.nodes
        final_energies = detail_result.get('final_energy', [])
        
        # 确定日主元素
        dm_char = case['day_master']
        dm_element_map = {
            '甲': 'wood', '乙': 'wood', '丙': 'fire', '丁': 'fire', '戊': 'earth',
            '己': 'earth', '庚': 'metal', '辛': 'metal', '壬': 'water', '癸': 'water'
        }
        dm_element = dm_element_map.get(dm_char, 'metal')
        
        # 考虑化气
        if engine_detail.day_master_element:
            dm_element = engine_detail.day_master_element
        
        # 确定十神关系
        # Output (食伤): 我生的
        output_elements = []
        for source, target in GENERATION.items():
            if source == dm_element:
                output_elements.append(target)
        
        # Officer (官杀): 克我的
        officer_elements = []
        for source, target in CONTROL.items():
            if target == dm_element:
                officer_elements.append(source)
        
        # Wealth (财): 我克的
        wealth_elements = []
        for source, target in CONTROL.items():
            if source == dm_element:
                wealth_elements.append(target)
        
        # Resource (印): 生我的
        resource_elements = []
        for source, target in GENERATION.items():
            if target == dm_element:
                resource_elements.append(source)
        
        print("📊 能量分析（初始 vs 最终）")
        print("-" * 80)
        
        # 分析各十神能量的初始值和最终值
        for role_name, elements in [
            ("日主 (Self)", [dm_element]),
            ("食伤 (Output)", output_elements),
            ("官杀 (Officer)", officer_elements),
            ("财星 (Wealth)", wealth_elements),
            ("印星 (Resource)", resource_elements)
        ]:
            if not elements:
                continue
            
            init_total = 0.0
            final_total = 0.0
            
            for elem in elements:
                for j, node in enumerate(nodes):
                    if node.element == elem:
                        init_total += node.initial_energy
                        final_total += final_energies[j] if j < len(final_energies) else node.current_energy
            
            change = final_total - init_total
            change_pct = (change / init_total * 100) if init_total > 0 else 0.0
            
            print(f"{role_name:15s}: 初始={init_total:6.3f} | 最终={final_total:6.3f} | "
                  f"变化={change:+7.3f} ({change_pct:+6.1f}%)")
        
        print()
        
        # 检查关键问题
        print("🔍 关键诊断")
        print("-" * 80)
        
        # 1. 检查食伤是否泄身
        output_final = sum(final_energies[j] if j < len(final_energies) else nodes[j].current_energy
                          for j, node in enumerate(nodes) if node.element in output_elements)
        self_final = sum(final_energies[j] if j < len(final_energies) else nodes[j].current_energy
                        for j, node in enumerate(nodes) if node.element == dm_element)
        
        if output_final > 0:
            output_ratio = output_final / (output_final + self_final) if (output_final + self_final) > 0 else 0
            if output_ratio > 0.3:
                print(f"⚠️  食伤能量占比高 ({output_ratio*100:.1f}%)，但日主未明显减弱")
                print(f"   疑点: 食伤可能没有有效泄身（能量循环？）")
        
        # 2. 检查官杀是否克身
        officer_final = sum(final_energies[j] if j < len(final_energies) else nodes[j].current_energy
                           for j, node in enumerate(nodes) if node.element in officer_elements)
        
        if officer_final > 0:
            officer_ratio = officer_final / (officer_final + self_final) if (officer_final + self_final) > 0 else 0
            if officer_ratio > 0.2 and self_final > self_final * 0.8:  # 官杀有但日主没明显降
                print(f"⚠️  官杀能量占比高 ({officer_ratio*100:.1f}%)，但日主未明显被压制")
                print(f"   疑点: 官杀可能没有有效克身（被转化？）")
        
        # 3. 检查能量闭环
        print(f"   建议: 检查邻接矩阵，寻找能量闭环路径")
        print()
    
    print("=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)
    print()


def analyze_failures():
    """分析失败案例"""
    print("=" * 80)
    print("🔍 Failure Analysis Report (V42.0)")
    print("=" * 80)
    print()
    
    # 1. 加载案例和配置
    print("📋 加载测试案例...")
    cases = load_golden_cases()
    print(f"   加载了 {len(cases)} 个案例")
    print()
    
    # 加载配置
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
    
    # 获取阈值
    grading = config.get('grading', {})
    strong_threshold = grading.get('strong_threshold', 60.0)
    weak_threshold = grading.get('weak_threshold', 40.0)
    
    print(f"🔧 当前判定阈值:")
    print(f"   Strong >= {strong_threshold}%")
    print(f"   Balanced: {weak_threshold}% - {strong_threshold}%")
    print(f"   Weak < {weak_threshold}%")
    print()
    
    # 2. 运行测试
    print("🧪 运行测试...")
    engine = GraphNetworkEngine(config=config)
    
    results = []
    for case in cases:
        true_label = case.get('true_label')
        if not true_label:
            continue
        
        try:
            result = engine.analyze(
                bazi=case['bazi'],
                day_master=case['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            strength_score = result.get('strength_score', 0.0)
            pred_label = predict_strength(strength_score, strong_threshold, weak_threshold)
            
            self_team = result.get('self_team_energy', 0.0)
            total_energy = result.get('total_energy', 0.0)
            
            results.append({
                'case_id': case.get('id', 'Unknown'),
                'true_label': true_label,
                'pred_label': pred_label,
                'strength_score': strength_score,
                'self_team_energy': self_team,
                'total_energy': total_energy,
                'description': case.get('description', ''),
                'is_correct': pred_label == true_label
            })
        except Exception as e:
            print(f"⚠️  案例 {case.get('id')} 出错: {e}")
    
    print(f"   完成了 {len(results)} 个案例的分析")
    print()
    
    # 3. 生成混淆矩阵
    print("=" * 80)
    print("📊 混淆矩阵 (Confusion Matrix)")
    print("=" * 80)
    
    confusion = defaultdict(lambda: defaultdict(int))
    for result in results:
        true_label = result['true_label']
        pred_label = result['pred_label']
        confusion[true_label][pred_label] += 1
    
    labels = ['Strong', 'Balanced', 'Weak']
    
    # 打印表头
    print(f"\n{'True\\Pred':15s}", end='')
    for pred in labels:
        print(f"{pred:15s}", end='')
    print()
    print("-" * 80)
    
    # 打印表格内容
    for true_label in labels:
        print(f"{true_label:15s}", end='')
        for pred_label in labels:
            count = confusion[true_label][pred_label]
            print(f"{count:15d}", end='')
        print()
    
    print("-" * 80)
    print()
    
    # 4. 分析误判方向
    print("=" * 80)
    print("🔍 误判方向分析")
    print("=" * 80)
    
    balanced_results = [r for r in results if r['true_label'] == 'Balanced']
    if balanced_results:
        balanced_pred_dist = defaultdict(int)
        for r in balanced_results:
            balanced_pred_dist[r['pred_label']] += 1
        
        print("\n📌 Balanced 案例的误判分布:")
        total_balanced = len(balanced_results)
        for pred_label, count in balanced_pred_dist.items():
            pct = (count / total_balanced * 100) if total_balanced > 0 else 0
            print(f"   -> 被判为 {pred_label}: {count} 个 ({pct:.1f}%)")
        
        # 诊断建议
        if balanced_pred_dist['Strong'] > balanced_pred_dist['Weak']:
            print("\n💡 诊断: Balanced 案例大多被判为 Strong")
            print("   -> 建议: 系统可能能量过载 (Over-boosted)")
            print("   -> 方案: 增加阻尼因子，或提高 Strong 阈值")
        elif balanced_pred_dist['Weak'] > balanced_pred_dist['Strong']:
            print("\n💡 诊断: Balanced 案例大多被判为 Weak")
            print("   -> 建议: 系统可能泄耗过重 (Over-drained)")
            print("   -> 方案: 减少控制影响，或降低 Weak 阈值，增加通根权重")
        else:
            print("\n💡 诊断: Balanced 案例误判分布相对均衡")
    
    print()
    
    # 5. 详细失败报告
    print("=" * 80)
    print("📝 详细失败案例报告")
    print("=" * 80)
    
    failures = [r for r in results if not r['is_correct']]
    
    print(f"\n共有 {len(failures)} 个失败案例:\n")
    
    for i, fail in enumerate(failures, 1):
        true_label = fail['true_label']
        pred_label = fail['pred_label']
        score = fail['strength_score']
        self_team = fail['self_team_energy']
        total = fail['total_energy']
        ratio = (self_team / total * 100) if total > 0 else 0
        
        # 计算偏差
        if true_label == "Strong":
            target = strong_threshold + 10.0  # 假设Strong目标为阈值+10
            diff = score - target
        elif true_label == "Balanced":
            target = (strong_threshold + weak_threshold) / 2  # 中间值
            diff = score - target
        else:  # Weak
            target = weak_threshold - 10.0  # 假设Weak目标为阈值-10
            diff = score - target
        
        print(f"[FAIL {i:02d}] {fail['case_id']} (True: {true_label})")
        print(f"         -> Pred: {pred_label} ({score:5.1f}%)")
        print(f"         -> Key Stats: Self_Team={self_team:.2f}, Total={total:.2f}, Ratio={ratio:.1f}%")
        print(f"         -> Diagnosis: {'Over-estimated' if diff > 0 else 'Under-estimated'} by {abs(diff):.1f}%")
        if fail['description']:
            print(f"         -> Description: {fail['description']}")
        print()
    
    print("=" * 80)
    print("✅ 标准分析完成")
    print("=" * 80)
    print()
    
    # [V42.0] 额外执行Weak案例通胀诊断
    print("\n")
    analyze_weak_inflation_cases(cases, config)


if __name__ == "__main__":
    try:
        analyze_failures()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

