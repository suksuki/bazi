"""
V26.0 Task 70: Atomic-Level Code Logic Alignment Validation
==========================================================
Validate fixed Earth energy calculation and parameter passing.
"""

import sys
import os
sys.path.append(os.getcwd())

import json
import os
from core.processors.physics import PhysicsProcessor
from core.engine_v88 import EngineV88

def validate_c07_earth_energy():
    """Validate C07 case Earth energy calculation"""
    
    print("=" * 80)
    print("V26.0 Task 70: C07 Earth Energy Validation")
    print("=" * 80)
    
    # C07: XinChou, YiWei, GengWu, JiaShen
    bazi_list = ['辛丑', '乙未', '庚午', '甲申']
    dm_char = '庚'
    
    # Load config from parameters.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Create engine
    engine = EngineV88(config=config)
    
    # Calculate energy using analyze method
    result = engine.analyze(bazi_list, dm_char)
    
    # Get raw energy from physics result
    raw_energy = result.raw_energy if hasattr(result, 'raw_energy') else {}
    if not raw_energy:
        # Try alternative: calculate directly
        context = {
            'bazi': bazi_list,
            'day_master': dm_char,
            'dm_element': engine.physics._get_element_stem(dm_char),
            'pillar_weights': config.get('physics', {}).get('pillarWeights', {}),
            'interactions_config': config.get('interactions', {}),
            'flow_config': config.get('flow', {})
        }
        physics_result = engine.physics.process(context)
        raw_energy = physics_result.get('raw_energy', {})
    
    earth_energy = raw_energy.get('earth', 0)
    
    print(f"\nC07 Bazi: {bazi_list}")
    print(f"Day Master: {dm_char}")
    print(f"\nStep B: Earth Energy After Complex Interactions: {earth_energy:.2f}")
    
    # Validate Earth energy is in expected range [18.0, 22.0]
    if 18.0 <= earth_energy <= 22.0:
        print(f"PASS: Earth energy in expected range [18.0, 22.0]")
        return True
    else:
        print(f"FAIL: Earth energy NOT in expected range [18.0, 22.0]")
        print(f"   Expected range: [18.0, 22.0]")
        print(f"   Actual value: {earth_energy:.2f}")
        return False

def validate_imp_base():
    """Validate imp_base parameter passing"""
    
    print("\n" + "=" * 80)
    print("V26.0 Task 70: imp_base Parameter Validation")
    print("=" * 80)
    
    # Load config from parameters.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    flow_config = config.get('flow', {})
    resource_impedance = flow_config.get('resourceImpedance', {})
    imp_base = resource_impedance.get('base', 0.30)
    
    print(f"\nimp_base in config: {imp_base}")
    
    if abs(imp_base - 0.20) < 0.01:
        print(f"PASS: imp_base parameter correct (0.20)")
        return True
    else:
        print(f"FAIL: imp_base parameter incorrect")
        print(f"   Expected: 0.20")
        print(f"   Actual: {imp_base}")
        return False

def validate_pillar_weights():
    """Validate Pillar Weights parameter passing"""
    
    print("\n" + "=" * 80)
    print("V26.0 Task 70: Pillar Weights Validation")
    print("=" * 80)
    
    # Load config from parameters.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    physics_config = config.get('physics', {})
    pillar_weights = physics_config.get('pillarWeights', {})
    month_weight = pillar_weights.get('month', 1.0)
    
    print(f"\nmonth pillar weight in config: {month_weight}")
    
    if abs(month_weight - 1.8) < 0.01:
        print(f"PASS: month pillar weight parameter correct (1.8)")
        return True
    else:
        print(f"FAIL: month pillar weight parameter incorrect")
        print(f"   Expected: 1.8")
        print(f"   Actual: {month_weight}")
        return False

def main():
    """Main validation function"""
    
    print("\n" + "=" * 80)
    print("V26.0 Task 70: Atomic-Level Code Logic Alignment Validation")
    print("=" * 80)
    
    results = []
    
    # Validation 1: C07 Earth energy
    results.append(("C07 Earth Energy", validate_c07_earth_energy()))
    
    # Validation 2: imp_base parameter
    results.append(("imp_base Parameter", validate_imp_base()))
    
    # Validation 3: Pillar Weights
    results.append(("Pillar Weights", validate_pillar_weights()))
    
    # Summary
    print("\n" + "=" * 80)
    print("Validation Results Summary")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("PASS: All validations passed!")
    else:
        print("FAIL: Some validations failed, please check code fixes.")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

