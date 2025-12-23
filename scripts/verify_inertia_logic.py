"""
Antigravity Inertia Logic Verification (Phase B-12)
===================================================
Purpose: Verify Spacetime Fluid Viscosity (Exponential Decay Model).
"""

import json
import sys
import os

# Ensure we can import the core asset
sys.path.append("/home/jin/bazi_predict")
from core.trinity.core.assets.spacetime_inertia_engine import calculate_transition_inertia

def run_verify():
    print("--- ANTIGRAVITY PHASE B-12 LOGIC AUDIT ---")
    print(f"Algorithm: calculate_transition_inertia")
    
    # Load Test Suite
    test_path = "/home/jin/bazi_predict/tests/stress_test_b12_inertia.json"
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
        name = sample['name']
        inputs = sample['inputs']
        expect = sample['expected_output']
        
        print(f"\n[TEST {total}] {case_id}: {name}")
        
        try:
            # Execute Logic
            months = inputs.get('months_since_switch')
            tau = inputs.get('tau', 3.0)
            
            res = calculate_transition_inertia(months, tau)
            
            print(f"  > Input Months: {months} (Tau={tau})")
            print(f"  > Output Weights: Prev={res['Prev_Luck']}, Next={res['Next_Luck']}")
            
            # Validation (Allow small float diffs)
            p_ok = abs(res['Prev_Luck'] - expect['Prev_Luck']) < 0.001
            v_ok = abs(res['Viscosity'] - expect['Viscosity']) < 0.001
            
            if p_ok and v_ok:
                print("  > STATUS: ✅ PASSED")
                passed += 1
            else:
                print(f"  > STATUS: ❌ FAILED")
                print(f"    Expected: Prev={expect['Prev_Luck']}")
                print(f"    Got:      Prev={res['Prev_Luck']}")

        except Exception as e:
            print(f"  > STATUS: ❌ ERROR - {str(e)}")
            
    print("-" * 40)
    print(f"AUDIT COMPLETE: {passed}/{total} Passed.")

if __name__ == "__main__":
    run_verify()
