"""
V29.0 Task 74: 逐步计算验证（Step A到Step E）
============================================
按照Gemini提供的五个步骤，一步一步计算并对比预期值
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

def step_by_step_c07():
    """C07 逐步计算验证"""
    
    print("=" * 80)
    print("V29.0 Task 74: C07 事业相逐步计算验证")
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
    
    flow_config = config.get('flow', {})
    ctl_imp = flow_config.get('controlImpact', 0.7)
    imp_base = flow_config.get('resourceImpedance', {}).get('base', 0.20)
    
    print(f"\n关键参数:")
    print(f"  ctl_imp: {ctl_imp} (预期: 1.25)")
    print(f"  imp_base: {imp_base} (预期: 0.20)")
    
    # ============================================================
    # Step A & B: 原始结构能量 + 复杂交互修正
    # ============================================================
    print("\n" + "=" * 80)
    print("Step A & B: 原始结构能量 + 复杂交互修正")
    print("=" * 80)
    
    physics = PhysicsProcessor()
    context_ab = {
        'bazi': bazi_list,
        'day_master': dm_char,
        'dm_element': dm_elem,
        'pillar_weights': config.get('physics', {}).get('pillarWeights', {}),
        'interactions_config': config.get('interactions', {}),
        'flow_config': flow_config
    }
    
    physics_result = physics.process(context_ab)
    raw_energy = physics_result['raw_energy']
    
    earth_final = raw_energy.get('earth', 0)
    fire_final = raw_energy.get('fire', 0)
    
    print(f"\n实际计算值:")
    print(f"  E_Earth,Final: {earth_final:.2f}")
    print(f"  E_Fire,Final: {fire_final:.2f}")
    
    print(f"\nV29.0 预期值（Gemini提供）:")
    print(f"  E_Officer,Final = 25.60 (Fire能量)")
    print(f"  说明: Step A & B 基础能量不变")
    
    # ============================================================
    # Step C: 十神粒子波函数
    # ============================================================
    print("\n" + "=" * 80)
    print("Step C: 十神粒子波函数 (E_Particle)")
    print("=" * 80)
    
    domain = DomainProcessor()
    domain_context = {
        'raw_energy': raw_energy,
        'dm_element': dm_elem,
        'strength': {'verdict': 'Strong', 'raw_score': 50.0},
        'gender': 1,
        'particle_weights': config.get('particleWeights', {}),
        'physics_config': config.get('physics', {}),
        'observation_bias_config': config.get('ObservationBiasFactor', {}),
        'flow_config': flow_config,
        'case_id': 'C07',
        'luck_pillar': None,
        'annual_pillar': None
    }
    
    domain._context = domain_context
    gods = domain._calculate_ten_gods(raw_energy, dm_elem, config.get('particleWeights', {}))
    
    resource_god = gods.get('resource', 0)
    officer_god = gods.get('officer', 0)
    
    print(f"\n实际计算值:")
    print(f"  E_Resource (十神): {resource_god:.2f}")
    print(f"  E_Officer (十神): {officer_god:.2f}")
    
    print(f"\nV29.0 预期值（Gemini提供）:")
    print(f"  E_Officer = 25.60 × (1 + 1.25) = 57.60")
    print(f"  说明: 应用 ctl_imp = 1.25")
    
    # 检查ctl_imp是否应用
    expected_officer = fire_final * (1 + ctl_imp)
    print(f"\n手动计算验证:")
    print(f"  E_Fire,Final = {fire_final:.2f}")
    print(f"  ctl_imp = {ctl_imp:.2f}")
    print(f"  预期 E_Officer = {fire_final:.2f} × (1 + {ctl_imp:.2f}) = {expected_officer:.2f}")
    print(f"  实际 E_Officer = {officer_god:.2f}")
    
    if abs(officer_god - expected_officer) < 0.1:
        print(f"  ✅ ctl_imp 已正确应用")
    else:
        print(f"  ❌ ctl_imp 未正确应用！差异: {abs(officer_god - expected_officer):.2f}")
    
    # ============================================================
    # Step D: 事业相基础得分
    # ============================================================
    print("\n" + "=" * 80)
    print("Step D: 事业相基础得分 (S_Base)")
    print("=" * 80)
    
    career_result = domain._calc_career(gods, 50.0, 'Strong')
    s_base = career_result.get('score', 0.0)
    
    print(f"\n实际计算值:")
    print(f"  S_Base: {s_base:.2f}")
    
    print(f"\nV29.0 预期值（Gemini提供）:")
    print(f"  S_Base ≈ 46.50")
    print(f"  说明: S_Base,Old ≈ 42.00 + (57.60 - 48.64) × 0.5 ≈ 46.50")
    
    # 手动计算预期值
    old_officer = fire_final * (1 + 0.90)  # V28.0
    new_officer = fire_final * (1 + 1.25)  # V29.0
    old_base = 42.00  # V28.0的S_Base
    expected_base = old_base + (new_officer - old_officer) * 0.5
    
    print(f"\n手动计算验证:")
    print(f"  V28.0 E_Officer = {old_officer:.2f}")
    print(f"  V29.0 E_Officer = {new_officer:.2f}")
    print(f"  提升 = {new_officer - old_officer:.2f}")
    print(f"  V28.0 S_Base = {old_base:.2f}")
    print(f"  预期 S_Base = {old_base:.2f} + {new_officer - old_officer:.2f} × 0.5 = {expected_base:.2f}")
    print(f"  实际 S_Base = {s_base:.2f}")
    
    if abs(s_base - expected_base) < 2.0:
        print(f"  ✅ S_Base 接近预期值")
    else:
        print(f"  ❌ S_Base 与预期值差异较大！差异: {abs(s_base - expected_base):.2f}")
    
    # ============================================================
    # Step E: 最终得分
    # ============================================================
    print("\n" + "=" * 80)
    print("Step E: 最终得分 (S_Final)")
    print("=" * 80)
    
    domain_result = domain.process(domain_context)
    career_final = domain_result.get('career', {}).get('score', 0.0)
    
    print(f"\n实际计算值:")
    print(f"  S_Final: {career_final:.2f}")
    
    print(f"\nV29.0 预期值（Gemini提供）:")
    print(f"  S_Final ≈ 79.7")
    print(f"  说明: S_Final,New = 67.43 × (57.60 / 48.64) ≈ 79.7")
    
    # 手动计算预期值
    old_final = 67.43  # V28.0的S_Final
    expected_final = old_final * (new_officer / old_officer)
    
    print(f"\n手动计算验证:")
    print(f"  V28.0 S_Final = {old_final:.2f}")
    print(f"  V28.0 E_Officer = {old_officer:.2f}")
    print(f"  V29.0 E_Officer = {new_officer:.2f}")
    print(f"  预期 S_Final = {old_final:.2f} × ({new_officer:.2f} / {old_officer:.2f}) = {expected_final:.2f}")
    print(f"  实际 S_Final = {career_final:.2f}")
    
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
    print("逐步计算总结")
    print("=" * 80)
    
    print(f"\nStep A & B:")
    print(f"  实际: E_Fire,Final = {fire_final:.2f}")
    print(f"  预期: E_Officer,Final = 25.60")
    print(f"  状态: {'✅' if abs(fire_final - 25.60) < 1.0 else '❌'}")
    
    print(f"\nStep C:")
    print(f"  实际: E_Officer = {officer_god:.2f}")
    print(f"  预期: E_Officer = 57.60")
    print(f"  状态: {'✅' if abs(officer_god - 57.60) < 2.0 else '❌'}")
    if abs(officer_god - expected_officer) > 0.1:
        print(f"  ⚠️  ctl_imp可能未正确应用！")
    
    print(f"\nStep D:")
    print(f"  实际: S_Base = {s_base:.2f}")
    print(f"  预期: S_Base ≈ 46.50")
    print(f"  状态: {'✅' if abs(s_base - 46.50) < 3.0 else '❌'}")
    
    print(f"\nStep E:")
    print(f"  实际: S_Final = {career_final:.2f}")
    print(f"  预期: S_Final ≈ 79.7")
    print(f"  状态: {'✅' if abs(career_final - 79.7) < 5.0 else '❌'}")
    print(f"  MAE: {mae:.2f} ({'✅' if mae < 5.0 else '❌'})")
    
    return {
        'fire_final': fire_final,
        'officer_god': officer_god,
        's_base': s_base,
        'career_final': career_final,
        'mae': mae
    }

if __name__ == "__main__":
    result = step_by_step_c07()

