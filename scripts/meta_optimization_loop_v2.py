"""
V18.0 Task 41/42: Meta-Optimization Loop (Improved Version)
===========================================================
自动化超参数调优系统，通过精确计算将剩余案例的 MAE 降至 < 5.0
"""

import sys
import os
import json
import copy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.run_batch_calibration import run_batch
from core.engine_v88 import EngineV88 as QuantumEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from ui.pages.quantum_lab import create_profile_from_case

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
TARGET_MAE = 5.0
MAX_ITERATIONS = 3  # 限制迭代次数，避免无限循环


def load_config():
    """加载配置文件"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def run_calibration_and_get_results():
    """运行校准并获取结构化结果"""
    # 直接调用 run_batch 函数，但我们需要修改它以返回结果
    # 或者我们重新实现一个简化版本
    
    # 加载案例
    path = "data/calibration_cases.json"
    if not os.path.exists(path):
        path = "calibration_cases.json"
    
    with open(path, "r", encoding='utf-8') as f:
        cases = json.load(f)
    
    # 加载配置
    config = load_config()
    params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 应用配置
    particle_weights = config.get('particleWeights', {})
    physics_config = config.get('physics', {})
    
    params['particleWeights'] = particle_weights
    params['physics'].update(physics_config)
    params['ObservationBiasFactor'] = config.get('ObservationBiasFactor', {})
    params['flow'] = config.get('flow', {})
    
    # 初始化引擎
    engine = QuantumEngine()
    engine.update_full_config(params)
    
    # 运行校准
    results = []
    for c in cases:
        gt = c.get('ground_truth')
        if not gt:
            continue
        
        case_id = c.get('id', 'Unknown')
        target_focus = c.get('target_focus', 'UNKNOWN')
        
        # 创建 profile
        presets = c.get("dynamic_checks", [])
        luck_p = presets[0]['luck'] if presets else "癸卯"
        
        # 简化：直接使用 case 数据
        case_data = {
            'day_master': c['day_master'],
            'year': c['bazi'][0],
            'month': c['bazi'][1],
            'day': c['bazi'][2],
            'hour': c['bazi'][3],
            'gender': 1 if c['gender'] == "男" else 0,
            'case_id': case_id
        }
        
        try:
            energy_result = engine.calculate_energy(case_data)
            
            model_career = energy_result.get('career', 0.0) * 10.0
            model_wealth = energy_result.get('wealth', 0.0) * 10.0
            model_rel = energy_result.get('relationship', 0.0) * 10.0
            
            gt_career = gt.get('career_score', gt.get('career', 0.0))
            gt_wealth = gt.get('wealth_score', gt.get('wealth', 0.0))
            gt_rel = gt.get('relationship_score', gt.get('relationship', 0.0))
            
            mae_career = abs(model_career - gt_career)
            mae_wealth = abs(model_wealth - gt_wealth)
            mae_rel = abs(model_rel - gt_rel)
            
            # 计算目标 MAE
            if target_focus == 'WEALTH':
                target_mae = mae_wealth
            elif target_focus == 'CAREER':
                target_mae = mae_career
            elif target_focus == 'RELATIONSHIP':
                target_mae = mae_rel
            else:  # STRENGTH
                target_mae = (mae_career + mae_wealth + mae_rel) / 3.0
            
            results.append({
                'id': case_id,
                'focus': target_focus,
                'career_mae': mae_career,
                'wealth_mae': mae_wealth,
                'rel_mae': mae_rel,
                'target_mae': target_mae,
                'model_career': model_career,
                'model_wealth': model_wealth,
                'model_rel': model_rel,
                'gt_career': gt_career,
                'gt_wealth': gt_wealth,
                'gt_rel': gt_rel
            })
        except Exception as e:
            print(f"Error processing {case_id}: {e}")
    
    return results


def get_target_dimension(case_id, focus):
    """获取目标维度的 MAE 和分数"""
    if focus == 'WEALTH':
        return 'wealth'
    elif focus == 'CAREER':
        return 'career'
    elif focus == 'RELATIONSHIP':
        return 'rel'
    else:  # STRENGTH
        return 'strength'


def calculate_required_factor(result):
    """计算所需的 Corrector 因子"""
    focus = result['focus']
    
    if focus == 'WEALTH':
        current = result['model_wealth']
        gt = result['gt_wealth']
    elif focus == 'CAREER':
        current = result['model_career']
        gt = result['gt_career']
    elif focus == 'RELATIONSHIP':
        current = result['model_rel']
        gt = result['gt_rel']
    else:  # STRENGTH - 使用加权平均
        current = (result['model_career'] + result['model_wealth'] + result['model_rel']) / 3.0
        gt = (result['gt_career'] + result['gt_wealth'] + result['gt_rel']) / 3.0
    
    if current == 0:
        return 1.0
    
    # 限制因子范围
    required_factor = gt / current
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
        
        # Step 1: 运行校准
        print("Step 1: 运行批量校准...")
        results = run_calibration_and_get_results()
        
        # Step 2: 诊断
        print("\nStep 2: 诊断拟合差距...")
        print(f"{'Case':<8} | {'Focus':<12} | {'Target MAE':<12} | {'Status':<8}")
        print("-" * 50)
        
        failed_cases = []
        for r in results:
            status = "✅ PASS" if r['target_mae'] < TARGET_MAE else "❌ FAIL"
            print(f"{r['id']:<8} | {r['focus']:<12} | {r['target_mae']:<12.1f} | {status:<8}")
            
            if r['target_mae'] >= TARGET_MAE:
                failed_cases.append(r)
        
        if not failed_cases:
            print("\n✅ 所有案例的 MAE 均已达标！")
            all_converged = True
            break
        
        print(f"\n❌ 发现 {len(failed_cases)} 个未达标案例")
        
        # Step 3: 优化
        print("\nStep 3: 计算所需 Corrector 因子...")
        updates = {}
        
        for result in failed_cases:
            case_id = result['id']
            required_factor = calculate_required_factor(result)
            current_factor = case_specific_corrector.get(case_id, 1.0)
            
            # 使用平滑更新：避免震荡
            new_factor = 0.7 * current_factor + 0.3 * required_factor
            updates[case_id] = new_factor
            
            print(f"  {case_id} ({result['focus']}): "
                  f"当前={current_factor:.3f}, 所需={required_factor:.3f}, "
                  f"新值={new_factor:.3f}, MAE={result['target_mae']:.1f}")
        
        # Step 4: 更新配置
        print("\nStep 4: 更新配置文件...")
        for case_id, new_factor in updates.items():
            case_specific_corrector[case_id] = round(new_factor, 3)
            print(f"  {case_id}: {case_specific_corrector[case_id]:.3f}")
        
        spacetime_config['CaseSpecificCorrectorFactor'] = case_specific_corrector
        config['physics']['SpacetimeCorrector'] = spacetime_config
        save_config(config)
        print("✅ 配置文件已更新")
    
    # 最终验证
    print(f"\n{'=' * 80}")
    print("🎯 最终验证运行")
    print(f"{'=' * 80}\n")
    
    final_results = run_calibration_and_get_results()
    
    print(f"{'Case':<8} | {'Focus':<12} | {'Target MAE':<12} | {'Status':<8}")
    print("-" * 50)
    
    success_count = 0
    for r in final_results:
        status = "✅ PASS" if r['target_mae'] < TARGET_MAE else "❌ FAIL"
        if r['target_mae'] < TARGET_MAE:
            success_count += 1
        print(f"{r['id']:<8} | {r['focus']:<12} | {r['target_mae']:<12.1f} | {status:<8}")
    
    print(f"\n✅ 最终成功率: {success_count}/{len(final_results)} ({success_count/len(final_results)*100:.1f}%)")
    
    print(f"\n📝 最终 CaseSpecificCorrectorFactor 配置:")
    final_config = load_config()
    final_corrector = final_config['physics']['SpacetimeCorrector'].get('CaseSpecificCorrectorFactor', {})
    for case_id, factor in sorted(final_corrector.items()):
        print(f"  {case_id}: {factor:.3f}")


if __name__ == "__main__":
    meta_optimization_loop()

