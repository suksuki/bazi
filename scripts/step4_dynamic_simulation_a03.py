#!/usr/bin/env python3
"""
FDS-V1.1 Step 4: 动态扩展与流年应力仿真 (The Crash Test)
模拟"流年冲刃"的物理场景，验证系统断裂阈值
"""

import sys
from pathlib import Path
import json
import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine

# 冲合关系定义
CLASH_PAIRS = [
    ('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
    ('辰', '戌'), ('巳', '亥')
]

COMBINATION_PAIRS = [
    ('子', '丑'), ('寅', '亥'), ('卯', '戌'), ('辰', '酉'),
    ('巳', '申'), ('午', '未')
]

def check_clash(branch1: str, branch2: str) -> bool:
    """检查两个地支是否对冲"""
    return (branch1, branch2) in CLASH_PAIRS or (branch2, branch1) in CLASH_PAIRS

def check_combination(branch1: str, branch2: str) -> bool:
    """检查两个地支是否相合"""
    return (branch1, branch2) in COMBINATION_PAIRS or (branch2, branch1) in COMBINATION_PAIRS

def get_clash_branch(branch: str) -> str:
    """获取与指定地支对冲的地支"""
    for b1, b2 in CLASH_PAIRS:
        if branch == b1:
            return b2
        if branch == b2:
            return b1
    return None

def check_has_combination_rescue(chart: List[str], clash_branch: str) -> bool:
    """
    检查原局是否有合来解救冲
    
    Args:
        chart: 四柱八字
        clash_branch: 流年冲刃的地支
        
    Returns:
        是否有合解救
    """
    branches = [p[1] for p in chart]
    
    # 检查原局是否有与冲刃地支相合的地支
    for branch in branches:
        if check_combination(branch, clash_branch):
            return True
    
    return False

def check_has_existing_clash(chart: List[str], month_branch: str) -> bool:
    """
    检查原局是否已有冲（如子午冲）
    
    Args:
        chart: 四柱八字
        month_branch: 月令地支（羊刃）
        
    Returns:
        是否已有冲
    """
    branches = [p[1] for p in chart]
    clash_branch = get_clash_branch(month_branch)
    
    if not clash_branch:
        return False
    
    # 检查原局是否有与月令对冲的地支
    for branch in branches:
        if branch == clash_branch:
            return True
    
    return False

def calculate_lambda(chart: List[str], month_branch: str, clash_branch: str) -> float:
    """
    计算激增系数 λ
    
    Args:
        chart: 四柱八字
        month_branch: 月令地支（羊刃）
        clash_branch: 流年冲刃的地支
        
    Returns:
        激增系数 λ
    """
    # 检查是否有合解救
    if check_has_combination_rescue(chart, clash_branch):
        return 1.2  # 有缓冲
    
    # 检查是否已有冲（共振破碎）
    if check_has_existing_clash(chart, month_branch):
        return 2.5  # 共振破碎
    
    # 无解救
    return 1.8  # 硬着陆

def simulate_clash_event(sample: Dict, s_base: float) -> Dict[str, Any]:
    """
    模拟流年冲刃事件
    
    Args:
        sample: 样本字典（包含chart, day_master, month_branch等）
        s_base: 基础应力值（Step 3计算得出）
        
    Returns:
        仿真结果字典
    """
    chart = sample['chart']
    day_master = sample['day_master']
    month_branch = sample.get('month_branch')
    
    # 如果没有month_branch，从chart中提取
    if not month_branch:
        month_branch = chart[1][1]  # 月支
    
    # 获取羊刃地支
    yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
    yang_ren_branch = yang_ren_map.get(day_master)
    
    # 如果月令不是羊刃，跳过
    if month_branch != yang_ren_branch:
        return None
    
    # 获取冲刃地支（流年）
    clash_branch = get_clash_branch(month_branch)
    if not clash_branch:
        return None
    
    # 计算激增系数
    lambda_val = calculate_lambda(chart, month_branch, clash_branch)
    
    # 计算新应力
    s_new = s_base * lambda_val
    
    # 断裂判定
    fracture_threshold = 50.0
    is_collapse = s_new >= fracture_threshold
    
    return {
        'chart': chart,
        'day_master': day_master,
        'month_branch': month_branch,
        'clash_branch': clash_branch,
        's_base': s_base,
        'lambda': lambda_val,
        's_new': round(s_new, 2),
        'is_collapse': is_collapse,
        'status': 'COLLAPSE' if is_collapse else 'SURVIVAL',
        'has_combination_rescue': check_has_combination_rescue(chart, clash_branch),
        'has_existing_clash': check_has_existing_clash(chart, month_branch)
    }

def main():
    print("=" * 70)
    print("🚀 FDS-V1.1 Step 4: 动态扩展与流年应力仿真 (The Crash Test)")
    print("=" * 70)
    print()
    
    # 加载Step 3的结果（需要包含S轴数据）
    # 尝试从TierA_Tensor_Analysis.md或重新计算
    data_file = project_root / "data" / "holographic_pattern" / "A-03_Standard_Dataset.json"
    
    if not data_file.exists():
        print(f"❌ 标准集文件不存在: {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    samples = data['samples']
    print(f"✅ 加载Tier A标准集: {len(samples)} 个样本")
    print()
    
    # 重新计算S轴（或从Step 3结果读取）
    # 这里简化：使用Step 3的算法重新计算
    from scripts.step3_tensor_fitting_a03 import calculate_5_axis
    
    print("开始流年冲刃仿真...")
    simulation_results = []
    collapse_count = 0
    survival_count = 0
    
    for i, sample in enumerate(samples):
        chart = sample['chart']
        day_master = sample['day_master']
        
        try:
            # 计算基础5维张量（获取S轴）
            tensor = calculate_5_axis(chart, day_master)
            s_base = tensor['S']
            
            # 模拟流年冲刃事件
            result = simulate_clash_event(sample, s_base)
            
            if result:
                result['sample_index'] = i
                result['s_base'] = s_base
                simulation_results.append(result)
                
                if result['is_collapse']:
                    collapse_count += 1
                else:
                    survival_count += 1
        except Exception as e:
            print(f"⚠️ 处理样本 {i} 失败: {e}")
            continue
        
        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{len(samples)} ({(i+1)/len(samples)*100:.1f}%)")
    
    print(f"✅ 完成：处理了 {len(simulation_results)} 个样本")
    print()
    
    # 统计分析
    total_simulated = len(simulation_results)
    collapse_rate = (collapse_count / total_simulated * 100) if total_simulated > 0 else 0
    
    print("=" * 70)
    print("【仿真结果统计】")
    print("=" * 70)
    print()
    print(f"总仿真样本: {total_simulated} 个")
    print(f"崩溃案例 (COLLAPSE): {collapse_count} 个")
    print(f"抗压案例 (SURVIVAL): {survival_count} 个")
    print(f"崩溃率: {collapse_rate:.2f}%")
    print()
    
    # Top 3 崩溃案例
    collapse_cases = sorted([r for r in simulation_results if r['is_collapse']], 
                           key=lambda x: x['s_new'], reverse=True)[:3]
    
    print("【Top 3 崩溃案例 (Collapse Cases)】")
    print("-" * 70)
    for i, case in enumerate(collapse_cases, 1):
        print(f"{i}. {' '.join(case['chart'])} (日主: {case['day_master']})")
        print(f"   月令羊刃: {case['month_branch']} | 流年冲刃: {case['clash_branch']}")
        print(f"   基础应力: {case['s_base']:.2f}")
        print(f"   激增系数 λ: {case['lambda']:.1f}")
        print(f"   新应力: {case['s_new']:.2f} ⚠️ 超过阈值50.0")
        print(f"   状态: {case['status']}")
        print(f"   有合解救: {'是' if case['has_combination_rescue'] else '否'}")
        print(f"   已有冲: {'是' if case['has_existing_clash'] else '否'}")
        print()
    
    # Top 3 抗压案例（S_base高但未崩溃）
    survival_cases = sorted([r for r in simulation_results if not r['is_collapse']], 
                           key=lambda x: x['s_base'], reverse=True)[:3]
    
    print("【Top 3 抗压案例 (Survival Cases)】")
    print("-" * 70)
    for i, case in enumerate(survival_cases, 1):
        print(f"{i}. {' '.join(case['chart'])} (日主: {case['day_master']})")
        print(f"   月令羊刃: {case['month_branch']} | 流年冲刃: {case['clash_branch']}")
        print(f"   基础应力: {case['s_base']:.2f} ⭐ 高应力但未崩溃")
        print(f"   激增系数 λ: {case['lambda']:.1f}")
        print(f"   新应力: {case['s_new']:.2f} ✅ 低于阈值50.0")
        print(f"   状态: {case['status']}")
        print(f"   有合解救: {'是' if case['has_combination_rescue'] else '否'}")
        print(f"   已有冲: {'是' if case['has_existing_clash'] else '否'}")
        print()
    
    # 生成Markdown报告
    report_file = project_root / "data" / "holographic_pattern" / "TierA_Dynamic_Simulation.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# FDS-V1.1 Step 4: Tier A 动态仿真报告 (The Crash Test)\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**仿真场景**: 流年冲刃事件\n\n")
        f.write("---\n\n")
        
        f.write("## 一、仿真结果统计\n\n")
        f.write(f"**总仿真样本**: {total_simulated} 个\n\n")
        f.write(f"**崩溃案例 (COLLAPSE)**: {collapse_count} 个\n\n")
        f.write(f"**抗压案例 (SURVIVAL)**: {survival_count} 个\n\n")
        f.write(f"**崩溃率**: {collapse_rate:.2f}%\n\n")
        
        if collapse_rate > 30:
            f.write("> ⚠️ **关键发现**: 崩溃率超过30%，说明'羊刃架杀'确实是一将功成万骨枯的格局。\n\n")
        else:
            f.write("> ✅ **关键发现**: 崩溃率低于30%，说明'羊刃架杀'在流年冲击下仍有一定的抗压能力。\n\n")
        
        f.write("---\n\n")
        f.write("## 二、Top 3 崩溃案例 (Collapse Cases)\n\n")
        f.write("> 这些样本在流年冲刃时发生了物理断裂（S_new >= 50.0）\n\n")
        for i, case in enumerate(collapse_cases, 1):
            f.write(f"### {i}. {' '.join(case['chart'])} (日主: {case['day_master']})\n\n")
            f.write(f"**月令羊刃**: {case['month_branch']} | **流年冲刃**: {case['clash_branch']}\n\n")
            f.write(f"**基础应力**: {case['s_base']:.2f}\n\n")
            f.write(f"**激增系数 λ**: {case['lambda']:.1f}\n\n")
            f.write(f"**新应力**: {case['s_new']:.2f} ⚠️ **超过阈值50.0**\n\n")
            f.write(f"**状态**: {case['status']}\n\n")
            f.write(f"**有合解救**: {'是' if case['has_combination_rescue'] else '否'}\n\n")
            f.write(f"**已有冲**: {'是' if case['has_existing_clash'] else '否'}\n\n")
            f.write("**物理意义**: 流年冲刃导致应力瞬间突破安全阈值，系统发生灾难性坍塌（车祸、暴亡）。\n\n")
        
        f.write("---\n\n")
        f.write("## 三、Top 3 抗压案例 (Survival Cases)\n\n")
        f.write("> 这些样本虽然基础应力很高，但在流年冲刃时依然没有崩溃（通常是因为有完美的'合'来解救）\n\n")
        for i, case in enumerate(survival_cases, 1):
            f.write(f"### {i}. {' '.join(case['chart'])} (日主: {case['day_master']})\n\n")
            f.write(f"**月令羊刃**: {case['month_branch']} | **流年冲刃**: {case['clash_branch']}\n\n")
            f.write(f"**基础应力**: {case['s_base']:.2f} ⭐ **高应力但未崩溃**\n\n")
            f.write(f"**激增系数 λ**: {case['lambda']:.1f}\n\n")
            f.write(f"**新应力**: {case['s_new']:.2f} ✅ **低于阈值50.0**\n\n")
            f.write(f"**状态**: {case['status']}\n\n")
            f.write(f"**有合解救**: {'是' if case['has_combination_rescue'] else '否'}\n\n")
            f.write(f"**已有冲**: {'是' if case['has_existing_clash'] else '否'}\n\n")
            f.write("**物理意义**: 虽然基础应力很高，但原局有合来缓冲流年冲击，系统依然保持稳定。\n\n")
        
        f.write("---\n\n")
        f.write("## 四、关键发现\n\n")
        f.write(f"1. **崩溃率**: {collapse_rate:.2f}%\n")
        if collapse_rate > 30:
            f.write("   - ⚠️ 超过30%，证明'羊刃架杀'确实是一将功成万骨枯的格局\n")
        else:
            f.write("   - ✅ 低于30%，说明格局在流年冲击下仍有一定的抗压能力\n")
        f.write(f"\n2. **激增系数分布**:\n")
        lambda_values = [r['lambda'] for r in simulation_results]
        lambda_12 = sum(1 for l in lambda_values if l == 1.2)
        lambda_18 = sum(1 for l in lambda_values if l == 1.8)
        lambda_25 = sum(1 for l in lambda_values if l == 2.5)
        f.write(f"   - λ=1.2 (有合解救): {lambda_12} 个样本\n")
        f.write(f"   - λ=1.8 (无解救): {lambda_18} 个样本\n")
        f.write(f"   - λ=2.5 (共振破碎): {lambda_25} 个样本\n")
        f.write(f"\n3. **抗压机制**:\n")
        rescue_count = sum(1 for r in simulation_results if r['has_combination_rescue'])
        f.write(f"   - 有合解救的样本: {rescue_count} 个 ({rescue_count/total_simulated*100:.1f}%)\n")
        f.write(f"   - 合的作用：缓冲流年冲击，降低激增系数\n")
    
    print("=" * 70)
    print("✅ 动态仿真报告已生成")
    print("=" * 70)
    print(f"📄 报告文件: {report_file}")
    print()

if __name__ == '__main__':
    main()

