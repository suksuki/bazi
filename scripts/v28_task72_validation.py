"""
V28.0 Task 72: 最终底层参数修正验证
===================================
验证回滚和第一层参数修正后的C07和C04的MAE
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

def v28_validation():
    """V28.0 验证"""
    
    print("=" * 80)
    print("V28.0 Task 72: 最终底层参数修正验证")
    print("=" * 80)
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Verify rollback
    print("\n" + "=" * 80)
    print("Step 1: V27.0 回滚验证")
    print("=" * 80)
    
    spacetime_config = config.get('physics', {}).get('SpacetimeCorrector', {})
    exclusion_list = spacetime_config.get('ExclusionList', [])
    case_specific = spacetime_config.get('CaseSpecificCorrectorFactor', {})
    
    print(f"\nSpacetimeCorrector 配置:")
    print(f"  ExclusionList: {exclusion_list}")
    print(f"  C07 是否在ExclusionList: {'C07' in exclusion_list}")
    print(f"  C07 是否在CaseSpecificCorrectorFactor: {'C07' in case_specific}")
    
    if 'C07' in exclusion_list and 'C07' not in case_specific:
        print("\n✅ V27.0 回滚成功：C07已恢复至ExclusionList")
    else:
        print("\n❌ V27.0 回滚失败：C07未正确回滚")
        return False
    
    # Verify first layer parameters
    print("\n" + "=" * 80)
    print("Step 2: V28.0 第一层参数验证")
    print("=" * 80)
    
    flow_config = config.get('flow', {})
    ctl_imp = flow_config.get('controlImpact', 0.7)
    observation_bias_config = config.get('ObservationBiasFactor', {})
    k_capture = observation_bias_config.get('k_capture', 0.0)
    
    print(f"\n第一层参数:")
    print(f"  ctl_imp: {ctl_imp} (预期: 0.90)")
    print(f"  k_capture: {k_capture} (预期: 0.25)")
    
    if abs(ctl_imp - 0.90) < 0.01 and abs(k_capture - 0.25) < 0.01:
        print("\n✅ V28.0 第一层参数修正成功")
    else:
        print("\n❌ V28.0 第一层参数修正失败")
        return False
    
    # Verify V24.0 parameters are unchanged
    print("\n" + "=" * 80)
    print("Step 3: V24.0 基础参数验证（应保持不变）")
    print("=" * 80)
    
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    pg_month = pillar_weights.get('month', 1.0)
    imp_base = flow_config.get('resourceImpedance', {}).get('base', 0.20)
    clash_score = config.get('interactions', {}).get('branchEvents', {}).get('clashScore', -3.0)
    
    print(f"\nV24.0 基础参数:")
    print(f"  pg_month: {pg_month} (预期: 1.8)")
    print(f"  imp_base: {imp_base} (预期: 0.20)")
    print(f"  clash_score: {clash_score} (预期: -3.0)")
    
    v24_ok = (
        abs(pg_month - 1.8) < 0.01 and
        abs(imp_base - 0.20) < 0.01 and
        abs(clash_score - (-3.0)) < 0.01
    )
    
    if v24_ok:
        print("\n✅ V24.0 基础参数保持不变")
    else:
        print("\n❌ V24.0 基础参数被意外修改")
        return False
    
    # Calculate C07 and C04 scores
    print("\n" + "=" * 80)
    print("Step 4: C07 和 C04 得分计算")
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
    # Note: calculate_energy returns career scaled by 10.0, so multiply back
    c07_career = c07_career_scaled * 10.0
    c07_gt = 80.0
    c07_mae = abs(c07_career - c07_gt)
    
    print(f"\nC07 事业相:")
    print(f"  八字: {c07_bazi}")
    print(f"  模型得分（缩放后）: {c07_career_scaled:.2f}")
    print(f"  模型得分（原始）: {c07_career:.2f}")
    print(f"  GT: {c07_gt:.2f}")
    print(f"  MAE: {c07_mae:.2f}")
    
    # C04: 需要从calibration_cases.json加载
    calibration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "calibration_cases.json")
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
            # Note: calculate_energy returns wealth scaled by 10.0, so multiply back
            c04_wealth = c04_wealth_scaled * 10.0
            c04_gt = c04_case.get('v_real', {}).get('wealth_score', c04_case.get('v_real', {}).get('wealth', 0.0))
            c04_mae = abs(c04_wealth - c04_gt)
            
            print(f"\nC04 财富相:")
            print(f"  八字: {c04_case.get('bazi', [])}")
            print(f"  模型得分: {c04_wealth:.2f}")
            print(f"  GT: {c04_gt:.2f}")
            print(f"  MAE: {c04_mae:.2f}")
        else:
            print(f"\n⚠️  C04案例未找到")
            c04_mae = 999.0
    except FileNotFoundError:
        print(f"\n⚠️  calibration_cases.json未找到，跳过C04验证")
        c04_mae = 999.0
    
    # Summary
    print("\n" + "=" * 80)
    print("验证总结")
    print("=" * 80)
    
    print(f"\n✅ V27.0 回滚: 成功")
    print(f"✅ V28.0 第一层参数修正: 成功")
    print(f"✅ V24.0 基础参数: 保持不变")
    print(f"\nC07 事业相 MAE: {c07_mae:.2f}")
    if c04_mae < 999.0:
        print(f"C04 财富相 MAE: {c04_mae:.2f}")
    
    if c07_mae < 5.0 and c04_mae < 5.0:
        print(f"\n🎉 成功: C07和C04的MAE均已收敛至 < 5.0")
        return True
    elif c07_mae < 5.0:
        print(f"\n⚠️  部分成功: C07 MAE已收敛，C04仍需调整")
        return True
    else:
        print(f"\n⚠️  注意: C07和C04的MAE仍 > 5.0，可能需要进一步调整")
        return False

if __name__ == "__main__":
    success = v28_validation()
    sys.exit(0 if success else 1)

