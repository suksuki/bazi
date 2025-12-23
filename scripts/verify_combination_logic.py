"""
Antigravity Logic Verification Runner (Phase B-09)
==================================================
Purpose: Verify Stem Combination Phase Threshold (0.65).
"""

import json
import sys
import os

# Ensure we can import the core asset
sys.path.append("/home/jin/bazi_predict")
from core.trinity.core.assets.combination_phase_logic import check_combination_phase

def run_verify():
    print("--- ANTIGRAVITY PHASE B-09 LOGIC AUDIT ---")
    print(f"Algorithm: check_combination_phase")
    
    # Load Test Suite
    test_path = "/home/jin/bazi_predict/tests/stress_test_e01_combination.json"
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
            stems = inputs.get('stems')
            month_energy = inputs.get('month_energy')
            
            result = check_combination_phase(stems, month_energy)
            print(f"  > Input Energy: {month_energy}")
            print(f"  > Output Status: {result['status']}")
            print(f"  > Output Power: {result['power_ratio']}")
            
            # Validation
            status_match = result['status'] == expect['status']
            power_match = result['power_ratio'] == expect['power_ratio']
            
            if status_match and power_match:
                print("  > STATUS: ✅ PASSED")
                passed += 1
            else:
                print(f"  > STATUS: ❌ FAILED (Expected {expect['status']} / {expect['power_ratio']})")

        except Exception as e:
            print(f"  > STATUS: ❌ ERROR - {str(e)}")
            
    print("-" * 40)
    print(f"AUDIT COMPLETE: {passed}/{total} Passed.")

if __name__ == "__main__":
    run_verify()
