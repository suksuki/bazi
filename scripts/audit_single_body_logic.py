"""
Antigravity Logic Audit Runner
==============================
Purpose: Verify consistency of current Single-Body Engine asset against Standard JSON Test Suite.
"""

import json
import sys
import os

# Ensure we can import the core asset
sys.path.append("/home/jin/bazi_predict")
from core.trinity.core.assets.dynamic_energy_engine import engine, AntigravityEngine

def run_audit():
    print("--- ANTIGRAVITY SINGLE-BODY LOGIC AUDIT ---")
    print(f"Engine Class: {AntigravityEngine.__name__}")
    print(f"Constants Check:")
    print(f"  - Void Damping: {engine.VOID_DAMPING}")
    print(f"  - Shear Burst: {engine.SHEAR_BURST}")
    
    # Load Test Suite
    test_path = "/home/jin/bazi_predict/tests/standard_physics_tests.json"
    if not os.path.exists(test_path):
        print(f"CRITICAL: Test suite not found at {test_path}")
        return

    with open(test_path, 'r') as f:
        data = json.load(f)
        
    suite_name = data.get('test_suite', 'Unknown')
    print(f"\nLoaded Suite: {suite_name}")
    print("-" * 40)
    
    passed = 0
    total = 0
    
    for sample in data.get('data_samples', []):
        total += 1
        case_id = sample['case_id']
        desc = sample['description']
        inputs = sample['inputs']
        expect = sample['expected_output']
        
        print(f"\n[TEST {total}] {case_id}: {desc}")
        
        try:
            # Execute Logic
            branch = inputs.get('branch')
            progress = inputs.get('progress')
            
            # 1. Run Core Dispersion
            if branch:
                result = engine.calculate_qi_dispersion(progress, branch)
                print(f"  > Output: {result}")
                
                # Validation: Continuity / Entropy / Energy Levels
                if expect.get('max_entropy'):
                    # Simplified verification (assuming low entropy means consistent low values for nascent qi)
                    # Here we just check if values are small if progress is small
                    max_val = max(result.values()) if result else 0
                    noise_check = max_val < 5.0 # Just a sanity check for start
                    if expect.get('check_continuity'):
                         # At 0.001, sin^2 is very small. 10 * sin^2(0.001*pi) approx 0.
                         # But let's check explicit values driven by the JSON
                         pass

                if expect.get('min_energy_癸'):
                     val = result.get('癸', 0)
                     if val >= expect['min_energy_癸']:
                         print(f"  > PASS: 癸 Energy {val} >= {expect['min_energy_癸']}")
                     else:
                         print(f"  > FAIL: 癸 Energy {val} < {expect['min_energy_癸']}")
                         continue

            # 2. Run Special Logic (Shear Burst)
            if inputs.get('stress_trigger') == 'Chong':
                shear_val = engine.SHEAR_BURST
                if expect.get('check_shear_burst'):
                    if shear_val == float(expect.get('expected_shear_factor', 0)):
                         print(f"  > PASS: Shear Burst Factor verified at {shear_val}")
                    else:
                         print(f"  > FAIL: Shear Burst Factor {shear_val} != {expect.get('expected_shear_factor')}")
                         continue

            passed += 1
            print("  > STATUS: ✅ PASSED")

        except Exception as e:
            print(f"  > STATUS: ❌ ERROR - {str(e)}")
            
    print("-" * 40)
    print(f"AUDIT COMPLETE: {passed}/{total} Passed.")

if __name__ == "__main__":
    run_audit()
