"""
V27.0 Task 71: C07 事业相详细计算路径
====================================
详细追踪C07事业相得分的完整计算过程
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

def detailed_c07_career():
    """详细追踪C07事业相计算"""
    
    print("=" * 80)
    print("V27.0 Task 71: C07 事业相详细计算路径")
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
    
    # Create engine
    engine = EngineV88(config=config)
    
    # Step A: Raw Energy
    print("\n" + "=" * 80)
    print("Step A: 原始结构能量")
    print("=" * 80)
    
    physics = PhysicsProcessor()
    context_a = {
        'bazi': bazi_list,
        'day_master': dm_char,
        'dm_element': dm_elem,
        'pillar_weights': config.get('physics', {}).get('pillarWeights', {}),
        'interactions_config': config.get('interactions', {}),
        'flow_config': config.get('flow', {})
    }
    
    physics_result = physics.process(context_a)
    raw_energy = physics_result['raw_energy']
    
    earth_a = raw_energy.get('earth', 0)
    fire_a = raw_energy.get('fire', 0)
    
    print(f"  E_Earth: {earth_a:.2f}")
    print(f"  E_Fire: {fire_a:.2f}")
    
    # Step B: Complex Interactions (already applied in physics.process)
    print("\n" + "=" * 80)
    print("Step B: 复杂交互修正（已在PhysicsProcessor中应用）")
    print("=" * 80)
    
    earth_final = raw_energy.get('earth', 0)
    fire_final = raw_energy.get('fire', 0)
    
    print(f"  E_Earth,Final: {earth_final:.2f}")
    print(f"  E_Fire,Final: {fire_final:.2f}")
    
    # Step C: Ten Gods
    print("\n" + "=" * 80)
    print("Step C: 十神粒子波函数")
    print("=" * 80)
    
    domain = DomainProcessor()
    flow_config = config.get('flow', {})
    
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
    
    print(f"  E_Resource (十神): {resource_god:.2f}")
    print(f"  E_Officer (十神): {officer_god:.2f}")
    
    # Step D: Career Base Score
    print("\n" + "=" * 80)
    print("Step D: 事业相基础得分")
    print("=" * 80)
    
    career_result = domain._calc_career(gods, 50.0, 'Strong')
    s_base = career_result.get('score', 0.0)
    
    print(f"  S_Base: {s_base:.2f}")
    
    # Check breakdown if available
    if hasattr(domain, '_context') and domain._context:
        breakdown = domain._context.get('score_breakdown', {})
        career_breakdown = breakdown.get('career', {})
        if career_breakdown:
            print(f"\n  详细分解:")
            for key, value in career_breakdown.items():
                print(f"    {key}: {value:.2f}")
    
    # Step E: Final Score (with SpacetimeCorrector)
    print("\n" + "=" * 80)
    print("Step E: 最终得分（应用SpacetimeCorrector）")
    print("=" * 80)
    
    # Get full domain result
    domain_result = domain.process(domain_context)
    career_final = domain_result.get('career', {}).get('score', 0.0)
    
    print(f"  S_Final: {career_final:.2f}")
    print(f"  GT: 80.0")
    print(f"  MAE: {abs(career_final - 80.0):.2f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("计算路径总结")
    print("=" * 80)
    
    print(f"\nStep A: E_Earth = {earth_a:.2f}")
    print(f"Step B: E_Earth,Final = {earth_final:.2f}")
    print(f"Step C: E_Resource = {resource_god:.2f}, E_Officer = {officer_god:.2f}")
    print(f"Step D: S_Base = {s_base:.2f}")
    print(f"Step E: S_Final = {career_final:.2f}")
    
    print(f"\n修正后的AI预期:")
    print(f"  Step A: E_Earth = 42.10")
    print(f"  Step B: E_Earth,Final = 37.10")
    print(f"  Step C: E_Resource = 29.68, E_Officer = 43.52")
    print(f"  Step D: S_Base = 36.60")
    print(f"  Step E: S_Final ≈ 43.19 (36.60 × 1.18)")
    
    return {
        'earth_a': earth_a,
        'earth_final': earth_final,
        'resource_god': resource_god,
        'officer_god': officer_god,
        's_base': s_base,
        'career_final': career_final,
        'mae': abs(career_final - 80.0)
    }

if __name__ == "__main__":
    result = detailed_c07_career()

