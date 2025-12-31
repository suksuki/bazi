import json
import numpy as np
from scipy.spatial.distance import mahalanobis

INPUT_FILE = "core/subjects/holographic_pattern/mining_cache/a01_tier_a_seeds.json"
OUTPUT_FILE = "scripts/a01_step4_audit_report.json"
REGISTRY_FRAGMENT = "core/subjects/holographic_pattern/registry_fragment_a01.json"

print("🕵️ [A-01 AUDIT] Auditing for Singularities...")

# Load Data
with open(INPUT_FILE, 'r') as f:
    seeds = json.load(f)['seeds']
    
with open(REGISTRY_FRAGMENT, 'r') as f:
    fragment = json.load(f)
    manifold = fragment['feature_anchors']['standard_manifold']
    mean_vec = np.array(list(manifold['mean_vector'].values()))
    cov_inv = np.linalg.inv(np.array(manifold['covariance_matrix']))

audit_results = {
    "SP_A01_STANDARD": [],
    "SP_A01_OVERCONTROL": []
}

for seed in seeds:
    t = seed['tensor']
    vec = np.array([t['E'], t['O'], t['M'], t['S'], t['R']])
    
    # 1. Mahalanobis Distance (Deviation from Standard)
    dist = mahalanobis(vec, mean_vec, cov_inv)
    
    # 2. Heuristic Rules
    
    # [Singularity X1] "The Rigid" (Over-controlled)
    # Extremely High Order, Low Entropy
    if t['O'] > 0.70 and t['S'] < 0.15:
        audit_results["SP_A01_OVERCONTROL"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })
    else:
        # Standard Judge
        audit_results["SP_A01_STANDARD"].append({
            "uid": seed['uid'],
            "dist": dist,
            "tensor": t
        })

print(f"📊 Audit Results:")
print(f"   - Standard Bureaucrats: {len(audit_results['SP_A01_STANDARD'])}")
print(f"   - Rigid/Over-controllers: {len(audit_results['SP_A01_OVERCONTROL'])}")

# Generate Sub-Pattern Specs
sub_patterns = [
    {
        "id": "SP_A01_STANDARD",
        "name": "The Bureaucrat (标准正官)",
        "type": "DEFAULT",
        "manifold_data": fragment['feature_anchors']['standard_manifold']
    },
    {
        "id": "SP_A01_OVERCONTROL",
        "name": "The Rigid (清官/僵化)",
        "type": "SINGULARITY",
        "description": "Excessive Order leading to brittleness. Resistant to change.",
        "matrix_override": {
            "transfer_matrix": {
                "S_row": {
                    "Seven_Killings": 2.0  # Extremely sensitive to deviation
                },
                "O_row": {
                    "Direct_Officer": 2.5 # Super-saturated Authority
                }
            }
        },
        "manifold_data": {
            # Approximate from detected samples
             "mean_vector": fragment['feature_anchors']['standard_manifold']['mean_vector'] # Placeholder
        }
    }
]

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump({"audit_stats": {k: len(v) for k,v in audit_results.items()}, "sub_patterns": sub_patterns}, f, indent=2, ensure_ascii=False)

print(f"✅ Audit Spec Generated: {OUTPUT_FILE}")
