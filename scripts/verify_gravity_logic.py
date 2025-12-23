"""
Antigravity Gravity Logic Verification (Phase B-11)
===================================================
Purpose: Verify Dynamic Pillar Weight Distribution (Sine Wave Model).
"""

import json
import sys
import os

# Ensure we can import the core asset
sys.path.append("/home/jin/bazi_predict")
from core.trinity.core.assets.pillar_gravity_engine import calculate_pillar_weights

def run_verify():
    print("--- ANTIGRAVITY PHASE B-11 LOGIC AUDIT ---")
    print(f"Algorithm: calculate_pillar_weights")
    
    # Load Test Suite
    test_path = "/home/jin/bazi_predict/tests/validation_suite_v10.json"
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
            progress = inputs.get('progress')
            
            weights = calculate_pillar_weights(progress)
            
            print(f"  > Input Progress: {progress}")
            print(f"  > Output Weights: {weights}")
            
            # Validation (Allow small float diffs)
            m_ok = abs(weights['Month'] - expect['Month']) < 0.02
            d_ok = abs(weights['Day'] - expect['Day']) < 0.02
            
            if m_ok and d_ok:
                print("  > STATUS: ✅ PASSED")
                passed += 1
            else:
                print(f"  > STATUS: ❌ FAILED")
                print(f"    Expected: M={expect['Month']}, D={expect['Day']}")
                print(f"    Got:      M={weights['Month']}, D={weights['Day']}")

        except Exception as e:
            print(f"  > STATUS: ❌ ERROR - {str(e)}")
            
    print("-" * 40)
    print(f"AUDIT COMPLETE: {passed}/{total} Passed.")

if __name__ == "__main__":
    run_verify()
