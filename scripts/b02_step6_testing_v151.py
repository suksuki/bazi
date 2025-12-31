import json
import numpy as np
from scipy.spatial.distance import mahalanobis

# Mock Registry Loader
with open("core/subjects/holographic_pattern/registry.json", 'r') as f:
    registry = json.load(f)

b02 = registry['patterns']['B-02']
router = b02['matching_router']
# Simplified: using standard manifold for distance check base
standard_manifold = b02['sub_patterns_registry'][0]['manifold_data']

mean_vec = np.array(list(standard_manifold['mean_vector'].values()))
cov_inv = np.linalg.inv(np.array(standard_manifold['covariance_matrix']))

def run_router_check(tensor, router_config):
    """Simulates the Safety Gate & Bifurcation Logic"""
    for strategy in router_config['strategies']:
        strategy_name = strategy['target']
        logic = strategy['logic']
        
        # 1. Gate/Rule Check
        passed_rules = True
        gate_logs = []
        
        if logic['condition'] == 'HYBRID':
            for rule in logic['rules']:
                val = tensor[rule['axis']]
                threshold = rule['value']
                
                # Check condition
                passed = False
                if rule['operator'] == 'gt':
                    passed = (val > threshold)
                elif rule['operator'] == 'lt':
                    passed = (val < threshold)
                    
                if not passed:
                    passed_rules = False
                    # Only log Rejections if they are Safety Gates (E < 0.45)
                    # or if it's the specific differentiation logic failing
                    gate_logs.append(f"   [{strategy_name}] Rule Fail: {rule['axis']}={val:.2f} !{rule['operator']} {threshold}")
                    break # Optimization: Start next strategy
                else:
                    gate_logs.append(f"   [{strategy_name}] Rule Pass: {rule['axis']}={val:.2f} {rule['operator']} {threshold}")
        
        if not passed_rules:
            continue # Try next strategy
            
        # 2. Distance Check (Simulated)
        vec = np.array([tensor[axis] for axis in 'EOMSR'])
        dist = mahalanobis(vec, mean_vec, cov_inv)
        threshold = logic['distance_check']['threshold']
        
        if dist <= threshold:
            return strategy['target'], [f"✅ MATCH: {strategy_name} (Dist {dist:.2f})"]
        else:
            # Distance fail is usually fatal for that strategy
            pass
            
    return None, ["❌ NO MATCH FOUND (All Strategies Failed)"]

print("🧪 [B-02 LOAD TEST V1.5.1] Firing Bifurcation Vectors...")

test_cases = [
    {
        "name": "Case A: The Neurotic Poet (身弱伤官)",
        "tensor": {"E": 0.30, "O": 0.70, "M": 0.20, "S": 0.60, "R": 0.10},
        "expected": None # Must be REJECTED by E-Gate
    },
    {
        "name": "Case B: The Guru (伤官配印)",
        "tensor": {"E": 0.75, "O": 0.60, "M": 0.30, "S": 0.40, "R": 0.50},
        # High E/R (0.75), High O (0.60).
        "expected": "SP_B02_AUTHORITY"
    },
    {
        "name": "Case C: The Tycoon (伤官生财)",
        "tensor": {"E": 0.55, "O": 0.60, "M": 0.75, "S": 0.40, "R": 0.20},
        # High M (0.75).
        "expected": "SP_B02_TYCOON"
    }
]

for case in test_cases:
    print(f"\n🔹 Testing: {case['name']}")
    result, logs = run_router_check(case['tensor'], router)
    
    # Simple log or detail?
    if result:
        print(logs[0])
    else:
        print("   ❌ REJECTED (Correct for Case A)" if case['expected'] is None else f"   ❌ FAILED (Expected {case['expected']})")

    status = "✅ PASS" if result == case['expected'] else f"❌ FAIL (Got {result})"
    print(f"   RESULT: {status}")

print("\n🏁 Validation Complete.")
