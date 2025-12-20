"""
V29.0 Task 74: 第一层参数最终微调验证
=====================================
验证ctl_imp=1.25对C07和C04的影响
"""

import sys
import os
import json
import io

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88

def v29_validation():
    """V29.0 验证"""
    
    print("=" * 80)
    print("V29.0 Task 74: 第一层参数最终微调验证")
    print("=" * 80)
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Verify V29.0 parameter
    print("\n" + "=" * 80)
    print("Step 1: V29.0 参数验证")
    print("=" * 80)
    
    flow_config = config.get('flow', {})
    ctl_imp = flow_config.get('controlImpact', 0.9)
    observation_bias_config = config.get('ObservationBiasFactor', {})
    k_capture = observation_bias_config.get('k_capture', 0.25)
    
    print(f"\nV29.0 参数:")
    print(f"  ctl_imp: {ctl_imp} (预期: 1.25)")
    print(f"  k_capture: {k_capture} (预期: 0.25)")
    
    if abs(ctl_imp - 1.25) < 0.01 and abs(k_capture - 0.25) < 0.01:
        print("\n✅ V29.0 参数对齐成功")
    else:
        print("\n❌ V29.0 参数对齐失败")
        return False
    
    # Verify second layer parameters are frozen
    print("\n" + "=" * 80)
    print("Step 2: 第二层参数冻结验证（V18.0冻结值）")
    print("=" * 80)
    
    spacetime_config = config.get('physics', {}).get('SpacetimeCorrector', {})
    exclusion_list = spacetime_config.get('ExclusionList', [])
    case_specific = spacetime_config.get('CaseSpecificCorrectorFactor', {})
    
    print(f"\nSpacetimeCorrector 配置:")
    print(f"  ExclusionList: {exclusion_list}")
    print(f"  CaseSpecificCorrectorFactor: {case_specific}")
    
    if 'C07' in exclusion_list and 'C07' not in case_specific:
        print("\n✅ 第二层参数保持V18.0冻结值")
    else:
        print("\n❌ 第二层参数未正确冻结")
        return False
    
    # Calculate C07 career score
    print("\n" + "=" * 80)
    print("Step 3: C07 事业相得分计算")
    print("=" * 80)
    
    engine = EngineV88(config=config)
    
    # C07: 辛丑、乙未、庚午、甲申 (事业相)
    c07_bazi = ['辛丑', '乙未', '庚午', '甲申']
    c07_case = {
        'year': c07_bazi[0],
        'month': c07_bazi[1],
        'day': c07_bazi[2],
        'hour': c07_bazi[3],
        'day_master': '庚',
        'gender': 1,
        'case_id': 'C07'
    }
    
    c07_result = engine.calculate_energy(c07_case)
    c07_career_scaled = c07_result.get('career', 0.0)
    c07_career = c07_career_scaled * 10.0
    c07_gt = 80.0
    c07_mae = abs(c07_career - c07_gt)
    
    print(f"\nC07 事业相:")
    print(f"  八字: {c07_bazi}")
    print(f"  模型得分（原始）: {c07_career:.2f}")
    print(f"  GT: {c07_gt:.2f}")
    print(f"  MAE: {c07_mae:.2f}")
    
    # Expected calculation path
    print(f"\n预期计算路径（V29.0）:")
    print(f"  Step C: E_Officer = 25.60 × (1 + 1.25) = 57.60")
    print(f"  Step D: S_Base ≈ 46.50")
    print(f"  Step E: S_Final ≈ 79.7")
    print(f"  预期 MAE: < 5.0")
    
    # Calculate C04 wealth score
    print("\n" + "=" * 80)
    print("Step 4: C04 财富相得分计算")
    print("=" * 80)
    
    calibration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "calibration_cases.json")
    c04_mae = None
    c04_wealth = None
    c04_gt = None
    
    try:
        with open(calibration_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        c04_case = None
        for case in cases:
            if case.get('id') == 'C04':
                c04_case = case
                break
        
        if c04_case:
            c04_result = engine.calculate_energy(c04_case)
            c04_wealth_scaled = c04_result.get('wealth', 0.0)
            c04_wealth = c04_wealth_scaled * 10.0
            c04_gt = c04_case.get('v_real', {}).get('wealth_score', c04_case.get('v_real', {}).get('wealth', 0.0))
            c04_mae = abs(c04_wealth - c04_gt)
            
            print(f"\nC04 财富相:")
            print(f"  八字: {c04_case.get('bazi', [])}")
            print(f"  模型得分（原始）: {c04_wealth:.2f}")
            print(f"  GT: {c04_gt:.2f}")
            print(f"  MAE: {c04_mae:.2f}")
            
            # Check if k_capture is applied
            print(f"\nk_capture 应用检查:")
            print(f"  k_capture = {k_capture}")
            print(f"  预期：身旺案例的财富得分应增加 25% 的财富能量")
        else:
            print(f"\n⚠️  C04案例未找到")
    except FileNotFoundError:
        print(f"\n⚠️  calibration_cases.json未找到，跳过C04验证")
    
    # Summary
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    
    print(f"\n✅ V29.0 参数: ctl_imp = {ctl_imp}, k_capture = {k_capture}")
    print(f"✅ 第二层参数: 保持V18.0冻结值")
    print(f"\nC07 事业相:")
    print(f"  模型得分: {c07_career:.2f}")
    print(f"  GT: {c07_gt:.2f}")
    print(f"  MAE: {c07_mae:.2f}")
    
    if c04_mae is not None:
        print(f"\nC04 财富相:")
        print(f"  模型得分: {c04_wealth:.2f}")
        print(f"  GT: {c04_gt:.2f}")
        print(f"  MAE: {c04_mae:.2f}")
    
    # Success criteria
    success = True
    if c07_mae >= 5.0:
        print(f"\n⚠️  C07事业相MAE ({c07_mae:.2f}) 仍 >= 5.0")
        success = False
    else:
        print(f"\n🎉 C07事业相MAE ({c07_mae:.2f}) 已收敛至 < 5.0")
    
    if c04_mae is not None:
        print(f"\n📊 C04财富相MAE: {c04_mae:.2f} (首次报告)")
    
    return success

if __name__ == "__main__":
    success = v29_validation()
    sys.exit(0 if success else 1)

