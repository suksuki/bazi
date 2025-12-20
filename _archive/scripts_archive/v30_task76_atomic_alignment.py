"""
V30.0 Task 76: C07 事业相黄金计算路径原子级对齐
===============================================
按照Gemini提供的原子级计算分解，逐步验证每一步的数值
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
from core.processors.domains import DomainProcessor
from core.processors.physics import PhysicsProcessor, STEM_ELEMENTS

def atomic_alignment_c07():
    """C07 原子级对齐验证"""
    
    print("=" * 80)
    print("V30.0 Task 76: C07 事业相黄金计算路径原子级对齐")
    print("=" * 80)
    
    # C07: 辛丑、乙未、庚午、甲申
    bazi_list = ['辛丑', '乙未', '庚午', '甲申']
    dm_char = '庚'
    dm_elem = STEM_ELEMENTS.get(dm_char, 'metal')
    
    print(f"\nC07 八字: {bazi_list}")
    print(f"日主: {dm_char} ({dm_elem})")
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 验证参数
    flow_config = config.get('flow', {})
    ctl_imp = flow_config.get('controlImpact', 0.7)
    imp_base = flow_config.get('resourceImpedance', {}).get('base', 0.20)
    observation_bias_config = config.get('ObservationBiasFactor', {})
    k_capture = observation_bias_config.get('k_capture', 0.0)
    
    print(f"\n参数验证:")
    print(f"  ctl_imp: {ctl_imp} (预期: 1.25)")
    print(f"  imp_base: {imp_base} (预期: 0.20)")
    print(f"  k_capture: {k_capture} (预期: 0.25)")
    
    if abs(ctl_imp - 1.25) > 0.01 or abs(imp_base - 0.20) > 0.01 or abs(k_capture - 0.25) > 0.01:
        print(f"\n❌ 参数未对齐！")
        return False
    
    print(f"\n✅ 参数已对齐")
    
    # ============================================================
    # Step A: 原始结构能量的绝对黄金基准
    # ============================================================
    print("\n" + "=" * 80)
    print("Step A: 原始结构能量的绝对黄金基准")
    print("=" * 80)
    
    pillar_weights = config.get('physics', {}).get('pillarWeights', {})
    pg_year = pillar_weights.get('year', 1.0)
    pg_month = pillar_weights.get('month', 1.8)
    pg_day = pillar_weights.get('day', 1.5)
    pg_hour = pillar_weights.get('hour', 1.2)
    
    print(f"\nPillar Weights:")
    print(f"  pg_year: {pg_year}")
    print(f"  pg_month: {pg_month} (预期: 1.8)")
    print(f"  pg_day: {pg_day}")
    print(f"  pg_hour: {pg_hour}")
    
    # 手动计算Step A（按照Gemini的分解）
    print(f"\n【Step A: E_Earth (42.10) 的计算分解】")
    print(f"  地支主气 (丑土)： 10.0 × {pg_year} = {10.0 * pg_year:.2f}")
    print(f"  地支主气 (未土)： 10.0 × {pg_month} = {10.0 * pg_month:.2f}")
    print(f"  地支藏干 (午藏己土)： 7.0 × {pg_day} = {7.0 * pg_day:.2f}")
    print(f"  地支藏干 (申藏戊土)： 3.0 × {pg_hour} = {3.0 * pg_hour:.2f}")
    earth_manual = 10.0 * pg_year + 10.0 * pg_month + 7.0 * pg_day + 3.0 * pg_hour
    print(f"  E_Earth 总计： {earth_manual:.2f} (预期: 42.10)")
    
    print(f"\n【Step A: E_Fire (27.60) 的计算分解】")
    print(f"  地支藏干 (未藏丁火)： 7.0 × {pg_month} = {7.0 * pg_month:.2f}")
    print(f"  地支主气 (午火)： 10.0 × {pg_day} = {10.0 * pg_day:.2f}")
    fire_manual = 7.0 * pg_month + 10.0 * pg_day
    print(f"  E_Fire 总计： {fire_manual:.2f} (预期: 27.60)")
    
    # 使用PhysicsProcessor计算实际值
    physics = PhysicsProcessor()
    context_a = {
        'bazi': bazi_list,
        'day_master': dm_char,
        'dm_element': dm_elem,
        'pillar_weights': pillar_weights,
        'interactions_config': config.get('interactions', {}),
        'flow_config': flow_config
    }
    
    physics_result = physics.process(context_a)
    raw_energy = physics_result['raw_energy']
    
    earth_actual = raw_energy.get('earth', 0)
    fire_actual = raw_energy.get('fire', 0)
    
    print(f"\n实际计算值（PhysicsProcessor）:")
    print(f"  E_Earth: {earth_actual:.2f}")
    print(f"  E_Fire: {fire_actual:.2f}")
    
    # 注意：PhysicsProcessor的结果已经包含了复杂交互，所以是Step B的结果
    # 我们需要手动计算Step A（无交互）和Step B（有交互）
    
    # ============================================================
    # Step B: 修正后 E_Final
    # ============================================================
    print("\n" + "=" * 80)
    print("Step B: 修正后 E_Final（复杂交互修正）")
    print("=" * 80)
    
    # 按照Gemini的分解，Step B的修正
    print(f"\n【Step B: 修正后 E_Final】")
    print(f"  E_Earth,Final (37.10) = 42.10 - 3.0 (冲) - 2.0 (害)")
    earth_final_expected = 42.10 - 3.0 - 2.0
    print(f"  预期 E_Earth,Final: {earth_final_expected:.2f}")
    
    print(f"  E_Fire,Final (25.60) = 27.60 - 2.0 (害)")
    fire_final_expected = 27.60 - 2.0
    print(f"  预期 E_Fire,Final: {fire_final_expected:.2f}")
    
    print(f"\n实际计算值（PhysicsProcessor已应用交互）:")
    print(f"  E_Earth,Final: {earth_actual:.2f}")
    print(f"  E_Fire,Final: {fire_actual:.2f}")
    
    # ============================================================
    # Step C: 粒子波函数（关键对齐点）
    # ============================================================
    print("\n" + "=" * 80)
    print("Step C: 粒子波函数（关键对齐点）")
    print("=" * 80)
    
    print(f"\n【Step C: 粒子波函数】")
    print(f"  E_Resource = E_Earth,Final × (1 - imp_base)")
    print(f"             = {earth_final_expected:.2f} × (1 - {imp_base:.2f})")
    resource_expected = earth_final_expected * (1 - imp_base)
    print(f"  预期 E_Resource: {resource_expected:.2f}")
    
    print(f"\n  E_Officer = E_Fire,Final × (1 + ctl_imp) × officer_weight")
    print(f"           = {fire_final_expected:.2f} × (1 + {ctl_imp:.2f}) × officer_weight")
    # 获取officer_weight
    particle_weights = config.get('particleWeights', {})
    officer_weight = max(particle_weights.get('ZhengGuan', 0.85), particle_weights.get('QiSha', 1.15))
    officer_expected = fire_final_expected * (1 + ctl_imp) * officer_weight
    print(f"  officer_weight: {officer_weight:.2f}")
    print(f"  预期 E_Officer: {officer_expected:.2f}")
    
    # 使用DomainProcessor计算实际值
    domain = DomainProcessor()
    domain_context = {
        'raw_energy': raw_energy,
        'dm_element': dm_elem,
        'strength': {'verdict': 'Strong', 'raw_score': 50.0},
        'gender': 1,
        'particle_weights': config.get('particleWeights', {}),
        'physics_config': config.get('physics', {}),
        'observation_bias_config': observation_bias_config,
        'flow_config': flow_config,
        'case_id': 'C07',
        'luck_pillar': None,
        'annual_pillar': None
    }
    
    domain._context = domain_context
    gods = domain._calculate_ten_gods(raw_energy, dm_elem, config.get('particleWeights', {}))
    
    resource_actual = gods.get('resource', 0)
    officer_actual = gods.get('officer', 0)
    
    print(f"\n实际计算值（DomainProcessor）:")
    print(f"  E_Resource: {resource_actual:.2f}")
    print(f"  E_Officer: {officer_actual:.2f}")
    
    # 关键对齐检查
    print(f"\n【关键对齐检查】")
    resource_diff = abs(resource_actual - resource_expected)
    officer_diff = abs(officer_actual - officer_expected)
    
    print(f"  E_Resource 差异: {resource_diff:.2f} ({'✅' if resource_diff < 0.5 else '❌'})")
    print(f"  E_Officer 差异: {officer_diff:.2f} ({'✅' if officer_diff < 0.5 else '❌'})")
    
    if resource_diff >= 0.5 or officer_diff >= 0.5:
        print(f"\n❌ Step C 值不匹配！必须立即停止，检查代码逻辑！")
        print(f"   不能进行任何额外修正。")
        return False
    
    print(f"\n✅ Step C 值已对齐")
    
    # ============================================================
    # Step D: 事业相基础得分
    # ============================================================
    print("\n" + "=" * 80)
    print("Step D: 事业相基础得分")
    print("=" * 80)
    
    career_result = domain._calc_career(gods, 50.0, 'Strong')
    s_base = career_result.get('score', 0.0)
    
    print(f"\n实际计算值:")
    print(f"  S_Base: {s_base:.2f}")
    
    # ============================================================
    # Step E: 最终得分
    # ============================================================
    print("\n" + "=" * 80)
    print("Step E: 最终得分")
    print("=" * 80)
    
    domain_result = domain.process(domain_context)
    career_final = domain_result.get('career', {}).get('score', 0.0)
    
    print(f"\n实际计算值:")
    print(f"  S_Final: {career_final:.2f}")
    
    # GT对比
    gt = 80.0
    mae = abs(career_final - gt)
    
    print(f"\nGT对比:")
    print(f"  GT: {gt:.2f}")
    print(f"  实际 S_Final: {career_final:.2f}")
    print(f"  MAE: {mae:.2f}")
    print(f"  预期 MAE: < 5.0")
    
    # ============================================================
    # 总结
    # ============================================================
    print("\n" + "=" * 80)
    print("原子级对齐总结")
    print("=" * 80)
    
    print(f"\nStep A:")
    print(f"  手动计算 E_Earth: {earth_manual:.2f} (预期: 42.10)")
    print(f"  手动计算 E_Fire: {fire_manual:.2f} (预期: 27.60)")
    print(f"  状态: {'✅' if abs(earth_manual - 42.10) < 0.1 and abs(fire_manual - 27.60) < 0.1 else '❌'}")
    
    print(f"\nStep B:")
    print(f"  预期 E_Earth,Final: {earth_final_expected:.2f}")
    print(f"  实际 E_Earth,Final: {earth_actual:.2f}")
    print(f"  预期 E_Fire,Final: {fire_final_expected:.2f}")
    print(f"  实际 E_Fire,Final: {fire_actual:.2f}")
    print(f"  状态: {'✅' if abs(earth_actual - earth_final_expected) < 1.0 and abs(fire_actual - fire_final_expected) < 1.0 else '❌'}")
    
    print(f"\nStep C (关键对齐点):")
    print(f"  预期 E_Resource: {resource_expected:.2f}")
    print(f"  实际 E_Resource: {resource_actual:.2f}")
    print(f"  预期 E_Officer: {officer_expected:.2f}")
    print(f"  实际 E_Officer: {officer_actual:.2f}")
    print(f"  状态: {'✅' if resource_diff < 0.5 and officer_diff < 0.5 else '❌'}")
    
    print(f"\nStep D:")
    print(f"  实际 S_Base: {s_base:.2f}")
    
    print(f"\nStep E:")
    print(f"  实际 S_Final: {career_final:.2f}")
    print(f"  MAE: {mae:.2f} ({'✅' if mae < 5.0 else '❌'})")
    
    return {
        'step_a_earth': earth_manual,
        'step_a_fire': fire_manual,
        'step_b_earth': earth_actual,
        'step_b_fire': fire_actual,
        'step_c_resource': resource_actual,
        'step_c_officer': officer_actual,
        'step_d_base': s_base,
        'step_e_final': career_final,
        'mae': mae,
        'aligned': resource_diff < 0.5 and officer_diff < 0.5
    }

if __name__ == "__main__":
    result = atomic_alignment_c07()
    if not result or not result.get('aligned', False):
        print(f"\n❌ 对齐失败！")
        sys.exit(1)
    else:
        print(f"\n✅ 对齐成功！")
        sys.exit(0)

