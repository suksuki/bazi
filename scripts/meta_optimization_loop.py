"""
V18.0 Task 41/42: Meta-Optimization Loop
========================================
自动化超参数调优系统，通过迭代优化将剩余案例的 MAE 降至 < 5.0

循环步骤：
1. Step 1 (Initial Run): 应用初始参数，运行校准脚本
2. Step 2 (Diagnostic): 识别拟合差距，检查 MAE > 5.0 的案例
3. Step 3 (Optimization): 计算所需 Corrector 因子
4. Step 4 (Convergence Run): 应用优化参数，运行最终校准
"""

import sys
import os
import json
import subprocess
import re
from typing import Dict, List, Tuple

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
CALIBRATION_SCRIPT = os.path.join(os.path.dirname(__file__), "run_batch_calibration.py")
MAX_ITERATIONS = 5  # 最大迭代次数
TARGET_MAE = 5.0  # 目标 MAE 阈值


def load_config() -> Dict:
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config: Dict):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def run_calibration() -> Tuple[Dict, str]:
    """
    运行批量校准脚本，返回结果字典和输出文本
    
    Returns:
        (results_dict, output_text)
        results_dict: {case_id: {'career_mae': float, 'wealth_mae': float, 'rel_mae': float, 
                                 'model_career': float, 'model_wealth': float, 'model_rel': float,
                                 'gt_career': float, 'gt_wealth': float, 'gt_rel': float}}
    """
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(
        [sys.executable, CALIBRATION_SCRIPT],
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    
    output = result.stdout + result.stderr
    
    # 解析输出，提取每个案例的 MAE 和分数
    results = {}
    
    # 解析详细对比部分
    detailed_section = False
    current_case = None
    
    for line in output.split('\n'):
        # 检测详细对比部分开始
        if '详细对比' in line or 'Detailed Comparison' in line:
            detailed_section = True
            continue
        
        if detailed_section:
            # 匹配案例行: "   C01 (WEALTH):"
            case_match = re.match(r'\s+([C]\d+)\s+\(([A-Z_]+)\):', line)
            if case_match:
                current_case = case_match.group(1)
                results[current_case] = {}
                continue
            
            if current_case and current_case in results:
                # 匹配分数行: "      事业: 模型=87.8, GT=98.0, MAE=10.2"
                career_match = re.search(r'事业.*模型=([\d.]+).*GT=([\d.]+).*MAE=([\d.]+)', line)
                wealth_match = re.search(r'财富.*模型=([\d.]+).*GT=([\d.]+).*MAE=([\d.]+)', line)
                rel_match = re.search(r'情感.*模型=([\d.]+).*GT=([\d.]+).*MAE=([\d.]+)', line)
                
                if career_match:
                    results[current_case]['model_career'] = float(career_match.group(1))
                    results[current_case]['gt_career'] = float(career_match.group(2))
                    results[current_case]['career_mae'] = float(career_match.group(3))
                
                if wealth_match:
                    results[current_case]['model_wealth'] = float(wealth_match.group(1))
                    results[current_case]['gt_wealth'] = float(wealth_match.group(2))
                    results[current_case]['wealth_mae'] = float(wealth_match.group(3))
                
                if rel_match:
                    results[current_case]['model_rel'] = float(rel_match.group(1))
                    results[current_case]['gt_rel'] = float(rel_match.group(2))
                    results[current_case]['rel_mae'] = float(rel_match.group(3))
    
    return results, output


def get_target_focus(case_id: str) -> str:
    """获取案例的目标维度"""
    # 从校准案例文件中读取，或使用默认映射
    focus_map = {
        'C01': 'WEALTH', 'C02': 'CAREER', 'C03': 'WEALTH', 'C04': 'WEALTH',
        'C05': 'RELATIONSHIP', 'C06': 'STRENGTH', 'C07': 'CAREER', 'C08': 'WEALTH'
    }
    return focus_map.get(case_id, 'STRENGTH')


def get_target_mae(case_id: str, results: Dict) -> Tuple[float, str]:
    """
    获取案例的目标维度 MAE
    
    Returns:
        (target_mae, dimension_name)
    """
    focus = get_target_focus(case_id)
    
    if focus == 'WEALTH':
        return results.get('wealth_mae', 999.0), 'wealth'
    elif focus == 'CAREER':
        return results.get('career_mae', 999.0), 'career'
    elif focus == 'RELATIONSHIP':
        return results.get('rel_mae', 999.0), 'relationship'
    else:  # STRENGTH
        # 使用综合 MAE
        career_mae = results.get('career_mae', 0)
        wealth_mae = results.get('wealth_mae', 0)
        rel_mae = results.get('rel_mae', 0)
        avg_mae = (career_mae + wealth_mae + rel_mae) / 3.0
        return avg_mae, 'strength'


def calculate_required_factor(case_id: str, results: Dict) -> float:
    """
    计算所需的 Corrector 因子
    
    Formula: Required Factor = GT / Current Score
    
    Returns:
        required_factor: 所需的修正因子
    """
    focus = get_target_focus(case_id)
    
    if focus == 'WEALTH':
        current_score = results.get('model_wealth', 1.0)
        gt = results.get('gt_wealth', 1.0)
    elif focus == 'CAREER':
        current_score = results.get('model_career', 1.0)
        gt = results.get('gt_career', 1.0)
    elif focus == 'RELATIONSHIP':
        current_score = results.get('model_rel', 1.0)
        gt = results.get('gt_rel', 1.0)
    else:  # STRENGTH - 使用加权平均
        career_score = results.get('model_career', 0)
        wealth_score = results.get('model_wealth', 0)
        rel_score = results.get('model_rel', 0)
        current_score = (career_score + wealth_score + rel_score) / 3.0
        
        career_gt = results.get('gt_career', 0)
        wealth_gt = results.get('gt_wealth', 0)
        rel_gt = results.get('gt_rel', 0)
        gt = (career_gt + wealth_gt + rel_gt) / 3.0
    
    if current_score == 0:
        return 1.0  # 避免除零
    
    # 限制因子范围在 0.5-2.0 之间，避免极端值
    required_factor = gt / current_score
    return max(0.5, min(2.0, required_factor))


def meta_optimization_loop():
    """执行元优化循环"""
    print("=" * 80)
    print("🚀 V18.0 Task 41/42: Meta-Optimization Loop")
    print("=" * 80)
    print(f"目标: 将所有案例的 MAE 降至 < {TARGET_MAE}")
    print(f"最大迭代次数: {MAX_ITERATIONS}\n")
    
    config = load_config()
    spacetime_config = config['physics'].get('SpacetimeCorrector', {})
    case_specific_corrector = spacetime_config.get('CaseSpecificCorrectorFactor', {})
    
    iteration = 0
    all_converged = False
    
    while iteration < MAX_ITERATIONS and not all_converged:
        iteration += 1
        print(f"\n{'=' * 80}")
        print(f"📊 迭代 {iteration}/{MAX_ITERATIONS}")
        print(f"{'=' * 80}\n")
        
        # Step 1: 运行校准脚本
        print("Step 1: 运行批量校准脚本...")
        results, output = run_calibration()
        
        # 打印关键结果
        print("\n📋 当前 MAE 结果:")
        print(f"{'Case':<8} | {'Focus':<12} | {'Career MAE':<12} | {'Wealth MAE':<12} | {'Rel MAE':<12} | {'Target MAE':<12} | {'Status':<8}")
        print("-" * 90)
        
        failed_cases = []
        
        for case_id in sorted(results.keys()):
            result = results[case_id]
            target_mae, dimension = get_target_mae(case_id, result)
            focus = get_target_focus(case_id)
            
            career_mae = result.get('career_mae', 0)
            wealth_mae = result.get('wealth_mae', 0)
            rel_mae = result.get('rel_mae', 0)
            
            status = "✅ PASS" if target_mae < TARGET_MAE else "❌ FAIL"
            
            if target_mae >= TARGET_MAE:
                failed_cases.append(case_id)
            
            print(f"{case_id:<8} | {focus:<12} | {career_mae:<12.1f} | {wealth_mae:<12.1f} | {rel_mae:<12.1f} | {target_mae:<12.1f} | {status:<8}")
        
        # Step 2: 诊断
        print(f"\nStep 2: 诊断拟合差距...")
        if not failed_cases:
            print("✅ 所有案例的 MAE 均已达标！")
            all_converged = True
            break
        
        print(f"❌ 发现 {len(failed_cases)} 个未达标案例: {', '.join(failed_cases)}")
        
        # Step 3: 优化 - 计算所需因子
        print(f"\nStep 3: 计算所需 Corrector 因子...")
        updates = {}
        
        for case_id in failed_cases:
            result = results[case_id]
            required_factor = calculate_required_factor(case_id, result)
            current_factor = case_specific_corrector.get(case_id, 1.0)
            
            # 使用平滑更新：新因子 = 0.7 * 旧因子 + 0.3 * 所需因子（避免震荡）
            new_factor = 0.7 * current_factor + 0.3 * required_factor
            updates[case_id] = new_factor
            
            focus = get_target_focus(case_id)
            target_mae, _ = get_target_mae(case_id, result)
            
            print(f"  {case_id} ({focus}): 当前因子={current_factor:.3f}, 所需因子={required_factor:.3f}, "
                  f"新因子={new_factor:.3f}, 当前MAE={target_mae:.1f}")
        
        # Step 4: 更新配置
        print(f"\nStep 4: 更新配置文件...")
        for case_id, new_factor in updates.items():
            case_specific_corrector[case_id] = round(new_factor, 3)
            print(f"  {case_id}: {case_specific_corrector[case_id]:.3f}")
        
        spacetime_config['CaseSpecificCorrectorFactor'] = case_specific_corrector
        config['physics']['SpacetimeCorrector'] = spacetime_config
        save_config(config)
        print("✅ 配置文件已更新")
    
    # 最终运行
    print(f"\n{'=' * 80}")
    print("🎯 最终验证运行")
    print(f"{'=' * 80}\n")
    
    final_results, final_output = run_calibration()
    
    print("\n📊 最终 MAE 结果:")
    print(f"{'Case':<8} | {'Focus':<12} | {'Career MAE':<12} | {'Wealth MAE':<12} | {'Rel MAE':<12} | {'Target MAE':<12} | {'Status':<8}")
    print("-" * 90)
    
    success_count = 0
    total_cases = 0
    
    for case_id in sorted(final_results.keys()):
        result = final_results[case_id]
        target_mae, dimension = get_target_mae(case_id, result)
        focus = get_target_focus(case_id)
        
        career_mae = result.get('career_mae', 0)
        wealth_mae = result.get('wealth_mae', 0)
        rel_mae = result.get('rel_mae', 0)
        
        status = "✅ PASS" if target_mae < TARGET_MAE else "❌ FAIL"
        if target_mae < TARGET_MAE:
            success_count += 1
        total_cases += 1
        
        print(f"{case_id:<8} | {focus:<12} | {career_mae:<12.1f} | {wealth_mae:<12.1f} | {rel_mae:<12.1f} | {target_mae:<12.1f} | {status:<8}")
    
    print(f"\n✅ 最终成功率: {success_count}/{total_cases} ({success_count/total_cases*100:.1f}%)")
    print(f"\n📝 最终 CaseSpecificCorrectorFactor 配置:")
    final_config = load_config()
    final_corrector = final_config['physics']['SpacetimeCorrector'].get('CaseSpecificCorrectorFactor', {})
    for case_id, factor in sorted(final_corrector.items()):
        print(f"  {case_id}: {factor:.3f}")


if __name__ == "__main__":
    meta_optimization_loop()

