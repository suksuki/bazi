import json
import numpy as np
from scipy.spatial.distance import mahalanobis

# Mock Registry Loader (Simulating Runtime Logic)
with open("core/subjects/holographic_pattern/registry.json", 'r') as f:
    registry = json.load(f)

a01 = registry['patterns']['A-01']
router = a01['matching_router']
standard_manifold = a01['sub_patterns_registry'][0]['manifold_data']

# Prepare Manifold Calc
mean_vec = np.array(list(standard_manifold['mean_vector'].values()))
cov_inv = np.linalg.inv(np.array(standard_manifold['covariance_matrix']))

def run_router_check(tensor, router_config):
    """Simulates the Safety Gate Logic"""
    for strategy in router_config['strategies']:
        # 1. Gate Check
        passed_gate = True
        gate_logs = []
        
        logic = strategy['logic']
        if logic['condition'] == 'HYBRID':
            for rule in logic['rules']:
                val = tensor[rule['axis']]
                threshold = rule['value']
                desc = rule.get('description', '')
                
                if rule['operator'] == 'gt':
                    if not (val > threshold): 
                        gate_logs.append(f"❌ REJECT: {rule['axis']}={val:.2f} <= {threshold} ({desc})")
                        passed_gate = False
                    else:
                        gate_logs.append(f"✅ PASS: {rule['axis']}={val:.2f} > {threshold}")
                        
        if not passed_gate:
            return None, gate_logs
            
        # 2. Distance Check (Simulated)
        vec = np.array([tensor[axis] for axis in 'EOMSR'])
        dist = mahalanobis(vec, mean_vec, cov_inv)
        threshold = logic['distance_check']['threshold']
        
        if dist <= threshold:
            return strategy['target'], [f"✅ DISTANCE: {dist:.2f} <= {threshold}"]
        else:
            return None, [f"❌ DISTANCE: {dist:.2f} > {threshold} (Too far from Manifold)"]
            
    return None, ["❌ NO MATCH"]

print("🧪 [A-01 LOAD TEST V1.5.1] Firing Test Vectors...")

test_cases = [
    {
        "name": "Case A: The Judge (大法官)",
        "tensor": {"E": 0.65, "O": 0.65, "M": 0.40, "S": 0.10, "R": 0.30},
        "expected": "SP_A01_STANDARD"
    },
    {
        "name": "Case B: The Puppet (傀儡/身弱杀重)",
        "tensor": {"E": 0.30, "O": 0.70, "M": 0.20, "S": 0.10, "R": 0.20},
        "expected": None # Should be rejected by Safety Gate
    },
    {
        "name": "Case C: The Rebel (伤官见官)",
        "tensor": {"E": 0.60, "O": 0.50, "M": 0.30, "S": 0.60, "R": 0.20},
        # High S should cause huge Distance deviation or fail logic if we had S-gate (implicit in matrix)
        # Here we test Distance rejection primarily due to Step 3 matrix weights
        "expected": None 
    }
]

for case in test_cases:
    print(f"\n🔹 Testing: {case['name']}")
    result, logs = run_router_check(case['tensor'], router)
    
    for log in logs:
        print(f"   {log}")
        
    status = "✅ PASS" if result == case['expected'] else f"❌ FAIL (Got {result})"
    print(f"   RESULT: {status}")

print("\n🏁 Validation Complete.")
