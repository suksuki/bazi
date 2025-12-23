"""
Antigravity Resonance Logic Verification (Phase B-10)
=====================================================
Purpose: Verify Stem-Branch Resonance & Rooting Gain (0.5x - 2.0x).
"""

import json
import sys
import os

# Ensure we can import the core asset
sys.path.append("/home/jin/bazi_predict")
from core.trinity.core.assets.resonance_booster import calculate_rooting_gain

def run_verify():
    print("--- ANTIGRAVITY PHASE B-10 LOGIC AUDIT ---")
    print(f"Algorithm: calculate_rooting_gain")
    
    # Load Test Suite
    test_path = "/home/jin/bazi_predict/tests/stress_test_b10_resonance.json"
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
            stem = inputs.get('stem')
            branches = inputs.get('branches')
            
            result = calculate_rooting_gain(stem, branches)
            print(f"  > Input: Stem {stem} | Branches {branches}")
            print(f"  > Output Gain: {result['gain']}")
            print(f"  > Output Status: {result['status']}")
            
            # Validation
            gain_match = result['gain'] == expect['resonance_gain']
            status_match = result['status'] == expect['stability_status']
            
            if gain_match and status_match:
                print("  > STATUS: ✅ PASSED")
                passed += 1
            else:
                print(f"  > STATUS: ❌ FAILED")
                print(f"    Expected: Gain {expect['resonance_gain']} | {expect['stability_status']}")
                print(f"    Got:      Gain {result['gain']} | {result['status']}")

        except Exception as e:
            print(f"  > STATUS: ❌ ERROR - {str(e)}")
            
    print("-" * 40)
    print(f"AUDIT COMPLETE: {passed}/{total} Passed.")

if __name__ == "__main__":
    run_verify()
